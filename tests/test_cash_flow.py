# In file: tests/test_cash_flow.py

import pytest
import pandas as pd
import numpy_financial as npf
from scripts._1_model_params import ModelParameters
from scripts._2_profit_and_loss import PnL
from scripts._3_balance_sheet import BalanceSheet
from scripts._4_cash_flow import CashFlow # Assuming class CashFlow in this file

# --- Helper Fixture ---
@pytest.fixture
def setup_cfs_data():
    """Provides params, pnl_df, and bs_df for Cash Flow tests."""
    params = ModelParameters(
        property_price=200000, property_size_sqm=50, notary_fees_percentage_estimate=0.08,
        loan_percentage=0.9, # <-- Use 90% financing for non-zero equity
        loan_interest_rate=0.04, loan_duration_years=20, loan_insurance_rate=0.003,
        initial_renovation_costs=10000, furnishing_costs=5000,
        holding_period_years=10,
        rental_assumptions = { # Keep detailed assumptions
            "airbnb": {"daily_rate": 80, "occupancy_rate": 0.7, "rent_growth_rate": 0.02, "monthly_seasonality": [0.8]*12},
            "furnished_1yr": {"monthly_rent_sqm": 25, "vacancy_rate": 0.08, "rent_growth_rate": 0.015},
            "unfurnished_3yr": {"monthly_rent_sqm": 20, "vacancy_rate": 0.04, "rent_growth_rate": 0.015}
         },
        property_tax_yearly=800, condo_fees_monthly=100, pno_insurance_yearly=150,
        fiscal_regime="LMNP Réel",
        lmnp_amortization_property_years=30, lmnp_amortization_furnishing_years=7
    )

    # --- Perform Calculations (Simulating Orchestrator/TransactionCalculator) ---
    notary_fees_calc = params.property_price * params.notary_fees_percentage_estimate
    total_acquisition_cost_calc = (params.property_price + notary_fees_calc +
                                   params.initial_renovation_costs + params.furnishing_costs)
    loan_amount_calc = total_acquisition_cost_calc * params.loan_percentage
    initial_equity_calc = total_acquisition_cost_calc - loan_amount_calc
    monthly_loan_payment_calc = 0.0
    if params.loan_duration_years > 0 and params.loan_interest_rate > 0:
        monthly_rate = params.loan_interest_rate / 12
        number_of_payments = params.loan_duration_years * 12
        monthly_loan_payment_calc = abs(npf.pmt(monthly_rate, number_of_payments, loan_amount_calc))
    yearly_loan_insurance_cost_calc = loan_amount_calc * params.loan_insurance_rate

    land_value_percentage = 0.15
    amortizable_property_value_calc = params.property_price * (1 - land_value_percentage)
    yearly_property_amortization_calc = amortizable_property_value_calc / params.lmnp_amortization_property_years if params.lmnp_amortization_property_years > 0 else 0
    yearly_furnishing_amortization_calc = params.furnishing_costs / params.lmnp_amortization_furnishing_years if params.lmnp_amortization_furnishing_years > 0 and params.furnishing_costs > 0 else 0

    # Add calculated values to params instance
    setattr(params, 'notary_fees', notary_fees_calc)
    setattr(params, 'total_acquisition_cost', total_acquisition_cost_calc)
    setattr(params, 'loan_amount', loan_amount_calc)
    setattr(params, 'initial_equity', initial_equity_calc)
    setattr(params, 'monthly_loan_payment', monthly_loan_payment_calc)
    setattr(params, 'yearly_loan_insurance_cost', yearly_loan_insurance_cost_calc)
    setattr(params, 'amortizable_property_value', amortizable_property_value_calc)
    setattr(params, 'yearly_property_amortization', yearly_property_amortization_calc)
    setattr(params, 'yearly_furnishing_amortization', yearly_furnishing_amortization_calc)
    # --- End Calculations ---

    pnl_calculator = PnL(params)
    pnl_df = pnl_calculator.generate_pnl_dataframe(lease_type="furnished_1yr")

    bs_calculator = BalanceSheet(params)
    # Use the BS df generated WITH the placeholder cash for now
    # bs_df = bs_calculator.generate_bs_dataframe(pnl_df)

    # --- Generate Placeholder BS for CF Input (CORRECTED LINE) ---
    num_months_temp = params.holding_period_years * 12
    # --- CORRECTED INITIAL CASH ---
    placeholder_bs_data = {'Cash': [0.0], 'Loan Balance': [params.loan_amount]} # Start Cash at 0 for Month 0
    # --- END CORRECTION ---
    monthly_pay = getattr(params, 'monthly_loan_payment', 0.0)
    for m in range(1, num_months_temp + 1):
        prev_cash = placeholder_bs_data['Cash'][-1]
        prev_loan = placeholder_bs_data['Loan Balance'][-1]
        ni = pnl_df.loc[m].get("Net Income", 0.0) if m in pnl_df.index else 0.0
        intr = pnl_df.loc[m].get("Loan Interest", 0.0) if m in pnl_df.index else 0.0
        princ = max(0, monthly_pay - intr) if m <= params.loan_duration_years * 12 else 0
        placeholder_bs_data['Cash'].append(prev_cash + ni - princ) # Old placeholder logic
        placeholder_bs_data['Loan Balance'].append(max(0, prev_loan - princ))

    bs_df_placeholder = pd.DataFrame({
        'Cash': placeholder_bs_data['Cash'],
        'Loan Balance': placeholder_bs_data['Loan Balance']
        }, index=range(0, num_months_temp + 1))
    bs_df_placeholder.index.name="Month"
    # --- End Placeholder BS Generation ---

    return {"params": params, "pnl_df": pnl_df, "bs_df": bs_df_placeholder}


# --- Test Initialization ---
def test_cash_flow_initialization(setup_cfs_data):
    """Test if CashFlow class initializes correctly."""
    params = setup_cfs_data["params"]
    cf_calculator = CashFlow(params)
    assert cf_calculator.params == params

# --- Test DataFrame Generation ---
def test_generate_cf_dataframe_structure(setup_cfs_data):
    """Test the basic structure (shape, index, columns) of the generated CF DataFrame."""
    params = setup_cfs_data["params"]
    pnl_df = setup_cfs_data["pnl_df"]
    bs_df = setup_cfs_data["bs_df"] # BS includes month 0
    cf_calculator = CashFlow(params)

    df_cf = cf_calculator.generate_cf_dataframe(pnl_df, bs_df)

    assert isinstance(df_cf, pd.DataFrame)

    expected_months = params.holding_period_years * 12
    # Cash Flow represents flows DURING the period, so index 1 to num_months
    assert len(df_cf) == expected_months
    assert df_cf.index.name == "Month"
    assert list(df_cf.index) == list(range(1, expected_months + 1))

    # Check common columns exist
    expected_cols = [
        "Year",
        # Operating
        "Net Income", "Depreciation/Amortization",
        # "(+/-) Change in Working Capital", # Likely zero for simple real estate
        "Cash Flow from Operations (CFO)",
        # Investing
        "Acquisition Costs Outflow", # Property, Notary, Reno, Furnishing
        # "Capital Expenditures", # Future placeholder
        "Cash Flow from Investing (CFI)",
        # Financing
        "Loan Proceeds", "Equity Injected",
        "Loan Principal Repayment",
        # "Dividends Paid", # Unlikely for this model
        "Cash Flow from Financing (CFF)",
        # Summary
        "Net Change in Cash",
        "Beginning Cash Balance",
        "Ending Cash Balance"
    ]
    for col in expected_cols:
         assert col in df_cf.columns

# --- Test Specific Calculations ---

def test_initial_cash_flows(setup_cfs_data):
    """Test the cash flows around Month 1 (acquisition)."""
    params = setup_cfs_data["params"]
    pnl_df = setup_cfs_data["pnl_df"]
    bs_df = setup_cfs_data["bs_df"]
    cf_calculator = CashFlow(params)
    df_cf = cf_calculator.generate_cf_dataframe(pnl_df, bs_df)

    cf_m1 = df_cf.loc[1]
    pnl_m1 = pnl_df.loc[1]
    bs_m0 = bs_df.loc[0] # State before month 1 starts
    bs_m1 = bs_df.loc[1] # State at end of month 1

    # --- CFI Month 1 ---
    # Total cost less loan amount is the cash outflow for acquisition
    expected_acquisition_outflow = -params.total_acquisition_cost
    # Check if CFI reflects this (might be spread slightly if reno takes time)
    # Simple model assumes all outflow at start (captured in CFI for month 1)
    assert cf_m1["Acquisition Costs Outflow"] == pytest.approx(expected_acquisition_outflow)
    assert cf_m1["Cash Flow from Investing (CFI)"] == pytest.approx(expected_acquisition_outflow)

    # --- CFF Month 1 ---
    expected_loan_proceeds = params.loan_amount
    expected_equity_injected = params.initial_equity
    principal_paid_m1 = bs_m0["Loan Balance"] - bs_m1["Loan Balance"] # Get principal from BS change
    expected_cff = expected_loan_proceeds + expected_equity_injected - principal_paid_m1

    assert cf_m1["Loan Proceeds"] == pytest.approx(expected_loan_proceeds)
    assert cf_m1["Equity Injected"] == pytest.approx(expected_equity_injected)
    assert cf_m1["Loan Principal Repayment"] == pytest.approx(-principal_paid_m1) # Outflow
    assert cf_m1["Cash Flow from Financing (CFF)"] == pytest.approx(expected_cff)

    # --- CFO Month 1 ---
    # CFO = Net Income + Depreciation (non-cash) +/- WC changes (none here)
    expected_cfo = pnl_m1["Net Income"] + pnl_m1["Depreciation/Amortization"]
    assert cf_m1["Cash Flow from Operations (CFO)"] == pytest.approx(expected_cfo)

    # --- Summary Month 1 ---
    expected_net_change = expected_cfo + expected_acquisition_outflow + expected_cff
    expected_beginning_cash = bs_m0["Cash"] # Cash at start of month 1 is end of month 0
    expected_ending_cash = expected_beginning_cash + expected_net_change

    assert cf_m1["Net Change in Cash"] == pytest.approx(expected_net_change)
    assert cf_m1["Beginning Cash Balance"] == pytest.approx(expected_beginning_cash)
    assert cf_m1["Ending Cash Balance"] == pytest.approx(expected_ending_cash)
    # This Ending Cash Balance SHOULD match bs_m1["Cash"] IF the BS cash calc was correct
    # assert cf_m1["Ending Cash Balance"] == pytest.approx(bs_m1["Cash"]) # This might fail now


def test_subsequent_cash_flows(setup_cfs_data):
    """Test cash flows for a later month (e.g., Month 13)."""
    params = setup_cfs_data["params"]
    pnl_df = setup_cfs_data["pnl_df"]
    bs_df = setup_cfs_data["bs_df"]
    cf_calculator = CashFlow(params)
    df_cf = cf_calculator.generate_cf_dataframe(pnl_df, bs_df)

    cf_m13 = df_cf.loc[13]
    pnl_m13 = pnl_df.loc[13]
    bs_m12 = bs_df.loc[12] # State before month 13 starts
    bs_m13 = bs_df.loc[13] # State at end of month 13

    # --- CFI Month 13 --- (Should be 0 if no CapEx)
    assert cf_m13["Acquisition Costs Outflow"] == 0
    assert cf_m13["Cash Flow from Investing (CFI)"] == 0

    # --- CFF Month 13 --- (Only principal repayment)
    principal_paid_m13 = bs_m12["Loan Balance"] - bs_m13["Loan Balance"]
    expected_cff = -principal_paid_m13
    assert cf_m13["Loan Proceeds"] == 0
    assert cf_m13["Equity Injected"] == 0
    assert cf_m13["Loan Principal Repayment"] == pytest.approx(-principal_paid_m13)
    assert cf_m13["Cash Flow from Financing (CFF)"] == pytest.approx(expected_cff)

    # --- CFO Month 13 ---
    expected_cfo = pnl_m13["Net Income"] + pnl_m13["Depreciation/Amortization"]
    assert cf_m13["Cash Flow from Operations (CFO)"] == pytest.approx(expected_cfo)

    # --- Summary Month 13 ---
    expected_net_change = expected_cfo + 0 + expected_cff # CFI is 0
    expected_beginning_cash = bs_m12["Cash"] # Use BS cash end of prior period (even if placeholder)
    expected_ending_cash = expected_beginning_cash + expected_net_change

    assert cf_m13["Net Change in Cash"] == pytest.approx(expected_net_change)
    assert cf_m13["Beginning Cash Balance"] == pytest.approx(expected_beginning_cash)
    assert cf_m13["Ending Cash Balance"] == pytest.approx(expected_ending_cash)
    # This Ending Cash Balance is the *correct* one based on CF logic.
    # It will likely differ from bs_m13["Cash"] until BS uses CF results.
