# In file: scripts/_2_profit_and_loss.py

# In file: scripts/_2_profit_and_loss.py

import pandas as pd
import numpy_financial as npf
import numpy as np
from typing import Dict, List
from ._1_model_params import ModelParameters
from ._11_taxes import Taxes # Import the new Tax class

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
        
        # Initialize the Tax Calculator
        self.tax_calculator = Taxes(params)

        # Pre-calculate values that are constant or needed often
        self._loan_amount = getattr(params, 'loan_amount', 0.0)
        self._yearly_property_amortization = getattr(params, 'yearly_property_amortization', 0.0)
        self._yearly_furnishing_amortization = getattr(params, 'yearly_furnishing_amortization', 0.0)
        self._yearly_renovation_amortization = getattr(params, 'yearly_renovation_amortization', 0.0)
        self._yearly_loan_insurance_cost = getattr(params, 'yearly_loan_insurance_cost', 0.0)
        
        if self._loan_amount == 0.0 and params.loan_percentage > 0:
             print("Warning: Loan amount seems missing in params. Ensure financing calculations ran.")

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
        years = [(m - 1) // 12 + 1 for m in months]

        # --- Data Storage ---
        pnl_data: Dict[str, List[float]] = {
            "Year": years,
            "Gross Potential Rent": [],
            "Vacancy Loss": [],
            "Gross Operating Income": [],
            "Property Tax": [],
            "Condo Fees": [],
            "PNO Insurance": [],
            "Maintenance": [],
            "Management Fees": [],
            "Airbnb Specific Costs": [],
            "Total Operating Expenses": [],
            "Net Operating Income": [],
            "Loan Interest": [],
            "Loan Insurance": [],
            "Depreciation/Amortization": [],
            "Taxable Income": [], # New field from Tax class
            "Income Tax": [],
            "Social Contributions": [],
            "Total Taxes": [],
            "Net Income": [],
        }

        # --- Monthly Loop ---
        for month in months:
            current_year = pnl_data["Year"][month-1]
            month_index = (month - 1) % 12 
            days_in_month_approx = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

            # --- 1. Revenue Calculation ---
            assumptions = self.params.rental_assumptions[lease_type]
            rent_growth_rate = assumptions.get("rent_growth_rate", 0.0)
            annual_growth_factor = (1 + rent_growth_rate) ** (current_year - 1)

            gross_potential_rent_month = 0.0
            vacancy_loss_month = 0.0
            goi_month = 0.0

            if lease_type == "airbnb":
                daily_rate = assumptions.get("daily_rate", 0.0)
                occupancy_rate = assumptions.get("occupancy_rate", 0.0)
                seasonality = assumptions.get("monthly_seasonality", [1.0]*12)
                
                current_daily_rate = daily_rate * annual_growth_factor
                gross_potential_rent_month = current_daily_rate * days_in_month_approx[month_index]
                
                # Apply occupancy and seasonality
                goi_month = gross_potential_rent_month * occupancy_rate * seasonality[month_index]
                vacancy_loss_month = 0.0 

            elif lease_type in ["furnished_1yr", "unfurnished_3yr"]:
                monthly_rent_sqm = assumptions.get("monthly_rent_sqm", 0.0)
                monthly_vacancy_rate = assumptions.get("vacancy_rate", 0.0) / 12 
                
                current_monthly_rent = monthly_rent_sqm * self.params.property_size_sqm * annual_growth_factor
                gross_potential_rent_month = current_monthly_rent
                vacancy_loss_month = gross_potential_rent_month * monthly_vacancy_rate
                goi_month = gross_potential_rent_month - vacancy_loss_month

            pnl_data["Gross Potential Rent"].append(gross_potential_rent_month)
            pnl_data["Vacancy Loss"].append(vacancy_loss_month)
            pnl_data["Gross Operating Income"].append(goi_month)

            # --- 2. Operating Expenses Calculation ---
            exp_growth_factor = (1 + self.params.expenses_growth_rate) ** (current_year - 1)

            prop_tax_month = (self.params.property_tax_yearly / 12) * exp_growth_factor
            pno_ins_month = (self.params.pno_insurance_yearly / 12) * exp_growth_factor
            condo_fees_month = self.params.condo_fees_monthly * exp_growth_factor

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
                interest_month = abs(npf.ipmt(monthly_rate, month, loan_years * 12, self._loan_amount))

            insurance_month = (self._yearly_loan_insurance_cost / 12) if month <= loan_years * 12 else 0.0

            pnl_data["Loan Interest"].append(interest_month)
            pnl_data["Loan Insurance"].append(insurance_month)

            # --- 4. Depreciation & Amortization ---
            # Logic now relies on params, Tax class validates if it applies to taxable income
            depreciation_month = 0.0
            
            # Check if we are in a regime that allows amortization in our model
            # (We calculate it for Accounting P&L even if Tax class ignores it for taxable income)
            prop_amort_month = 0.0
            if current_year <= self.params.lmnp_amortization_property_years:
                prop_amort_month = self._yearly_property_amortization / 12
            
            furn_amort_month = 0.0
            if current_year <= self.params.lmnp_amortization_furnishing_years:
                 furn_amort_month = self._yearly_furnishing_amortization / 12

            reno_amort_month = 0.0
            if current_year <= self.params.lmnp_amortization_renovation_years:
                 reno_amort_month = self._yearly_renovation_amortization / 12

            depreciation_month = prop_amort_month + furn_amort_month + reno_amort_month
            pnl_data["Depreciation/Amortization"].append(depreciation_month)

            # --- 5. Taxes (Integration) ---
            # Calculate expenses deductible for tax purposes (Cash based)
            deductible_expenses_month = total_opex_month + interest_month + insurance_month
            
            # Delegate calculation to Taxes class
            # It handles Micro vs Real logic and depreciation deductibility
            tax_results_month = self.tax_calculator.calculate_tax_details(
                gross_revenue=goi_month,
                deductible_expenses=deductible_expenses_month,
                depreciation=depreciation_month,
                lease_type=lease_type
            )

            pnl_data["Taxable Income"].append(tax_results_month["taxable_income"])
            pnl_data["Income Tax"].append(tax_results_month["income_tax"])
            pnl_data["Social Contributions"].append(tax_results_month["social_contributions"])
            pnl_data["Total Taxes"].append(tax_results_month["total_taxes"])

            # --- 6. Net Income ---
            # Accounting Net Income (NOI - Financing - Depreciation - Taxes)
            net_income_month = (noi_month - interest_month - insurance_month - depreciation_month) - tax_results_month["total_taxes"]
            pnl_data["Net Income"].append(net_income_month)

        # --- Create DataFrame ---
        df_pnl = pd.DataFrame(pnl_data)
        df_pnl.index = months 
        df_pnl.index.name = "Month"
        
        # Cleanup columns
        if lease_type != "airbnb":
             df_pnl = df_pnl.drop(columns=["Airbnb Specific Costs"])
        if lease_type == "airbnb":
            df_pnl = df_pnl.drop(columns=["Vacancy Loss"])

        return df_pnl
