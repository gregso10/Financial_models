# In file: tests/test_profit_and_loss.py

import pytest
import pandas as pd
from scripts._1_model_params import ModelParameters
from scripts._2_profit_and_loss import PnL # Assuming class PnL in this file

# --- Helper Fixture to create default parameters ---
@pytest.fixture
def default_params():
    """Provides a default ModelParameters instance for tests."""
    params = ModelParameters(
        property_price=200000, property_size_sqm=50,
        loan_percentage=1.0, loan_interest_rate=0.04, loan_duration_years=20, loan_insurance_rate=0.003,
        initial_renovation_costs=10000, furnishing_costs=5000,
        holding_period_years=10, # Default holding period for tests
        rental_assumptions = {
            "airbnb": {"daily_rate": 80, "occupancy_rate": 0.7, "rent_growth_rate": 0.02,
                       "monthly_seasonality": [0.8, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.2, 1.0, 0.9, 0.8, 0.8]},
            "furnished_1yr": {"monthly_rent_sqm": 25, "vacancy_rate": 0.08, "rent_growth_rate": 0.015},
            "unfurnished_3yr": {"monthly_rent_sqm": 20, "vacancy_rate": 0.04, "rent_growth_rate": 0.015}
         },
        property_tax_yearly=800, condo_fees_monthly=100, pno_insurance_yearly=150,
        maintenance_percentage_rent=0.05,
        management_fees_percentage_rent= {"airbnb": 0.20, "furnished_1yr": 0.07, "unfurnished_3yr": 0.07},
        airbnb_specific_costs_percentage_rent=0.15,
        expenses_growth_rate=0.02,
        fiscal_regime="LMNP Réel", # Important for depreciation tests
        lmnp_amortization_property_years=30,
        lmnp_amortization_furnishing_years=7
    )
    return params

# --- Test Initialization ---
def test_pnl_initialization(default_params):
    """Test if PnL class initializes correctly with parameters."""
    pnl_calculator = PnL(default_params)
    assert pnl_calculator.params == default_params
    assert pnl_calculator.params.holding_period_years == 10 # Check a param value

def test_pnl_initialization_wrong_type():
    """Test that TypeError is raised if params are not ModelParameters."""
    with pytest.raises(TypeError):
        PnL("not_a_parameter_object")

# --- Test DataFrame Generation ---
@pytest.mark.parametrize("lease_type", ["airbnb", "furnished_1yr", "unfurnished_3yr"])
def test_generate_pnl_dataframe_structure(default_params, lease_type):
    """Test the basic structure (shape, index, columns) of the generated DataFrame."""
    pnl_calculator = PnL(default_params)
    df_pnl = pnl_calculator.generate_pnl_dataframe(lease_type)

    assert isinstance(df_pnl, pd.DataFrame)

    expected_months = default_params.holding_period_years * 12
    assert len(df_pnl) == expected_months
    assert df_pnl.index.name == "Month"
    assert list(df_pnl.index) == list(range(1, expected_months + 1)) # Index should be 1 to num_months

    # Check common columns exist
    common_cols = ["Year", "Gross Potential Rent", #"Vacancy Loss", <-- Temporarily remove or handle conditionally
                   "Gross Operating Income",
                   "Property Tax", "Condo Fees", "PNO Insurance", "Maintenance",
                   "Management Fees", "Total Operating Expenses", "Net Operating Income",
                   "Loan Interest", "Loan Insurance", "Depreciation/Amortization",
                   "Taxable Income", "Income Tax", "Social Contributions", "Total Taxes",
                   "Net Income"]

    # Add lease-specific expectations to common_cols BEFORE the loop
    if lease_type != "airbnb":
        common_cols.insert(2, "Vacancy Loss") # Add Vacancy Loss if NOT Airbnb

    for col in common_cols:
         assert col in df_pnl.columns # Now this check adapts

    # Check lease-specific columns (This part remains the same)
    if lease_type == "airbnb":
        assert "Airbnb Specific Costs" in df_pnl.columns
        assert "Vacancy Loss" not in df_pnl.columns # Explicitly check it's NOT there
    else:
        assert "Airbnb Specific Costs" not in df_pnl.columns # Explicitly check it's NOT there
        assert "Vacancy Loss" in df_pnl.columns # It should be there

# --- Test Specific Calculations (Simplified Examples) ---
# Add more detailed tests for specific months/years and edge cases

def test_furnished_revenue_calculation(default_params):
    """Test furnished rent calculation for specific months, including growth."""
    pnl_calculator = PnL(default_params)
    df_pnl = pnl_calculator.generate_pnl_dataframe("furnished_1yr")

    params = default_params
    base_monthly_rent = params.rental_assumptions["furnished_1yr"]["monthly_rent_sqm"] * params.property_size_sqm
    growth = params.rental_assumptions["furnished_1yr"]["rent_growth_rate"]
    vacancy = params.rental_assumptions["furnished_1yr"]["vacancy_rate"]

    # Month 1 (Year 1)
    expected_potential_rent_m1 = base_monthly_rent * (1 + growth)**0
    expected_vacancy_loss_m1 = expected_potential_rent_m1 * (vacancy / 12) # Distribute annual vacancy
    expected_goi_m1 = expected_potential_rent_m1 - expected_vacancy_loss_m1
    assert df_pnl.loc[1, "Gross Potential Rent"] == pytest.approx(expected_potential_rent_m1)
    # Vacancy loss might be calculated differently (e.g., specific months vacant), this is simplified
    # assert df_pnl.loc[1, "Vacancy Loss"] == pytest.approx(expected_vacancy_loss_m1)
    assert df_pnl.loc[1, "Gross Operating Income"] == pytest.approx(expected_goi_m1)

    # Month 13 (Start of Year 2)
    expected_potential_rent_m13 = base_monthly_rent * (1 + growth)**1
    expected_vacancy_loss_m13 = expected_potential_rent_m13 * (vacancy / 12)
    expected_goi_m13 = expected_potential_rent_m13 - expected_vacancy_loss_m13
    assert df_pnl.loc[13, "Gross Potential Rent"] == pytest.approx(expected_potential_rent_m13)
    assert df_pnl.loc[13, "Gross Operating Income"] == pytest.approx(expected_goi_m13)

def test_airbnb_revenue_calculation(default_params):
    """Test Airbnb rent calculation, including seasonality and growth."""
    pnl_calculator = PnL(default_params)
    df_pnl = pnl_calculator.generate_pnl_dataframe("airbnb")

    params = default_params
    daily_rate = params.rental_assumptions["airbnb"]["daily_rate"]
    occupancy = params.rental_assumptions["airbnb"]["occupancy_rate"]
    growth = params.rental_assumptions["airbnb"]["rent_growth_rate"]
    seasonality = params.rental_assumptions["airbnb"]["monthly_seasonality"] # List of 12 factors
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31] # Approx. no leap years

    # Month 1 (Jan - Year 1)
    expected_potential_rent_m1 = daily_rate * days_in_month[0] * (1 + growth)**0
    # Vacancy is handled by occupancy for Airbnb
    expected_goi_m1 = expected_potential_rent_m1 * occupancy * seasonality[0]
    assert df_pnl.loc[1, "Gross Potential Rent"] == pytest.approx(expected_potential_rent_m1)
    assert df_pnl.loc[1, "Gross Operating Income"] == pytest.approx(expected_goi_m1)
    # Month 13 (Jan - Year 2)
    expected_potential_rent_m13 = daily_rate * days_in_month[0] * (1 + growth)**1
    expected_goi_m13 = expected_potential_rent_m13 * occupancy * seasonality[0]
    assert df_pnl.loc[13, "Gross Potential Rent"] == pytest.approx(expected_potential_rent_m13)
    assert df_pnl.loc[13, "Gross Operating Income"] == pytest.approx(expected_goi_m13)

def test_expense_calculation(default_params):
    """Test calculation of operating expenses, including growth."""
    pnl_calculator = PnL(default_params)
    df_pnl_furn = pnl_calculator.generate_pnl_dataframe("furnished_1yr")

    params = default_params
    exp_growth = params.expenses_growth_rate

    # Month 1 (Year 1)
    expected_tax_m1 = (params.property_tax_yearly / 12) * (1 + exp_growth)**0
    expected_condo_m1 = params.condo_fees_monthly * (1 + exp_growth)**0
    goi_m1 = df_pnl_furn.loc[1, "Gross Operating Income"]
    expected_maint_m1 = goi_m1 * params.maintenance_percentage_rent # Based on monthly GOI
    mgnt_rate_furn = params.management_fees_percentage_rent["furnished_1yr"]
    expected_mgmt_m1 = goi_m1 * mgnt_rate_furn # Based on monthly GOI

    assert df_pnl_furn.loc[1, "Property Tax"] == pytest.approx(expected_tax_m1)
    assert df_pnl_furn.loc[1, "Condo Fees"] == pytest.approx(expected_condo_m1)
    assert df_pnl_furn.loc[1, "Maintenance"] == pytest.approx(expected_maint_m1)
    assert df_pnl_furn.loc[1, "Management Fees"] == pytest.approx(expected_mgmt_m1)

    # Month 13 (Year 2)
    expected_tax_m13 = (params.property_tax_yearly / 12) * (1 + exp_growth)**1
    expected_condo_m13 = params.condo_fees_monthly * (1 + exp_growth)**1

    assert df_pnl_furn.loc[13, "Property Tax"] == pytest.approx(expected_tax_m13)
    assert df_pnl_furn.loc[13, "Condo Fees"] == pytest.approx(expected_condo_m13)

# TODO: Add tests for Interest, Depreciation, Taxes, Net Income for different scenarios.
