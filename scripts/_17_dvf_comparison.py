# scripts/_17_dvf_comparison.py
"""
DVF Market Comparison Module.
Provides local market insights based on DVF transaction data.
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from math import radians, sin, cos, sqrt, atan2


class DVFComparison:
    """
    Compare a property against local DVF transactions.
    """
    
    # Minimum/Maximum realistic price per sqm (filter out data errors)
    MIN_PRICE_SQM = 200
    MAX_PRICE_SQM = 25000
    
    # DVF source info
    DVF_SOURCE_URL = "https://www.data.gouv.fr/fr/datasets/demandes-de-valeurs-foncieres/"
    
    def __init__(self, db_path: str = "dvf_processed.db"):
        self.db_path = Path(db_path)
        self.conn = None
        
    def _connect(self) -> bool:
        """Connect to DVF database if exists."""
        if not self.db_path.exists():
            return False
        try:
            self.conn = sqlite3.connect(self.db_path)
            return True
        except Exception:
            return False
    
    def _close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
    
    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance in km between two points."""
        R = 6371  # Earth radius in km
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    def get_city_coordinates(self, city: str) -> Optional[Tuple[float, float]]:
        """Get approximate coordinates for a city."""
        CITY_COORDS = {
            "Paris": (48.8566, 2.3522),
            "Lyon": (45.7640, 4.8357),
            "Marseille": (43.2965, 5.3698),
            "Bordeaux": (44.8378, -0.5792),
            "Nantes": (47.2184, -1.5536),
            "Toulouse": (43.6047, 1.4442),
            "Nice": (43.7102, 7.2620),
            "Lille": (50.6292, 3.0573),
            "Strasbourg": (48.5734, 7.7521),
        }
        return CITY_COORDS.get(city)
    
    def get_adaptive_radius(self, city: str) -> float:
        dense_cities = ["Paris", "Lyon", "Marseille", "Bordeaux", "Nice"]
        if any(c in city for c in dense_cities):
            return 0.5  # 500m max in dense areas
        return 2.0

    def get_market_comparison(
        self,
        city: str,
        price: float,
        surface_sqm: float,
        radius_km: float = 2.0,
        months_back: int = 12,
        surface_tolerance: float = 0.15,
    ) -> Optional[Dict]:
        """
        Compare property against local market.
        Filters out unrealistic values (< 200€/m² or > 25000€/m²).
        """
        if not self._connect():
            return None
        
        try:
            user_price_sqm = price / surface_sqm if surface_sqm > 0 else 0
            
            coords = self.get_city_coordinates(city)
            if not coords:
                coords = self._get_coords_from_db(city)
            
            if not coords:
                return self._get_city_only_comparison(city, user_price_sqm, surface_sqm, surface_tolerance)
            
            lat, lon = coords
            radius_km = self.get_adaptive_radius(city)

            lat_delta = radius_km / 111
            lon_delta = radius_km / (111 * cos(radians(lat)))
            
            min_surface = surface_sqm * (1 - surface_tolerance)
            max_surface = surface_sqm * (1 + surface_tolerance)
            
            # Query with price filters
            query = """
            SELECT 
                m.valeur_fonciere,
                m.surface_totale,
                m.prix_m2,
                m.mutation_year,
                m.type_local,
                g.latitude,
                g.longitude
            FROM mutations_agg m
            JOIN geocoded_addresses g ON m.adresse_complete = g.adresse_complete
            WHERE g.latitude BETWEEN ? AND ?
              AND g.longitude BETWEEN ? AND ?
              AND m.surface_totale BETWEEN ? AND ?
              AND m.prix_m2 >= ?
              AND m.prix_m2 <= ?
            ORDER BY m.mutation_year DESC
            LIMIT 500
            """
            
            df = pd.read_sql_query(
                query, 
                self.conn,
                params=(
                    lat - lat_delta, lat + lat_delta,
                    lon - lon_delta, lon + lon_delta,
                    min_surface, max_surface,
                    self.MIN_PRICE_SQM, self.MAX_PRICE_SQM
                )
            )
            
            if len(df) == 0:
                return self._get_city_only_comparison(city, user_price_sqm, surface_sqm, surface_tolerance)
            
            # Filter by actual distance
            df['distance_km'] = df.apply(
                lambda r: self.haversine_distance(lat, lon, r['latitude'], r['longitude']),
                axis=1
            )
            df = df[df['distance_km'] <= radius_km]
            
            if len(df) == 0:
                return self._get_city_only_comparison(city, user_price_sqm, surface_sqm, surface_tolerance)
            
            return self._compute_insights(df, user_price_sqm, radius_km)
            
        except Exception as e:
            print(f"DVF comparison error: {e}")
            return None
        finally:
            self._close()
    
    def get_nearby_districts_comparison(
        self,
        city: str,
        lat: float,
        lon: float,
        radius_km: float = 0.5,
    ) -> Optional[List[Dict]]:
        """
        Get price/m² breakdown for nearby areas within radius.
        Groups by approximate district/zone.
        """
        if not self._connect():
            return None
        
        try:
            lat_delta = radius_km / 111
            lon_delta = radius_km / (111 * cos(radians(lat)))
            
            query = """
            SELECT 
                m.prix_m2,
                g.latitude,
                g.longitude
            FROM mutations_agg m
            JOIN geocoded_addresses g ON m.adresse_complete = g.adresse_complete
            WHERE g.latitude BETWEEN ? AND ?
              AND g.longitude BETWEEN ? AND ?
              AND m.prix_m2 >= ?
              AND m.prix_m2 <= ?
            ORDER BY m.mutation_year DESC
            LIMIT 1000
            """
            
            df = pd.read_sql_query(
                query,
                self.conn,
                params=(
                    lat - lat_delta, lat + lat_delta,
                    lon - lon_delta, lon + lon_delta,
                    self.MIN_PRICE_SQM, self.MAX_PRICE_SQM
                )
            )
            
            if len(df) == 0:
                return None
            
            # Calculate distance from center
            df['distance_km'] = df.apply(
                lambda r: self.haversine_distance(lat, lon, r['latitude'], r['longitude']),
                axis=1
            )
            df = df[df['distance_km'] <= radius_km]
            
            if len(df) == 0:
                return None
            
            # Group by distance bands (0-200m, 200-400m, 400-500m)
            bands = [
                (0, 0.2, "0-200m"),
                (0.2, 0.4, "200-400m"),
                (0.4, 0.5, "400-500m"),
            ]
            
            results = []
            for min_d, max_d, label in bands:
                band_df = df[(df['distance_km'] >= min_d) & (df['distance_km'] < max_d)]
                if len(band_df) >= 3:  # Minimum 3 transactions for stats
                    results.append({
                        "band": label,
                        "count": len(band_df),
                        "median_price_sqm": band_df['prix_m2'].median(),
                        "min_price_sqm": band_df['prix_m2'].min(),
                        "max_price_sqm": band_df['prix_m2'].max(),
                    })
            
            return results if results else None
            
        except Exception as e:
            print(f"District comparison error: {e}")
            return None
        finally:
            self._close()
    
    def _get_coords_from_db(self, city: str) -> Optional[Tuple[float, float]]:
        """Try to get city coordinates from DB addresses."""
        try:
            query = """
            SELECT AVG(g.latitude) as lat, AVG(g.longitude) as lon
            FROM geocoded_addresses g
            JOIN mutations_agg m ON g.adresse_complete = m.adresse_complete
            WHERE m.adresse_complete LIKE ?
            LIMIT 1
            """
            result = pd.read_sql_query(query, self.conn, params=(f"%{city}%",))
            if len(result) > 0 and result.iloc[0]['lat'] is not None:
                return (result.iloc[0]['lat'], result.iloc[0]['lon'])
        except Exception:
            pass
        return None
    
    def _get_city_only_comparison(
        self, 
        city: str, 
        user_price_sqm: float,
        surface_sqm: float,
        surface_tolerance: float
    ) -> Optional[Dict]:
        """Fallback: compare by city name only (no geo)."""
        try:
            min_surface = surface_sqm * (1 - surface_tolerance)
            max_surface = surface_sqm * (1 + surface_tolerance)
            
            query = """
            SELECT 
                m.valeur_fonciere,
                m.surface_totale,
                m.prix_m2,
                m.mutation_year,
                m.type_local
            FROM mutations_agg m
            WHERE m.adresse_complete LIKE ?
              AND m.surface_totale BETWEEN ? AND ?
              AND m.prix_m2 >= ?
              AND m.prix_m2 <= ?
            ORDER BY m.mutation_year DESC
            LIMIT 200
            """
            
            df = pd.read_sql_query(
                query,
                self.conn,
                params=(f"%{city}%", min_surface, max_surface, 
                       self.MIN_PRICE_SQM, self.MAX_PRICE_SQM)
            )
            
            if len(df) == 0:
                return None
            
            return self._compute_insights(df, user_price_sqm, radius_km=None)
            
        except Exception:
            return None
    
    def _compute_insights(
        self, 
        df: pd.DataFrame, 
        user_price_sqm: float,
        radius_km: Optional[float]
    ) -> Dict:
        """Compute market insights from transactions."""
        
        median_price_sqm = df['prix_m2'].median()
        mean_price_sqm = df['prix_m2'].mean()
        min_price_sqm = df['prix_m2'].min()
        max_price_sqm = df['prix_m2'].max()
        q25 = df['prix_m2'].quantile(0.25)
        q75 = df['prix_m2'].quantile(0.75)
        
        percentile = (df['prix_m2'] < user_price_sqm).mean() * 100
        diff_vs_median = ((user_price_sqm - median_price_sqm) / median_price_sqm) * 100 if median_price_sqm > 0 else 0
        
        if user_price_sqm <= q25:
            assessment = "below_market"
            assessment_score = 1
        elif user_price_sqm <= median_price_sqm:
            assessment = "fair"
            assessment_score = 2
        elif user_price_sqm <= q75:
            assessment = "above_median"
            assessment_score = 3
        else:
            assessment = "expensive"
            assessment_score = 4
        
        return {
            "transaction_count": len(df),
            "radius_km": radius_km,
            "median_price_sqm": median_price_sqm,
            "mean_price_sqm": mean_price_sqm,
            "min_price_sqm": min_price_sqm,
            "max_price_sqm": max_price_sqm,
            "q25_price_sqm": q25,
            "q75_price_sqm": q75,
            "user_price_sqm": user_price_sqm,
            "user_percentile": percentile,
            "diff_vs_median_pct": diff_vs_median,
            "assessment": assessment,
            "assessment_score": assessment_score,
            "years_covered": sorted(df['mutation_year'].unique().tolist()) if 'mutation_year' in df.columns else [],
            "source_url": self.DVF_SOURCE_URL,
        }


# === ALERTES RENTABILITÉ ===

def generate_profitability_alerts(
    irr: float,
    monthly_cashflow: float,
    cash_on_cash: float,
    equity_multiple: float,
    risk_free_rate: float = 0.035,
    livret_a_rate: float = 0.03,
    lang: str = "fr"
) -> list:
    """Generate list of profitability alerts."""
    alerts = []
    
    if monthly_cashflow >= 0:
        msg = "Cash-flow positif dès le départ" if lang == "fr" else "Positive cash flow from day 1"
        alerts.append({"type": "success", "icon": "✅", "message": msg})
    elif monthly_cashflow >= -100:
        msg = f"Effort d'épargne modéré: {abs(monthly_cashflow):.0f}€/mois" if lang == "fr" else f"Moderate saving effort: €{abs(monthly_cashflow):.0f}/month"
        alerts.append({"type": "warning", "icon": "⚠️", "message": msg})
    else:
        msg = f"Cash-flow négatif: {monthly_cashflow:.0f}€/mois" if lang == "fr" else f"Negative cash flow: €{monthly_cashflow:.0f}/month"
        alerts.append({"type": "error", "icon": "🔴", "message": msg})
    
    if irr > 0.08:
        msg = "Rendement excellent (>8%)" if lang == "fr" else "Excellent return (>8%)"
        alerts.append({"type": "success", "icon": "🌟", "message": msg})
    elif irr > risk_free_rate:
        msg = f"Rendement supérieur au taux sans risque ({risk_free_rate*100:.1f}%)" if lang == "fr" else f"Return above risk-free rate ({risk_free_rate*100:.1f}%)"
        alerts.append({"type": "success", "icon": "✅", "message": msg})
    elif irr > livret_a_rate:
        msg = f"Rendement > Livret A ({livret_a_rate*100:.0f}%) mais < obligations" if lang == "fr" else f"Return > Livret A ({livret_a_rate*100:.0f}%) but < bonds"
        alerts.append({"type": "warning", "icon": "⚠️", "message": msg})
    else:
        msg = f"Rendement inférieur au Livret A ({livret_a_rate*100:.0f}%)" if lang == "fr" else f"Return below Livret A ({livret_a_rate*100:.0f}%)"
        alerts.append({"type": "error", "icon": "🔴", "message": msg})
    
    if equity_multiple >= 2.0:
        msg = "Capital doublé sur la période" if lang == "fr" else "Capital doubled over period"
        alerts.append({"type": "success", "icon": "💰", "message": msg})
    elif equity_multiple >= 1.5:
        msg = f"Multiplication du capital: {equity_multiple:.1f}x" if lang == "fr" else f"Capital multiple: {equity_multiple:.1f}x"
        alerts.append({"type": "success", "icon": "📈", "message": msg})
    elif equity_multiple < 1.0:
        msg = "Perte en capital probable" if lang == "fr" else "Likely capital loss"
        alerts.append({"type": "error", "icon": "📉", "message": msg})
    
    if cash_on_cash >= 0.05:
        msg = f"Rendement cash Y1: {cash_on_cash*100:.1f}%" if lang == "fr" else f"Cash return Y1: {cash_on_cash*100:.1f}%"
        alerts.append({"type": "success", "icon": "💵", "message": msg})
    elif cash_on_cash < 0:
        msg = "Apport de trésorerie nécessaire en Y1" if lang == "fr" else "Cash injection needed in Y1"
        alerts.append({"type": "warning", "icon": "💳", "message": msg})
    
    return alerts


def get_market_assessment_text(assessment: str, lang: str = "fr") -> Tuple[str, str]:
    """Get human-readable assessment and color."""
    assessments = {
        "below_market": {
            "fr": ("En dessous du marché", "#22c55e"),
            "en": ("Below market", "#22c55e"),
        },
        "fair": {
            "fr": ("Prix correct", "#22c55e"),
            "en": ("Fair price", "#22c55e"),
        },
        "above_median": {
            "fr": ("Au-dessus de la médiane", "#eab308"),
            "en": ("Above median", "#eab308"),
        },
        "expensive": {
            "fr": ("Prix élevé pour le secteur", "#ef4444"),
            "en": ("Expensive for area", "#ef4444"),
        },
    }
    
    data = assessments.get(assessment, assessments["fair"])
    return data.get(lang, data["en"])


def get_dvf_disclaimer(lang: str = "fr") -> str:
    """Get DVF methodology disclaimer."""
    if lang == "fr":
        return (
            "📋 **Source**: Base DVF (Demandes de Valeurs Foncières) - "
            "[data.gouv.fr](https://www.data.gouv.fr/fr/datasets/demandes-de-valeurs-foncieres/)\n\n"
            "⚠️ **Méthodologie**: Les prix/m² sont calculés sur la surface totale de la transaction "
            "(qui peut inclure caves, parkings, etc.) et non la surface Loi Carrez, "
            "souvent incomplète dans la base DVF. Cela peut sous-estimer les prix réels. "
            "Les valeurs aberrantes (<200€/m² ou >25 000€/m²) ont été exclues."
        )
    else:
        return (
            "📋 **Source**: DVF Database (Property Value Requests) - "
            "[data.gouv.fr](https://www.data.gouv.fr/fr/datasets/demandes-de-valeurs-foncieres/)\n\n"
            "⚠️ **Methodology**: Price/sqm is calculated using total transaction area "
            "(which may include cellars, parking, etc.) rather than Loi Carrez surface, "
            "often incomplete in DVF data. This may underestimate actual prices. "
            "Outliers (<€200/sqm or >€25,000/sqm) have been excluded."
        )