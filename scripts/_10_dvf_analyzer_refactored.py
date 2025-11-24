# scripts/_10_dvf_analyzer.py

import pandas as pd
import numpy as np
import requests
import io
import sqlite3
from pathlib import Path
from typing import Optional, List, Generator
import pydeck as pdk

class DVFAnalyzer:
    """
    Memory-efficient DVF analyzer for datasets too large for RAM.
    Uses chunked processing + SQLite for intermediate storage.
    """
    
    def __init__(self, 
                 data_dir: str = "/home/greg/code/gregso10/financial_models/real_estate/data",
                 db_path: str = "dvf_processed.db"):
        self.data_dir = Path(data_dir)
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        
        # Essential columns only (reduce from 43 to ~15)
        self.essential_cols = [
            'Date mutation', 'Nature mutation', 'Valeur fonciere', 
            'No voie', 'Type de voie', 'Voie', 'Code postal', 'Commune',
            'Surface reelle bati', 'No disposition', 'Code commune', 'Type local'
        ]
    
    def load_and_process_incremental(self, chunksize: int = 100000):
        """Load files one by one, process in chunks, write to SQLite."""
        print("Processing files incrementally...")
        
        # Create table
        self._create_tables()
        
        txt_files = sorted(self.data_dir.rglob("*.txt"))
        total_rows = 0
        
        for file_idx, file in enumerate(txt_files, 1):
            print(f"\n[{file_idx}/{len(txt_files)}] Processing {file.name}...")
            
            try:
                # Read in chunks
                for chunk_idx, chunk in enumerate(pd.read_csv(
                    file, 
                    sep="|", 
                    usecols=lambda x: x in self.essential_cols,
                    chunksize=chunksize,
                    low_memory=False
                ), 1):
                    
                    # Immediate filtering to reduce memory
                    chunk = chunk[chunk['Nature mutation'] == 'Vente'].copy()
                    
                    if len(chunk) == 0:
                        continue
                    
                    # Extract year
                    chunk['Date mutation'] = pd.to_datetime(
                        chunk['Date mutation'], 
                        format='%d/%m/%Y', 
                        errors='coerce'
                    )
                    chunk['mutation_year'] = chunk['Date mutation'].dt.year
                    
                    # Create mutation ID
                    chunk['id_mutation'] = (
                        chunk['mutation_year'].astype(str) + '_' +
                        chunk['Date mutation'].dt.strftime('%Y%m%d').fillna('') + '_' +
                        chunk['Valeur fonciere'].astype(str) + '_' +
                        chunk['No disposition'].astype(str) + '_' +
                        chunk['Code commune'].astype(str)
                    )
                    
                    # Build address
                    chunk['adresse_complete'] = (
                        chunk['No voie'].fillna('').astype(str) + ' ' +
                        chunk['Type de voie'].fillna('') + ' ' +
                        chunk['Voie'].fillna('') + ' ' +
                        chunk['Code postal'].fillna('').astype(str) + ' ' +
                        chunk['Commune'].fillna('')
                    ).str.strip()
                    
                    # Keep only needed columns
                    chunk_slim = chunk[[
                        'id_mutation', 'mutation_year', 'Valeur fonciere',
                        'Surface reelle bati', 'adresse_complete', 'Type local'
                    ]].copy()
                    
                    # Write to SQLite
                    chunk_slim.to_sql('mutations_raw', self.conn, if_exists='append', index=False)
                    
                    total_rows += len(chunk_slim)
                    
                    if chunk_idx % 10 == 0:
                        print(f"  Chunk {chunk_idx}: {total_rows:,} rows accumulated")
                    
                    # Force garbage collection
                    del chunk, chunk_slim
                    
            except Exception as e:
                print(f"  Error: {e}")
                continue
        
        print(f"\nTotal raw sales loaded: {total_rows:,}")
        self.conn.commit()
    
    def aggregate_mutations(self):
        """Aggregate by mutation ID using SQL (memory efficient)."""
        print("\nAggregating mutations in SQL...")
        
        query = """
        CREATE TABLE IF NOT EXISTS mutations_agg AS
        SELECT 
            id_mutation,
            MAX(mutation_year) as mutation_year,
            MAX(CAST(REPLACE("Valeur fonciere", ',', '.') AS REAL)) as valeur_fonciere,
            SUM(CAST("Surface reelle bati" AS REAL)) as surface_totale,
            MAX(adresse_complete) as adresse_complete,
            MAX("Type local") as type_local,
            COUNT(*) as nb_lots
        FROM mutations_raw
        WHERE 
            CAST(REPLACE("Valeur fonciere", ',', '.') AS REAL) > 0
            AND CAST("Surface reelle bati" AS REAL) > 0
            AND LENGTH(adresse_complete) > 10
        GROUP BY id_mutation
        """
        
        self.conn.execute("DROP TABLE IF EXISTS mutations_agg")
        self.conn.execute(query)
        self.conn.commit()
        
        count = self.conn.execute("SELECT COUNT(*) FROM mutations_agg").fetchone()[0]
        print(f"  Aggregated mutations: {count:,}")
        
        # Add price per sqm
        self.conn.execute("""
            ALTER TABLE mutations_agg ADD COLUMN prix_m2 REAL
        """)
        self.conn.execute("""
            UPDATE mutations_agg 
            SET prix_m2 = valeur_fonciere / NULLIF(surface_totale, 0)
        """)
        self.conn.commit()
    
    def geocode_smart_batched(self, batch_size: int = 10000):
        """Geocode in batches to avoid memory overflow."""
        print("\nSmart batched geocoding...")
        
        # Create geocoding table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS geocoded_addresses (
                adresse_complete TEXT PRIMARY KEY,
                latitude REAL,
                longitude REAL,
                result_score REAL
            )
        """)
        
        # Get unique addresses not yet geocoded
        query = """
        SELECT DISTINCT adresse_complete 
        FROM mutations_agg 
        WHERE adresse_complete NOT IN (SELECT adresse_complete FROM geocoded_addresses)
        """
        
        total_to_geocode = self.conn.execute(
            f"SELECT COUNT(DISTINCT adresse_complete) FROM mutations_agg"
        ).fetchone()[0]
        
        print(f"  Total unique addresses: {total_to_geocode:,}")
        
        batch_num = 0
        while True:
            # Get next batch
            df_batch = pd.read_sql_query(
                f"{query} LIMIT {batch_size}", 
                self.conn
            )
            
            if len(df_batch) == 0:
                break
            
            batch_num += 1
            print(f"  Batch {batch_num}: Geocoding {len(df_batch):,} addresses...")
            
            # Geocode batch
            df_geo = self._geocode_bulk(df_batch, 'adresse_complete')
            
            if df_geo is not None and 'latitude' in df_geo.columns:
                df_geo = df_geo[['adresse_complete', 'latitude', 'longitude', 'result_score']]
                df_geo.to_sql('geocoded_addresses', self.conn, if_exists='append', index=False)
                self.conn.commit()
                
                success_rate = df_geo['latitude'].notna().mean()
                print(f"    Success rate: {success_rate*100:.1f}%")
            
            del df_batch, df_geo
        
        # Show final stats
        geocoded_count = self.conn.execute(
            "SELECT COUNT(*) FROM geocoded_addresses WHERE latitude IS NOT NULL"
        ).fetchone()[0]
        print(f"\n  Total addresses geocoded: {geocoded_count:,}")
    
    def export_to_parquet(self, output_dir: str = "dvf_parquet"):
        """Export final dataset partitioned by year."""
        print("\nExporting to Parquet...")
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Get year range
        years = pd.read_sql_query(
            "SELECT DISTINCT mutation_year FROM mutations_agg ORDER BY mutation_year",
            self.conn
        )['mutation_year'].tolist()
        
        for year in years:
            print(f"  Exporting year {year}...")
            
            query = """
            SELECT 
                m.id_mutation,
                m.mutation_year,
                m.valeur_fonciere,
                m.surface_totale,
                m.prix_m2,
                m.adresse_complete,
                m.type_local,
                m.nb_lots,
                g.latitude,
                g.longitude,
                g.result_score
            FROM mutations_agg m
            LEFT JOIN geocoded_addresses g ON m.adresse_complete = g.adresse_complete
            WHERE m.mutation_year = ?
            """
            
            df_year = pd.read_sql_query(query, self.conn, params=(year,))
            
            file_path = output_path / f"year={year}.parquet"
            df_year.to_parquet(file_path, index=False, engine='pyarrow')
            
            print(f"    Saved {len(df_year):,} rows")
            del df_year
    
    def _geocode_bulk(self, df: pd.DataFrame, address_col: str) -> Optional[pd.DataFrame]:
        """Call BAN API for bulk geocoding."""
        try:
            csv_buffer = io.BytesIO()
            df.to_csv(csv_buffer, index=False, encoding='utf-8')
            csv_buffer.seek(0)
            
            url = "https://api-adresse.data.gouv.fr/search/csv/"
            files = {'data': ('data.csv', csv_buffer)}
            data = {
                'columns': address_col,
                'result_columns': ['latitude', 'longitude', 'result_score']
            }
            
            response = requests.post(url, files=files, data=data, timeout=300)
            response.raise_for_status()
            return pd.read_csv(io.StringIO(response.text))
        except Exception as e:
            print(f"    Geocoding error: {e}")
            return None
    
    def _create_tables(self):
        """Create SQLite tables."""
        self.conn.execute("DROP TABLE IF EXISTS mutations_raw")
        self.conn.execute("""
            CREATE TABLE mutations_raw (
                id_mutation TEXT,
                mutation_year INTEGER,
                "Valeur fonciere" TEXT,
                "Surface reelle bati" TEXT,
                adresse_complete TEXT,
                "Type local" TEXT
            )
        """)
        self.conn.commit()
    
    def load_for_analysis(self, 
                         year: Optional[int] = None,
                         city: Optional[str] = None,
                         max_rows: int = 100000) -> pd.DataFrame:
        """Load filtered dataset for analysis/visualization."""
        query = """
        SELECT 
            m.mutation_year,
            m.valeur_fonciere,
            m.surface_totale,
            m.prix_m2,
            m.adresse_complete,
            m.type_local,
            g.latitude,
            g.longitude
        FROM mutations_agg m
        LEFT JOIN geocoded_addresses g ON m.adresse_complete = g.adresse_complete
        WHERE g.latitude IS NOT NULL
        """
        
        params = []
        if year:
            query += " AND m.mutation_year = ?"
            params.append(year)
        if city:
            query += " AND m.adresse_complete LIKE ?"
            params.append(f"%{city}%")
        
        query += f" LIMIT {max_rows}"
        
        return pd.read_sql_query(query, self.conn, params=params)
    
    def create_3d_visualization(self, df: pd.DataFrame, output_file: str = "dvf_3d.html"):
        """Generate 3D map (same as before)."""
        max_val = df['valeur_fonciere'].max()
        log_max = np.log1p(max_val)
        df['color'] = df['valeur_fonciere'].apply(
            lambda x: self._get_heatmap_color(np.log1p(x) / log_max)
        )
        
        view_state = pdk.ViewState(
            latitude=df['latitude'].mean(),
            longitude=df['longitude'].mean(),
            zoom=12, pitch=60, bearing=45
        )
        
        layer = pdk.Layer(
            "ColumnLayer",
            data=df,
            get_position=["longitude", "latitude"],
            get_elevation="valeur_fonciere",
            radius=25, diskResolution=4, angle=45,
            elevation_scale=0.001,
            get_fill_color="color",
            pickable=True, extruded=True,
        )
        
        pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
            tooltip={"html": "<b>{valeur_fonciere}€</b><br/>{adresse_complete}<br/>{prix_m2:.0f}€/m²"}
        ).to_html(output_file)
        
        print(f"Saved to {output_file}")
    
    @staticmethod
    def _get_heatmap_color(v: float) -> List[int]:
        """Blue->Green->Yellow->Red gradient."""
        v = max(0, min(1, v))
        if v < 0.25: return [0, int(v*4*255), 255, 180]
        elif v < 0.5: return [0, 255, int(255-(v-0.25)*4*255), 180]
        elif v < 0.75: return [int((v-0.5)*4*255), 255, 0, 180]
        else: return [255, int(255-(v-0.75)*4*255), 0, 180]
    
    def close(self):
        """Close database connection."""
        self.conn.close()


# === USAGE ===
if __name__ == "__main__":
    analyzer = DVFAnalyzer()
    
    # Full pipeline (memory efficient)
    analyzer.load_and_process_incremental(chunksize=50000)  # Adjust based on RAM
    analyzer.aggregate_mutations()
    analyzer.geocode_smart_batched(batch_size=5000)  # Smaller batches
    analyzer.export_to_parquet("dvf_parquet")
    
    # Visualize Paris 2024
    df_viz = analyzer.load_for_analysis(year=2024, city="Paris", max_rows=50000)
    analyzer.create_3d_visualization(df_viz, "paris_2024.html")
    
    analyzer.close()