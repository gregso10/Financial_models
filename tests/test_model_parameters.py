import pytest
from scripts._1_model_params import *

# --- Test Initialization with Defaults ---

def test_model_parameters_default_initialization():
    """Test if the class initializes with default values where specified."""
    params = ModelParameters()

    assert params.property_price == 0.0
    assert params.property_address_city == "Paris" # Check a default string
    assert params.loan_duration_years == 20 # Check a default integer
    assert params.notary_fees_percentage_estimate == 0.08 # Check a default float
    assert isinstance(params.rental_assumptions, dict) # Check if it's a dictionary
    assert "airbnb" in params.rental_assumptions # Check default keys exist
    assert "furnished_1yr" in params.rental_assumptions
    assert "unfurnished_3yr" in params.rental_assumptions
    assert params.rental_assumptions["airbnb"]["occupancy_rate"] == 0.70 # Check a default nested value
    assert params.management_fees_percentage_rent.get("airbnb") == 0.20 # Check another default nested value

# --- Test Initialization with Specific Values ---

def test_model_parameters_specific_initialization():
    """Test if the class correctly stores values passed during initialization."""
    input_values = {
        "property_price": 250000.0,
        "property_size_sqm": 60.0,
        "property_address_city": "Lyon",
        "loan_interest_rate": 0.035,
        "holding_period_years": 15,
        "rental_assumptions": { # Partially override defaults
            "airbnb": {
                "daily_rate": 120.0,
                "occupancy_rate": 0.75,
                "rent_growth_rate": 0.025
            },
            "furnished_1yr": { # Keep defaults for others
                "monthly_rent_sqm": 28.0,
                "vacancy_rate": 0.06,
                "rent_growth_rate": 0.018
            },
            "unfurnished_3yr": { # <<< ADD THIS explicitly using default values
                "monthly_rent_sqm": 10.0, # Default value
                "vacancy_rate": 0.04, # Default value
                "rent_growth_rate": 0.015 # Default value
            }
        },
         "management_fees_percentage_rent": { # Completely override this dict
            "airbnb": 0.22,
            "furnished_1yr": 0.08,
            "unfurnished_3yr": 0.06
        }
    }
    params = ModelParameters(**input_values)

    assert params.property_price == 250000.0
    assert params.property_address_city == "Lyon"
    assert params.loan_interest_rate == 0.035
    assert params.holding_period_years == 15
    # Check overridden nested values
    assert params.rental_assumptions["airbnb"]["daily_rate"] == 120.0
    assert params.rental_assumptions["airbnb"]["occupancy_rate"] == 0.75
    # Check partially overridden structure still contains other keys/defaults
    assert "unfurnished_3yr" in params.rental_assumptions
    assert params.rental_assumptions["unfurnished_3yr"]["vacancy_rate"] == 0.04 # Default value
    # Check fully overridden dictionary
    assert params.management_fees_percentage_rent.get("airbnb") == 0.22
    assert params.management_fees_percentage_rent.get("unfurnished_3yr") == 0.06

# --- Test Helper Method ---

def test_get_lease_assumption_method():
    """Test the helper method for accessing nested rental assumptions."""
    params = ModelParameters()
    # Override one value for testing
    params.rental_assumptions["furnished_1yr"]["monthly_rent_sqm"] = 30.0

    # Test getting existing values
    assert params.get_lease_assumption("furnished_1yr", "monthly_rent_sqm") == 30.0
    assert params.get_lease_assumption("airbnb", "occupancy_rate") == 0.70 # Default

    # Test getting non-existent key with default
    assert params.get_lease_assumption("airbnb", "non_existent_key") is None
    assert params.get_lease_assumption("airbnb", "non_existent_key", default=0.0) == 0.0

    # Test getting non-existent lease type with default
    assert params.get_lease_assumption("non_existent_lease", "monthly_rent_sqm") is None
    assert params.get_lease_assumption("non_existent_lease", "monthly_rent_sqm", default=10.0) == 10.0
