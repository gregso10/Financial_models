# scripts/_19_address_widget.py
"""
Address autocomplete widget using French BAN API.
"""

import streamlit as st
import requests
from typing import Optional, Tuple, List, Dict
import pydeck as pdk
import pandas as pd


def address_autocomplete(
    label: str = "Adresse",
    key: str = "address_input",
    placeholder: str = "Ex: 15 rue de la Paix, Paris",
    help_text: str = None
) -> Optional[Dict]:
    """
    Streamlit address autocomplete widget.
    
    Returns:
        Dict with {address, lat, lon, city, postcode} or None
    """
    # Initialize session state
    suggestions_key = f"{key}_suggestions"
    selected_key = f"{key}_selected"
    
    if suggestions_key not in st.session_state:
        st.session_state[suggestions_key] = []
    if selected_key not in st.session_state:
        st.session_state[selected_key] = None
    
    # Text input
    query = st.text_input(
        label,
        key=key,
        placeholder=placeholder,
        help=help_text
    )
    
    # Fetch suggestions when query changes
    if query and len(query) >= 5:
        suggestions = _fetch_suggestions(query)
        st.session_state[suggestions_key] = suggestions
    else:
        st.session_state[suggestions_key] = []
    
    # Display suggestions as buttons
    suggestions = st.session_state[suggestions_key]
    if suggestions and not st.session_state[selected_key]:
        st.caption("Suggestions:")
        for i, sug in enumerate(suggestions[:5]):
            if st.button(f"📍 {sug['label']}", key=f"{key}_sug_{i}", use_container_width=True):
                st.session_state[selected_key] = sug
                st.rerun()
    
    # Return selected address
    if st.session_state[selected_key]:
        selected = st.session_state[selected_key]
        st.success(f"✅ {selected['label']}")
        
        # Clear button
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🔄", key=f"{key}_clear", help="Changer d'adresse"):
                st.session_state[selected_key] = None
                st.rerun()
        
        return {
            "address": selected['label'],
            "lat": selected['lat'],
            "lon": selected['lon'],
            "city": selected['city'],
            "postcode": selected['postcode'],
        }
    
    return None


def address_input_simple(
    label: str = "Adresse",
    key: str = "address",
    default_city: str = "Paris"
) -> Tuple[Optional[str], Optional[float], Optional[float], str]:
    """
    Simpler address input with geocoding on demand.
    Returns (address, lat, lon, city).
    """
    col1, col2 = st.columns([3, 1])
    
    with col1:
        address = st.text_input(
            label,
            key=key,
            placeholder="Ex: 15 rue de la Paix, 75002 Paris"
        )
    
    with col2:
        geocode_btn = st.button("📍", key=f"{key}_geocode", help="Localiser")
    
    # Store geocoded result in session
    geo_key = f"{key}_geocoded"
    if geo_key not in st.session_state:
        st.session_state[geo_key] = None
    
    if geocode_btn and address:
        result = _geocode_address(address)
        if result:
            st.session_state[geo_key] = result
        else:
            st.warning("Adresse non trouvée")
    
    if st.session_state[geo_key]:
        lat, lon, label, city = st.session_state[geo_key]
        st.caption(f"📍 {label}")
        return address, lat, lon, city
    
    # Fallback to city from address or default
    city = _extract_city(address) or default_city
    return address, None, None, city


@st.cache_data(ttl=3600)
def _fetch_suggestions(query: str, limit: int = 5) -> List[Dict]:
    """Fetch address suggestions from BAN API."""
    if not query or len(query) < 3:
        return []
    
    try:
        url = "https://api-adresse.data.gouv.fr/search/"
        params = {"q": query, "limit": limit}
        response = requests.get(url, params=params, timeout=3)
        response.raise_for_status()
        
        results = []
        for feat in response.json().get("features", []):
            props = feat["properties"]
            coords = feat["geometry"]["coordinates"]
            results.append({
                "label": props.get("label", ""),
                "lat": coords[1],
                "lon": coords[0],
                "city": props.get("city", ""),
                "postcode": props.get("postcode", ""),
            })
        return results
    except Exception:
        return []


@st.cache_data(ttl=86400)
def _geocode_address(address: str) -> Optional[Tuple[float, float, str, str]]:
    """Geocode single address. Returns (lat, lon, label, city)."""
    if not address:
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
            props = feat["properties"]
            return (
                coords[1], coords[0],
                props.get("label", address),
                props.get("city", "")
            )
        return None
    except Exception:
        return None


def _extract_city(address: str) -> Optional[str]:
    """Try to extract city name from address string."""
    if not address:
        return None
    
    # Common French cities
    cities = ["Paris", "Lyon", "Marseille", "Bordeaux", "Nantes", "Toulouse", 
              "Nice", "Lille", "Strasbourg", "Montpellier", "Rennes"]
    
    address_lower = address.lower()
    for city in cities:
        if city.lower() in address_lower:
            return city
    return None


def create_dvf_map(
    user_lat: float,
    user_lon: float,
    transactions: List[Dict],
    user_price_sqm: float,
    radius_km: float = 0.5
) -> pdk.Deck:
    """
    Create PyDeck map showing DVF transactions around user location.
    """
    import numpy as np
    
    # Prepare transaction data
    df = pd.DataFrame(transactions)
    
    if len(df) == 0:
        # Empty map centered on user
        return pdk.Deck(
            initial_view_state=pdk.ViewState(
                latitude=user_lat, longitude=user_lon,
                zoom=15, pitch=0
            ),
            map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
        )
    
    # Color by price relative to user
    median = df['prix_m2'].median()
    
    def get_color(price):
        if price < median * 0.9:
            return [34, 197, 94, 180]   # Green - cheaper
        elif price < median * 1.1:
            return [59, 130, 246, 180]  # Blue - similar
        else:
            return [239, 68, 68, 180]   # Red - more expensive
    
    df['color'] = df['prix_m2'].apply(get_color)
    df['radius'] = 15
    
    # Pre-format tooltip values
    df['prix_m2_fmt'] = df['prix_m2'].apply(lambda x: f"{x:,.0f}".replace(",", " "))
    df['surface_fmt'] = df['surface_totale'].apply(lambda x: f"{x:.0f}")
    df['prix_total_fmt'] = df['valeur_fonciere'].apply(lambda x: f"{x:,.0f}".replace(",", " "))
    df['annee'] = df['mutation_year'].astype(int)
    
    # Transaction layer
    transaction_layer = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position=["longitude", "latitude"],
        get_radius="radius",
        get_fill_color="color",
        pickable=True,
        opacity=0.8,
    )
    
    # User location marker
    user_df = pd.DataFrame([{
        "latitude": user_lat,
        "longitude": user_lon,
        "color": [255, 255, 255, 255],
        "radius": 25
    }])
    
    user_layer = pdk.Layer(
        "ScatterplotLayer",
        data=user_df,
        get_position=["longitude", "latitude"],
        get_radius="radius",
        get_fill_color="color",
        pickable=False,
    )
    
    # Radius circle (approximate)
    # Create circle points
    import math
    circle_points = []
    for angle in range(0, 360, 10):
        rad = math.radians(angle)
        dlat = radius_km / 111 * math.cos(rad)
        dlon = radius_km / (111 * math.cos(math.radians(user_lat))) * math.sin(rad)
        circle_points.append([user_lon + dlon, user_lat + dlat])
    circle_points.append(circle_points[0])  # Close the circle
    
    circle_layer = pdk.Layer(
        "PathLayer",
        data=[{"path": circle_points}],
        get_path="path",
        get_color=[255, 255, 255, 100],
        width_min_pixels=2,
    )
    
    view_state = pdk.ViewState(
        latitude=user_lat,
        longitude=user_lon,
        zoom=15 if radius_km <= 0.5 else 13,
        pitch=0
    )
    
    tooltip = {
        "html": "<b>€{prix_m2_fmt}/m²</b><br/>"
                "{surface_fmt} m² • €{prix_total_fmt}<br/>"
                "{adresse_complete}<br/>"
                "<i>Transaction: {annee}</i>",
        "style": {"backgroundColor": "#1f2937", "color": "white", "fontSize": "12px"}
    }
    
    return pdk.Deck(
        layers=[circle_layer, transaction_layer, user_layer],
        initial_view_state=view_state,
        map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
        tooltip=tooltip
    )
