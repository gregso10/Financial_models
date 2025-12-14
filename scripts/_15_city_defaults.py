# scripts/_15_city_defaults.py
"""
Default parameters by city and region for simplified investment mode.
Easy to edit - just update the dictionaries below.

Sources: INSEE, notaires de France, observatoires locaux (2024 estimates)
"""

from typing import Dict, Any

# === MAJOR CITIES ===
CITY_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "Paris": {
        "notary_pct": 0.08,
        "property_tax_per_sqm": 18,       # €/m²/an (taxe foncière)
        "condo_fees_per_sqm": 5.0,        # €/m²/mois
        "pno_insurance": 250,             # €/an
        "vacancy_rate": 0.03,             # 3% - forte demande
        "price_growth": 0.015,            # 1.5%/an - marché mature
        "rent_per_sqm_furnished": 35,     # €/m²/mois meublé
        "rent_per_sqm_unfurnished": 28,   # €/m²/mois nu
        "management_fee_pct": 0.08,       # 8% gestion
    },
    "Lyon": {
        "notary_pct": 0.08,
        "property_tax_per_sqm": 14,
        "condo_fees_per_sqm": 3.8,
        "pno_insurance": 180,
        "vacancy_rate": 0.04,
        "price_growth": 0.02,
        "rent_per_sqm_furnished": 22,
        "rent_per_sqm_unfurnished": 17,
        "management_fee_pct": 0.07,
    },
    "Marseille": {
        "notary_pct": 0.08,
        "property_tax_per_sqm": 16,
        "condo_fees_per_sqm": 3.2,
        "pno_insurance": 200,
        "vacancy_rate": 0.06,
        "price_growth": 0.025,
        "rent_per_sqm_furnished": 18,
        "rent_per_sqm_unfurnished": 14,
        "management_fee_pct": 0.07,
    },
    "Bordeaux": {
        "notary_pct": 0.08,
        "property_tax_per_sqm": 15,
        "condo_fees_per_sqm": 3.5,
        "pno_insurance": 170,
        "vacancy_rate": 0.05,
        "price_growth": 0.02,
        "rent_per_sqm_furnished": 20,
        "rent_per_sqm_unfurnished": 15,
        "management_fee_pct": 0.07,
    },
    "Nantes": {
        "notary_pct": 0.08,
        "property_tax_per_sqm": 13,
        "condo_fees_per_sqm": 3.2,
        "pno_insurance": 160,
        "vacancy_rate": 0.04,
        "price_growth": 0.022,
        "rent_per_sqm_furnished": 18,
        "rent_per_sqm_unfurnished": 14,
        "management_fee_pct": 0.07,
    },
    "Toulouse": {
        "notary_pct": 0.08,
        "property_tax_per_sqm": 14,
        "condo_fees_per_sqm": 3.3,
        "pno_insurance": 165,
        "vacancy_rate": 0.05,
        "price_growth": 0.02,
        "rent_per_sqm_furnished": 17,
        "rent_per_sqm_unfurnished": 13,
        "management_fee_pct": 0.07,
    },
    "Nice": {
        "notary_pct": 0.08,
        "property_tax_per_sqm": 17,
        "condo_fees_per_sqm": 4.2,
        "pno_insurance": 220,
        "vacancy_rate": 0.05,
        "price_growth": 0.018,
        "rent_per_sqm_furnished": 24,
        "rent_per_sqm_unfurnished": 19,
        "management_fee_pct": 0.08,
    },
    "Lille": {
        "notary_pct": 0.08,
        "property_tax_per_sqm": 16,
        "condo_fees_per_sqm": 3.0,
        "pno_insurance": 155,
        "vacancy_rate": 0.05,
        "price_growth": 0.02,
        "rent_per_sqm_furnished": 17,
        "rent_per_sqm_unfurnished": 13,
        "management_fee_pct": 0.07,
    },
    "Strasbourg": {
        "notary_pct": 0.08,
        "property_tax_per_sqm": 12,
        "condo_fees_per_sqm": 3.0,
        "pno_insurance": 160,
        "vacancy_rate": 0.04,
        "price_growth": 0.02,
        "rent_per_sqm_furnished": 16,
        "rent_per_sqm_unfurnished": 12,
        "management_fee_pct": 0.07,
    },
}

# === REGIONS (13 métropolitaines) ===
REGION_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "Île-de-France": {
        "notary_pct": 0.08,
        "property_tax_per_sqm": 15,
        "condo_fees_per_sqm": 4.0,
        "pno_insurance": 200,
        "vacancy_rate": 0.04,
        "price_growth": 0.018,
        "rent_per_sqm_furnished": 25,
        "rent_per_sqm_unfurnished": 20,
        "management_fee_pct": 0.07,
    },
    "Auvergne-Rhône-Alpes": {
        "notary_pct": 0.08,
        "property_tax_per_sqm": 12,
        "condo_fees_per_sqm": 3.2,
        "pno_insurance": 160,
        "vacancy_rate": 0.05,
        "price_growth": 0.02,
        "rent_per_sqm_furnished": 16,
        "rent_per_sqm_unfurnished": 12,
        "management_fee_pct": 0.07,
    },
    "Provence-Alpes-Côte d'Azur": {
        "notary_pct": 0.08,
        "property_tax_per_sqm": 15,
        "condo_fees_per_sqm": 3.8,
        "pno_insurance": 190,
        "vacancy_rate": 0.06,
        "price_growth": 0.02,
        "rent_per_sqm_furnished": 20,
        "rent_per_sqm_unfurnished": 15,
        "management_fee_pct": 0.07,
    },
    "Occitanie": {
        "notary_pct": 0.08,
        "property_tax_per_sqm": 13,
        "condo_fees_per_sqm": 3.0,
        "pno_insurance": 155,
        "vacancy_rate": 0.06,
        "price_growth": 0.02,
        "rent_per_sqm_furnished": 15,
        "rent_per_sqm_unfurnished": 11,
        "management_fee_pct": 0.07,
    },
    "Nouvelle-Aquitaine": {
        "notary_pct": 0.08,
        "property_tax_per_sqm": 12,
        "condo_fees_per_sqm": 3.0,
        "pno_insurance": 150,
        "vacancy_rate": 0.06,
        "price_growth": 0.02,
        "rent_per_sqm_furnished": 15,
        "rent_per_sqm_unfurnished": 11,
        "management_fee_pct": 0.07,
    },
    "Pays de la Loire": {
        "notary_pct": 0.08,
        "property_tax_per_sqm": 11,
        "condo_fees_per_sqm": 2.8,
        "pno_insurance": 145,
        "vacancy_rate": 0.05,
        "price_growth": 0.02,
        "rent_per_sqm_furnished": 14,
        "rent_per_sqm_unfurnished": 11,
        "management_fee_pct": 0.07,
    },
    "Bretagne": {
        "notary_pct": 0.08,
        "property_tax_per_sqm": 10,
        "condo_fees_per_sqm": 2.5,
        "pno_insurance": 140,
        "vacancy_rate": 0.05,
        "price_growth": 0.02,
        "rent_per_sqm_furnished": 13,
        "rent_per_sqm_unfurnished": 10,
        "management_fee_pct": 0.07,
    },
    "Hauts-de-France": {
        "notary_pct": 0.08,
        "property_tax_per_sqm": 14,
        "condo_fees_per_sqm": 2.8,
        "pno_insurance": 150,
        "vacancy_rate": 0.06,
        "price_growth": 0.015,
        "rent_per_sqm_furnished": 13,
        "rent_per_sqm_unfurnished": 10,
        "management_fee_pct": 0.07,
    },
    "Grand Est": {
        "notary_pct": 0.08,
        "property_tax_per_sqm": 11,
        "condo_fees_per_sqm": 2.6,
        "pno_insurance": 145,
        "vacancy_rate": 0.06,
        "price_growth": 0.015,
        "rent_per_sqm_furnished": 12,
        "rent_per_sqm_unfurnished": 9,
        "management_fee_pct": 0.07,
    },
    "Normandie": {
        "notary_pct": 0.08,
        "property_tax_per_sqm": 11,
        "condo_fees_per_sqm": 2.5,
        "pno_insurance": 140,
        "vacancy_rate": 0.06,
        "price_growth": 0.015,
        "rent_per_sqm_furnished": 12,
        "rent_per_sqm_unfurnished": 9,
        "management_fee_pct": 0.07,
    },
    "Bourgogne-Franche-Comté": {
        "notary_pct": 0.08,
        "property_tax_per_sqm": 10,
        "condo_fees_per_sqm": 2.4,
        "pno_insurance": 135,
        "vacancy_rate": 0.07,
        "price_growth": 0.012,
        "rent_per_sqm_furnished": 11,
        "rent_per_sqm_unfurnished": 8,
        "management_fee_pct": 0.07,
    },
    "Centre-Val de Loire": {
        "notary_pct": 0.08,
        "property_tax_per_sqm": 10,
        "condo_fees_per_sqm": 2.4,
        "pno_insurance": 135,
        "vacancy_rate": 0.06,
        "price_growth": 0.015,
        "rent_per_sqm_furnished": 11,
        "rent_per_sqm_unfurnished": 9,
        "management_fee_pct": 0.07,
    },
    "Corse": {
        "notary_pct": 0.08,
        "property_tax_per_sqm": 8,
        "condo_fees_per_sqm": 2.8,
        "pno_insurance": 180,
        "vacancy_rate": 0.08,
        "price_growth": 0.02,
        "rent_per_sqm_furnished": 16,
        "rent_per_sqm_unfurnished": 12,
        "management_fee_pct": 0.08,
    },
}

# === FALLBACK DEFAULT ===
DEFAULT_VALUES: Dict[str, Any] = {
    "notary_pct": 0.08,
    "property_tax_per_sqm": 12,
    "condo_fees_per_sqm": 3.0,
    "pno_insurance": 150,
    "vacancy_rate": 0.05,
    "price_growth": 0.02,
    "rent_per_sqm_furnished": 15,
    "rent_per_sqm_unfurnished": 11,
    "management_fee_pct": 0.07,
}

# === FIXED DEFAULTS (same everywhere) ===
FIXED_DEFAULTS: Dict[str, Any] = {
    "loan_duration_years": 20,
    "loan_insurance_rate": 0.003,
    "maintenance_pct": 0.05,
    "tmi": 0.30,
    "social_contributions": 0.172,
    "holding_period_years": 10,
    "risk_free_rate": 0.035,
    "discount_rate": 0.05,
    "expenses_growth": 0.02,
    "rent_growth": 0.015,
}


def get_location_defaults(location: str) -> Dict[str, Any]:
    """
    Get defaults for a city or region.
    Falls back to DEFAULT_VALUES if not found.
    """
    # Check cities first
    if location in CITY_DEFAULTS:
        return {**DEFAULT_VALUES, **CITY_DEFAULTS[location]}
    
    # Check regions
    if location in REGION_DEFAULTS:
        return {**DEFAULT_VALUES, **REGION_DEFAULTS[location]}
    
    # Fallback
    return DEFAULT_VALUES.copy()


def get_all_locations() -> list:
    """Return sorted list of all available locations (cities first, then regions)."""
    cities = sorted(CITY_DEFAULTS.keys())
    regions = sorted(REGION_DEFAULTS.keys())
    return ["-- Villes --"] + cities + ["-- Régions --"] + regions


def get_selectable_locations() -> list:
    """Return flat list for selectbox (no separators)."""
    cities = sorted(CITY_DEFAULTS.keys())
    regions = sorted(REGION_DEFAULTS.keys())
    return cities + regions
