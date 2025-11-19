### Importing libraries ###

import pandas as pd
import numpy as np
import pydeck as pdk
import requests
import time
import io


df = pd.read_csv("/home/greg/code/gregso10/financial_models/real_estate/data/ValeursFoncieres-2025-S1.txt", sep= "|")

# --- 1. Fonction de Nettoyage ---
def clean_dvf_data(df):
    df['id_mutation'] = (df['Date mutation'].astype(str) + '_' + 
                         df['Valeur fonciere'].astype(str) + '_' + 
                         df['No disposition'].astype(str) + '_' + 
                         df['Code commune'].astype(str))

    def analyze_mutation(group):
        first = group.iloc[0]
        # Construction adresse
        num = str(int(first['No voie'])) if pd.notna(first['No voie']) else ""
        type_voie = str(first['Type de voie']) if pd.notna(first['Type de voie']) else ""
        voie = str(first['Voie']) if pd.notna(first['Voie']) else ""
        code_postal = str(int(first['Code postal'])) if pd.notna(first['Code postal']) else ""
        commune = str(first['Commune']) if pd.notna(first['Commune']) else ""
        full_address = f"{num} {type_voie} {voie} {code_postal} {commune}".strip()
        
        return pd.Series({
            'valeur_fonciere': float(str(first['Valeur fonciere']).replace(',', '.')),
            'adresse_complete': full_address,
            'surface_totale': group['Surface reelle bati'].sum()
        })

    # Filtrage Vente uniquement
    return df[df['Nature mutation'] == 'Vente'].groupby('id_mutation').apply(analyze_mutation).reset_index()

def geocode_bulk(df, address_col='adresse_complete'):
    """
    Géocode un DataFrame entier en une seule requête via l'API CSV de la BAN.
    1000 adresses prennent environ 2-5 secondes au lieu de 10 minutes.
    """
    print(f"Envoi de {len(df)} adresses au géocodeur en masse...")
    
    # 1. Conversion du DF en CSV en mémoire (encodage UTF-8)
    csv_buffer = io.BytesIO()
    df.to_csv(csv_buffer, index=False, encoding='utf-8')
    csv_buffer.seek(0)
    
    # 2. Préparation de la requête
    url = "https://api-adresse.data.gouv.fr/search/csv/"
    files = {
        'data': ('data.csv', csv_buffer)
    }
    data = {
        'columns': address_col,  # On précise quelle colonne contient l'adresse
        'result_columns': ['latitude', 'longitude', 'result_score'] # On ne garde que l'essentiel
    }
    
    # 3. Appel API (POST)
    try:
        response = requests.post(url, files=files, data=data)
        response.raise_for_status() # Vérifie les erreurs HTTP
        
        # 4. Lecture de la réponse (CSV) directement dans un DataFrame
        # L'API renvoie le CSV d'origine + les colonnes latitude/longitude
        df_result = pd.read_csv(io.StringIO(response.text))
        
        print("Géocodage terminé avec succès !")
        return df_result
        
    except Exception as e:
        print(f"Erreur lors du géocodage en masse : {e}")
        return df

# --- EXECUTION ---

# On suppose que 'df_clean' existe déjà (créé dans l'étape précédente)
# Si tu as perdu la variable, relance juste la fonction 'clean_dvf_data'
if 'df_clean' in locals():
    # Appel de la fonction rapide
    df_geo = geocode_bulk(df_clean, address_col='adresse_complete')
    
    # Nettoyage des résultats vides (si l'adresse n'a pas été trouvée)
    df_geo = df_geo.dropna(subset=['latitude', 'longitude'])
    
    # Affichage
    print(f"Nombre final d'adresses géolocalisées : {len(df_geo)}")
    display(df_geo.head())
else:
    print("Le DataFrame 'df_clean' n'est pas défini. Veuillez relancer l'étape de nettoyage.")

# --- 1. Création du Gradient de Couleurs (Bleu -> Vert -> Jaune -> Rouge) ---
def get_heatmap_color(normalized_value):
    """
    Renvoie une couleur [R, G, B] selon une échelle thermique (Spectrale).
    0.0 = Bleu (Froid), 0.5 = Vert/Jaune, 1.0 = Rouge (Chaud)
    """
    # On clamp la valeur entre 0 et 1
    v = max(0, min(1, normalized_value))
    
    # Logique simplifiée d'un gradient "Jet" / "Turbo"
    # Bleu (0, 0, 255) -> Cyan (0, 255, 255) -> Vert (0, 255, 0) -> Jaune (255, 255, 0) -> Rouge (255, 0, 0)
    if v < 0.25:
        # Bleu vers Cyan
        return [0, int(v * 4 * 255), 255, 180]
    elif v < 0.5:
        # Cyan vers Vert
        return [0, 255, int(255 - (v - 0.25) * 4 * 255), 180]
    elif v < 0.75:
        # Vert vers Jaune
        return [int((v - 0.5) * 4 * 255), 255, 0, 180]
    else:
        # Jaune vers Rouge
        return [255, int(255 - (v - 0.75) * 4 * 255), 0, 180]

# Appliquer la couleur aux données
max_val = df_geo['valeur_fonciere'].max()
# On utilise le log pour mieux répartir les couleurs si les écarts de prix sont énormes
# (sinon une seule transaction à 10M€ écrase tout le reste en bleu)
import numpy as np
log_max = np.log1p(max_val)

df_geo['color_spectral'] = df_geo['valeur_fonciere'].apply(
    lambda x: get_heatmap_color(np.log1p(x) / log_max)
)

# --- 2. Configuration de la Vue ---
view_state = pdk.ViewState(
    latitude=df_geo['latitude'].mean(),
    longitude=df_geo['longitude'].mean(),
    zoom=13,
    pitch=60,
    bearing=45
)

# --- 3. Couche "Pseudo-Bâtiments" ---
column_layer = pdk.Layer(
    "ColumnLayer",
    data=df_geo,
    get_position=["longitude", "latitude"],
    get_elevation="valeur_fonciere",
    
    # Rendu "Immeuble" (Carré au lieu de Rond)
    radius=25,          # Taille du bâtiment
    diskResolution=4,   # 4 côtés = Carré (C'est l'astuce !)
    angle=45,           # Rotation pour orienter les carrés
    
    elevation_scale=0.001, # Ajuster selon vos montants
    get_fill_color="color_spectral",
    
    pickable=True,
    extruded=True,
    auto_highlight=True,
    
    # Ajout d'un effet de lumière pour le volume
    material={
        "ambient": 0.2,
        "diffuse": 0.8,
        "shininess": 32,
        "specularColor": [255, 255, 255]
    }
)

# --- 4. Rendu avec Lumière ---
# On ajoute une source de lumière pour faire ressortir la 3D (ombres)
r = pdk.Deck(
    layers=[column_layer],
    initial_view_state=view_state,
    map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json", # Fond sombre pour faire ressortir les couleurs
    tooltip={"html": "<b>Prix:</b> {valeur_fonciere} €<br/>{adresse_complete}"}
)

r.to_html("testing3D_layer2.html")