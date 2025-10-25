# In file: scripts/_6_viewer.py

import streamlit as st
import pandas as pd
from typing import Dict, Any # For type hinting
from ._1_model_params import ModelParameters
from ._0_financial_model import FinancialModel # Assuming orchestrator is here
from ._7_data_visualizer import DataVisualizer #

class ModelViewer:
    """
    Handles the Streamlit interface for user inputs and displaying model results.
    """
    def __init__(self):
        """Initializes the viewer."""
        self.visualizer = DataVisualizer()
        pass

    def display_sidebar_inputs(self, defaults: ModelParameters) -> Dict[str, Any]:
        """
        Creates Streamlit widgets in the sidebar for all model parameters.

        Args:
            defaults: A ModelParameters instance with default values.

        Returns:
            A dictionary containing the current values from the widgets.
        """
        st.sidebar.header("Simulation Parameters")

        inputs: Dict[str, Any] = {} # Dictionary to store widget values

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
        inputs["lease_type_choice"] = lease_type_choice # Store the selected type

        # We need to structure the inputs dict correctly for nested params
        inputs["rental_assumptions"] = defaults.rental_assumptions.copy() # Start with defaults

        # Display inputs specific to the selected lease type (basic example)
        if lease_type_choice == "airbnb":
            st.sidebar.write("**Airbnb Specifics:**")
            inputs["rental_assumptions"]["airbnb"]["daily_rate"] = st.sidebar.number_input("Daily Rate (€)", value=defaults.rental_assumptions["airbnb"]["daily_rate"], step=1.0)
            inputs["rental_assumptions"]["airbnb"]["occupancy_rate"] = st.sidebar.slider("Occupancy Rate", 0.0, 1.0, value=defaults.rental_assumptions["airbnb"]["occupancy_rate"], step=0.01)
            # Add widget for seasonality if needed (more complex - maybe input avg factor?)
        elif lease_type_choice in ["furnished_1yr", "unfurnished_3yr"]:
             st.sidebar.write(f"**{lease_type_choice} Specifics:**")
             inputs["rental_assumptions"][lease_type_choice]["monthly_rent_sqm"] = st.sidebar.number_input("Monthly Rent / sqm (€)", value=defaults.rental_assumptions[lease_type_choice]["monthly_rent_sqm"], step=0.5)
             inputs["rental_assumptions"][lease_type_choice]["vacancy_rate"] = st.sidebar.slider("Annual Vacancy Rate", 0.0, 0.5, value=defaults.rental_assumptions[lease_type_choice]["vacancy_rate"], step=0.01)

        # General rent growth (could also be lease-type specific if needed)
        # inputs["rent_growth_rate"] = st.sidebar.slider("Annual Rent Growth Rate", 0.0, 0.05, value=defaults.rent_growth_rate, step=0.001, format="%.3f")

        # --- Operating Expenses ---
        st.sidebar.subheader("Operating Expenses")
        inputs["property_tax_yearly"] = st.sidebar.number_input("Property Tax (€/Year)", value=defaults.property_tax_yearly, step=10.0, format="%.0f")
        inputs["condo_fees_monthly"] = st.sidebar.number_input("Condo Fees (€/Month)", value=defaults.condo_fees_monthly, step=5.0, format="%.0f")
        inputs["maintenance_percentage_rent"] = st.sidebar.slider("Maintenance (% of GOI)", 0.0, 0.15, value=defaults.maintenance_percentage_rent, step=0.005, format="%.3f")
        inputs["pno_insurance_yearly"] = st.sidebar.number_input("PNO Insurance (€/Year)", value=defaults.pno_insurance_yearly, step=5.0, format="%.0f")
        # Management fees could be edited per type
        # For simplicity, just show the selected one or use the default dict
        inputs["management_fees_percentage_rent"] = defaults.management_fees_percentage_rent # Keep default dict for now
        inputs["expenses_growth_rate"] = st.sidebar.slider("Annual Expenses Growth Rate", 0.0, 0.05, value=defaults.expenses_growth_rate, step=0.001, format="%.3f")

        # --- Fiscal Parameters ---
        st.sidebar.subheader("Fiscal Parameters (Simplified)")
        inputs["fiscal_regime"] = st.sidebar.selectbox("Fiscal Regime", ["LMNP Réel"], index=0) # Limited choice for now
        inputs["personal_income_tax_bracket"] = st.sidebar.slider("Income Tax Bracket (TMI)", 0.0, 0.45, value=defaults.personal_income_tax_bracket, step=0.01)
        inputs["social_contributions_rate"] = st.sidebar.slider("Social Contributions Rate", 0.0, 0.20, value=defaults.social_contributions_rate, step=0.001, format="%.3f")

        # --- Exit Parameters ---
        st.sidebar.subheader("Exit Strategy")
        inputs["holding_period_years"] = st.sidebar.number_input("Holding Period (Years)", min_value=1, max_value=50, value=defaults.holding_period_years, step=1)
        inputs["property_value_growth_rate"] = st.sidebar.slider("Annual Property Value Growth", 0.0, 0.10, value=defaults.property_value_growth_rate, step=0.001, format="%.3f")
        inputs["exit_selling_fees_percentage"] = st.sidebar.slider("Selling Fees (%)", 0.0, 0.10, value=defaults.exit_selling_fees_percentage, step=0.005, format="%.3f")

        return inputs


    def display_outputs(self, model: FinancialModel):
        """
        Displays the generated P&L, BS, and CF DataFrames, filtered for Year 1.

        Args:
            model: The executed FinancialModel instance containing the results.
        """
        st.header("Financial Statements - Year 1")

        pnl = model.get_pnl()
        bs = model.get_balance_sheet()
        cf = model.get_cash_flow()

        # Inside ModelViewer.display_outputs, after getting a DataFrame (e.g., pnl_y1_sum)

        # st.subheader("Profit & Loss (Year 1 Summary - Formatted)")

        # if pnl is not None:
        #     st.subheader("Profit & Loss (Year 1)")
        #     pnl_y1 = pnl[pnl["Year"] == 1]
        #     # Optional: Sum monthly to show annual total for Year 1
        #     pnl_y1_sum = pnl_y1.drop(columns='Year').sum().to_frame('Year 1 Total')
        #     # st                                                                        .dataframe(pnl_y1_sum.style.format("{:,.2f}"))
        #     st.dataframe(pnl_y1.style.format("{:,.2f}")) # To show monthly
        # else:
        #     st.warning("P&L Statement not generated.")
        #         # Function to apply bold style to the index (row labels)

        st.subheader("Profit & Loss (Yearly Summary)")

        if pnl is not None:
            pnl_all = pnl.groupby(["Year"]).sum()
            pnl_pivoted = pnl_all.T
            pnl_pivoted.columns = [f"Year {col}" for col in pnl_pivoted.columns]
            
            # --- Start: P&L Formatting Modifications ---

            # 1. (Req 1) Define expense rows to flip their sign for (xx) display
            # These items are stored as positive values but represent outflows.
            expense_rows = [
                "Vacancy Loss", "Property Tax", "Condo Fees", "PNO Insurance",
                "Maintenance", "Management Fees", "Airbnb Specific Costs",
                "Total Operating Expenses", "Loan Interest", "Loan Insurance",
                "Depreciation/Amortization", "Income Tax", 
                "Social Contributions", "Total Taxes"
            ]
            
            # Find which of these rows actually exist in the dataframe and flip their sign
            rows_to_flip = pnl_pivoted.index.intersection(expense_rows)
            pnl_pivoted.loc[rows_to_flip] *= -1

            # 2. (Req 4) Divide by 1000 to get k€
            pnl_pivoted_k = pnl_pivoted / 1000.0

            # 3. (Req 7) Set the index name (top-left corner)
            pnl_pivoted_k.index.name = "(in €k)"

            # 4. (Req 5) Create a label map for indentation and cleaner names
            label_map = {
                "Gross Potential Rent": "Gross Potential Rent",
                "Vacancy Loss": "  Vacancy Loss",
                "Gross Operating Income": "Gross Operating Income",
                "Property Tax": "  Property Tax",
                "Condo Fees": "  Condo Fees",
                "PNO Insurance": "  PNO Insurance",
                "Maintenance": "  Maintenance",
                "Management Fees": "  Management Fees",
                "Airbnb Specific Costs": "  Airbnb Specific Costs",
                "Total Operating Expenses": "Total Operating Expenses",
                "Net Operating Income": "Net Operating Income",
                "Loan Interest": "  Loan Interest",
                "Loan Insurance": "  Loan Insurance",
                "Depreciation/Amortization": "  Depreciation/Amortization",
                "Taxable Income": "Taxable Income",
                "Income Tax": "  Income Tax",
                "Social Contributions": "  Social Contributions",
                "Total Taxes": "Total Taxes",
                "Net Income": "Net Income"
            }
            # Apply the map, keeping original name if not in map
            pnl_pivoted_k.index = pnl_pivoted_k.index.map(lambda x: label_map.get(x, x))

            # 5. (Req 1, 2, 3) Define the custom formatter
            def format_k_euros(val):
                """Formats numbers in k€: (xx) for negative, xx for positive, 0 for zero."""
                if pd.isna(val):
                    return "-" # Handle missing data
                try:
                    # Round to nearest integer (k€)
                    val_int = int(round(val, 0)) 
                    if val_int < 0:
                        return f"({abs(val_int):,})" # (1,234)
                    elif val_int == 0:
                        return "0"
                    else:
                        return f"{val_int:,}" # 1,234
                except (ValueError, TypeError):
                    return val # Return as-is if not a number

            # 6. (Req 6) Define the styling function for separators and bolding
            def style_financial_rows(row):
                """
                Applies styles to a row based on its *new* index name (row.name).
                - Bolds any 'Total' or 'Net' row.
                - Adds line separators above key summary rows.
                - Highlights 'Net Income'.
                """
                row_name_clean = row.name.strip() # Remove indentation for matching
                styles = [''] * len(row) # Default
                
                # Bolding for totals/net
                if 'Total' in row_name_clean or 'Net' in row_name_clean:
                    styles = ['font-weight: bold'] * len(row)
                
                # (Req 6) Line separators
                separator_rows = [
                    "Gross Operating Income", 
                    "Total Operating Expenses", 
                    "Net Operating Income",
                    "Taxable Income",
                    "Total Taxes",
                    "Net Income"
                ]
                if row_name_clean in separator_rows:
                    # Apply a border-top to all cells in this row
                    styles = [s + '; border-top: 1px solid #4b5563' for s in styles]
                
                # Specific override for 'Net Income'
                if row_name_clean == 'Net Income':
                    styles = [
                        'background-color: lightgrey; font-weight: bold; color: black; border-top: 2px solid white;'
                    ] * len(row)
                    
                return styles
            
            def style_pnl_index_label(label):
                """
                Applies styles to the *index label* based on its name.
                Mirrors the logic in 'style_financial_rows' for consistency.
                """
                label_clean = label.strip() # Remove indentation
                # Start with base styles from .set_table_styles
                style = 'text-align: left; padding-left: 5px; ' 

                # Bolding for totals/net
                if 'Total' in label_clean or 'Net' in label_clean:
                    style += 'font-weight: bold; '
                
                # Line separators
                separator_rows = [
                    "Gross Operating Income", 
                    "Total Operating Expenses", 
                    "Net Operating Income",
                    "Taxable Income",
                    "Total Taxes",
                    "Net Income"
                ]
                if label_clean in separator_rows:
                    style += 'border-top: 1px solid #4b5563; '
                
                # Specific override for 'Net Income'
                if label_clean == 'Net Income':
                    # This style will *override* the previous ones
                    style = 'background-color: lightgrey; font-weight: bold; color: black; border-top: 2px solid white; text-align: left; padding-left: 5px; '
                    
                return style

            # 7. Build the *complete* Styler object
            styled_pnl = pnl_pivoted_k.style \
                .format(format_k_euros) \
                .set_properties(
                    **{
                        # 'background-color': '#1f2937',
                        'color': 'white',
                        'border-color': '#4b5563'
                    }
                ) \
                .set_table_styles([
                    {
                        'selector': 'th', # All headers (index and columns)
                        'props': [
                            ('background-color', '#111827'),
                            ('color', 'white'),
                            ('font-weight', 'bold')
                        ]
                    },
                    # {
                    #     'selector': 'th.row_heading', # Index labels (e.g., "Net Income")
                    #     'props': [
                    #         ('text-align', 'left'),
                    #         ('padding-left', '5px')
                    #     ]
                    # },
                    {
                        'selector': 'th.col_heading.level0', # Index name (top-left)
                        'props': [
                            ('font-size', '0.8em'),
                            ('font-style', 'italic'),
                            ('text-align', 'left'),
                            ('padding-left', '5px')
                        ]
                    }
                ]) \
                .apply(style_financial_rows, axis=1) \
                .map_index(style_pnl_index_label, axis=0)

            st.dataframe(styled_pnl, use_container_width=True)
        
        st.subheader("P&L Flow (Year 1)")
        pnl_sankey_fig = self.visualizer.create_pnl_sankey(pnl)
        
        if pnl_sankey_fig:
            st.plotly_chart(pnl_sankey_fig, use_container_width=True)
        else:
            # This is the warning message you were seeing
            st.warning("Could not generate P&L Sankey chart.")
        
        if bs is not None:
            st.subheader("Balance Sheet (End of Year 1)")
             # Show Month 0 (Initial) and Month 12 (End of Year 1)
            bs_y1 = bs.loc[[0, 12]]
            st.dataframe(bs_y1.style.format("{:,.2f}"))
        else:
            st.warning("Balance Sheet not generated.")

        if cf is not None:
            st.subheader("Cash Flow (Year 1)")
            cf_y1 = cf[cf["Year"] == 1]
            # Optional: Sum monthly to show annual total for Year 1
            cf_y1_sum = cf_y1.drop(columns=['Year', 'Beginning Cash Balance', 'Ending Cash Balance']).sum().to_frame('Year 1 Total')
            # Add back Beg/End Cash
            cf_y1_sum.loc['Beginning Cash Balance'] = cf_y1['Beginning Cash Balance'].iloc[0]
            cf_y1_sum.loc['Ending Cash Balance'] = cf_y1['Ending Cash Balance'].iloc[-1]
            st.dataframe(cf_y1_sum.style.format("{:,.2f}"))
            # st.dataframe(cf_y1.style.format("{:,.2f}")) # To show monthly
        else:
            st.warning("Cash Flow Statement not generated.")


    def run(self):
        """
        Main method to run the Streamlit application interface.
        """
        st.title("Real Estate Financial Model")

        # 1. Create default parameters
        default_params = ModelParameters() # Use class defaults

        # 2. Display sidebar inputs and get current values
        user_widget_values = self.display_sidebar_inputs(default_params)

        # 3. Create a new ModelParameters instance from widget values
        # Need to handle potential nested dicts like rental_assumptions separately if edited
        # For simplicity now, assume display_sidebar_inputs returns a dict that maps directly
        # Extract lease_type choice as it's not a direct param
        selected_lease = user_widget_values.pop("lease_type_choice", "furnished_1yr")

        try:
             # Create params instance using dictionary unpacking
             current_params = ModelParameters(**user_widget_values)
        except TypeError as e:
            st.error(f"Error creating parameters from inputs: {e}")
            st.stop() # Stop execution if params can't be created

        # 4. Run Simulation Button
        if st.sidebar.button("Run Simulation"):
            # 5. Instantiate and run the model
            model = FinancialModel(current_params)
            try:
                model.run_simulation(lease_type=selected_lease)
                # 6. Display results
                self.display_outputs(model)
            except Exception as e:
                st.error(f"An error occurred during simulation: {e}")
                # Optionally display traceback for debugging
                # st.exception(e)
        else:
            st.info("Adjust parameters in the sidebar and click 'Run Simulation'.")


# --- To run this Streamlit app ---
# 1. Save this code as scripts/_6_viewer.py
# 2. Create a main app file (e.g., app.py) in your root directory:
#    ```python
#    # app.py
#    from scripts._6_viewer import ModelViewer
#
#    if __name__ == "__main__":
#        viewer = ModelViewer()
#        viewer.run()
#    ```
# 3. Make sure you have __init__.py in the scripts folder.
# 4. Run from your terminal in the root directory: streamlit run app.py
