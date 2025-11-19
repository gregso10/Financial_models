# In file: scripts/_10_dvf_analyzer.py

import pandas as pd
import numpy as np
import pydeck as pdk
import requests
import io
from typing import Optional, Dict, List


class DVFAnalyzer:
    """
    Analyzes and visualizes French real estate transaction data (DVF).
    Handles data cleaning, geocoding, and 3D map generation.
    Auto-loads all .txt files from data directory.
    """
    
    def __init__(self, data_dir: str = None):
        """
        Initialize analyzer with DVF data directory.
        
        Args:
            data_dir: Path to directory containing DVF .txt files.
                     Defaults to ../data/ relative to script location.
        """
        if data_dir is None:
            # Default to data folder in project root
            import os
            script_dir = os.path.dirname(os.path.abspath(__file__))
            self.data_dir = os.path.join(os.path.dirname(script_dir), 'data')
        else:
            self.data_dir = data_dir
        
        self.raw_data: Optional[pd.DataFrame] = None
        self.cleaned_data: Optional[pd.DataFrame] = None  # FIXED: renamed from clean_data
        self.geocoded_data: Optional[pd.DataFrame] = None
        self.txt_files: List[str] = []
    
    def load_data(self) -> pd.DataFrame:
        """
        Load and concatenate all DVF .txt files from data directory.
        
        Returns:
            Combined DataFrame from all files
        """
        import os
        import glob
        
        # Find all .txt files
        pattern = os.path.join(self.data_dir, "*.txt")
        self.txt_files = glob.glob(pattern)
        
        if not self.txt_files:
            raise FileNotFoundError(f"No .txt files found in {self.data_dir}")
        
        print(f"Found {len(self.txt_files)} DVF file(s):")
        for f in self.txt_files:
            print(f"  - {os.path.basename(f)}")
        
        # Load and concatenate all files
        dfs = []
        for file_path in self.txt_files:
            try:
                df = pd.read_csv(file_path, sep="|", low_memory=False)
                dfs.append(df)
                print(f"  ✓ Loaded {len(df):,} rows from {os.path.basename(file_path)}")
            except Exception as e:
                print(f"  ✗ Error loading {os.path.basename(file_path)}: {e}")
        
        if not dfs:
            raise ValueError("Failed to load any DVF files")
        
        # Concatenate all dataframes
        self.raw_data = pd.concat(dfs, ignore_index=True)
        print(f"\n📊 Total loaded: {len(self.raw_data):,} raw records")
        
        return self.raw_data
    
    def clean_data(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Clean and aggregate DVF data by mutation.
        Groups parcels by transaction, builds full addresses.
        
        Args:
            df: Optional DataFrame to clean. If None, uses self.raw_data
        """
        # Use provided df or fall back to self.raw_data
        if df is None:
            if self.raw_data is None:
                raise ValueError("Load data first using load_data()")
            df = self.raw_data.copy()[0:10000]
        else:
            df = df.copy()[0:10000]
        
        # Create mutation ID
        df['id_mutation'] = (
            df['Date mutation'].astype(str) + '_' + 
            df['Valeur fonciere'].astype(str) + '_' + 
            df['No disposition'].astype(str) + '_' + 
            df['Code commune'].astype(str)
        )
        
        def analyze_mutation(group):
            """Aggregate mutation data - extract price, address, surface."""
            if len(group) == 0:
                return None  # Will be filtered out
            
            first = group.iloc[0]
            
            # Build full address with safe access
            num = str(int(first['No voie'])) if pd.notna(first['No voie']) and first['No voie'] != '' else ""
            type_voie = str(first['Type de voie']) if pd.notna(first['Type de voie']) and first['Type de voie'] != '' else ""
            voie = str(first['Voie']) if pd.notna(first['Voie']) and first['Voie'] != '' else ""
            code_postal = str(int(first['Code postal'])) if pd.notna(first['Code postal']) and first['Code postal'] != '' else ""
            commune = str(first['Commune']) if pd.notna(first['Commune']) and first['Commune'] != '' else ""
            
            # Clean up spacing
            full_address = " ".join([num, type_voie, voie, code_postal, commune]).strip()
            full_address = " ".join(full_address.split())  # Remove extra spaces
            
            # Parse price safely
            try:
                price_str = str(first['Valeur fonciere']).replace(',', '.').replace(' ', '')
                valeur = float(price_str) if price_str else 0.0
            except (ValueError, TypeError):
                valeur = 0.0
            
            # Sum surfaces safely
            try:
                surface = group['Surface reelle bati'].fillna(0).sum()
            except:
                surface = 0.0
            
            return pd.Series({
                'valeur_fonciere': valeur,
                'adresse_complete': full_address,
                'surface_totale': surface
            })
        
        # Filter sales only
        sales_only = df[df['Nature mutation'] == 'Vente']
        
        if len(sales_only) == 0:
            print("Warning: No sales found in dataset")
            self.cleaned_data = pd.DataFrame(columns=['id_mutation', 'valeur_fonciere', 'adresse_complete', 'surface_totale'])
            return self.cleaned_data
        
        # Apply aggregation - use apply with proper arguments
        print(f"Aggregating {len(sales_only):,} records into transactions...")
        
        # Group and apply - this is the fix
        grouped = sales_only.groupby('id_mutation', group_keys=False)
        aggregated = grouped.apply(analyze_mutation, include_groups=False)
        
        # Handle None results from apply
        if aggregated is None or len(aggregated) == 0:
            print("ERROR: Groupby apply returned None or empty")
            self.cleaned_data = pd.DataFrame(columns=['id_mutation', 'valeur_fonciere', 'adresse_complete', 'surface_totale'])
            return self.cleaned_data
        
        # Reset index to get id_mutation as a column
        self.cleaned_data = aggregated.reset_index()
        
        # Validate and filter out invalid entries
        if 'valeur_fonciere' in self.cleaned_data.columns:
            initial_count = len(self.cleaned_data)
            self.cleaned_data = self.cleaned_data[self.cleaned_data['valeur_fonciere'] > 0]
            self.cleaned_data = self.cleaned_data[self.cleaned_data['adresse_complete'] != '']
            filtered_count = len(self.cleaned_data)
            
            if filtered_count < initial_count:
                print(f"Filtered out {initial_count - filtered_count} invalid transactions")
        
        print(f"✓ Cleaned data: {len(self.cleaned_data):,} valid transactions")
        if len(self.cleaned_data) > 0:
            print(f"Sample:\n{self.cleaned_data.head(2)}")
        
        return self.cleaned_data
    
    def geocode_bulk(self, address_col: str = 'adresse_complete', chunk_size: int = 5000) -> pd.DataFrame:
        """
        Bulk geocode addresses using French government BAN API.
        Processes in chunks to respect API limits.
        
        Args:
            address_col: Name of column containing addresses
            chunk_size: Number of addresses per API call (default 5000)
            
        Returns:
            DataFrame with latitude/longitude columns added
        """
        if self.cleaned_data is None:
            raise ValueError("Clean data first using clean_data()")
        
        total_addresses = len(self.cleaned_data)
        print(f"Geocoding {total_addresses:,} addresses in chunks of {chunk_size:,}...")
        
        # Calculate number of chunks
        num_chunks = (total_addresses + chunk_size - 1) // chunk_size
        print(f"Processing {num_chunks} chunks...")
        
        geocoded_chunks = []
        
        for i in range(num_chunks):
            start_idx = i * chunk_size
            end_idx = min((i + 1) * chunk_size, total_addresses)
            chunk_df = self.cleaned_data.iloc[start_idx:end_idx].copy()
            
            print(f"  Chunk {i+1}/{num_chunks}: Geocoding addresses {start_idx:,} to {end_idx:,}...")
            
            try:
                # Convert chunk to CSV in memory
                csv_buffer = io.BytesIO()
                chunk_df.to_csv(csv_buffer, index=False, encoding='utf-8')
                csv_buffer.seek(0)
                
                # API request
                url = "https://api-adresse.data.gouv.fr/search/csv/"
                files = {'data': ('data.csv', csv_buffer)}
                data = {
                    'columns': address_col,
                    'result_columns': ['latitude', 'longitude', 'result_score']
                }
                
                response = requests.post(url, files=files, data=data, timeout=60)
                response.raise_for_status()
                
                # Parse response
                chunk_result = pd.read_csv(io.StringIO(response.text))
                geocoded_chunks.append(chunk_result)
                
                print(f"    ✓ Geocoded {len(chunk_result):,} addresses")
                
                # Small delay to be polite to API
                if i < num_chunks - 1:
                    import time
                    time.sleep(0.5)
                    
            except Exception as e:
                print(f"    ✗ Error in chunk {i+1}: {e}")
                # Add chunk without geocoding
                geocoded_chunks.append(chunk_df)
        
        # Combine all chunks
        print("Combining chunks...")
        self.geocoded_data = pd.concat(geocoded_chunks, ignore_index=True)
        
        # Clean empty results
        initial_count = len(self.geocoded_data)
        self.geocoded_data = self.geocoded_data.dropna(subset=['latitude', 'longitude'])
        
        print(f"✓ Successfully geocoded {len(self.geocoded_data):,}/{initial_count:,} addresses")
        return self.geocoded_data
    
    def add_heatmap_colors(self) -> pd.DataFrame:
        """
        Add spectral heatmap colors based on property values.
        Blue (low) -> Cyan -> Green -> Yellow -> Red (high)
        """
        if self.geocoded_data is None:
            raise ValueError("Geocode data first using geocode_bulk()")
        
        def get_heatmap_color(normalized_value):
            """Blue -> Cyan -> Green -> Yellow -> Red gradient."""
            v = max(0, min(1, normalized_value))
            
            if v < 0.25:
                # Blue to Cyan
                return [0, int(v * 4 * 255), 255, 180]
            elif v < 0.5:
                # Cyan to Green
                return [0, 255, int(255 - (v - 0.25) * 4 * 255), 180]
            elif v < 0.75:
                # Green to Yellow
                return [int((v - 0.5) * 4 * 255), 255, 0, 180]
            else:
                # Yellow to Red
                return [255, int(255 - (v - 0.75) * 4 * 255), 0, 180]
        
        # Use log scale for better distribution
        max_val = self.geocoded_data['valeur_fonciere'].max()
        log_max = np.log1p(max_val)
        
        self.geocoded_data['color_spectral'] = self.geocoded_data['valeur_fonciere'].apply(
            lambda x: get_heatmap_color(np.log1p(x) / log_max)
        )
        
        return self.geocoded_data
    
    def create_3d_map(self, output_file: Optional[str] = None) -> pdk.Deck:
        """
        Create 3D building-style map visualization.
        Height represents property value, color represents heatmap.
        
        Args:
            output_file: Optional path to save HTML file
            
        Returns:
            pdk.Deck object
        """
        if self.geocoded_data is None or 'color_spectral' not in self.geocoded_data.columns:
            raise ValueError("Add heatmap colors first using add_heatmap_colors()")
        
        # View configuration
        view_state = pdk.ViewState(
            latitude=self.geocoded_data['latitude'].mean(),
            longitude=self.geocoded_data['longitude'].mean(),
            zoom=13,
            pitch=60,
            bearing=45
        )
        
        # 3D column layer (square buildings)
        column_layer = pdk.Layer(
            "ColumnLayer",
            data=self.geocoded_data,
            get_position=["longitude", "latitude"],
            get_elevation="valeur_fonciere",
            radius=25,
            disk_resolution=4,  # 4 sides = square
            angle=45,
            elevation_scale=0.001,
            get_fill_color="color_spectral",
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
        
        # Create deck
        deck = pdk.Deck(
            layers=[column_layer],
            initial_view_state=view_state,
            map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
            tooltip={"html": "<b>Price:</b> €{valeur_fonciere:,}<br/>{adresse_complete}"}
        )
        
        # Save to HTML if requested
        if output_file:
            deck.to_html(output_file)
            print(f"Map saved to {output_file}")
        
        return deck
    
    def get_summary_stats(self) -> Dict[str, any]:
        """Get summary statistics of the dataset."""
        if self.geocoded_data is None:
            return {}
        
        return {
            'total_transactions': len(self.geocoded_data),
            'mean_price': self.geocoded_data['valeur_fonciere'].mean(),
            'median_price': self.geocoded_data['valeur_fonciere'].median(),
            'min_price': self.geocoded_data['valeur_fonciere'].min(),
            'max_price': self.geocoded_data['valeur_fonciere'].max(),
            'total_volume': self.geocoded_data['valeur_fonciere'].sum()
        }
    
    def run_full_pipeline(self) -> 'DVFAnalyzer':
        """
        Run complete analysis pipeline:
        1. Load all data files
        2. Clean and aggregate
        3. Geocode addresses
        4. Add heatmap colors
        
        Returns:
            self (for chaining)
        """
        print("=== Starting DVF Analysis Pipeline ===\n")
        
        try:
            print("Step 1/4: Loading data files...")
            self.load_data()
            
            if self.raw_data is None or len(self.raw_data) == 0:
                raise ValueError("No data loaded - check data directory and file format")
            
            print(f"✓ Loaded {len(self.raw_data):,} raw records")
            
        except Exception as e:
            print(f"❌ Error in Step 1 (Loading): {e}")
            raise
        
        try:
            print("\nStep 2/4: Cleaning and aggregating...")
            result = self.clean_data()
            
            if result is None or len(result) == 0:
                raise ValueError("No data after cleaning - check data format")
            
        except Exception as e:
            print(f"❌ Error in Step 2 (Cleaning): {e}")
            import traceback
            traceback.print_exc()
            raise
        
        try:
            print("\nStep 3/4: Geocoding addresses...")
            self.geocode_bulk()
            
            if self.geocoded_data is None or len(self.geocoded_data) == 0:
                raise ValueError("No data after geocoding")
            
        except Exception as e:
            print(f"❌ Error in Step 3 (Geocoding): {e}")
            raise
        
        try:
            print("\nStep 4/4: Adding heatmap colors...")
            self.add_heatmap_colors()
        except Exception as e:
            print(f"❌ Error in Step 4 (Colors): {e}")
            raise
        
        print("\n=== Pipeline Complete ===")
        stats = self.get_summary_stats()
        print(f"Final dataset: {stats['total_transactions']:,} geocoded transactions")
        print(f"Price range: €{stats['min_price']:,.0f} - €{stats['max_price']:,.0f}")
        print(f"Median: €{stats['median_price']:,.0f}")
        
        return self


# Example usage
if __name__ == "__main__":
    # Option 1: Use default data directory (../data/)
    analyzer = DVFAnalyzer()
    analyzer.run_full_pipeline()
    
    # Option 2: Specify custom directory
    # analyzer = DVFAnalyzer(data_dir="/custom/path/to/data")
    # analyzer.run_full_pipeline()
    
    # Generate map
    deck = analyzer.create_3d_map(output_file="dvf_3d_map.html")
    
    # Stats
    stats = analyzer.get_summary_stats()
    print(f"\nMedian price: €{stats['median_price']:,.2f}")
    print(f"Total volume: €{stats['total_volume']:,.2f}")