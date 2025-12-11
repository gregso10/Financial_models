# In file: scripts/_1_model_params.py

from dataclasses import dataclass, field
from typing import Dict, Optional, List # Import Dict and Optional for type hinting

@dataclass
class ModelParameters:
    """
    Stores user input parameters for the real estate financial model.
    Designed to hold raw inputs before complex calculations or rule applications.
    Parameters dependent on lease type are stored in dictionaries.
    """
    # --- Property & Acquisition ---
    property_address_city: str = "Paris" # Example: City for location-specific rules
    property_address_zipcode: Optional[str] = None # Optional: More specific location
    property_price: float = 0.0 # Prix d'achat FAI in Euros
    agency_fees_percentage: float = 0.0 # % frais d'agence (sur prix net vendeur, if applicable)
    notary_fees_percentage_estimate: float = 0.08 # Estimation initiale % frais de notaire
    property_size_sqm: float = 1.0 # Surface en m²
    initial_renovation_costs: float = 0.0 # Coût travaux initiaux en Euros
    furnishing_costs: float = 0.0 # Coût ameublement (pour meublé/Airbnb)

    # --- Financing ---
    loan_percentage: float = 1.0 # % du coût total financé par emprunt
    loan_interest_rate: float = 0.04 # Taux d'intérêt annuel nominal
    loan_duration_years: int = 20 # Durée du prêt en années
    loan_insurance_rate: float = 0.003 # Taux annuel assurance emprunteur (sur K initial)

    # --- Rental Income (Lease Type Dependent) ---
    # User inputs their *target* rents and vacancy assumptions per lease type
    rental_assumptions: Dict[str, Dict] = field(default_factory=lambda: {
        "airbnb": {
            "daily_rate": 0.0,
            "occupancy_rate": 0.70,
            "rent_growth_rate": 0.02,
            # Added: Monthly seasonality factors (Jan=index 0 to Dec=index 11)
            "monthly_seasonality": [0.8, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.2, 1.0, 0.9, 0.8, 0.8]
        },
        "furnished_1yr": {
            "monthly_rent_sqm": 0.0,
            "vacancy_rate": 0.08, # e.g., ~1 month / year
            "rent_growth_rate": 0.015
        },
        "unfurnished_3yr": {
            "monthly_rent_sqm": 0.0,
            "vacancy_rate": 0.04, # e.g., ~0.5 month / year
            "rent_growth_rate": 0.015
        }
    })

    # --- Operating Expenses ---
    property_tax_yearly: float = 0.0 # Taxe foncière annuelle en Euros
    condo_fees_monthly: float = 0.0 # Charges copropriété mensuelles
    maintenance_percentage_rent: float = 0.05 # % loyer annuel brut pour entretien
    pno_insurance_yearly: float = 0.0 # Assurance PNO annuelle
    # Management fees might also depend on lease type (e.g., higher for Airbnb)
    management_fees_percentage_rent: Dict[str, float] = field(default_factory=lambda: {
        "airbnb": 0.20, # Higher % for short-term rental management
        "furnished_1yr": 0.07,
        "unfurnished_3yr": 0.07
    })
    # Specific Airbnb costs (platform fees, cleaning etc.) could be added here or calculated later
    airbnb_specific_costs_percentage_rent: float = 0.15 # e.g., Platform + Cleaning fees as % of Airbnb rent
    expenses_growth_rate: float = 0.02 # Croissance annuelle des charges (hors gestion)

    # --- Fiscal Parameters ---
    # These might vary significantly based on lease type and structure (e.g., SCI vs Nom Propre)
    # Keeping it simple for now, assuming LMNP Réel for furnished/Airbnb
    fiscal_regime: str = "LMNP Réel" # Example, could be user choice
    lmnp_amortization_property_years: int = 30
    lmnp_amortization_furnishing_years: int = 7
    lmnp_amortization_renovation_years: int = 7
    personal_income_tax_bracket: float = 0.30 # TMI
    social_contributions_rate: float = 0.172 # Prélèvements Sociaux

    # --- Exit Parameters ---
    holding_period_years: int = 10
    property_value_growth_rate: float = 0.02
    exit_selling_fees_percentage: float = 0.05

    # --- Investment Analysis Parameters ---
    risk_free_rate: float = 0.035  # French OAT 20-year rate (~3.5%)
    discount_rate: float = 0.05    # Project discount rate (includes risk premium)

    # --- Calculated Values (Minimal - moved to orchestrator/statements) ---
    # We keep only things directly derivable without complex logic or time series

    # Example method to get a specific lease type's assumption easily
    def get_lease_assumption(self, lease_type: str, key: str, default=None):
        """Helper to safely get a value from the rental_assumptions dictionary."""
        return self.rental_assumptions.get(lease_type, {}).get(key, default)
