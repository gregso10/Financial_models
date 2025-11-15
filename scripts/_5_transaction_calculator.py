import numpy_financial as npf
from typing import Dict
from ._1_model_params import ModelParameters # Relative import

class TransactionCalculator:
    """
    Calculates initial transaction figures based on ModelParameters.
    Separates one-time setup calculations (acquisition, financing)
    from recurring operational calculations.
    """

    def __init__(self, params: ModelParameters):
        """
        Initializes the calculator with the model parameters.

        Args:
            params: An instance of the ModelParameters dataclass.
        """
        if not isinstance(params, ModelParameters):
            raise TypeError("params must be an instance of ModelParameters")
        self.params = params

    def calculate_all(self) -> Dict[str, float]:
        """
        Performs all initial acquisition and financing calculations.

        Returns:
            A dictionary containing key calculated figures:
            - net_seller_price
            - agency_fees
            - notary_fees
            - total_acquisition_cost
            - loan_amount
            - initial_equity
            - monthly_loan_payment
            - yearly_loan_insurance_cost
            - amortizable_property_value
            - yearly_property_amortization
            - yearly_furnishing_amortization
        """
        results: Dict[str, float] = {}

        # --- 1. Acquisition Costs ---
        # Assumption: property_price is FAI (Frais d'Agence Inclus)
        # Assumption: agency_fees_percentage is applied to net seller price
        # Price FAI = Net Seller * (1 + Agency %) => Net Seller = Price FAI / (1 + Agency %)
        if self.params.agency_fees_percentage > 0:
            results["net_seller_price"] = self.params.property_price / (1 + self.params.agency_fees_percentage)
            results["agency_fees"] = self.params.property_price - results["net_seller_price"]
        else:
            results["net_seller_price"] = self.params.property_price
            results["agency_fees"] = 0.0

        # Assumption: Notary fees calculated on Price FAI for simplicity.
        # Refine this based on actual notary fee rules (usually excludes agency fees).
        results["notary_fees"] = self.params.property_price * self.params.notary_fees_percentage_estimate

        results["total_acquisition_cost"] = (self.params.property_price +
                                            results["notary_fees"] +
                                            self.params.initial_renovation_costs +
                                            self.params.furnishing_costs)

        # --- 2. Financing ---
        results["loan_amount"] = results["total_acquisition_cost"] * self.params.loan_percentage
        results["initial_equity"] = results["total_acquisition_cost"] - results["loan_amount"]

        print(f"DEBUG: Initial Equity = {results['initial_equity']}")
        print(f"DEBUG: Total Acq Cost = {results['total_acquisition_cost']}")
        print(f"DEBUG: Loan Amount = {results['loan_amount']}")
        monthly_payment = 0.0
        if self.params.loan_duration_years > 0 and self.params.loan_interest_rate > 0 and results["loan_amount"] > 0:
            monthly_rate = self.params.loan_interest_rate / 12
            number_of_payments = self.params.loan_duration_years * 12
            monthly_payment = abs(npf.pmt(monthly_rate, number_of_payments, results["loan_amount"]))
        results["monthly_loan_payment"] = monthly_payment

        # Assumption: Insurance based on initial loan amount
        results["yearly_loan_insurance_cost"] = results["loan_amount"] * self.params.loan_insurance_rate

        # --- 3. Amortization Bases (Simplified LMNP Réel) ---
        # Assumption: Land value is 15% of *net seller price*
        land_value_percentage = 0.15
        results["amortizable_property_value"] = results["net_seller_price"] * (1 - land_value_percentage)

        yearly_prop_amort = 0.0
        if self.params.lmnp_amortization_property_years > 0:
            yearly_prop_amort = results["amortizable_property_value"] / self.params.lmnp_amortization_property_years
        results["yearly_property_amortization"] = yearly_prop_amort

        yearly_furn_amort = 0.0
        if self.params.lmnp_amortization_furnishing_years > 0 and self.params.furnishing_costs > 0:
             yearly_furn_amort = self.params.furnishing_costs / self.params.lmnp_amortization_furnishing_years
        results["yearly_furnishing_amortization"] = yearly_furn_amort

        # TODO: Add amortization basis for initial_renovation_costs if needed

        return results

# --- Example Usage (for testing/debugging) ---
# if __name__ == "__main__":
#     sample_params = ModelParameters(
#         property_price=200000, agency_fees_percentage=0.05,
#         notary_fees_percentage_estimate=0.08, initial_renovation_costs=10000,
#         furnishing_costs=5000, loan_percentage=0.9, loan_interest_rate=0.04,
#         loan_duration_years=20, loan_insurance_rate=0.003,
#         lmnp_amortization_property_years=30, lmnp_amortization_furnishing_years=7
#     )

#     calculator = TransactionCalculator(sample_params)
#     calculated_values = calculator.calculate_all()

#     print("--- Calculated Transaction Values ---")
#     for key, value in calculated_values.items():
#         print(f"{key}: {value:,.2f}")
