# scripts/_10_dvf_analyzer.py

import pandas as pd
import sqlite3
import requests
from pathlib import Path
from typing import Optional, List
from difflib import SequenceMatcher
import re

class DVFAnalyzer:
    """
    DVF geocoding using fragmented BAN CSV files.
    """
    
    def __init__(self):
        self.data_dir = Path("data")
        self.dvf_db_path = self.data_dir / "dvf_fresh_local.db"
        self.ban_db_path = self.data_dir / "ban_addresses.db"
        
        self.dvf_conn = sqlite3.connect(self.dvf_db_path)
        self.ban_conn = None
    
    def download_all_ban_csv(self) -> List[Path]:
        """Download all BAN CSV fragments."""
        ban_dir = self.data_dir / "BAN" / "csv"
        ban_dir.mkdir(parents=True, exist_ok=True)
        
        base_url = "https://adresse.data.gouv.fr/data/ban/adresses/latest/csv"
        fragment_numbers = [range(1, 96), "2A", "2B"]
        downloaded_files = []
        
        for num in fragment_numbers:
            filename = f"adresses-{num:02d}.csv.gz"
            file_path = ban_dir / filename
            
            if file_path.exists():
                print(f"✓ Already exists: {filename}")
                downloaded_files.append(file_path)
                continue
            
            url = f"{base_url}/{filename}"
            print(f"\nDownloading: {filename}")
            
            try:
                response = requests.get(url, stream=True, timeout=300)
                
                if response.status_code == 404:
                    print(f"  ✗ Not found (end of fragments)")
                    break
                
                response.raise_for_status()
                total_size = int(response.headers.get('content-length', 0))
                
                with open(file_path, 'wb') as f:
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            pct = downloaded / total_size * 100
                            print(f"\r  {downloaded/1e6:.1f}/{total_size/1e6:.1f} MB ({pct:.1f}%)", end='')
                
                print(f"\n  ✓ Downloaded: {filename}")
                downloaded_files.append(file_path)
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
                continue
        
        print(f"\n{'='*60}")
        print(f"Total BAN CSV files: {len(downloaded_files)}")
        print(f"{'='*60}")
        
        return downloaded_files
    
    def load_ban_to_sqlite(self, ban_csv_files: List[Path], chunksize: int = 500000):
        """Load all BAN CSV fragments into SQLite."""
        print(f"\nLoading BAN CSV fragments into: {self.ban_db_path}")
        
        if self.ban_conn:
            self.ban_conn.close()
        
        self.ban_conn = sqlite3.connect(self.ban_db_path)
        
        # Create table WITHOUT PRIMARY KEY constraint
        self.ban_conn.execute("DROP TABLE IF EXISTS ban_addresses")
        self.ban_conn.execute("""
            CREATE TABLE ban_addresses (
                id TEXT,
                numero TEXT,
                nom_voie TEXT,
                code_postal TEXT,
                nom_commune TEXT,
                lon REAL,
                lat REAL,
                adresse_normalized TEXT
            )
        """)  # ← Removed "PRIMARY KEY" from id
        
        ban_cols = ['id', 'numero', 'nom_voie', 'code_postal', 'nom_commune', 'lon', 'lat']
        total_rows = 0
        
        for file_idx, csv_file in enumerate(ban_csv_files, 1):
            print(f"\n[{file_idx}/{len(ban_csv_files)}] Processing: {csv_file.name}")
            
            chunk_num = 0
            file_rows = 0
            
            try:
                for chunk in pd.read_csv(
                    csv_file,
                    sep=';',
                    compression='gzip',
                    usecols=ban_cols,
                    chunksize=chunksize,
                    low_memory=False,
                    on_bad_lines='skip'
                ):
                    chunk_num += 1
                    
                    # Normalize addresses
                    chunk['adresse_normalized'] = chunk.apply(
                        lambda row: self._normalize_address(
                            f"{row['numero']} {row['nom_voie']} {row['code_postal']} {row['nom_commune']}"
                        ), axis=1
                    )
                    
                    # Write to SQLite (duplicates are OK now)
                    chunk.to_sql('ban_addresses', self.ban_conn, if_exists='append', index=False)
                    
                    file_rows += len(chunk)
                    total_rows += len(chunk)
                    
                    print(f"\r  Chunk {chunk_num}: {file_rows:,} rows | Total: {total_rows/1e6:.1f}M", end='')
                    
                    if chunk_num % 10 == 0:
                        self.ban_conn.commit()
                    
                    del chunk
                
                self.ban_conn.commit()
                print(f"\n  ✓ Completed: {file_rows:,} rows")
                
            except Exception as e:
                print(f"\n  ✗ Error: {e}")
                continue
        
        print(f"\n{'='*60}")
        print(f"✓ Total BAN addresses: {total_rows:,}")
        print(f"{'='*60}")
        
        # Create indexes on what we ACTUALLY use for matching
        print("\nCreating indexes (this may take 5-10 minutes)...")
        print("  Creating index on normalized addresses...")
        self.ban_conn.execute("CREATE INDEX IF NOT EXISTS idx_ban_normalized ON ban_addresses(adresse_normalized)")
        print("  Creating index on postal codes...")
        self.ban_conn.execute("CREATE INDEX IF NOT EXISTS idx_ban_postal ON ban_addresses(code_postal)")
        self.ban_conn.commit()
        print("✓ Indexes created")
    
    def geocode_dvf_addresses(self, fuzzy_threshold: float = 0.85, batch_size: int = 50000):
        """Geocode DVF addresses."""
        print("\n" + "="*60)
        print("GEOCODING DVF ADDRESSES")
        print("="*60)
        
        if self.ban_conn is None:
            if not self.ban_db_path.exists():
                print("ERROR: BAN database not found.")
                return
            self.ban_conn = sqlite3.connect(self.ban_db_path)
        
        ban_count = self.ban_conn.execute("SELECT COUNT(*) FROM ban_addresses").fetchone()[0]
        print(f"BAN addresses available: {ban_count:,}")
        
        print("\nPreparing DVF addresses...")
        self.dvf_conn.execute("DROP TABLE IF EXISTS mutations_geocoded")
        
        tables = pd.read_sql_query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='mutations_agg'",
            self.dvf_conn
        )
        
        if len(tables) == 0:
            print("ERROR: mutations_agg not found")
            return
        
        # Create table with columns
        self.dvf_conn.execute("""
            CREATE TABLE mutations_geocoded AS
            SELECT 
                id_mutation, mutation_year, valeur_fonciere, surface_totale,
                prix_m2, adresse_complete, type_local, nb_lots,
                CAST(NULL AS TEXT) as adresse_normalized,
                CAST(NULL AS REAL) as latitude,
                CAST(NULL AS REAL) as longitude,
                0 as match_type,
                CAST(NULL AS REAL) as match_score
            FROM mutations_agg
        """)
        self.dvf_conn.commit()
        
        total_dvf = self.dvf_conn.execute("SELECT COUNT(*) FROM mutations_geocoded").fetchone()[0]
        print(f"Total DVF addresses: {total_dvf:,}")
        
        # ULTRA-FAST: Normalize directly in SQL (2-3 minutes for 10M rows!)
        print("\nNormalizing addresses in SQL (fast!)...")
        
        self.dvf_conn.execute("""
            UPDATE mutations_geocoded
            SET adresse_normalized = 
                TRIM(
                    REPLACE(
                        REPLACE(
                            REPLACE(
                                REPLACE(
                                    REPLACE(
                                        REPLACE(
                                            REPLACE(
                                                REPLACE(
                                                    REPLACE(UPPER(adresse_complete), ',', ' '),
                                                    '.', ' '
                                                ),
                                                '-', ' '
                                            ),
                                            '  ', ' '
                                        ),
                                        ' R ', ' RUE '
                                    ),
                                    ' AV ', ' AVENUE '
                                ),
                                ' BD ', ' BOULEVARD '
                            ),
                            ' PL ', ' PLACE '
                        ),
                        ' IMP ', ' IMPASSE '
                    )
                )
        """)
        self.dvf_conn.commit()
        
        print("✓ Normalization complete (~2-3 min)")
        
        # EXACT MATCH
        print("\nStrategy 1: Exact matching...")
        self.dvf_conn.execute(f"ATTACH DATABASE '{self.ban_db_path}' AS ban_db")
        
        # Add index on normalized addresses first (makes UPDATE 10x faster)
        print("  Creating temp index...")
        self.dvf_conn.execute("CREATE INDEX IF NOT EXISTS idx_dvf_norm ON mutations_geocoded(adresse_normalized)")
        self.dvf_conn.commit()
        
        print("  Matching addresses...")
        self.dvf_conn.execute("""
            UPDATE mutations_geocoded
            SET 
                latitude = (SELECT b.lat FROM ban_db.ban_addresses b WHERE b.adresse_normalized = mutations_geocoded.adresse_normalized LIMIT 1),
                longitude = (SELECT b.lon FROM ban_db.ban_addresses b WHERE b.adresse_normalized = mutations_geocoded.adresse_normalized LIMIT 1),
                match_type = 1,
                match_score = 1.0
            WHERE EXISTS (
                SELECT 1 FROM ban_db.ban_addresses b WHERE b.adresse_normalized = mutations_geocoded.adresse_normalized
            )
        """)
        self.dvf_conn.commit()
        
        exact_count = self.dvf_conn.execute("SELECT COUNT(*) FROM mutations_geocoded WHERE match_type = 1").fetchone()[0]
        print(f"✓ Exact matches: {exact_count:,} ({exact_count/total_dvf*100:.1f}%)")
        
        # FUZZY MATCH
        print(f"\nStrategy 2: Fuzzy matching (threshold={fuzzy_threshold})...")
        
        unmatched = pd.read_sql_query("SELECT id_mutation, adresse_normalized FROM mutations_geocoded WHERE match_type = 0 LIMIT 500000", self.dvf_conn)
        
        if len(unmatched) == 0:
            print("✓ All addresses matched!")
            self._print_final_stats(total_dvf)
            self.dvf_conn.execute("DETACH DATABASE ban_db")
            return
        
        print(f"Unmatched (processing first 500k): {len(unmatched):,}")
        
        unmatched['code_postal'] = unmatched['adresse_normalized'].str.extract(r'(\d{5})', expand=False)
        unmatched = unmatched[unmatched['code_postal'].notna()].copy()
        print(f"With postal code: {len(unmatched):,}")
        
        fuzzy_matched = 0
        fuzzy_batch_size = 10000
        batches = [unmatched[i:i+fuzzy_batch_size] for i in range(0, len(unmatched), fuzzy_batch_size)]
        
        for batch_idx, batch in enumerate(batches, 1):
            print(f"\r  Batch {batch_idx}/{len(batches)}: {fuzzy_matched:,} fuzzy", end='')
            
            update_data = []
            
            for postal in batch['code_postal'].unique():
                dvf_addrs = batch[batch['code_postal'] == postal]
                
                ban_candidates = pd.read_sql_query(
                    "SELECT adresse_normalized, lat, lon FROM ban_addresses WHERE code_postal = ?",
                    self.ban_conn, params=(postal,)
                )
                
                if len(ban_candidates) == 0:
                    continue
                
                for _, dvf_row in dvf_addrs.iterrows():
                    best_match = None
                    best_score = 0.0
                    
                    for _, ban_row in ban_candidates.iterrows():
                        score = SequenceMatcher(None, dvf_row['adresse_normalized'], ban_row['adresse_normalized']).ratio()
                        if score > best_score:
                            best_score = score
                            best_match = ban_row
                    
                    if best_score >= fuzzy_threshold and best_match is not None:
                        update_data.append((best_match['lat'], best_match['lon'], best_score, dvf_row['id_mutation']))
                        fuzzy_matched += 1
            
            if update_data:
                self.dvf_conn.executemany("""
                    UPDATE mutations_geocoded
                    SET latitude = ?, longitude = ?, match_type = 2, match_score = ?
                    WHERE id_mutation = ?
                """, update_data)
            
            # Commit every 5 batches
            if batch_idx % 5 == 0:
                self.dvf_conn.commit()
        
        self.dvf_conn.commit()
        print(f"\n✓ Fuzzy matches: {fuzzy_matched:,}")
        self._print_final_stats(total_dvf)
        self.dvf_conn.execute("DETACH DATABASE ban_db")
    
    def _normalize_address(self, addr: str) -> str:
        """Normalize address."""
        if pd.isna(addr) or addr == '':
            return ''
        
        addr = str(addr).upper().strip()
        addr = re.sub(r'[^\w\s]', ' ', addr)
        
        replacements = {
            r'\bR\b': 'RUE', r'\bAV\b': 'AVENUE', r'\bBD\b': 'BOULEVARD',
            r'\bBVD\b': 'BOULEVARD', r'\bPL\b': 'PLACE', r'\bIMP\b': 'IMPASSE',
            r'\bCH\b': 'CHEMIN', r'\bALL\b': 'ALLEE', r'\bCRS\b': 'COURS',
        }
        
        for pattern, replacement in replacements.items():
            addr = re.sub(pattern, replacement, addr)
        
        return ' '.join(addr.split())
    
    def _print_final_stats(self, total: int):
        """Print final statistics."""
        stats = pd.read_sql_query("""
            SELECT match_type, COUNT(*) as count, AVG(match_score) as avg_score
            FROM mutations_geocoded GROUP BY match_type
        """, self.dvf_conn)
        
        print(f"\n{'='*60}")
        print("FINAL STATISTICS")
        print(f"{'='*60}")
        print(f"Total addresses: {total:,}\n")
        
        for _, row in stats.iterrows():
            match_type = int(row['match_type'])
            count = int(row['count'])
            pct = count / total * 100
            
            labels = {0: "Not found", 1: "Exact", 2: "Fuzzy"}
            
            if match_type == 0:
                print(f"  {labels[match_type]:12s}: {count:>10,} ({pct:5.1f}%)")
            else:
                print(f"  {labels[match_type]:12s}: {count:>10,} ({pct:5.1f}%) - score: {row['avg_score']:.3f}")
        
        matched = total - (stats[stats['match_type'] == 0]['count'].iloc[0] if 0 in stats['match_type'].values else 0)
        print(f"\n  {'TOTAL MATCHED':12s}: {matched:>10,} ({matched/total*100:5.1f}%)")
        print(f"{'='*60}")
    
    def export_to_parquet(self, output_dir: str = "data/dvf_parquet"):
        """Export by year."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        print(f"\nExporting to: {output_path}")
        
        years = pd.read_sql_query("SELECT DISTINCT mutation_year FROM mutations_geocoded ORDER BY mutation_year", self.dvf_conn)['mutation_year'].tolist()
        
        for year in years:
            df = pd.read_sql_query("SELECT * FROM mutations_geocoded WHERE mutation_year = ?", self.dvf_conn, params=(year,))
            file_path = output_path / f"year={year}.parquet"
            df.to_parquet(file_path, index=False)
            print(f"  Year {year}: {len(df):,} rows")
        
        print("✓ Export complete")
    
    def close(self):
        self.dvf_conn.close()
        if self.ban_conn:
            self.ban_conn.close()


# === USAGE ===
if __name__ == "__main__":
    analyzer = DVFAnalyzer()

    # # Files already downloaded, so skip download step
    # ban_csv_files = sorted(Path("ban_data").glob("adresses-*.csv.gz"))
    # print(f"Found {len(ban_csv_files)} existing BAN CSV files")
    
    # # Load into SQLite
    # analyzer.load_ban_to_sqlite(ban_csv_files)
    
    # Geocode
    analyzer.geocode_dvf_addresses(fuzzy_threshold=0.85)
    
    # Export
    analyzer.export_to_parquet()
    
    analyzer.close()
    print("\n✓ ALL DONE!")