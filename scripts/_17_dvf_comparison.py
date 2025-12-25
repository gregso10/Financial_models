# scripts/_17_dvf_comparison.py
"""
DVF Market Comparison Module - Optimized version.
Provides local market insights based on DVF transaction data.
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from math import radians, sin, cos, sqrt, atan2
import streamlit as st


class DVFComparison:
    """Compare a property against local DVF transactions."""
    
    MIN_PRICE_SQM = 500
    MAX_PRICE_SQM = 25000
    DVF_SOURCE_URL = "https://www.data.gouv.fr/fr/datasets/demandes-de-valeurs-foncieres/"
    
    # City coordinates cache
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
    
    def __init__(self, db_path: str = "dvf_processed.db"):
        self.db_path = Path(db_path)
        self.conn = None
        
    def _connect(self) -> bool:
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
        R = 6371
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        return R * 2 * atan2(sqrt(a), sqrt(1-a))
    
    def get_city_coordinates(self, city: str) -> Optional[Tuple[float, float]]:
        return self.CITY_COORDS.get(city)
    
    def is_dense_city(self, city: str) -> bool:
        return city in ["Paris", "Lyon", "Marseille", "Bordeaux", "Nice", "Lille"]
    
    @st.cache_data(ttl=3600)
    def get_market_comparison_simple(_self, city: str, price: float, surface_sqm: float) -> Optional[Dict]:
        """
        Simplified market comparison - faster, city-level only.
        Used for simple mode dashboard.
        """
        if not _self._connect():
            return None
        
        try:
            user_price_sqm = price / surface_sqm if surface_sqm > 0 else 0
            
            # Simple city-based query - no geo filtering
            query = """
            SELECT prix_m2, mutation_year
            FROM mutations_agg
            WHERE adresse_complete LIKE ?
              AND prix_m2 BETWEEN ? AND ?
              AND surface_totale BETWEEN ? AND ?
            ORDER BY mutation_year DESC
            LIMIT 200
            """
            
            min_surface = surface_sqm * 0.7
            max_surface = surface_sqm * 1.3
            
            df = pd.read_sql_query(
                query, _self.conn,
                params=(f"%{city}%", _self.MIN_PRICE_SQM, _self.MAX_PRICE_SQM, min_surface, max_surface)
            )
            
            if len(df) < 5:
                return None
            
            median = df['prix_m2'].median()
            q25, q75 = df['prix_m2'].quantile(0.25), df['prix_m2'].quantile(0.75)
            
            if user_price_sqm <= q25:
                assessment = "below_market"
            elif user_price_sqm <= median:
                assessment = "fair"
            elif user_price_sqm <= q75:
                assessment = "above_median"
            else:
                assessment = "expensive"
            
            return {
                "transaction_count": len(df),
                "median_price_sqm": median,
                "q25_price_sqm": q25,
                "q75_price_sqm": q75,
                "user_price_sqm": user_price_sqm,
                "diff_vs_median_pct": ((user_price_sqm - median) / median) * 100 if median > 0 else 0,
                "assessment": assessment,
            }
            
        except Exception as e:
            print(f"DVF simple comparison error: {e}")
            return None
        finally:
            _self._close()
    
    def get_market_comparison_geo(self, lat: float, lon: float, price: float, 
                                   surface_sqm: float, radius_km: float = 0.5) -> Optional[Dict]:
        """
        Geo-based market comparison for expert mode.
        Returns transactions within radius for map display.
        """
        if not self._connect():
            return None
        
        try:
            user_price_sqm = price / surface_sqm if surface_sqm > 0 else 0
            
            lat_delta = radius_km / 111
            lon_delta = radius_km / (111 * cos(radians(lat)))
            
            min_surface = surface_sqm * 0.7
            max_surface = surface_sqm * 1.3
            
            query = """
            SELECT 
                m.valeur_fonciere, m.surface_totale, m.prix_m2,
                m.mutation_year, m.adresse_complete,
                g.latitude, g.longitude
            FROM mutations_agg m
            JOIN geocoded_addresses g ON m.adresse_complete = g.adresse_complete
            WHERE g.latitude BETWEEN ? AND ?
              AND g.longitude BETWEEN ? AND ?
              AND m.prix_m2 BETWEEN ? AND ?
              AND m.surface_totale BETWEEN ? AND ?
            ORDER BY m.mutation_year DESC
            LIMIT 500
            """
            
            df = pd.read_sql_query(
                query, self.conn,
                params=(
                    lat - lat_delta, lat + lat_delta,
                    lon - lon_delta, lon + lon_delta,
                    self.MIN_PRICE_SQM, self.MAX_PRICE_SQM,
                    min_surface, max_surface
                )
            )
            
            if len(df) < 3:
                return None
            
            # Filter by actual distance
            df['distance_km'] = df.apply(
                lambda r: self.haversine_distance(lat, lon, r['latitude'], r['longitude']),
                axis=1
            )
            df = df[df['distance_km'] <= radius_km]
            
            if len(df) < 3:
                return None
            
            median = df['prix_m2'].median()
            q25, q75 = df['prix_m2'].quantile(0.25), df['prix_m2'].quantile(0.75)
            
            if user_price_sqm <= q25:
                assessment = "below_market"
            elif user_price_sqm <= median:
                assessment = "fair"
            elif user_price_sqm <= q75:
                assessment = "above_median"
            else:
                assessment = "expensive"
            
            return {
                "transactions": df.to_dict('records'),
                "transaction_count": len(df),
                "median_price_sqm": median,
                "mean_price_sqm": df['prix_m2'].mean(),
                "min_price_sqm": df['prix_m2'].min(),
                "max_price_sqm": df['prix_m2'].max(),
                "q25_price_sqm": q25,
                "q75_price_sqm": q75,
                "user_price_sqm": user_price_sqm,
                "user_lat": lat,
                "user_lon": lon,
                "diff_vs_median_pct": ((user_price_sqm - median) / median) * 100 if median > 0 else 0,
                "assessment": assessment,
                "radius_km": radius_km,
            }
            
        except Exception as e:
            print(f"DVF geo comparison error: {e}")
            return None
        finally:
            self._close()


# === ADDRESS GEOCODING ===

import requests

@st.cache_data(ttl=86400)
def geocode_address(address: str) -> Optional[Tuple[float, float, str]]:
    """
    Geocode address using BAN API.
    Returns (lat, lon, formatted_address) or None.
    """
    if not address or len(address) < 5:
        return None
    
    try:
        url = "https://api-adresse.data.gouv.fr/search/"
        params = {"q": address, "limit": 1}
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        if data.get("features"):
            feat = data["features"][0]
            coords = feat["geometry"]["coordinates"]
            label = feat["properties"].get("label", address)
            return (coords[1], coords[0], label)  # lat, lon
        return None
    except Exception as e:
        print(f"Geocoding error: {e}")
        return None


def search_addresses(query: str, limit: int = 5) -> List[Dict]:
    """
    Search for address suggestions using BAN API.
    Returns list of {label, lat, lon, city, postcode}.
    """
    if not query or len(query) < 3:
        return []
    
    try:
        url = "https://api-adresse.data.gouv.fr/search/"
        params = {"q": query, "limit": limit, "type": "housenumber"}
        response = requests.get(url, params=params, timeout=3)
        response.raise_for_status()
        
        data = response.json()
        results = []
        for feat in data.get("features", []):
            props = feat["properties"]
            coords = feat["geometry"]["coordinates"]
            results.append({
                "label": props.get("label", ""),
                "lat": coords[1],
                "lon": coords[0],
                "city": props.get("city", ""),
                "postcode": props.get("postcode", ""),
                "street": props.get("street", ""),
            })
        return results
    except Exception:
        return []


# === ALERTES RENTABILITÉ ===

def generate_profitability_alerts(
    irr: float, monthly_cashflow: float, cash_on_cash: float,
    equity_multiple: float, risk_free_rate: float = 0.035, lang: str = "fr"
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
        msg = f"Rendement > taux sans risque ({risk_free_rate*100:.1f}%)" if lang == "fr" else f"Return > risk-free ({risk_free_rate*100:.1f}%)"
        alerts.append({"type": "success", "icon": "✅", "message": msg})
    elif irr > 0.03:
        msg = "Rendement > Livret A mais < obligations" if lang == "fr" else "Return > Livret A but < bonds"
        alerts.append({"type": "warning", "icon": "⚠️", "message": msg})
    else:
        msg = "Rendement < Livret A (3%)" if lang == "fr" else "Return < Livret A (3%)"
        alerts.append({"type": "error", "icon": "🔴", "message": msg})
    
    if equity_multiple >= 2.0:
        msg = "Capital doublé sur la période" if lang == "fr" else "Capital doubled"
        alerts.append({"type": "success", "icon": "💰", "message": msg})
    elif equity_multiple < 1.0:
        msg = "Perte en capital probable" if lang == "fr" else "Likely capital loss"
        alerts.append({"type": "error", "icon": "📉", "message": msg})
    
    return alerts


def get_market_assessment_text(assessment: str, lang: str = "fr") -> Tuple[str, str]:
    """Get human-readable assessment and color."""
    assessments = {
        "below_market": (("En dessous du marché", "#22c55e") if lang == "fr" else ("Below market", "#22c55e")),
        "fair": (("Prix correct", "#22c55e") if lang == "fr" else ("Fair price", "#22c55e")),
        "above_median": (("Au-dessus de la médiane", "#eab308") if lang == "fr" else ("Above median", "#eab308")),
        "expensive": (("Prix élevé", "#ef4444") if lang == "fr" else ("Expensive", "#ef4444")),
    }
    return assessments.get(assessment, assessments["fair"])


def get_dvf_disclaimer(lang: str = "fr") -> str:
    if lang == "fr":
        return "📋 **Source**: DVF ([data.gouv.fr](https://www.data.gouv.fr/fr/datasets/demandes-de-valeurs-foncieres/)) • Prix/m² sur surface totale, peut sous-estimer les prix réels."
    return "📋 **Source**: DVF ([data.gouv.fr](https://www.data.gouv.fr/fr/datasets/demandes-de-valeurs-foncieres/)) • Price/sqm on total area, may underestimate actual prices."