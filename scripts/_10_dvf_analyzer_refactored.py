# scripts/_10_dvf_analyzer.py

import pandas as pd
import numpy as np
import requests
import io
from pathlib import Path
from typing import Optional, List
import pydeck as pdk

class DVFAnalyzer:
    """
    Analyzes DVF (Demandes de Valeurs Foncières) data at scale.
    Handles multi-year datasets with efficient geocoding.
    """
    
    def __init__(self, data_dir: str = "/home/greg/code/gregso10/financial_models/real_estate/data"):
        self.data_dir = Path(data_dir)
        self.df_raw: Optional[pd.DataFrame] = None
        self.df_clean: Optional[pd.DataFrame] = None
        self.df_geocoded: Optional[pd.DataFrame] = None
        
    def load_all_files(self) -> pd.DataFrame:
        """Load all DVF txt files from data directory."""
        print("Loading DVF files...")
        
        txt_files = list(self.data_dir.rglob("*.txt"))
        print(f"Found {len(txt_files)} files")
        
        dfs = []
        for file in txt_files:
            try:
                df = pd.read_csv(file, sep="|", low_memory=False)
                # Extract year from filename or date
                df['source_file'] = file.name
                dfs.append(df)
                print(f"  Loaded {file.name}: {len(df):,} rows")
            except Exception as e:
                print(f"  Error loading {file.name}: {e}")
        
        self.df_raw = pd.concat(dfs, ignore_index=True)
        print(f"\nTotal raw records: {len(self.df_raw):,}")
        return self.df_raw
    
    def preprocess(self) -> pd.DataFrame:
        """Preprocess DVF data: create IDs, remove duplicates, clean data."""
        print("\nPreprocessing data...")
        df = self.df_raw.copy()
        
        # 1. Extract year from date
        df['Date mutation'] = pd.to_datetime(df['Date mutation'], format='%d/%m/%Y', errors='coerce')
        df['mutation_year'] = df['Date mutation'].dt.year
        
        # 2. Create unique mutation ID (WITH year for time series)
        df['id_mutation'] = (
            df['mutation_year'].astype(str) + '_' +
            df['Date mutation'].astype(str) + '_' + 
            df['Valeur fonciere'].astype(str) + '_' + 
            df['No disposition'].astype(str) + '_' + 
            df['Code commune'].astype(str)
        )
        
        # 3. Filter to sales only
        df = df[df['Nature mutation'] == 'Vente'].copy()
        print(f"  After filtering to sales: {len(df):,} rows")
        
        # 4. Aggregate by mutation (sum surfaces, build address)
        def analyze_mutation(group):
            first = group.iloc[0]
            
            # Build address
            num = str(int(first['No voie'])) if pd.notna(first['No voie']) else ""
            type_voie = str(first['Type de voie']) if pd.notna(first['Type de voie']) else ""
            voie = str(first['Voie']) if pd.notna(first['Voie']) else ""
            code_postal = str(int(first['Code postal'])) if pd.notna(first['Code postal']) else ""
            commune = str(first['Commune']) if pd.notna(first['Commune']) else ""
            adresse_complete = f"{num} {type_voie} {voie} {code_postal} {commune}".strip()
            
            return pd.Series({
                'mutation_year': first['mutation_year'],
                'valeur_fonciere': float(str(first['Valeur fonciere']).replace(',', '.')),
                'adresse_complete': adresse_complete,
                'surface_totale': group['Surface reelle bati'].sum(),
                'nb_lots': len(group),
                'type_local': first.get('Type local', None)
            })
        
        self.df_clean = df.groupby('id_mutation', as_index=False).apply(analyze_mutation).reset_index(drop=True)
        
        # 5. Remove invalid data
        self.df_clean = self.df_clean[
            (self.df_clean['valeur_fonciere'] > 1) &
            (self.df_clean['surface_totale'] > 1) &
            (self.df_clean['adresse_complete'].str.len() > 10)
        ].copy()
        
        # 6. Calculate price per sqm
        self.df_clean['prix_m2'] = self.df_clean['valeur_fonciere'] / self.df_clean['surface_totale']
        
        print(f"  Final clean records: {len(self.df_clean):,}")
        print(f"  Years covered: {self.df_clean['mutation_year'].min()} - {self.df_clean['mutation_year'].max()}")
        
        return self.df_clean
    
    def geocode_smart(self) -> pd.DataFrame:
        """Geocode ONLY unique addresses, then merge back."""
        print("\nSmart geocoding...")
        
        # 1. Get unique addresses
        unique_addresses = self.df_clean[['adresse_complete']].drop_duplicates()
        print(f"  Unique addresses to geocode: {len(unique_addresses):,}")
        
        # 2. Geocode only unique addresses
        df_geo_unique = self._geocode_bulk(unique_addresses, address_col='adresse_complete')
        
        if df_geo_unique is None or len(df_geo_unique) == 0:
            print("  Geocoding failed")
            return self.df_clean
        
        # 3. Keep only successful geocodes
        df_geo_unique = df_geo_unique.dropna(subset=['latitude', 'longitude'])
        print(f"  Successfully geocoded: {len(df_geo_unique):,}")
        
        # 4. Merge back to full dataset
        self.df_geocoded = self.df_clean.merge(
            df_geo_unique[['adresse_complete', 'latitude', 'longitude', 'result_score']],
            on='adresse_complete',
            how='left'
        )
        
        geocoded_count = self.df_geocoded['latitude'].notna().sum()
        print(f"  Total records with coordinates: {geocoded_count:,} ({geocoded_count/len(self.df_geocoded)*100:.1f}%)")
        
        return self.df_geocoded
    
    def _geocode_bulk(self, df: pd.DataFrame, address_col: str = 'adresse_complete') -> pd.DataFrame:
        """Call BAN API for bulk geocoding."""
        csv_buffer = io.BytesIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8')
        csv_buffer.seek(0)
        
        url = "https://api-adresse.data.gouv.fr/search/csv/"
        files = {'data': ('data.csv', csv_buffer)}
        data = {
            'columns': address_col,
            'result_columns': ['latitude', 'longitude', 'result_score']
        }
        
        try:
            response = requests.post(url, files=files, data=data, timeout=300)
            response.raise_for_status()
            return pd.read_csv(io.StringIO(response.text))
        except Exception as e:
            print(f"  Geocoding error: {e}")
            return df
    
    def filter_for_visualization(self, 
                                 year: Optional[int] = None,
                                 min_price: float = 0,
                                 max_price: float = float('inf'),
                                 city: Optional[str] = None) -> pd.DataFrame:
        """Filter dataset for visualization."""
        df = self.df_geocoded.copy()
        
        if year:
            df = df[df['mutation_year'] == year]
        if min_price > 0:
            df = df[df['valeur_fonciere'] >= min_price]
        if max_price < float('inf'):
            df = df[df['valeur_fonciere'] <= max_price]
        if city:
            df = df[df['adresse_complete'].str.contains(city, case=False, na=False)]
        
        print(f"Filtered to {len(df):,} records for visualization")
        return df
    
    def create_3d_visualization(self, df: pd.DataFrame, output_file: str = "dvf_3d_map.html"):
        """Generate 3D pydeck visualization."""
        # Color gradient
        max_val = df['valeur_fonciere'].max()
        log_max = np.log1p(max_val)
        
        df['color'] = df['valeur_fonciere'].apply(
            lambda x: self._get_heatmap_color(np.log1p(x) / log_max)
        )
        
        # View configuration
        view_state = pdk.ViewState(
            latitude=df['latitude'].mean(),
            longitude=df['longitude'].mean(),
            zoom=13,
            pitch=60,
            bearing=45
        )
        
        # Column layer
        layer = pdk.Layer(
            "ColumnLayer",
            data=df,
            get_position=["longitude", "latitude"],
            get_elevation="valeur_fonciere",
            radius=25,
            diskResolution=4,  # Square buildings
            angle=45,
            elevation_scale=0.001,
            get_fill_color="color",
            pickable=True,
            extruded=True,
            auto_highlight=True,
            material={
                "ambient": 0.2,
                "diffuse": 0.8,
                "shininess": 32,
                "specularColor": [255, 255, 255]
            }
        )
        
        # Render
        deck = pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
            tooltip={"html": "<b>Prix:</b> {valeur_fonciere} €<br/>{adresse_complete}<br/><b>Surface:</b> {surface_totale} m²<br/><b>Prix/m²:</b> {prix_m2:.0f} €"}
        )
        
        deck.to_html(output_file)
        print(f"Saved visualization to {output_file}")
    
    @staticmethod
    def _get_heatmap_color(normalized_value: float) -> List[int]:
        """Blue -> Cyan -> Green -> Yellow -> Red gradient."""
        v = max(0, min(1, normalized_value))
        
        if v < 0.25:
            return [0, int(v * 4 * 255), 255, 180]
        elif v < 0.5:
            return [0, 255, int(255 - (v - 0.25) * 4 * 255), 180]
        elif v < 0.75:
            return [int((v - 0.5) * 4 * 255), 255, 0, 180]
        else:
            return [255, int(255 - (v - 0.75) * 4 * 255), 0, 180]


# === USAGE ===
if __name__ == "__main__":
    analyzer = DVFAnalyzer()
    
    # Pipeline
    analyzer.load_all_files()
    analyzer.preprocess()
    analyzer.geocode_smart()
    
    # Visualize 2024 data
    df_viz = analyzer.filter_for_visualization(
        year=2024,
        min_price=50000,
        max_price=1000000,
        city="Paris"
    )
    
    analyzer.create_3d_visualization(df_viz, "paris_2024_3d.html")
    
    # Save processed data for ML
    analyzer.df_geocoded.to_parquet("dvf_processed.parquet", index=False)
    print("\nSaved processed data for ML")