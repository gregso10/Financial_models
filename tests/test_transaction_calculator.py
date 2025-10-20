# In file: tests/test_transaction_calculator.py

import pytest
import numpy_financial as npf
from scripts._1_model_params import ModelParameters
from scripts._5_transaction_calculator import TransactionCalculator # Assuming class name

# --- Helper Fixture ---
@pytest.fixture
def sample_params():
    """Provides a ModelParameters instance for transaction tests."""
    return ModelParameters(
        property_price=200000,
        agency_fees_percentage=0.05, # Assuming % on net seller price
        notary_fees_percentage_estimate=0.08,
        initial_renovation_costs=10000,
        furnishing_costs=5000,
        loan_percentage=0.9, # 90% financing
        loan_interest_rate=0.04,
        loan_duration_years=20,
        loan_insurance_rate=0.003,
        lmnp_amortization_property_years=30, # Needed for amortization base
        lmnp_amortization_furnishing_years=7
    )

# --- Test Initialization ---
def test_calculator_initialization(sample_params):
    """Test if the calculator initializes correctly."""
    calculator = TransactionCalculator(sample_params)
    assert calculator.params == sample_params

def test_calculator_initialization_wrong_type():
    """Test TypeError if params are wrong type."""
    with pytest.raises(TypeError):
        TransactionCalculator("not_a_parameter_object")

# --- Test Calculation Results ---
def test_calculate_all(sample_params):
    """Test the main calculation method returns expected keys and types."""
    calculator = TransactionCalculator(sample_params)
    results = calculator.calculate_all()

    assert isinstance(results, dict)
    expected_keys = [
        "net_seller_price", "agency_fees", "notary_fees",
        "total_acquisition_cost", "loan_amount", "initial_equity",
        "monthly_loan_payment", "yearly_loan_insurance_cost",
        "amortizable_property_value", "yearly_property_amortization",
        "yearly_furnishing_amortization"
    ]
    for key in expected_keys:
        assert key in results
        assert isinstance(results[key], (float, int)) # Check types


def test_acquisition_cost_calculations(sample_params):
    """Test the calculation of various acquisition costs."""
    calculator = TransactionCalculator(sample_params)
    results = calculator.calculate_all()

    # Calculation logic based on assumptions (e.g., agency fees % on net seller)
    # Price FAI = Net Seller * (1 + Agency %) => Net Seller = Price FAI / (1 + Agency %)
    expected_net_seller = 200000 / (1 + 0.05)
    expected_agency_fees = 200000 - expected_net_seller
    # Assuming notary fees on price FAI for simplicity in this test case
    expected_notary_fees = 200000 * 0.08
    expected_total_cost = (200000 + expected_notary_fees +
                           sample_params.initial_renovation_costs +
                           sample_params.furnishing_costs)

    assert results["net_seller_price"] == pytest.approx(expected_net_seller)
    assert results["agency_fees"] == pytest.approx(expected_agency_fees)
    assert results["notary_fees"] == pytest.approx(expected_notary_fees)
    assert results["total_acquisition_cost"] == pytest.approx(expected_total_cost)

def test_financing_calculations(sample_params):
    """Test the calculation of loan, equity, payment, and insurance."""
    calculator = TransactionCalculator(sample_params)
    results = calculator.calculate_all() # Depends on total_acquisition_cost

    expected_total_cost = results["total_acquisition_cost"] # Use calculated total cost
    expected_loan_amount = expected_total_cost * 0.9
    expected_equity = expected_total_cost - expected_loan_amount
    expected_yearly_insurance = expected_loan_amount * 0.003

    # Calculate expected monthly payment
    monthly_rate = 0.04 / 12
    n_periods = 20 * 12
    expected_monthly_payment = 0.0
    if monthly_rate > 0:
        expected_monthly_payment = abs(npf.pmt(monthly_rate, n_periods, expected_loan_amount))

    assert results["loan_amount"] == pytest.approx(expected_loan_amount)
    assert results["initial_equity"] == pytest.approx(expected_equity)
    assert results["yearly_loan_insurance_cost"] == pytest.approx(expected_yearly_insurance)
    assert results["monthly_loan_payment"] == pytest.approx(expected_monthly_payment)

def test_amortization_base_calculations(sample_params):
    """Test the calculation of yearly amortization amounts."""
    calculator = TransactionCalculator(sample_params)
    results = calculator.calculate_all() # Depends on net_seller_price

    # Assuming land value is 15% of net seller price
    expected_amortizable_property = results["net_seller_price"] * (1 - 0.15)
    expected_yearly_prop_amort = expected_amortizable_property / 30 if sample_params.lmnp_amortization_property_years > 0 else 0
    expected_yearly_furn_amort = sample_params.furnishing_costs / 7 if sample_params.lmnp_amortization_furnishing_years > 0 else 0

    assert results["amortizable_property_value"] == pytest.approx(expected_amortizable_property)
    assert results["yearly_property_amortization"] == pytest.approx(expected_yearly_prop_amort)
    assert results["yearly_furnishing_amortization"] == pytest.approx(expected_yearly_furn_amort)
