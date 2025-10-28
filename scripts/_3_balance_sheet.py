# In file: scripts/_3_balance_sheet.py

import pandas as pd
import numpy_financial as npf
import numpy as np # For loan balance calculation if needed
from typing import Dict, List
from ._1_model_params import ModelParameters
# No direct import of PnL needed, as we receive its results (DataFrame)

class BalanceSheet:
    """
    Calculates the Balance Sheet statement as a monthly DataFrame
    for the duration of the holding period, including the initial state (Month 0).
    Accepts ModelParameters via composition and requires PnL results.
    """

    # In file: scripts/_3_balance_sheet.py

import pandas as pd
import numpy_financial as npf
import numpy as np
from typing import Dict, List
from ._1_model_params import ModelParameters
from ._2_profit_and_loss import PnL

class BalanceSheet:
    """
    Calculates the Balance Sheet statement as a monthly DataFrame
    for the duration of the holding period, including the initial state (Month 0).
    Accepts ModelParameters (expected to contain pre-calculated transaction values)
    via composition and requires PnL results.
    """
    def __init__(self, params: ModelParameters):
        if not isinstance(params, ModelParameters):
            raise TypeError("params must be an instance of ModelParameters")
        self.params = params
        # self.pnl = PnL.generate_pnl_dataframe(params)

        # --- Retrieve pre-calculated financing values ---
        self._loan_amount = getattr(params, 'loan_amount', 0.0)
        self._initial_equity = getattr(params, 'initial_equity', 0.0)
        self._monthly_loan_payment = getattr(params, 'monthly_loan_payment', 0.0)
        self._yearly_loan_insurance_cost = getattr(params, 'yearly_loan_insurance_cost', 0.0)

        # --- Define Initial Asset Costs for BS (T=0 state) ---
        # Property cost = Price FAI + Notary Fees + Initial Renovations
        # These costs represent the value capitalized into the Property asset account.
        notary_fees_calc = getattr(params, 'notary_fees', params.property_price * params.notary_fees_percentage_estimate)
        self._initial_property_cost = (params.property_price +
                                       notary_fees_calc +
                                       params.initial_renovation_costs)

        self._initial_furnishing_cost = params.furnishing_costs

        # --- Store Initial Liabilities & Equity (T=0 state) ---
        self._initial_loan_balance = self._loan_amount
        # self._initial_equity is already retrieved above

        # --- Pre-calculate monthly depreciation ---
        yearly_prop_amort = getattr(params, 'yearly_property_amortization', 0.0)
        yearly_furn_amort = getattr(params, 'yearly_furnishing_amortization', 0.0)
        self._monthly_property_depreciation = yearly_prop_amort / 12 if yearly_prop_amort > 0 else 0.0
        self._monthly_furnishing_depreciation = yearly_furn_amort / 12 if yearly_furn_amort > 0 else 0.0

        # --- Basic Checks ---
        if self._initial_loan_balance == 0.0 and params.loan_percentage > 0:
             print("Warning (BS Init): Loan amount seems missing or zero in params.")
        if self._initial_equity == 0.0 and params.loan_percentage < 1.0 and self._initial_loan_balance > 0 :
             # Only warn if there should be equity (loan < 100%) and a loan exists
             print("Warning (BS Init): Initial equity seems missing or zero in params.")
        if self._monthly_loan_payment == 0.0 and self._initial_loan_balance > 0:
             print("Warning (BS Init): Monthly loan payment seems missing or zero in params.")

    def generate_bs_dataframe(self, pnl_df: pd.DataFrame, cf_df: pd.DataFrame) -> pd.DataFrame: # <-- Added cf_df parameter
        """
        Generates the full Balance Sheet DataFrame over the holding period
        on a monthly basis, including the initial state (Month 0).
        Uses Ending Cash Balance from the Cash Flow statement.

        Args:
            pnl_df: DataFrame with monthly P&L results (Index 1 to num_months).
            cf_df: DataFrame with monthly CF results (Index 1 to num_months).
                   Must include 'Ending Cash Balance'.

        Returns:
            A pandas DataFrame containing the balanced monthly Balance Sheet statement.
        """
        num_months = self.params.holding_period_years * 12

        # Initialize with Month 0 data
        bs_data: Dict[str, List[float]] = {
            "Year": [0],
            "Property Cost": [self._initial_property_cost],
            "Property Accumulated Depreciation": [0.0],
            "Furnishing Cost": [self._initial_furnishing_cost],
            "Furnishing Accumulated Depreciation": [0.0],
            "Cash": [0.0], # <-- CORRECTED: Initial Cash is 0 after acquisition outflows
            "Loan Balance": [self._initial_loan_balance],
            "Initial Equity": [self._initial_equity],
            "Retained Earnings": [0.0],
        }

        # Monthly Loop (Starts from Month 1)
        for month in range(1, num_months + 1):
            current_year = (month - 1) // 12 + 1
            bs_data["Year"].append(current_year)

            # Get previous month's BS data
            prev_prop_acc_dep = bs_data["Property Accumulated Depreciation"][month-1]
            prev_furn_acc_dep = bs_data["Furnishing Accumulated Depreciation"][month-1]
            prev_loan_balance = bs_data["Loan Balance"][month-1]
            prev_retained_earnings = bs_data["Retained Earnings"][month-1]
            # prev_cash is no longer directly used for calculation, but needed for CF's BegBal

            # Get current month's P&L and CF data
            pnl_month_data = pnl_df.loc[month] if month in pnl_df.index else pd.Series(dtype='float64')
            cf_month_data = cf_df.loc[month] if month in cf_df.index else pd.Series(dtype='float64')
            net_income_month = pnl_month_data.get("Net Income", 0.0)
            interest_month = pnl_month_data.get("Loan Interest", 0.0)
            prop_dep_month = self._monthly_property_depreciation if current_year <= self.params.lmnp_amortization_property_years else 0.0
            furn_dep_month = self._monthly_furnishing_depreciation if current_year <= self.params.lmnp_amortization_furnishing_years else 0.0

            # --- Calculate BS Items for Current Month ---

            # Assets (Property, Furnishing - same as before)
            bs_data["Property Cost"].append(self._initial_property_cost)
            current_prop_acc_dep = min(prev_prop_acc_dep + prop_dep_month, self._initial_property_cost)
            bs_data["Property Accumulated Depreciation"].append(current_prop_acc_dep)
            bs_data["Furnishing Cost"].append(self._initial_furnishing_cost)
            current_furn_acc_dep = min(prev_furn_acc_dep + furn_dep_month, self._initial_furnishing_cost)
            bs_data["Furnishing Accumulated Depreciation"].append(current_furn_acc_dep)

            # --- Cash (UPDATED) ---
            # Get the ending cash directly from the cash flow statement for this month
            current_cash = cf_month_data.get("Ending Cash Balance", 0.0) # Use CF result

            # --- ADD THIS DEBUG LINE ---
            if month == 1:
                print(f"DEBUG BS M1: Cash value read from cf_df = {current_cash}")
            # --- END DEBUG LINE ---

            bs_data["Cash"].append(current_cash)
            # --- End Cash Update ---

            # Liabilities & Equity (Loan Balance, Retained Earnings - same logic as before)
            principal_paid_month = 0.0
            if month <= self.params.loan_duration_years * 12:
                 principal_paid_month = max(0, self._monthly_loan_payment - interest_month)
            current_loan_balance = max(0, prev_loan_balance - principal_paid_month)
            bs_data["Loan Balance"].append(current_loan_balance)
            bs_data["Initial Equity"].append(self._initial_equity)
            current_retained_earnings = prev_retained_earnings + net_income_month
            bs_data["Retained Earnings"].append(current_retained_earnings)

        # Create DataFrame
        df_bs = pd.DataFrame(bs_data)
        df_bs.index.name = "Month"

        # Calculate Derived Rows (same as before)
        df_bs["Property Net Value"] = df_bs["Property Cost"] - df_bs["Property Accumulated Depreciation"]
        # ... (rest of derived rows calculations are identical) ...
        df_bs["Furnishing Net Value"] = df_bs["Furnishing Cost"] - df_bs["Furnishing Accumulated Depreciation"]
        df_bs["Total Fixed Assets"] = df_bs["Property Net Value"] + df_bs["Furnishing Net Value"]

        # --- Debugging Point ---
        if 1 in df_bs.index:
             print("\nDEBUG BS Month 1 (Before Total Assets Calc):")
             print(f"  Total Fixed Assets: {df_bs.loc[1, 'Total Fixed Assets']}")
             print(f"  Cash (from loop): {df_bs.loc[1, 'Cash']}") # Check the cash value just before use
        # --- End Debugging Point ---

        df_bs["Total Assets"] = df_bs["Total Fixed Assets"] + df_bs["Cash"]
        df_bs["Total Liabilities"] = df_bs["Loan Balance"]
        df_bs["Total Equity"] = df_bs["Initial Equity"] + df_bs["Retained Earnings"]
        df_bs["Total Liabilities and Equity"] = df_bs["Total Liabilities"] + df_bs["Total Equity"]

        # --- Debugging ---
        if 1 in df_bs.index: # Check Month 1 specifically
            print(f"\nDEBUG BS Month 1:")
            print(f"  Total Assets: {df_bs.loc[1, 'Total Assets']}")
            print(f"  Total Liab+Eq: {df_bs.loc[1, 'Total Liabilities and Equity']}")
            print(f"  Calculated Check: {df_bs.loc[1, 'Total Assets'] - df_bs.loc[1, 'Total Liabilities and Equity']}")
        # --- End Debugging ---

        df_bs["Balance Check"] = df_bs["Total Assets"] - df_bs["Total Liabilities and Equity"]

        # Reorder columns (same as before)
        ordered_cols = [
            "Year", "Property Cost", "Property Accumulated Depreciation", "Property Net Value",
            "Furnishing Cost", "Furnishing Accumulated Depreciation", "Furnishing Net Value",
            "Total Fixed Assets", "Cash", "Total Assets", "Loan Balance",
            "Total Liabilities", "Initial Equity", "Retained Earnings",
            "Total Equity", "Total Liabilities and Equity", "Balance Check"
        ]
        df_bs = df_bs[ordered_cols]

        return df_bs

# --- (Example Usage section remains the same) ---

# --- Example Usage ---
# if __name__ == "__main__":
#     # (Use the same params and pnl_df setup as in the test fixture)
#     params = ModelParameters(...)
#     params._calculate_acquisition_costs()
#     params._calculate_financing()
#     params._calculate_amortization_bases()

#     pnl_calculator = PnL(params)
#     pnl_df = pnl_calculator.generate_pnl_dataframe(lease_type="furnished_1yr")

#     bs_calculator = BalanceSheet(params)
#     bs_df = bs_calculator.generate_bs_dataframe(pnl_df)

#     print("--- Balance Sheet (Months 0-5) ---")
#     print(bs_df.head(6))

#     print("\n--- Balance Sheet (Last 5 Months) ---")
#     print(bs_df.tail(5))

#     # Check Balance Check column for issues
#     print("\n--- Max Absolute Balance Check Error ---")
#     print(bs_df["Balance Check"].abs().max())
