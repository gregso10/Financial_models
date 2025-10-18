# In file: scripts/_2_profit_and_loss.py

import pandas as pd
import numpy_financial as npf
import numpy as np # Needed for array operations if we refine loan calcs
import math
from typing import Dict, List # For type hinting
from ._1_model_params import ModelParameters # Relative import

class PnL:
    """
    Calculates the Profit and Loss statement as a monthly DataFrame
    for the duration of the holding period.
    Accepts ModelParameters via composition.
    """

    def __init__(self, params: ModelParameters):
        """
        Initializes the PnL calculator with the model parameters.

        Args:
            params: An instance of the ModelParameters dataclass.
        """
        if not isinstance(params, ModelParameters):
            raise TypeError("params must be an instance of ModelParameters")
        self.params = params
        # Pre-calculate values that are constant or needed often (if params class doesn't do it)
        # Ensure these attributes/methods exist and are correct in ModelParameters
        self._loan_amount = getattr(params, 'loan_amount', 0.0)
        self._yearly_property_amortization = getattr(params, 'yearly_property_amortization', 0.0)
        self._yearly_furnishing_amortization = getattr(params, 'yearly_furnishing_amortization', 0.0)
        self._yearly_loan_insurance_cost = getattr(params, 'yearly_loan_insurance_cost', 0.0)

        # Basic check for required derived params
        if self._loan_amount == 0.0 and params.loan_percentage > 0:
             print("Warning: Loan amount seems missing in params. Ensure financing calculations ran.")
        if self._yearly_property_amortization == 0.0 and params.fiscal_regime == "LMNP Réel":
             print("Warning: Property amortization seems missing in params.")


    def generate_pnl_dataframe(self, lease_type: str) -> pd.DataFrame:
        """
        Generates the full P&L DataFrame over the holding period on a monthly basis.

        Args:
            lease_type: The type of lease ("airbnb", "furnished_1yr", "unfurnished_3yr").

        Returns:
            A pandas DataFrame containing the monthly P&L statement.
        """
        if lease_type not in self.params.rental_assumptions:
            raise ValueError(f"Lease type '{lease_type}' not found in parameters.")

        num_months = self.params.holding_period_years * 12
        months = list(range(1, num_months + 1))
        years = [(m - 1) // 12 + 1 for m in months] # Calculate corresponding year for each month

        # --- Data Storage ---
        pnl_data: Dict[str, List[float]] = {
            "Year": years,
            "Month_Index": [(m - 1) % 12 for m in months], # 0=Jan, 1=Feb, ...
            "Gross Potential Rent": [],
            "Vacancy Loss": [], # Only for lease types, 0 for Airbnb (handled by occupancy)
            "Gross Operating Income": [],
            "Property Tax": [],
            "Condo Fees": [],
            "PNO Insurance": [],
            "Maintenance": [],
            "Management Fees": [],
            "Airbnb Specific Costs": [], # Will be 0 if not Airbnb
            "Total Operating Expenses": [],
            "Net Operating Income": [],
            "Loan Interest": [],
            "Loan Insurance": [],
            "Depreciation/Amortization": [], # Total fiscal D&A
            "Allowable Amortization For Tax": [], # D&A actually used to reduce tax base
            "Taxable Income": [],
            "Income Tax": [],
            "Social Contributions": [],
            "Total Taxes": [],
            "Net Income": [],
        }

        # --- Monthly Loop ---
        for month in months:
            current_year = pnl_data["Year"][month-1] # Get current year (1-based)
            month_index = pnl_data["Month_Index"][month-1] # Get month index (0-based)
            days_in_month_approx = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31] # No leap year approx

            # --- 1. Revenue Calculation ---
            assumptions = self.params.rental_assumptions[lease_type]
            rent_growth_rate = assumptions.get("rent_growth_rate", 0.0)
            # Apply growth factor based on the *start* of the year
            annual_growth_factor = (1 + rent_growth_rate) ** (current_year - 1)

            gross_potential_rent_month = 0.0
            vacancy_loss_month = 0.0
            goi_month = 0.0

            if lease_type == "airbnb":
                daily_rate = assumptions.get("daily_rate", 0.0)
                occupancy_rate = assumptions.get("occupancy_rate", 0.0)
                seasonality = assumptions.get("monthly_seasonality", [1.0]*12) # Default to 1 if missing

                # Apply annual growth to daily rate
                current_daily_rate = daily_rate * annual_growth_factor

                gross_potential_rent_month = current_daily_rate * days_in_month_approx[month_index]
                # Apply occupancy and monthly seasonality
                goi_month = gross_potential_rent_month * occupancy_rate * seasonality[month_index]
                vacancy_loss_month = 0.0 # Handled via occupancy

            elif lease_type in ["furnished_1yr", "unfurnished_3yr"]:
                monthly_rent_sqm = assumptions.get("monthly_rent_sqm", 0.0)
                # Distribute annual vacancy evenly per month (simplification)
                monthly_vacancy_rate = assumptions.get("vacancy_rate", 0.0) / 12

                # Apply annual growth to monthly rent
                current_monthly_rent = monthly_rent_sqm * self.params.property_size_sqm * annual_growth_factor

                gross_potential_rent_month = current_monthly_rent
                vacancy_loss_month = gross_potential_rent_month * monthly_vacancy_rate
                goi_month = gross_potential_rent_month - vacancy_loss_month

            pnl_data["Gross Potential Rent"].append(gross_potential_rent_month)
            pnl_data["Vacancy Loss"].append(vacancy_loss_month)
            pnl_data["Gross Operating Income"].append(goi_month)

            # --- 2. Operating Expenses Calculation ---
            exp_growth_factor = (1 + self.params.expenses_growth_rate) ** (current_year - 1)

            # Distribute annual expenses monthly, apply growth
            prop_tax_month = (self.params.property_tax_yearly / 12) * exp_growth_factor
            pno_ins_month = (self.params.pno_insurance_yearly / 12) * exp_growth_factor

            # Monthly expenses, apply growth
            condo_fees_month = self.params.condo_fees_monthly * exp_growth_factor

            # Variable expenses (based on current month's GOI)
            maintenance_month = goi_month * self.params.maintenance_percentage_rent
            management_rate = self.params.management_fees_percentage_rent.get(lease_type, 0.0)
            management_fees_month = goi_month * management_rate

            airbnb_costs_month = 0.0
            if lease_type == "airbnb":
                airbnb_costs_month = goi_month * self.params.airbnb_specific_costs_percentage_rent

            total_opex_month = (prop_tax_month + condo_fees_month + pno_ins_month +
                                maintenance_month + management_fees_month + airbnb_costs_month)
            noi_month = goi_month - total_opex_month

            pnl_data["Property Tax"].append(prop_tax_month)
            pnl_data["Condo Fees"].append(condo_fees_month)
            pnl_data["PNO Insurance"].append(pno_ins_month)
            pnl_data["Maintenance"].append(maintenance_month)
            pnl_data["Management Fees"].append(management_fees_month)
            pnl_data["Airbnb Specific Costs"].append(airbnb_costs_month)
            pnl_data["Total Operating Expenses"].append(total_opex_month)
            pnl_data["Net Operating Income"].append(noi_month)

            # --- 3. Financing Costs ---
            interest_month = 0.0
            monthly_rate = self.params.loan_interest_rate / 12
            loan_years = self.params.loan_duration_years

            if monthly_rate > 0 and loan_years > 0 and self._loan_amount > 0 and month <= loan_years * 12:
                 # npf.ipmt period is 1-based index
                interest_month = abs(npf.ipmt(monthly_rate, month, loan_years * 12, self._loan_amount))

            insurance_month = (self._yearly_loan_insurance_cost / 12) if month <= loan_years * 12 else 0.0

            pnl_data["Loan Interest"].append(interest_month)
            pnl_data["Loan Insurance"].append(insurance_month)

            # --- 4. Depreciation & Amortization ---
            depreciation_month = 0.0
            if self.params.fiscal_regime == "LMNP Réel": # Example check
                prop_amort_month = 0.0
                if current_year <= self.params.lmnp_amortization_property_years:
                    prop_amort_month = self._yearly_property_amortization / 12

                furn_amort_month = 0.0
                if current_year <= self.params.lmnp_amortization_furnishing_years:
                     furn_amort_month = self._yearly_furnishing_amortization / 12

                # TODO: Add renovation amortization if needed
                depreciation_month = prop_amort_month + furn_amort_month

            pnl_data["Depreciation/Amortization"].append(depreciation_month)

            # --- 5. Taxable Income ---
            # Simplified: Amortization cannot make taxable income negative (excess carried forward - not modeled here)
            allowable_amort_month = min(depreciation_month, max(0, noi_month - interest_month))
            taxable_income_month = noi_month - interest_month - allowable_amort_month

            pnl_data["Allowable Amortization For Tax"].append(allowable_amort_month)
            pnl_data["Taxable Income"].append(taxable_income_month)

            # --- 6. Taxes ---
            income_tax_month = max(0, taxable_income_month) * self.params.personal_income_tax_bracket
            social_contrib_month = max(0, taxable_income_month) * self.params.social_contributions_rate
            total_taxes_month = income_tax_month + social_contrib_month

            pnl_data["Income Tax"].append(income_tax_month)
            pnl_data["Social Contributions"].append(social_contrib_month)
            pnl_data["Total Taxes"].append(total_taxes_month)

            # --- 7. Net Income ---
            # Using accounting EBT (NOI - Interest - Full Depreciation) - Taxes
            net_income_month = (noi_month - interest_month - depreciation_month) - total_taxes_month
            pnl_data["Net Income"].append(net_income_month)

        # --- Create DataFrame ---
        df_pnl = pd.DataFrame(pnl_data)
        df_pnl.index = months # Set index to month number (1 to num_months)
        df_pnl.index.name = "Month"

        # Remove columns not applicable to the lease type
        if lease_type != "airbnb":
             df_pnl = df_pnl.drop(columns=["Airbnb Specific Costs"])
        if lease_type == "airbnb":
            df_pnl = df_pnl.drop(columns=["Vacancy Loss"]) # Redundant for Airbnb

        # Remove internal calculation columns if desired
        df_pnl = df_pnl.drop(columns=["Month_Index", "Allowable Amortization For Tax"])

        return df_pnl

# --- Example Usage (requires a ModelParameters instance) ---
# if __name__ == "__main__":
#     # (Use the same params setup as in the test fixture)
#     params = ModelParameters(...)
#     params._calculate_acquisition_costs()
#     params._calculate_financing()
#     params._calculate_amortization_bases()

#     pnl_calculator = PnL(params)

#     df_pnl_airbnb = pnl_calculator.generate_pnl_dataframe(lease_type="airbnb")
#     df_pnl_furn = pnl_calculator.generate_pnl_dataframe(lease_type="furnished_1yr")

#     print("--- Airbnb P&L (First 5 Months) ---")
#     print(df_pnl_airbnb.head())

#     print("\n--- Furnished P&L (First 5 Months) ---")
#     print(df_pnl_furn.head())

#     # Example: Yearly summary
#     yearly_summary = df_pnl_furn.groupby("Year").sum()
#     print("\n--- Furnished P&L (Yearly Summary) ---")
#     print(yearly_summary)
