# In file: tests/test_balance_sheet.py

import pytest
import pandas as pd
from scripts._1_model_params import ModelParameters
from scripts._2_profit_and_loss import PnL # Needed to generate PnL results for BS input
from scripts._3_balance_sheet import BalanceSheet # Assuming class BalanceSheet in this file

# --- Helper Fixture to create default parameters and initial PnL ---
# In file: tests/test_balance_sheet.py
import pytest
import pandas as pd
import numpy_financial as npf # Make sure this is imported
from scripts._1_model_params import ModelParameters
from scripts._2_profit_and_loss import PnL
from scripts._3_balance_sheet import BalanceSheet
from scripts._4_cash_flow import CashFlow # <-- Import CashFlow

@pytest.fixture
def setup_bs_data_final():
    """Provides params, pnl_df, and cf_df for final Balance Sheet tests."""
    # --- Parameter setup (same as before) ---
    params = ModelParameters(
        property_price=200000, property_size_sqm=50, notary_fees_percentage_estimate=0.08,
        loan_percentage=0.9, loan_interest_rate=0.04, loan_duration_years=20, loan_insurance_rate=0.003,
        initial_renovation_costs=10000, furnishing_costs=5000,
        holding_period_years=10,
        rental_assumptions = {
            "airbnb": {"daily_rate": 80, "occupancy_rate": 0.7, "rent_growth_rate": 0.02, "monthly_seasonality": [0.8]*12},
            "furnished_1yr": {"monthly_rent_sqm": 25, "vacancy_rate": 0.08, "rent_growth_rate": 0.015},
            "unfurnished_3yr": {"monthly_rent_sqm": 20, "vacancy_rate": 0.04, "rent_growth_rate": 0.015}
         },
        property_tax_yearly=800, condo_fees_monthly=100, pno_insurance_yearly=150,
        fiscal_regime="LMNP Réel",
        lmnp_amortization_property_years=30, lmnp_amortization_furnishing_years=7
    )
    # --- Perform Calculations (Simulating Orchestrator/TransactionCalculator - same as before) ---
    notary_fees_calc = params.property_price * params.notary_fees_percentage_estimate
    total_acquisition_cost_calc = (params.property_price + notary_fees_calc + params.initial_renovation_costs + params.furnishing_costs)
    loan_amount_calc = total_acquisition_cost_calc * params.loan_percentage
    initial_equity_calc = total_acquisition_cost_calc - loan_amount_calc
    monthly_loan_payment_calc = 0.0
    if params.loan_duration_years > 0 and params.loan_interest_rate > 0:
        monthly_rate = params.loan_interest_rate / 12; n_periods = params.loan_duration_years * 12
        monthly_loan_payment_calc = abs(npf.pmt(monthly_rate, n_periods, loan_amount_calc))
    yearly_loan_insurance_cost_calc = loan_amount_calc * params.loan_insurance_rate
    land_value_percentage = 0.15
    amortizable_property_value_calc = params.property_price * (1 - land_value_percentage)
    yearly_property_amortization_calc = amortizable_property_value_calc / params.lmnp_amortization_property_years if params.lmnp_amortization_property_years > 0 else 0
    yearly_furnishing_amortization_calc = params.furnishing_costs / params.lmnp_amortization_furnishing_years if params.lmnp_amortization_furnishing_years > 0 and params.furnishing_costs > 0 else 0
    setattr(params, 'notary_fees', notary_fees_calc); setattr(params, 'total_acquisition_cost', total_acquisition_cost_calc)
    setattr(params, 'loan_amount', loan_amount_calc); setattr(params, 'initial_equity', initial_equity_calc)
    setattr(params, 'monthly_loan_payment', monthly_loan_payment_calc); setattr(params, 'yearly_loan_insurance_cost', yearly_loan_insurance_cost_calc)
    setattr(params, 'amortizable_property_value', amortizable_property_value_calc); setattr(params, 'yearly_property_amortization', yearly_property_amortization_calc)
    setattr(params, 'yearly_furnishing_amortization', yearly_furnishing_amortization_calc)
    # --- End Calculations ---

    # --- Generate PnL ---
    pnl_calculator = PnL(params)
    pnl_df = pnl_calculator.generate_pnl_dataframe(lease_type="furnished_1yr")

    # --- Generate Placeholder BS for CF Input ---
    # Create a temporary BS instance *just for the old cash logic*
    # You could alternatively copy the old generate method here temporarily
    bs_calculator_temp = BalanceSheet(params)
    # Temporarily revert cash logic inside this instance for the placeholder calculation
    # (This is a bit hacky for a test fixture, but demonstrates the need)
    # A cleaner way might be to have a dedicated method for placeholder BS generation

    # --- Simpler approach: Simulate the placeholder BS directly ---
    num_months_temp = params.holding_period_years * 12
    placeholder_bs_data = {'Cash': [params.initial_equity], 'Loan Balance': [params.loan_amount]}
    monthly_pay = getattr(params, 'monthly_loan_payment', 0.0)
    for m in range(1, num_months_temp + 1):
        prev_cash = placeholder_bs_data['Cash'][-1]
        prev_loan = placeholder_bs_data['Loan Balance'][-1]
        ni = pnl_df.loc[m].get("Net Income", 0.0)
        intr = pnl_df.loc[m].get("Loan Interest", 0.0)
        princ = max(0, monthly_pay - intr) if m <= params.loan_duration_years * 12 else 0
        placeholder_bs_data['Cash'].append(prev_cash + ni - princ) # Old placeholder logic
        placeholder_bs_data['Loan Balance'].append(max(0, prev_loan - princ))

    bs_df_placeholder = pd.DataFrame({
        'Cash': placeholder_bs_data['Cash'],
        'Loan Balance': placeholder_bs_data['Loan Balance']
        }, index=range(0, num_months_temp + 1))
    bs_df_placeholder.index.name="Month"
    # --- End Placeholder BS Generation ---

    # --- Generate CF ---
    cf_calculator = CashFlow(params)
    cf_df = cf_calculator.generate_cf_dataframe(pnl_df, bs_df_placeholder) # Use placeholder BS here

    # --- Return final needed data ---
    return {"params": params, "pnl_df": pnl_df, "cf_df": cf_df} # Return the *correct* CF df


# --- Test Initialization (No changes needed) ---
def test_balance_sheet_initialization(setup_bs_data_final):
    params = setup_bs_data_final["params"]
    bs_calculator = BalanceSheet(params)
    assert bs_calculator.params == params
    assert bs_calculator._initial_property_cost > 0
    assert bs_calculator._initial_furnishing_cost == params.furnishing_costs
    assert bs_calculator._initial_loan_balance > 0
    assert bs_calculator._initial_equity >= 0 # Check >= 0


# --- Updated DataFrame Generation Test ---
def test_generate_bs_dataframe_structure(setup_bs_data_final):
    """Test the structure of the BS DataFrame (now using CF results)."""
    params = setup_bs_data_final["params"]
    pnl_df = setup_bs_data_final["pnl_df"]
    cf_df = setup_bs_data_final["cf_df"] # <-- Get CF results
    bs_calculator = BalanceSheet(params)

    # Pass cf_df to the generate method
    df_bs = bs_calculator.generate_bs_dataframe(pnl_df, cf_df) # <-- Pass cf_df

    assert isinstance(df_bs, pd.DataFrame)
    expected_months = params.holding_period_years * 12
    assert len(df_bs) == expected_months + 1
    assert df_bs.index.name == "Month"
    assert list(df_bs.index) == list(range(0, expected_months + 1))

    expected_cols = [ # (Column list remains the same)
        "Year", "Property Cost", "Property Accumulated Depreciation", "Property Net Value",
        "Furnishing Cost", "Furnishing Accumulated Depreciation", "Furnishing Net Value",
        "Total Fixed Assets", "Cash", "Total Assets", "Loan Balance",
        "Total Liabilities", "Initial Equity", "Retained Earnings",
        "Total Equity", "Total Liabilities and Equity", "Balance Check"
    ]
    for col in expected_cols:
         assert col in df_bs.columns

def test_initial_balance_sheet_state(setup_bs_data_final):
    """Test the values at Month 0 (initial state)."""
    params = setup_bs_data_final["params"]
    pnl_df = setup_bs_data_final["pnl_df"]
    cf_df = setup_bs_data_final["cf_df"] # Need cf_df to call the method
    bs_calculator = BalanceSheet(params)
    df_bs = bs_calculator.generate_bs_dataframe(pnl_df, cf_df) # Pass cf_df

    initial_state = df_bs.loc[0]

    # Use the value calculated in BS init
    assert initial_state["Property Cost"] == pytest.approx(bs_calculator._initial_property_cost)
    assert initial_state["Property Accumulated Depreciation"] == 0
    assert initial_state["Furnishing Cost"] == pytest.approx(params.furnishing_costs)
    assert initial_state["Furnishing Accumulated Depreciation"] == 0

    # --- CORRECTED ASSERTION ---
    assert initial_state["Cash"] == pytest.approx(0.0) # Initial cash should be 0 post-transaction
    # --- END CORRECTION ---

    assert initial_state["Loan Balance"] == pytest.approx(params.loan_amount)
    assert initial_state["Initial Equity"] == pytest.approx(params.initial_equity)
    assert initial_state["Retained Earnings"] == 0

    # Check balance (should balance now for Month 0)
    assert initial_state["Total Assets"] == pytest.approx(initial_state["Total Liabilities and Equity"])
    assert initial_state["Balance Check"] == pytest.approx(0.0, abs=1e-6)

# --- Updated Evolution Test ---
def test_balance_sheet_evolution(setup_bs_data_final):
    """Test how key items evolve, checking cash from CF and overall balance."""
    params = setup_bs_data_final["params"]
    pnl_df = setup_bs_data_final["pnl_df"]
    cf_df = setup_bs_data_final["cf_df"] # <-- Get CF results
    bs_calculator = BalanceSheet(params)
    df_bs = bs_calculator.generate_bs_dataframe(pnl_df, cf_df) # <-- Pass cf_df

    # --- Month 1 ---
    state_m0 = df_bs.loc[0]
    state_m1 = df_bs.loc[1]
    pnl_m1 = pnl_df.loc[1]
    cf_m1 = cf_df.loc[1] # <-- Get CF results for month 1

    # Depreciation assertions remain the same
    monthly_prop_dep = bs_calculator._monthly_property_depreciation
    monthly_furn_dep = bs_calculator._monthly_furnishing_depreciation
    expected_prop_dep_m1 = state_m0["Property Accumulated Depreciation"] + monthly_prop_dep
    expected_furn_dep_m1 = state_m0["Furnishing Accumulated Depreciation"] + monthly_furn_dep
    assert state_m1["Property Accumulated Depreciation"] == pytest.approx(expected_prop_dep_m1)
    assert state_m1["Furnishing Accumulated Depreciation"] == pytest.approx(expected_furn_dep_m1)

    # Loan Balance assertions remain the same
    monthly_payment = getattr(params, 'monthly_loan_payment', 0.0) # Retrieve monthly payment
    interest_m1 = pnl_m1["Loan Interest"]
    principal_paid_m1 = max(0, monthly_payment - interest_m1)
    expected_loan_bal_m1 = state_m0["Loan Balance"] - principal_paid_m1
    assert state_m1["Loan Balance"] == pytest.approx(expected_loan_bal_m1)

    # Retained Earnings assertions remain the same
    expected_re_m1 = state_m0["Retained Earnings"] + pnl_m1["Net Income"]
    assert state_m1["Retained Earnings"] == pytest.approx(expected_re_m1)

    # --- Cash Assertion (Updated) ---
    # Check that BS Cash matches the Ending Cash from CF statement
    assert state_m1["Cash"] == pytest.approx(cf_m1["Ending Cash Balance"])
    # --- End Cash Assertion ---

    # --- Balance Check Assertion (Updated) ---
    # Now that cash is correct, the BS should balance
    assert state_m1["Balance Check"] == pytest.approx(0.0, abs=1e-6)
    # --- End Balance Check Assertion ---

    # --- Month 13 --- (Similar updates)
    state_m12 = df_bs.loc[12]
    state_m13 = df_bs.loc[13]
    pnl_m13 = pnl_df.loc[13]
    cf_m13 = cf_df.loc[13] # <-- Get CF results for month 13

    # (Depreciation, Loan Balance, Retained Earnings assertions remain similar)
    expected_prop_dep_m13 = state_m12["Property Accumulated Depreciation"] + monthly_prop_dep
    expected_furn_dep_m13 = state_m12["Furnishing Accumulated Depreciation"] + monthly_furn_dep
    assert state_m13["Property Accumulated Depreciation"] == pytest.approx(expected_prop_dep_m13)
    assert state_m13["Furnishing Accumulated Depreciation"] == pytest.approx(expected_furn_dep_m13)

    interest_m13 = pnl_m13["Loan Interest"]
    principal_paid_m13 = max(0, monthly_payment - interest_m13)
    expected_loan_bal_m13 = state_m12["Loan Balance"] - principal_paid_m13
    assert state_m13["Loan Balance"] == pytest.approx(expected_loan_bal_m13)

    expected_re_m13 = state_m12["Retained Earnings"] + pnl_m13["Net Income"]
    assert state_m13["Retained Earnings"] == pytest.approx(expected_re_m13)

    # --- Cash Assertion (Updated) ---
    assert state_m13["Cash"] == pytest.approx(cf_m13["Ending Cash Balance"])
    # --- End Cash Assertion ---

    # --- Balance Check Assertion (Updated) ---
    assert state_m13["Balance Check"] == pytest.approx(0.0, abs=1e-6)
    # --- End Balance Check Assertion ---

# TODO: Add tests for end-of-amortization periods (e.g., furnishing after 7 years).
# TODO: Add tests checking the Cash balance (although it will be rudimentary until CF statement integration).
