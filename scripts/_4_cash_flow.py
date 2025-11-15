# In file: scripts/_4_cash_flow.py

import pandas as pd
import numpy as np # Might be needed for more complex calcs later
from typing import Dict, List
from ._1_model_params import ModelParameters

class CashFlow:
    """
    Calculates the Cash Flow statement as a monthly DataFrame
    for the duration of the holding period.
    Accepts ModelParameters via composition and requires PnL and BS results.
    #TODO: refine CFs logic so it starts from the EBITDA and then splits into operating CFs, Financing and Investing properly
    """

    def __init__(self, params: ModelParameters):
        """
        Initializes the CashFlow calculator with the model parameters.
        Expects 'params' to have pre-calculated transaction values.

        Args:
            params: An instance of the ModelParameters dataclass, augmented
                    with calculated values by TransactionCalculator or an orchestrator.
        """
        if not isinstance(params, ModelParameters):
            raise TypeError("params must be an instance of ModelParameters")
        self.params = params

        # Retrieve necessary pre-calculated values using getattr for safety
        self._total_acquisition_cost = getattr(params, 'total_acquisition_cost', 0.0)
        self._loan_amount = getattr(params, 'loan_amount', 0.0)
        self._initial_equity = getattr(params, 'initial_equity', 0.0)

        # Basic check
        if self._total_acquisition_cost == 0.0:
            print("Warning (CF Init): Total acquisition cost seems missing or zero in params.")

    def generate_cf_dataframe(self, pnl_df: pd.DataFrame, bs_df: pd.DataFrame, loan_schedule: pd.DataFrame) -> pd.DataFrame:
        """
        Generates the full Cash Flow DataFrame over the holding period (monthly).

        Args:
            pnl_df: DataFrame with monthly P&L results (Index 1 to num_months).
                    Must include 'Net Income', 'Depreciation/Amortization'.
            bs_df: DataFrame with monthly Balance Sheet results (Index 0 to num_months).
                   Must include 'Loan Balance', 'Cash'.

        Returns:
            A pandas DataFrame containing the monthly Cash Flow statement (Index 1 to num_months).
        """
        num_months = self.params.holding_period_years * 12

        # --- Data Storage ---
        # CF statement runs from month 1 onwards
        cf_data: Dict[str, List[float]] = {
            "Year": [(m - 1) // 12 + 1 for m in range(1, num_months + 1)],
            # Operating
            "Net Income": [],
            "Depreciation/Amortization": [],
            # "(+/-) Change in Working Capital": [0.0] * num_months, # Assume 0 for now
            "Cash Flow from Operations (CFO)": [],
            # Investing
            "Acquisition Costs Outflow": [],
            # "Capital Expenditures": [0.0] * num_months, # Placeholder
            "Cash Flow from Investing (CFI)": [],
            # Financing
            "Loan Proceeds": [],
            "Equity Injected": [],
            "Loan Principal Repayment": [],
            "Cash Flow from Financing (CFF)": [],
            # Summary
            "Net Change in Cash": [],
            "Beginning Cash Balance": [],
            "Ending Cash Balance": []
        }

        # --- Monthly Loop (Month 1 to num_months) ---
        for month in range(1, num_months + 1):
            # Get P&L data for the current month
            pnl_month_data = pnl_df.loc[month] if month in pnl_df.index else pd.Series(dtype='float64')
            net_income = pnl_month_data.get("Net Income", 0.0)
            depreciation = pnl_month_data.get("Depreciation/Amortization", 0.0) # Non-cash expense

            # Get Balance Sheet data for previous (month-1) and current (month) state
            bs_prev_month = bs_df.loc[month - 1] if (month - 1) in bs_df.index else pd.Series(dtype='float64')
            bs_curr_month = bs_df.loc[month] if month in bs_df.index else pd.Series(dtype='float64')

            # --- 1. Cash Flow from Operations (CFO) ---
            # Indirect method: Start with Net Income, add back non-cash charges
            # Add/Subtract changes in working capital accounts (N/A for simple model)
            # if month == 1:
            #     # Don't add back depreciation in Month 1 since assets just acquired
            #     cfo = net_income  # Don't add depreciation
            # else:
            cfo = net_income + depreciation 
            cf_data["Net Income"].append(net_income)
            cf_data["Depreciation/Amortization"].append(depreciation)
            cf_data["Cash Flow from Operations (CFO)"].append(cfo)

            # --- 2. Cash Flow from Investing (CFI) ---
            acquisition_outflow = 0.0
            if month == 1:
                # The entire acquisition cost is an outflow for investing
                acquisition_outflow = -self._total_acquisition_cost

            # capital_expenditures = 0.0 # Placeholder
            cfi = acquisition_outflow # + capital_expenditures
            cf_data["Acquisition Costs Outflow"].append(acquisition_outflow) # Recorded as negative
            cf_data["Cash Flow from Investing (CFI)"].append(cfi)

            # --- 3. Cash Flow from Financing (CFF) ---
            loan_proceeds = 0.0
            equity_injected = 0.0

            if month == 1:
                loan_proceeds = self._loan_amount # Inflow
                equity_injected = self._initial_equity # Inflow

            # Principal repayment calculation (remains the same)
            principal_repayment_outflow = 0.0
            if month in loan_schedule.index:
                principal_repayment_outflow = loan_schedule.loc[month, 'Principal Payment']
            

            # CFF = Inflows - Outflows
            cff = loan_proceeds + equity_injected - principal_repayment_outflow
            cf_data["Loan Proceeds"].append(loan_proceeds)
            cf_data["Equity Injected"].append(equity_injected)
            cf_data["Loan Principal Repayment"].append(-principal_repayment_outflow) # Report as negative
            cf_data["Cash Flow from Financing (CFF)"].append(cff)

            # --- 4. Summary ---
            net_change_in_cash = cfo + cfi + cff
            beginning_cash = bs_prev_month.get("Cash", 0.0) # Cash at end of previous month
            ending_cash = beginning_cash + net_change_in_cash

            cf_data["Net Change in Cash"].append(net_change_in_cash)
            cf_data["Beginning Cash Balance"].append(beginning_cash)
            cf_data["Ending Cash Balance"].append(ending_cash)

        # --- Create DataFrame ---
        df_cf = pd.DataFrame(cf_data)
        df_cf.index = range(1, num_months + 1) # Set index 1 to num_months
        df_cf.index.name = "Month"

        # Reorder columns if needed (matches test order)
        ordered_cols = [
            "Year", "Net Income", "Depreciation/Amortization",
            "Cash Flow from Operations (CFO)",
            "Acquisition Costs Outflow", "Cash Flow from Investing (CFI)",
            "Loan Proceeds", "Equity Injected", "Loan Principal Repayment",
            "Cash Flow from Financing (CFF)", 
            "Beginning Cash Balance", "Net Change in Cash", "Ending Cash Balance"
        ]
        df_cf = df_cf[ordered_cols]

        print(f"\nDEBUG: CF DataFrame columns = {df_cf.columns.tolist()}")
        return df_cf

# --- (Example Usage section remains similar to before) ---
