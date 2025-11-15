# In file: scripts/_6_viewer.py

import streamlit as st
import pandas as pd
# import plotly.graph_objects as go  <-- No longer needed here
from typing import Dict, Any # For type hinting
from ._1_model_params import ModelParameters
from ._0_financial_model import FinancialModel 
from ._7_data_visualizer import DataVisualizer # <-- Import new class

st.set_page_config(layout="wide")
class ModelViewer:
    """
    Handles the Streamlit interface for user inputs and displaying model results.
    #TODO: work on the CFs viz logic to add sankey + waterfall
    """
    def __init__(self):
        """Initializes the viewer."""
        self.visualizer = DataVisualizer() # <-- Instantiate it

    def display_sidebar_inputs(self, defaults: ModelParameters) -> Dict[str, Any]:
        """
        Creates Streamlit widgets in the sidebar for all model parameters.
        (This method is unchanged, assuming it's correct)
        """
        st.sidebar.header("Simulation Parameters")

        inputs: Dict[str, Any] = {} 

        # --- Property & Acquisition ---
        st.sidebar.subheader("Property & Acquisition")
        inputs["property_address_city"] = st.sidebar.text_input("City", value=defaults.property_address_city)
        inputs["property_price"] = st.sidebar.number_input("Property Price (€, FAI)", value=defaults.property_price, step=1000.0, format="%.0f")
        inputs["agency_fees_percentage"] = st.sidebar.slider("Agency Fees (%)", 0.0, 0.15, value=defaults.agency_fees_percentage, step=0.005, format="%.3f")
        inputs["notary_fees_percentage_estimate"] = st.sidebar.slider("Notary Fees Est. (%)", 0.0, 0.12, value=defaults.notary_fees_percentage_estimate, step=0.001, format="%.3f")
        inputs["property_size_sqm"] = st.sidebar.number_input("Size (sqm)", value=defaults.property_size_sqm, step=1.0, format="%.1f")
        inputs["initial_renovation_costs"] = st.sidebar.number_input("Initial Renovation (€)", value=defaults.initial_renovation_costs, step=500.0, format="%.0f")
        inputs["furnishing_costs"] = st.sidebar.number_input("Furnishing (€)", value=defaults.furnishing_costs, step=100.0, format="%.0f")

        # --- Financing ---
        st.sidebar.subheader("Financing")
        inputs["loan_percentage"] = st.sidebar.slider("Loan Percentage (%)", 0.0, 1.1, value=defaults.loan_percentage, step=0.01, format="%.2f")
        inputs["loan_interest_rate"] = st.sidebar.slider("Loan Interest Rate (%)", 0.0, 0.08, value=defaults.loan_interest_rate, step=0.001, format="%.3f")
        inputs["loan_duration_years"] = st.sidebar.number_input("Loan Duration (Years)", min_value=1, max_value=30, value=defaults.loan_duration_years, step=1)
        inputs["loan_insurance_rate"] = st.sidebar.slider("Loan Insurance Rate (%)", 0.0, 0.01, value=defaults.loan_insurance_rate, step=0.0005, format="%.4f")

        # --- Rental Assumptions ---
        st.sidebar.subheader("Rental Assumptions")
        lease_type_choice = st.sidebar.selectbox("Select Lease Type for Simulation", list(defaults.rental_assumptions.keys()))
        inputs["lease_type_choice"] = lease_type_choice 

        inputs["rental_assumptions"] = defaults.rental_assumptions.copy() 

        if lease_type_choice == "airbnb":
            st.sidebar.write("**Airbnb Specifics:**")
            inputs["rental_assumptions"]["airbnb"]["daily_rate"] = st.sidebar.number_input("Daily Rate (€)", value=defaults.rental_assumptions["airbnb"]["daily_rate"], step=1.0)
            inputs["rental_assumptions"]["airbnb"]["occupancy_rate"] = st.sidebar.slider("Occupancy Rate", 0.0, 1.0, value=defaults.rental_assumptions["airbnb"]["occupancy_rate"], step=0.01)
        elif lease_type_choice in ["furnished_1yr", "unfurnished_3yr"]:
             st.sidebar.write(f"**{lease_type_choice} Specifics:**")
             inputs["rental_assumptions"][lease_type_choice]["monthly_rent_sqm"] = st.sidebar.number_input("Monthly Rent / sqm (€)", value=defaults.rental_assumptions[lease_type_choice]["monthly_rent_sqm"], step=0.5)
             inputs["rental_assumptions"][lease_type_choice]["vacancy_rate"] = st.sidebar.slider("Annual Vacancy Rate", 0.0, 0.5, value=defaults.rental_assumptions[lease_type_choice]["vacancy_rate"], step=0.01)

        # --- Operating Expenses ---
        st.sidebar.subheader("Operating Expenses")
        inputs["property_tax_yearly"] = st.sidebar.number_input("Property Tax (€/Year)", value=defaults.property_tax_yearly, step=10.0, format="%.0f")
        inputs["condo_fees_monthly"] = st.sidebar.number_input("Condo Fees (€/Month)", value=defaults.condo_fees_monthly, step=5.0, format="%.0f")
        inputs["maintenance_percentage_rent"] = st.sidebar.slider("Maintenance (% of GOI)", 0.0, 0.15, value=defaults.maintenance_percentage_rent, step=0.005, format="%.3f")
        inputs["pno_insurance_yearly"] = st.sidebar.number_input("PNO Insurance (€/Year)", value=defaults.pno_insurance_yearly, step=5.0, format="%.0f")
        inputs["management_fees_percentage_rent"] = defaults.management_fees_percentage_rent 
        inputs["expenses_growth_rate"] = st.sidebar.slider("Annual Expenses Growth Rate", 0.0, 0.05, value=defaults.expenses_growth_rate, step=0.001, format="%.3f")

        # --- Fiscal Parameters ---
        st.sidebar.subheader("Fiscal Parameters (Simplified)")
        inputs["fiscal_regime"] = st.sidebar.selectbox("Fiscal Regime", ["LMNP Réel"], index=0) 
        inputs["personal_income_tax_bracket"] = st.sidebar.slider("Income Tax Bracket (TMI)", 0.0, 0.45, value=defaults.personal_income_tax_bracket, step=0.01)
        inputs["social_contributions_rate"] = st.sidebar.slider("Social Contributions Rate", 0.0, 0.20, value=defaults.social_contributions_rate, step=0.001, format="%.3f")

        # --- Exit Parameters ---
        st.sidebar.subheader("Exit Strategy")
        inputs["holding_period_years"] = st.sidebar.number_input("Holding Period (Years)", min_value=1, max_value=50, value=defaults.holding_period_years, step=1)
        inputs["property_value_growth_rate"] = st.sidebar.slider("Annual Property Value Growth", 0.0, 0.10, value=defaults.property_value_growth_rate, step=0.001, format="%.3f")
        inputs["exit_selling_fees_percentage"] = st.sidebar.slider("Selling Fees (%)", 0.0, 0.10, value=defaults.exit_selling_fees_percentage, step=0.005, format="%.3f")

        return inputs


    def display_outputs(self, model: FinancialModel, params: ModelParameters):
        """
        Displays the generated P&L, BS, and CF DataFrames, filtered for Year 1.

        Args:
            model: The executed FinancialModel instance containing the results.
        """
        st.header("Financial Statements")

        pnl = model.get_pnl()
        bs = model.get_balance_sheet()
        cf = model.get_cash_flow()

        # --- START: NEW LAYOUT ---
        # Create two columns, 3/5 width for table, 2/5 for charts
        col1, col2 = st.columns([3, 2])

        with col1:
            st.subheader("Profit & Loss (Yearly Summary)")
            if pnl is not None:
                pnl_all = pnl.groupby(["Year"]).sum()
                pnl_pivoted = pnl_all.T
                pnl_pivoted.columns = [f"Year {col}" for col in pnl_pivoted.columns]
                
                # --- Start: P&L Formatting ---
                expense_rows = [
                    "Vacancy Loss", "Property Tax", "Condo Fees", "PNO Insurance",
                    "Maintenance", "Management Fees", "Airbnb Specific Costs",
                    "Total Operating Expenses", "Loan Interest", "Loan Insurance",
                    "Depreciation/Amortization", "Income Tax", 
                    "Social Contributions", "Total Taxes"
                ]
                
                rows_to_flip = pnl_pivoted.index.intersection(expense_rows)
                pnl_pivoted.loc[rows_to_flip] *= -1
                pnl_pivoted_k = pnl_pivoted / 1000.0
                pnl_pivoted_k.index.name = "(in €k)"

                label_map = {
                    "Gross Potential Rent": "Gross Potential Rent", "Vacancy Loss": "  Vacancy Loss",
                    "Gross Operating Income": "Gross Operating Income", "Property Tax": "  Property Tax",
                    "Condo Fees": "  Condo Fees", "PNO Insurance": "  PNO Insurance",
                    "Maintenance": "  Maintenance", "Management Fees": "  Management Fees",
                    "Airbnb Specific Costs": "  Airbnb Specific Costs",
                    "Total Operating Expenses": "Total Operating Expenses",
                    "Net Operating Income": "Net Operating Income",
                    "Loan Interest": "  Loan Interest", "Loan Insurance": "  Loan Insurance",
                    "Depreciation/Amortization": "  Depreciation/Amortization",
                    "Taxable Income": "Taxable Income", "Income Tax": "  Income Tax",
                    "Social Contributions": "  Social Contributions", "Total Taxes": "Total Taxes",
                    "Net Income": "Net Income"
                }
                pnl_pivoted_k.index = pnl_pivoted_k.index.map(lambda x: label_map.get(x, x))

                def format_k_euros(val):
                    if pd.isna(val): return "-"
                    try:
                        val_int = int(round(val, 0)) 
                        if val_int < 0: return f"({abs(val_int):,})"
                        elif val_int == 0: return "0"
                        else: return f"{val_int:,}"
                    except (ValueError, TypeError): return val

                def style_financial_rows(row):
                    row_name_clean = row.name.strip()
                    styles = [''] * len(row)
                    
                    if 'Total' in row_name_clean or 'Net' in row_name_clean:
                        styles = ['font-weight: bold'] * len(row)
                    
                    separator_rows = [
                        "Gross Operating Income", "Total Operating Expenses", 
                        "Net Operating Income", "Taxable Income",
                        "Total Taxes", "Net Income"
                    ]
                    if row_name_clean in separator_rows:
                        styles = [s + '; border-top: 1px solid #4b5563' for s in styles]
                    
                    if row_name_clean == 'Net Income':
                        styles = [
                            'background-color: lightgrey; font-weight: bold; color: black; border-top: 2px solid white;'
                        ] * len(row)
                    return styles

                def style_pnl_index_label(label):
                    label_clean = label.strip()
                    style = 'text-align: left; padding-left: 5px; ' 
                    if 'Total' in label_clean or 'Net' in label_clean:
                        style += 'font-weight: bold; '
                    separator_rows = [
                        "Gross Operating Income", "Total Operating Expenses", 
                        "Net Operating Income", "Taxable Income",
                        "Total Taxes", "Net Income"
                    ]
                    if label_clean in separator_rows:
                        style += 'border-top: 1px solid #4b5563; '
                    
                    if label_clean == 'Net Income':
                        style = (
                            'background-color: lightgrey !important; '
                            'font-weight: bold !important; '
                            'color: black !important; '
                            'border-top: 2px solid white !important; '
                            'text-align: left !important; '
                            'padding-left: 5px !important; '
                        )
                    return style

                styled_pnl = pnl_pivoted_k.style \
                    .format(format_k_euros) \
                    .set_properties(**{'color': 'white', 'border-color': '#4b5563'}) \
                    .set_table_styles([
                        {'selector': 'th', 'props': [('background-color', '#111827'), ('color', 'white'), ('font-weight', 'bold')]},
                        {'selector': 'th.col_heading.level0', 'props': [('font-size', '0.8em'), ('font-style', 'italic'), ('text-align', 'left'), ('padding-left', '5px')]}
                    ]) \
                    .apply(style_financial_rows, axis=1) \
                    .map_index(style_pnl_index_label, axis=0)

                st.dataframe(styled_pnl, use_container_width=True, height=700)
            
            else:
                st.warning("P&L Statement not generated.")
            
        with col2:
            # --- Row 1: Sankey ---
            st.subheader("P&L Flow (Year 1)")
            pnl_sankey_fig = self.visualizer.create_pnl_sankey(pnl)
            
            if pnl_sankey_fig:
                st.plotly_chart(pnl_sankey_fig, use_container_width=True)
            else:
                st.warning("Could not generate P&L Sankey chart.")
            
            # --- Row 2: Cumulative ---
            st.subheader("Cumulative P&L Performance")
            pnl_cumulative_fig = self.visualizer.create_pnl_cumulative_chart(pnl)
            
            if pnl_cumulative_fig:
                st.plotly_chart(pnl_cumulative_fig, use_container_width=True)
            else:
                st.warning("Could not generate Cumulative P&L chart.")

        # --- END: NEW LAYOUT ---

        # The BS and CF statements will now appear below the columns

        st.subheader("Balance Sheet (Yearly)")

        if bs is not None:
            # Get key months: 0, 12, 24, ...
            key_months = [0] + [12 * y for y in range(1, params.holding_period_years + 1)]
            bs_yearly = bs.loc[key_months]
            
            # Transpose for year columns
            bs_pivoted = bs_yearly.T
            bs_pivoted.columns = ["Initial"] + [f"Year {i}" for i in range(1, params.holding_period_years + 1)]
            
            # Convert to k€
            bs_pivoted_k = bs_pivoted / 1000.0
            bs_pivoted_k.index.name = "(in €k)"
            
            # Format function (reuse from P&L)
            def format_k_euros(val):
                if pd.isna(val): return "-"
                val_int = int(round(val, 0))
                if val_int < 0: return f"({abs(val_int):,})"
                return f"{val_int:,}" if val_int != 0 else "0"
            
            # Style with sections
            styled_bs = bs_pivoted_k.style.format(format_k_euros)
            st.dataframe(styled_bs, use_container_width=True)

        else:
            st.warning("Balance sheet Statement not generated.")    

        if cf is not None:
            st.subheader("Cash Flow (Year 1)")
            cf_y1 = cf[cf["Year"] == 1]
            # Select columns in correct order
            cf_cols_ordered = [
                'Cash Flow from Operations (CFO)',
                'Acquisition Costs Outflow', 
                'Cash Flow from Investing (CFI)',
                'Loan Proceeds', 'Equity Injected', 'Loan Principal Repayment',
                'Cash Flow from Financing (CFF)',
                'Net Change in Cash',
                'Beginning Cash Balance',
                'Net Change in Cash',
                'Ending Cash Balance'
            ]
            cf_y1_sum = cf_y1[cf_cols_ordered].sum().to_frame('Year 1 Total')
            # Overwrite beginning/ending with first/last values
            cf_y1_sum.loc['Beginning Cash Balance'] = cf_y1['Beginning Cash Balance'].iloc[0]
            cf_y1_sum.loc['Ending Cash Balance'] = cf_y1['Ending Cash Balance'].iloc[-1]
            st.dataframe(cf_y1_sum.style.format("{:,.2f}"))
        else:
            st.warning("Cash Flow Statement not generated.")


    def run(self):
        """
        Main method to run the Streamlit application interface.
        """
        st.title("Real Estate Financial Model")

        default_params = ModelParameters() 
        user_widget_values = self.display_sidebar_inputs(default_params)
        selected_lease = user_widget_values.pop("lease_type_choice", "furnished_1yr")

        try:
             current_params = ModelParameters(**user_widget_values)
        except TypeError as e:
            st.error(f"Error creating parameters from inputs: {e}")
            st.stop() 

        if st.sidebar.button("Run Simulation"):
            model = FinancialModel(current_params)
            try:
                model.run_simulation(lease_type=selected_lease)
                self.display_outputs(model, current_params)
            except Exception as e:
                st.error(f"An error occurred during simulation: {e}")
                st.exception(e) # Add traceback for debugging
        else:
            st.info("Adjust parameters in the sidebar and click 'Run Simulation'.")
