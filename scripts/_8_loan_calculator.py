# In file: scripts/_9_loan_calculator.py

import pandas as pd
import numpy as np
import numpy_financial as npf
from typing import Dict, List, Optional
from ._1_model_params import ModelParameters


class LoanCalculator:
    """
    Calculates loan amortization schedule and provides sensitivity analysis.
    Returns DataFrames for integration with P&L, Balance Sheet, and Cash Flow statements.
    """

    def __init__(self, params: ModelParameters):
        """
        Initializes the loan calculator with model parameters.

        Args:
            params: ModelParameters instance with loan details.
        """
        if not isinstance(params, ModelParameters):
            raise TypeError("params must be an instance of ModelParameters")
        
        self.params = params
        self._loan_amount = getattr(params, 'loan_amount', 0.0)
        self._loan_duration_years = params.loan_duration_years
        self._loan_interest_rate = params.loan_interest_rate
        self._monthly_rate = self._loan_interest_rate / 12
        self._num_payments = self._loan_duration_years * 12
        
        # Calculate monthly payment
        self._monthly_payment = 0.0
        if self._monthly_rate > 0 and self._num_payments > 0 and self._loan_amount > 0:
            self._monthly_payment = abs(npf.pmt(self._monthly_rate, self._num_payments, self._loan_amount))

    def generate_loan_schedule(self) -> pd.DataFrame:
        """
        Generates the complete loan amortization schedule.

        Returns:
            DataFrame with columns:
            - Month: Payment period (1 to num_payments)
            - Beginning Balance: Loan balance at start of month
            - Monthly Payment: Total payment (principal + interest)
            - Interest Payment: Interest portion
            - Principal Payment: Principal portion
            - Ending Balance: Loan balance at end of month
        """
        if self._loan_amount == 0 or self._monthly_payment == 0:
            # Return empty schedule if no loan
            return pd.DataFrame(columns=[
                "Month", "Beginning Balance", "Monthly Payment", 
                "Interest Payment", "Principal Payment", "Ending Balance"
            ])

        schedule_data: Dict[str, List[float]] = {
            "Month": [],
            "Beginning Balance": [],
            "Monthly Payment": [],
            "Interest Payment": [],
            "Principal Payment": [],
            "Ending Balance": []
        }

        remaining_balance = self._loan_amount

        for month in range(1, self._num_payments + 1):
            beginning_balance = remaining_balance
            
            # Calculate interest for this month
            interest_payment = beginning_balance * self._monthly_rate
            
            # Calculate principal payment
            principal_payment = self._monthly_payment - interest_payment
            
            # Ensure we don't overpay on last payment
            if principal_payment > beginning_balance:
                principal_payment = beginning_balance
                interest_payment = self._monthly_payment - principal_payment
            
            # Update balance
            ending_balance = max(0, beginning_balance - principal_payment)
            
            # Store data
            schedule_data["Month"].append(month)
            schedule_data["Beginning Balance"].append(beginning_balance)
            schedule_data["Monthly Payment"].append(self._monthly_payment)
            schedule_data["Interest Payment"].append(interest_payment)
            schedule_data["Principal Payment"].append(principal_payment)
            schedule_data["Ending Balance"].append(ending_balance)
            
            # Update for next iteration
            remaining_balance = ending_balance
            
            # Stop if loan is paid off
            if ending_balance == 0:
                break

        df_schedule = pd.DataFrame(schedule_data)
        df_schedule.set_index("Month", inplace=True)
        
        return df_schedule

    def calculate_monthly_payment(self, loan_amount: float, annual_rate: float, duration_months: int) -> float:
        """
        Helper method to calculate monthly payment for given parameters.

        Args:
            loan_amount: Principal amount
            annual_rate: Annual interest rate (e.g., 0.04 for 4%)
            duration_months: Loan duration in months

        Returns:
            Monthly payment amount
        """
        if annual_rate == 0 or duration_months == 0 or loan_amount == 0:
            return 0.0
        
        monthly_rate = annual_rate / 12
        return abs(npf.pmt(monthly_rate, duration_months, loan_amount))

    def generate_sensitivity_analysis(self, 
                                      rate_delta: float = 0.005,
                                      rate_range: float = 0.005,
                                      duration_delta_months: int = 12,
                                      duration_range_months: int = 12) -> pd.DataFrame:
        """
        Generates sensitivity analysis for monthly payment changes.

        Args:
            rate_delta: Interest rate increment (default 0.5% = 0.005)
            rate_range: Total range above/below base rate (default ±0.5% = 0.005)
            duration_delta_months: Duration increment in months (default 12)
            duration_range_months: Total range above/below base duration (default ±12)

        Returns:
            DataFrame with:
            - Rows: Loan duration (months)
            - Columns: Interest rates
            - Values: Monthly payment amounts
        """
        base_rate = self._loan_interest_rate
        base_duration = self._num_payments
        loan_amount = self._loan_amount

        # Generate rate range (corrected: use rate_delta for steps)
        rates = np.arange(
            base_rate - rate_range,
            base_rate + rate_range + rate_delta/2,  # Add small epsilon for inclusive upper bound
            rate_delta
        )

        # Generate duration range
        durations = np.arange(
            base_duration - duration_range_months,
            base_duration + duration_range_months + duration_delta_months/2,
            duration_delta_months
        )
        durations = durations[durations > 0]  # Ensure positive durations

        # Build sensitivity matrix
        sensitivity_data: Dict[str, List[float]] = {}
        
        for rate in rates:
            rate_label = f"{rate*100:.1f}%"
            payments = []
            
            for duration in durations:
                payment = self.calculate_monthly_payment(loan_amount, rate, int(duration))
                payments.append(payment)
            
            sensitivity_data[rate_label] = payments

        df_sensitivity = pd.DataFrame(sensitivity_data, index=durations.astype(int))
        df_sensitivity.index.name = "Duration (Months)"
        
        return df_sensitivity


# --- Example Usage ---
if __name__ == "__main__":
    # Create sample parameters
    from scripts._1_model_params import ModelParameters
    from scripts._5_transaction_calculator import TransactionCalculator
    
    params = ModelParameters(
        property_price=200000,
        loan_percentage=0.9,
        loan_interest_rate=0.04,
        loan_duration_years=20
    )
    
    # Calculate loan amount first
    calc = TransactionCalculator(params)
    results = calc.calculate_all()
    for key, val in results.items():
        setattr(params, key, val)
    
    # Generate loan schedule
    loan_calc = LoanCalculator(params)
    schedule = loan_calc.generate_loan_schedule()
    
    print("--- Loan Amortization Schedule (First 12 months) ---")
    print(schedule.head(12))
    
    print("\n--- Loan Amortization Schedule (Last 12 months) ---")
    print(schedule.tail(12))
    
    print("\n--- Summary Statistics ---")
    print(f"Total Interest Paid: €{schedule['Interest Payment'].sum():,.2f}")
    print(f"Total Principal Paid: €{schedule['Principal Payment'].sum():,.2f}")
    print(f"Total Payments: €{(schedule['Interest Payment'].sum() + schedule['Principal Payment'].sum()):,.2f}")
    
    # Generate sensitivity analysis
    sensitivity = loan_calc.generate_sensitivity_analysis()
    
    print("\n--- Sensitivity Analysis: Monthly Payment ---")
    print(sensitivity)