# In file: scripts/_9_investment_metrics.py

import pandas as pd
import numpy as np
import numpy_financial as npf
from typing import Dict, List, Tuple, Optional
from ..models.params import ModelParameters
from ..fiscal.taxes import Taxes

class InvestmentMetrics:
    """
    Calculates investment performance metrics: IRR, NPV, Cash-on-Cash, Equity Multiple.
    Handles exit scenario calculations including property sale and capital gains tax.
    """

    def __init__(self, params: ModelParameters):
        """
        Initializes the investment metrics calculator.

        Args:
            params: ModelParameters instance with all necessary data
        """
        if not isinstance(params, ModelParameters):
            raise TypeError("params must be an instance of ModelParameters")
        
        self.params = params
        self._initial_equity = getattr(params, 'initial_equity', 0.0)
        self._property_price = params.property_price
        self.tax_calculator = Taxes(params)

    def calculate_exit_proceeds(self, cf_df: pd.DataFrame, bs_df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculates net proceeds from property sale at end of holding period.
        Uses the Taxes class to calculate capital gains tax, respecting the 25-year exemption rule.
        
        Returns:
            Dict with: exit_property_value, selling_costs, remaining_loan_balance,
                    gross_proceeds, capital_gain, capital_gains_tax, net_exit_proceeds
        """
        try:
            holding_years = self.params.holding_period_years
            growth_rate = self.params.property_value_growth_rate
            
            # 1. Estimate Selling Price (Future Value)
            exit_property_value = self._property_price * ((1 + growth_rate) ** holding_years)
            
            # 2. Selling Costs (Agency fees etc. on resale)
            selling_costs = exit_property_value * self.params.exit_selling_fees_percentage
            net_selling_price = exit_property_value - selling_costs
            
            # 3. Remaining Loan Balance
            # Get the loan balance at the very end of the holding period
            final_month_index = holding_years * 12
            if final_month_index in bs_df.index:
                remaining_loan_balance = bs_df.loc[final_month_index, "Loan Balance"]
            else:
                # Fallback if index not found (e.g. loan paid off or indexing issue)
                remaining_loan_balance = 0.0
                
            # 4. Capital Gains Tax
            # Delegate calculation to Taxes class to apply specific rules (abatement, 25yr exemption)
            # We use the original property price as the purchase price basis (simplified)
            tax_results = self.tax_calculator.calculate_capital_gain_tax(
                selling_price=net_selling_price,
                purchase_price=self._property_price,
                years_held=holding_years
            )
            
            capital_gains_tax = tax_results["total_exit_tax"]
            capital_gain = tax_results["gross_capital_gain"]

            # 5. Net Exit Proceeds (Cash flow to equity holder)
            # Net Sale Price - Mortgage Balance - Taxes
            net_exit_proceeds = net_selling_price - remaining_loan_balance - capital_gains_tax
            
            return {
                "exit_property_value": exit_property_value,
                "selling_costs": selling_costs,
                "net_selling_price": net_selling_price,
                "remaining_loan_balance": remaining_loan_balance,
                "capital_gain": capital_gain,
                "capital_gains_tax": capital_gains_tax,
                "net_exit_proceeds": net_exit_proceeds
            }
            
        except Exception as e:
            print(f"Error calculating exit proceeds: {e}")
            return {
                "exit_property_value": 0.0, "selling_costs": 0.0, "net_selling_price": 0.0,
                "remaining_loan_balance": 0.0, "capital_gain": 0.0, "capital_gains_tax": 0.0,
                "net_exit_proceeds": 0.0
            }
        
    def calculate_irr(self, cf_df: pd.DataFrame, bs_df: pd.DataFrame) -> float:
        """
        Calculates IRR using ANNUAL cash flows (not monthly).
        """
        try:
            exit_data = self.calculate_exit_proceeds(cf_df, bs_df)
            net_exit_proceeds = exit_data.get('net_exit_proceeds', 0.0)
            
            # Build ANNUAL cash flow array
            cash_flows = [-self._initial_equity]  # Year 0
            
            # Group by year and sum net changes (exclude Year 0 if it exists)
            cf_df_copy = cf_df.copy()
            cf_df_copy['Year_Index'] = cf_df_copy['Year']
            
            # Filter out Year 0 to avoid double-counting initial equity
            cf_df_filtered = cf_df_copy[cf_df_copy['Year_Index'] > 0]
            annual_cf = cf_df_filtered.groupby('Year_Index')['Net Change in Cash'].sum()
            
            # Add annual cash flows for each year
            for year in range(1, self.params.holding_period_years + 1):
                if year in annual_cf.index:
                    cash_flows.append(annual_cf[year])
                else:
                    cash_flows.append(0.0)
            
            # Add exit proceeds to final year
            if len(cash_flows) > 1:  # Ensure we have at least one year beyond initial investment
                cash_flows[-1] += net_exit_proceeds
            
            # Calculate IRR (already annual since we used annual CFs)
            annual_irr = npf.irr(cash_flows)
            
            return annual_irr
            
        except Exception as e:
            print(f"Error calculating IRR: {e}")
            return 0.0

    def calculate_npv(self, cf_df: pd.DataFrame, bs_df: pd.DataFrame, 
                      discount_rate: Optional[float] = None) -> float:
        """
        Calculates Net Present Value (NPV) at a given discount rate.
        
        Args:
            discount_rate: Annual discount rate (uses params default if None)
        
        Returns:
            NPV in euros
        """
        try:
            if discount_rate is None:
                discount_rate = getattr(self.params, 'discount_rate', 0.05)
            
            monthly_discount_rate = (1 + discount_rate) ** (1/12) - 1
            
            exit_data = self.calculate_exit_proceeds(cf_df, bs_df)
            net_exit_proceeds = exit_data.get('net_exit_proceeds', 0.0)
            
            # Build cash flow array (same as IRR)
            cash_flows = [-self._initial_equity]
            
            for month in range(1, len(cf_df) + 1):
                if month in cf_df.index:
                    net_change = cf_df.loc[month, 'Net Change in Cash']
                    cash_flows.append(net_change)
                else:
                    cash_flows.append(0.0)
            
            cash_flows[-1] += net_exit_proceeds
            
            # Calculate NPV
            npv = npf.npv(monthly_discount_rate, cash_flows)
            
            return npv
            
        except Exception as e:
            print(f"Error calculating NPV: {e}")
            return 0.0

    def calculate_cash_on_cash(self, cf_df: pd.DataFrame) -> float:
        """
        Calculates Cash-on-Cash return (Year 1 cash flow / Initial equity).
        
        Returns:
            Cash-on-Cash as decimal (e.g., 0.05 for 5%)
        """
        try:
            year_1_cf = cf_df[cf_df['Year'] == 1]['Net Change in Cash'].sum()
            
            if self._initial_equity > 0:
                return year_1_cf / self._initial_equity
            else:
                return 0.0
                
        except Exception as e:
            print(f"Error calculating Cash-on-Cash: {e}")
            return 0.0

    def calculate_equity_multiple(self, cf_df: pd.DataFrame, bs_df: pd.DataFrame) -> float:
        """
        Calculates Equity Multiple (Total cash returned / Initial equity).
        
        Returns:
            Equity multiple as ratio (e.g., 1.5 means 1.5x return)
        """
        try:
            # Total operating cash flows
            total_operating_cf = cf_df['Net Change in Cash'].sum()
            
            # Exit proceeds
            exit_data = self.calculate_exit_proceeds(cf_df, bs_df)
            net_exit_proceeds = exit_data.get('net_exit_proceeds', 0.0)
            
            total_cash_returned = total_operating_cf + net_exit_proceeds
            
            if self._initial_equity > 0:
                return total_cash_returned / self._initial_equity
            else:
                return 0.0
                
        except Exception as e:
            print(f"Error calculating Equity Multiple: {e}")
            return 0.0

    def generate_irr_sensitivity(self, cf_df: pd.DataFrame, bs_df: pd.DataFrame,
                                 lease_type: str,
                                 financing_cost_range: float = 0.01,
                                 property_growth_range: float = 0.01,
                                 step: float = 0.005) -> pd.DataFrame:
        """
        Generates IRR sensitivity table varying financing rate and property value growth.

        Args:
            lease_type: The lease type to use for simulations ("airbnb", "furnished_1yr", "unfurnished_3yr")
                       This should match the lease type used in the base case
            financing_cost_range: +/- range for financing costs (e.g., 0.01 for ±1%)
            property_growth_range: +/- range for property value growth (e.g., 0.01 for ±1%)
            step: Step size for variations (default 0.005 = 0.5%)

        Returns:
            DataFrame with IRR sensitivity (rows = property growth, cols = financing costs)
        """
        try:
            from ..models.financial import FinancialModel
            
            base_financing_costs = self.params.loan_interest_rate
            base_property_growth = self.params.property_value_growth_rate
            
            # print(f"DEBUG Sensitivity: Base financing = {base_financing_costs*100:.2f}%, Base growth = {base_property_growth*100:.2f}%")
            # print(f"DEBUG Sensitivity: Using lease_type = {lease_type}")
            
            # Generate ranges
            financing_costs_values = np.arange(
                base_financing_costs - financing_cost_range,
                base_financing_costs + financing_cost_range + step/2,
                step
            )
            
            property_growth_values = np.arange(
                base_property_growth - property_growth_range,
                base_property_growth + property_growth_range + step/2,
                step
            )
            
            # Build sensitivity matrix
            irr_matrix = []
            
            for prop_growth in property_growth_values:
                irr_row = []
                
                for fin_costs in financing_costs_values:
                    # Create modified params
                    params_copy = self._create_params_copy()
                    
                    # Update parameters
                    params_copy.loan_interest_rate = fin_costs
                    params_copy.property_value_growth_rate = prop_growth
                    
                    # Ensure initial_equity is preserved
                    if hasattr(self.params, 'initial_equity'):
                        params_copy.initial_equity = self.params.initial_equity
                                        
                    # Re-run model with modified params
                    model = FinancialModel(params_copy)
                    model.run_simulation(lease_type)  # Use the passed lease type

                    # Calculate IRR
                    temp_cf = model.get_cash_flow()
                    temp_bs = model.get_balance_sheet()

                    temp_metrics = InvestmentMetrics(params_copy)
                    irr = temp_metrics.calculate_irr(temp_cf, temp_bs)
                    
                    irr_row.append(irr * 100)  # Convert to percentage
                
                irr_matrix.append(irr_row)
            
            # Create DataFrame
            df_sensitivity = pd.DataFrame(
                irr_matrix,
                index=[f"{v*100:.1f}%" for v in property_growth_values],
                columns=[f"{v*100:.1f}%" for v in financing_costs_values]
            )

            df_sensitivity.index.name = "Property Growth"
            df_sensitivity.columns.name = "Financing Costs"
            
            return df_sensitivity
            
        except Exception as e:
            print(f"Error generating IRR sensitivity: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()

    def generate_npv_sensitivity(self, cf_df: pd.DataFrame, bs_df: pd.DataFrame,
                               lease_type,
                               discount_rate,
                               financing_cost_range: float = 0.01,
                               property_growth_range: float = 0.01,
                               step: float = 0.005) -> pd.DataFrame:
        """
        Generates NPV scenarios as a datatable
        
        Varies: growth, discount rate, financing costs
        
        Returns:
            DataFrame with scenario results
        """
        try:
            
            from ..models.financial import FinancialModel
            
            base_financing_costs = self.params.loan_interest_rate
            base_property_growth = self.params.property_value_growth_rate

            # Generate ranges
            financing_costs_values = np.arange(
                base_financing_costs - financing_cost_range,
                base_financing_costs + financing_cost_range + step/2,
                step
            )
            
            property_growth_values = np.arange(
                base_property_growth - property_growth_range,
                base_property_growth + property_growth_range + step/2,
                step
            )
            
            # Build sensitivity matrix
            npv_matrix = []
            
            for prop_growth in property_growth_values:
                npv_row = []
                
                for fin_costs in financing_costs_values:
                    # Create modified params
                    params_copy = self._create_params_copy()
                    
                    # Update parameters
                    params_copy.loan_interest_rate = fin_costs
                    params_copy.property_value_growth_rate = prop_growth
                    
                    # Ensure initial_equity is preserved
                    if hasattr(self.params, 'initial_equity'):
                        params_copy.initial_equity = self.params.initial_equity
                                        
                    # Re-run model with modified params
                    model = FinancialModel(params_copy)
                    model.run_simulation(lease_type)  # Use the passed lease type

                    # Calculate IRR
                    temp_cf = model.get_cash_flow()
                    temp_bs = model.get_balance_sheet()

                    temp_metrics = InvestmentMetrics(params_copy)
                    npv = temp_metrics.calculate_npv(temp_cf, temp_bs, discount_rate)

                    npv_row.append(npv * 100)  # Convert to percentage
                
                npv_matrix.append(npv_row)
            
            # Create DataFrame
            df_sensitivity = pd.DataFrame(
                npv_matrix,
                index=[f"{v*100:.1f}%" for v in property_growth_values],
                columns=[f"{v*100:.1f}%" for v in financing_costs_values]
            )

            df_sensitivity.index.name = "Property Growth"
            df_sensitivity.columns.name = "Financing Costs"
            
            return df_sensitivity

        except Exception as e:
            print(f"Error generating NPV scenarios: {e}")
            return pd.DataFrame()

    def _create_params_copy(self) -> ModelParameters:
        """Helper to create a deep copy of parameters for sensitivity analysis"""
        import copy
        return copy.deepcopy(self.params)

    def calculate_all_metrics(self, cf_df: pd.DataFrame, bs_df: pd.DataFrame) -> Dict[str, any]:
        """
        Calculates all investment metrics at once.
        
        Returns:
            Dict with all metrics and exit details
        """
        try:
            exit_data = self.calculate_exit_proceeds(cf_df, bs_df)
            
            metrics = {
                'irr': self.calculate_irr(cf_df, bs_df),
                'npv': self.calculate_npv(cf_df, bs_df),
                'cash_on_cash': self.calculate_cash_on_cash(cf_df),
                'equity_multiple': self.calculate_equity_multiple(cf_df, bs_df),
                **exit_data  # Include all exit details
            }
            
            return metrics
            
        except Exception as e:
            print(f"Error calculating all metrics: {e}")
            return {}