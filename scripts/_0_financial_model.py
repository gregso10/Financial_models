# In file: scripts/_0_financial_model.py

import pandas as pd
from typing import Dict, Optional
from ._1_model_params import ModelParameters
from ._5_transaction_calculator import TransactionCalculator
from ._2_profit_and_loss import PnL
from ._3_balance_sheet import BalanceSheet
from ._4_cash_flow import CashFlow

class FinancialModel:
    """
    Orchestrator for the real estate financial model.
    Initializes parameters, runs transaction calculations, and generates
    the P&L, Balance Sheet, and Cash Flow statements.
    """

    def __init__(self, params: ModelParameters):
        """
        Initializes the financial model orchestrator.

        Args:
            params: An instance of ModelParameters containing user inputs.
        """
        if not isinstance(params, ModelParameters):
            raise TypeError("params must be an instance of ModelParameters")

        self.params = params # Store the raw input parameters
        self.calculated_params: Optional[Dict[str, float]] = None # To store transaction results

        # Placeholders for the final statement DataFrames
        self.pnl_statement: Optional[pd.DataFrame] = None
        self.bs_statement: Optional[pd.DataFrame] = None
        self.cf_statement: Optional[pd.DataFrame] = None

        # Instantiate calculator/statement classes (will need augmented params later)
        self.transaction_calculator = TransactionCalculator(self.params)
        # Defer instantiation of PnL, BS, CF until params are augmented


    def run_simulation(self, lease_type: str):
        """
        Runs the full financial simulation for the specified lease type.
        1. Performs initial transaction calculations.
        2. Augments parameters.
        3. Generates P&L statement.
        4. Generates Cash Flow statement.
        5. Generates final Balance Sheet statement.

        Args:
            lease_type: The lease type ("airbnb", "furnished_1yr", "unfurnished_3yr")
                        to use for the simulation.
        """
        print(f"--- Running Simulation for Lease Type: {lease_type} ---")

        # --- 1. Perform Initial Transaction Calculations ---
        print("Calculating initial transaction values...")
        self.calculated_params = self.transaction_calculator.calculate_all()

        # --- 2. Augment Parameters ---
        # Add the calculated values as attributes to the params object
        # for easy access by the statement classes.
        for key, value in self.calculated_params.items():
            setattr(self.params, key, value)
        print("Parameters augmented with calculated values.")

        # --- Instantiate statement generators with augmented params ---
        pnl_generator = PnL(self.params)
        bs_generator = BalanceSheet(self.params)
        cf_generator = CashFlow(self.params)

        # --- 3. Generate P&L Statement ---
        print("Generating P&L statement...")
        self.pnl_statement = pnl_generator.generate_pnl_dataframe(lease_type)
        if self.pnl_statement is None or self.pnl_statement.empty:
             print("Error: P&L generation failed.")
             return # Stop if P&L fails

        # --- 4. Generate Cash Flow Statement ---
        # Requires a preliminary BS to get starting cash and loan balances
        # We need a BS *before* CF to get BegBal Cash & Loan change
        # Let's generate a temporary BS *without* final cash from CF first.
        # This requires a temporary method or modification in BS class,
        # OR we build BS incrementally alongside CF. Let's try the latter.

        # --- Alternative: Generate BS and CF somewhat iteratively ---
        # For simplicity in this structure, let's first generate a BS
        # using a placeholder (like 0 or initial equity) for cash flow effects.
        # Then generate CF, then regenerate BS with correct cash.

        # Generate preliminary BS (using placeholder cash logic internally if needed)
        # We need a version of generate_bs_dataframe that *doesn't* require cf_df yet.
        # Let's assume BalanceSheet can generate a preliminary version.
        # This highlights a dependency challenge in this strict sequential approach.

        # --- Revised Approach: Stick to Sequence, Use Placeholder BS for CF ---
        print("Generating preliminary Balance Sheet for Cash Flow input...")
        # Create a temporary BS DataFrame using the old placeholder cash logic
        # This logic should ideally be encapsulated, maybe a static method?
        num_months_temp = self.params.holding_period_years * 12
        placeholder_bs_data = {'Cash': [self.params.initial_equity], 'Loan Balance': [self.params.loan_amount]}
        monthly_pay = getattr(self.params, 'monthly_loan_payment', 0.0)
        for m in range(1, num_months_temp + 1):
            prev_cash = placeholder_bs_data['Cash'][-1]
            prev_loan = placeholder_bs_data['Loan Balance'][-1]
            ni = self.pnl_statement.loc[m].get("Net Income", 0.0) if m in self.pnl_statement.index else 0.0
            intr = self.pnl_statement.loc[m].get("Loan Interest", 0.0) if m in self.pnl_statement.index else 0.0
            princ = max(0, monthly_pay - intr) if m <= self.params.loan_duration_years * 12 else 0
            placeholder_bs_data['Cash'].append(prev_cash + ni - princ)
            placeholder_bs_data['Loan Balance'].append(max(0, prev_loan - princ))

        bs_df_placeholder = pd.DataFrame({
            'Cash': placeholder_bs_data['Cash'],
            'Loan Balance': placeholder_bs_data['Loan Balance']
            }, index=range(0, num_months_temp + 1))
        bs_df_placeholder.index.name="Month"
        print("Preliminary Balance Sheet generated.")

        print("Generating Cash Flow statement...")
        self.cf_statement = cf_generator.generate_cf_dataframe(self.pnl_statement, bs_df_placeholder)
        if self.cf_statement is None or self.cf_statement.empty:
             print("Error: Cash Flow generation failed.")
             return # Stop if CF fails

        # --- 5. Generate Final (Balanced) Balance Sheet ---
        print("Generating final Balance Sheet statement...")
        self.bs_statement = bs_generator.generate_bs_dataframe(self.pnl_statement, self.cf_statement)
        if self.bs_statement is None or self.bs_statement.empty:
             print("Error: Final Balance Sheet generation failed.")
             return # Stop if BS fails

        # Optional: Final Balance Check Assertion
        max_imbalance = self.bs_statement["Balance Check"].abs().max()
        if max_imbalance > 1e-5: # Allow small tolerance
             print(f"WARNING: Balance Sheet does not balance! Max imbalance: {max_imbalance:.6f}")
        else:
             print("Balance Sheet successfully generated and balanced.")

        print("--- Simulation Complete ---")

    # --- Methods to retrieve results ---
    def get_pnl(self) -> Optional[pd.DataFrame]:
        return self.pnl_statement

    def get_balance_sheet(self) -> Optional[pd.DataFrame]:
        return self.bs_statement

    def get_cash_flow(self) -> Optional[pd.DataFrame]:
        return self.cf_statement

    def get_summary_metrics(self):
        # Placeholder for calculating KPIs (e.g., ROI, IRR, Cash-on-Cash)
        if self.cf_statement is None:
            print("Run simulation first.")
            return None
        # ... calculate metrics ...
        pass

# --- Example Usage ---
# if __name__ == "__main__":
#     # 1. Create parameters
#     user_params = ModelParameters(
#         property_price=250000, property_size_sqm=60, loan_percentage=0.8,
#         loan_interest_rate=0.035, loan_duration_years=25, initial_equity=0 # Equity will be calculated
#         # ... fill in other necessary params ...
#     )
#     user_params.rental_assumptions["furnished_1yr"]["monthly_rent_sqm"] = 28

#     # 2. Instantiate the model
#     model = FinancialModel(user_params)

#     # 3. Run the simulation for a specific lease type
#     model.run_simulation(lease_type="furnished_1yr")

#     # 4. Retrieve results
#     pnl_result = model.get_pnl()
#     bs_result = model.get_balance_sheet()
#     cf_result = model.get_cash_flow()

#     if pnl_result is not None:
#         print("\n--- P&L (First 5 Months) ---")
#         print(pnl_result.head())
#         print("\n--- P&L (Yearly Summary) ---")
#         print(pnl_result.groupby("Year").sum())

#     if bs_result is not None:
#         print("\n--- Balance Sheet (First 5 Months) ---")
#         print(bs_result.head(6)) # Show month 0 too
#         print("\n--- Balance Sheet (Last 5 Months) ---")
#         print(bs_result.tail())

#     if cf_result is not None:
#         print("\n--- Cash Flow (First 5 Months) ---")
#         print(cf_result.head())
