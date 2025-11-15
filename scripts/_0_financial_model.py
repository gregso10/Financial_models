# In file: scripts/_0_financial_model.py

import pandas as pd
from typing import Dict, Optional
from ._1_model_params import ModelParameters
from ._5_transaction_calculator import TransactionCalculator
from ._8_loan_calculator import LoanCalculator
from ._2_profit_and_loss import PnL
from ._3_balance_sheet import BalanceSheet
from ._4_cash_flow import CashFlow

class FinancialModel:
    """
    Orchestrator for the real estate financial model.
    Initializes parameters, runs transaction calculations, generates loan schedule,
    and generates the P&L, Balance Sheet, and Cash Flow statements.
    """

    def __init__(self, params: ModelParameters):
        """
        Initializes the financial model orchestrator.

        Args:
            params: An instance of ModelParameters containing user inputs.
        """
        if not isinstance(params, ModelParameters):
            raise TypeError("params must be an instance of ModelParameters")

        self.params = params
        self.calculated_params: Optional[Dict[str, float]] = None
        
        # Placeholders for results
        self.loan_schedule: Optional[pd.DataFrame] = None
        self.pnl_statement: Optional[pd.DataFrame] = None
        self.bs_statement: Optional[pd.DataFrame] = None
        self.cf_statement: Optional[pd.DataFrame] = None

        # Instantiate calculator
        self.transaction_calculator = TransactionCalculator(self.params)


    def run_simulation(self, lease_type: str):
        """
        Runs the full financial simulation for the specified lease type.
        
        Steps:
        1. Perform initial transaction calculations
        2. Augment parameters
        3. Generate loan amortization schedule
        4. Generate P&L statement
        5. Generate preliminary BS for CF input
        6. Generate Cash Flow statement
        7. Generate final Balance Sheet statement

        Args:
            lease_type: The lease type ("airbnb", "furnished_1yr", "unfurnished_3yr")
        """
        print(f"--- Running Simulation for Lease Type: {lease_type} ---")

        # --- 1. Perform Initial Transaction Calculations ---
        self.calculated_params = self.transaction_calculator.calculate_all()

        # --- 2. Augment Parameters ---
        for key, value in self.calculated_params.items():
            setattr(self.params, key, value)

        # --- 3. Generate Loan Schedule ---
        loan_calc = LoanCalculator(self.params)
        self.loan_schedule = loan_calc.generate_loan_schedule()
        
        if len(self.loan_schedule) > 0:
            print(f"Loan schedule generated: {len(self.loan_schedule)} payments")
            print(f"Total interest over life: €{self.loan_schedule['Interest Payment'].sum():,.2f}")
        else:
            print("No loan schedule (100% equity financing)")
            # Create empty schedule for consistency
            self.loan_schedule = pd.DataFrame(columns=[
                "Beginning Balance", "Monthly Payment", "Interest Payment", 
                "Principal Payment", "Ending Balance"
            ])

        # --- 4. Instantiate Statement Generators ---
        pnl_generator = PnL(self.params)
        bs_generator = BalanceSheet(self.params)
        cf_generator = CashFlow(self.params)

        # --- 5. Generate P&L Statement ---
        self.pnl_statement = pnl_generator.generate_pnl_dataframe(lease_type, self.loan_schedule)
        if self.pnl_statement is None or self.pnl_statement.empty:
             print("Error: P&L generation failed.")
             return

        # --- 6. Generate Preliminary BS for CF Input ---
        num_months = self.params.holding_period_years * 12
        
        # Initialize placeholder BS data
        placeholder_bs_data = {
            'Cash': [0.0],  # Initial cash at Month 0
            'Loan Balance': [self.params.loan_amount]
        }
        
        # Build placeholder BS month by month
        for m in range(1, num_months + 1):
            prev_cash = placeholder_bs_data['Cash'][-1]
            
            # Get loan balance from schedule
            if m in self.loan_schedule.index:
                current_loan_bal = self.loan_schedule.loc[m, 'Ending Balance']
                principal_paid = self.loan_schedule.loc[m, 'Principal Payment']
            else:
                current_loan_bal = 0.0
                principal_paid = 0.0
            
            # Simple cash calculation: previous + net income - principal payment
            net_income = self.pnl_statement.loc[m].get("Net Income", 0.0) if m in self.pnl_statement.index else 0.0
            depreciation = self.pnl_statement.loc[m].get("Depreciation/Amortization", 0.0) if m in self.pnl_statement.index else 0.0
            current_cash = prev_cash + net_income + depreciation - principal_paid 
            
            placeholder_bs_data['Cash'].append(current_cash)
            placeholder_bs_data['Loan Balance'].append(current_loan_bal)

        # Create placeholder BS DataFrame
        bs_df_placeholder = pd.DataFrame(
            placeholder_bs_data, 
            index=range(0, num_months + 1)
        )
        bs_df_placeholder.index.name = "Month"

        # --- 7. Generate Cash Flow Statement ---
        print("Generating Cash Flow statement...")
        self.cf_statement = cf_generator.generate_cf_dataframe(
            self.pnl_statement, 
            bs_df_placeholder, 
            self.loan_schedule
        )
        if self.cf_statement is None or self.cf_statement.empty:
             print("Error: Cash Flow generation failed.")
             return

        # --- 8. Generate Final (Balanced) Balance Sheet ---
        print("Generating final Balance Sheet statement...")
        self.bs_statement = bs_generator.generate_bs_dataframe(
            self.pnl_statement, 
            self.cf_statement, 
            self.loan_schedule
        )
        if self.bs_statement is None or self.bs_statement.empty:
             print("Error: Final Balance Sheet generation failed.")
             return

        # --- 9. Final Balance Check ---
        max_imbalance = self.bs_statement["Balance Check"].abs().max()
        if max_imbalance > 1e-5:
             print(f"WARNING: Balance Sheet does not balance! Max imbalance: €{max_imbalance:,.2f}")
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
    
    def get_loan_schedule(self) -> Optional[pd.DataFrame]:
        return self.loan_schedule

    def get_summary_metrics(self):
        """Placeholder for calculating KPIs (e.g., ROI, IRR, Cash-on-Cash)"""
        if self.cf_statement is None:
            print("Run simulation first.")
            return None
        # ... calculate metrics ...
        pass