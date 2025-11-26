# In file: scripts/_6_viewer.py

import streamlit as st
import pandas as pd
from typing import Dict, Any
from ._1_model_params import ModelParameters
from ._0_financial_model import FinancialModel 
from ._7_data_visualizer import DataVisualizer

st.set_page_config(layout="wide", page_title="Real Estate Financial Model")

class ModelViewer:
    """
    Multi-page Streamlit interface for the financial model.
    Pages: Dashboard, P&L, Balance Sheet, Cash Flow
    """
    
    def __init__(self):
        self.visualizer = DataVisualizer()
        
        # Initialize session state for model results
        if 'model' not in st.session_state:
            st.session_state.model = None
        if 'params' not in st.session_state:
            st.session_state.params = None

    def display_sidebar_inputs(self, defaults: ModelParameters) -> Dict[str, Any]:
        """Creates sidebar inputs (unchanged from before)"""
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
        # --- Rental Assumptions ---
        st.sidebar.subheader("Rental Assumptions")
        # Trigger a rerun when lease type changes to update fiscal options immediately
        lease_type_choice = st.sidebar.selectbox(
            "Select Lease Type for Simulation", list(defaults.rental_assumptions.keys()),
            key="lease_type_selector"
        )
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

        # # --- Fiscal Parameters ---
        # st.sidebar.subheader("Fiscal Parameters")
        # inputs["fiscal_regime"] = st.sidebar.selectbox("Fiscal Regime", ["LMNP Réel"], index=0) 
        # inputs["personal_income_tax_bracket"] = st.sidebar.slider("Income Tax Bracket (TMI)", 0.0, 0.45, value=defaults.personal_income_tax_bracket, step=0.01)
        # inputs["social_contributions_rate"] = st.sidebar.slider("Social Contributions Rate", 0.0, 0.20, value=defaults.social_contributions_rate, step=0.001, format="%.3f")

        # --- Fiscal Parameters (Dynamic) ---     
        # Define valid regimes based on lease type
        if lease_type_choice == "unfurnished_3yr":
            valid_regimes = ["Revenu Foncier Réel", "Micro-Foncier"]
        else:
            # Furnished (Airbnb / 1yr)
            valid_regimes = ["LMNP Réel", "Micro-BIC"]
        
        # Let user choose from valid options only
        inputs["fiscal_regime"] = st.sidebar.selectbox("Fiscal Regime", valid_regimes, index=0)
        inputs["personal_income_tax_bracket"] = st.sidebar.slider("Income Tax Bracket (TMI)", 0.0, 0.45, value=defaults.personal_income_tax_bracket, step=0.01)

        # --- Exit Parameters ---
        st.sidebar.subheader("Exit Strategy")
        inputs["holding_period_years"] = st.sidebar.number_input("Holding Period (Years)", min_value=1, max_value=50, value=defaults.holding_period_years, step=1)
        inputs["property_value_growth_rate"] = st.sidebar.slider("Annual Property Value Growth", 0.0, 0.10, value=defaults.property_value_growth_rate, step=0.001, format="%.3f")
        inputs["exit_selling_fees_percentage"] = st.sidebar.slider("Selling Fees (%)", 0.0, 0.10, value=defaults.exit_selling_fees_percentage, step=0.005, format="%.3f")
        
        # --- Investment Analysis ---
        st.sidebar.subheader("Investment Analysis")
        inputs["risk_free_rate"] = st.sidebar.slider("Risk-Free Rate (OAT 20Y)", 0.0, 0.10, value=getattr(defaults, 'risk_free_rate', 0.035), step=0.001, format="%.3f", help="French government bond rate")
        inputs["discount_rate"] = st.sidebar.slider("Discount Rate", 0.0, 0.15, value=getattr(defaults, 'discount_rate', 0.05), step=0.005, format="%.3f", help="Project discount rate (risk-free + risk premium)")

        return inputs

    def format_financial_table(self, df: pd.DataFrame, expense_rows: list, label_map: dict) -> pd.DataFrame:
        """Common formatting for financial statements"""
        # Flip expense signs
        rows_to_flip = df.index.intersection(expense_rows)
        df.loc[rows_to_flip] *= -1
        
        # Convert to thousands
        df_k = df / 1000.0
        df_k.index.name = "(in €k)"
        
        # Apply label mapping
        df_k.index = df_k.index.map(lambda x: label_map.get(x, x))
        
        return df_k

    def style_financial_dataframe(self, df: pd.DataFrame):
        """Apply styling to financial dataframes"""
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
                "Net Operating Income", "Taxable Income", "Total Taxes", 
                "Net Income", "Cash Flow from Operations (CFO)",
                "Cash Flow from Investing (CFI)", "Cash Flow from Financing (CFF)"
            ]
            if row_name_clean in separator_rows:
                styles = [s + '; border-top: 1px solid #4b5563' for s in styles]
            
            if row_name_clean == 'Net Income':
                styles = ['background-color: lightgrey; font-weight: bold; color: black; border-top: 2px solid white;'] * len(row)
            return styles

        def style_index_label(label):
            label_clean = label.strip()
            style = 'text-align: left; padding-left: 5px; '
            if 'Total' in label_clean or 'Net' in label_clean:
                style += 'font-weight: bold; '
            
            separator_rows = [
                "Gross Operating Income", "Total Operating Expenses", 
                "Net Operating Income", "Taxable Income", "Total Taxes", 
                "Net Income", "Cash Flow from Operations (CFO)",
                "Cash Flow from Investing (CFI)", "Cash Flow from Financing (CFF)"
            ]
            if label_clean in separator_rows:
                style += 'border-top: 1px solid #4b5563; '
            
            if label_clean == 'Net Income':
                style = 'background-color: lightgrey !important; font-weight: bold !important; color: black !important; border-top: 2px solid white !important; text-align: left !important; padding-left: 5px !important;'
            return style

        styled = df.style \
            .format(format_k_euros) \
            .set_properties(**{'color': 'white', 'border-color': '#4b5563'}) \
            .set_table_styles([
                {'selector': 'th', 'props': [('background-color', '#111827'), ('color', 'white'), ('font-weight', 'bold')]},
                {'selector': 'th.col_heading.level0', 'props': [('font-size', '0.8em'), ('font-style', 'italic'), ('text-align', 'left'), ('padding-left', '5px')]}
            ]) \
            .apply(style_financial_rows, axis=1) \
            .map_index(style_index_label, axis=0)
        
        return styled

    def display_dashboard(self):
        """Dashboard page with summary metrics and charts"""
        st.header("📊 Investment Dashboard")
        
        if st.session_state.model is None:
            st.info("Run simulation from sidebar to see dashboard.")
            return
        
        model = st.session_state.model
        params = st.session_state.params
        pnl = model.get_pnl()
        cf = model.get_cash_flow()
        loan_schedule = model.get_loan_schedule()
        metrics = model.get_investment_metrics()
        
        # === ROW 1: KEY INVESTMENT METRICS ===
        if metrics:
            st.subheader("🎯 Investment Performance Metrics")
            
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            
            with col_m1:
                irr_value = metrics.get('irr', 0) * 100
                st.metric(
                    "IRR", 
                    f"{irr_value:.2f}%",
                    help="Internal Rate of Return - annualized return on equity investment"
                )
            
            with col_m2:
                npv_value = metrics.get('npv', 0) / 1000
                discount_rate = getattr(params, 'discount_rate', 0.05) * 100
                st.metric(
                    "NPV", 
                    f"€{npv_value:.1f}k",
                    help=f"Net Present Value at {discount_rate:.1f}% discount rate"
                )
            
            with col_m3:
                coc_value = metrics.get('cash_on_cash', 0) * 100
                st.metric(
                    "Cash-on-Cash (Y1)", 
                    f"{coc_value:.2f}%",
                    help="Year 1 cash flow divided by initial equity invested"
                )
            
            with col_m4:
                em_value = metrics.get('equity_multiple', 0)
                st.metric(
                    "Equity Multiple", 
                    f"{em_value:.2f}x",
                    help="Total cash returned divided by initial equity"
                )
            
            # Exit details in expander
            with st.expander("📤 Exit Scenario Details"):
                col_e1, col_e2, col_e3 = st.columns(3)
                
                with col_e1:
                    st.metric("Exit Property Value", f"€{metrics.get('exit_property_value', 0)/1000:.1f}k")
                    st.metric("Capital Gain", f"€{metrics.get('capital_gain', 0)/1000:.1f}k")
                
                with col_e2:
                    st.metric("Selling Costs", f"€{metrics.get('selling_costs', 0)/1000:.1f}k")
                    st.metric("Capital Gains Tax", f"€{metrics.get('capital_gains_tax', 0)/1000:.1f}k")
                
                with col_e3:
                    st.metric("Remaining Loan", f"€{metrics.get('remaining_loan_balance', 0)/1000:.1f}k")
                    st.metric("Net Exit Proceeds", f"€{metrics.get('net_exit_proceeds', 0)/1000:.1f}k")
            
            st.markdown("---")
        
        # === ROW 2: CONSOLIDATED CF + SANKEY CHARTS ===
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("Consolidated Cash Flow (Total Period)")
            consolidated_cf = self.visualizer.create_consolidated_cf_table(pnl, cf, params)
            if consolidated_cf is not None:
                st.dataframe(self.style_financial_dataframe(consolidated_cf), use_container_width=True, height=600)
        
        with col2:
            st.subheader("P&L Sankey (Total Period)")
            pnl_sankey = self.visualizer.create_pnl_sankey_total(pnl)
            if pnl_sankey:
                st.plotly_chart(pnl_sankey, use_container_width=True)
            
            st.subheader("Cash Flow Sankey (Total Period)")
            cf_sankey = self.visualizer.create_cf_sankey_total(cf)
            if cf_sankey:
                st.plotly_chart(cf_sankey, use_container_width=True)
        
        st.markdown("---")
        
        # === ROW 3: LOAN ANALYSIS ===
        if loan_schedule is not None and len(loan_schedule) > 0:
            st.subheader("📋 Loan Analysis")
            
            col_loan1, col_loan2 = st.columns([1, 1])
            
            with col_loan1:
                st.markdown("**Amortization Schedule (Yearly)**")
                loan_table = self.visualizer.format_loan_schedule_table(loan_schedule)
                if loan_table is not None:
                    st.dataframe(
                        loan_table.style.format("{:,.1f}"),
                        use_container_width=True,
                        height=400
                    )
            
            with col_loan2:
                loan_chart = self.visualizer.create_loan_balance_chart(loan_schedule)
                if loan_chart:
                    st.plotly_chart(loan_chart, use_container_width=True)
            
            # Loan sensitivity
            st.markdown("**Payment Sensitivity Analysis**")
            sensitivity_heatmap = self.visualizer.create_loan_sensitivity_heatmap(params)
            if sensitivity_heatmap:
                st.plotly_chart(sensitivity_heatmap, use_container_width=True)
        else:
            st.info("💰 No loan in this scenario (100% equity financing)")
        
        st.markdown("---")
        
        # === ROW 4: INVESTMENT RETURN SENSITIVITY ===
        if st.session_state.model is None:
            return
        st.subheader("💎 Investment Return Sensitivity Analysis")
        
        lease_type_used = getattr(params, 'lease_type_used', 'furnished_1yr')
        setattr(params, 'current_lease_type', lease_type_used)
        
        col_sens1, col_sens2 = st.columns([1, 1])
        
        with col_sens1:
            st.markdown("**IRR Sensitivity Heatmap**")
            st.caption("Varying property value growth rate and loan interest rate")
            
            with st.spinner("Calculating IRR sensitivity... (this may take a moment)"):
                irr_heatmap = self.visualizer.create_irr_sensitivity_heatmap(params)
                
                if irr_heatmap:
                    st.plotly_chart(irr_heatmap, use_container_width=True)
                else:
                    st.warning("Could not calculate IRR sensitivity")
        
        with col_sens2:
            st.markdown("**NPV Range Analysis**")
            st.caption("Varying property value growth rate and loan interest rate")
            
            with st.spinner("Calculating NPV range..."):
                npv_heatmap = self.visualizer.create_npv_sensitivity_heatmap(params)
            
                if npv_heatmap:
                    st.plotly_chart(npv_heatmap, use_container_width=True)
                else:
                    st.warning("Could not calculate npv sensitivity")

    def display_pnl_page(self):
        """P&L statement page"""
        st.header("💰 Profit & Loss Statement")
        
        if st.session_state.model is None:
            st.info("Run simulation from sidebar to see P&L.")
            return
        
        pnl = st.session_state.model.get_pnl()
        params = st.session_state.params
        
        if pnl is not None:
            # Yearly summary
            pnl_yearly = pnl.groupby("Year").sum()
            pnl_pivoted = pnl_yearly.T
            pnl_pivoted.columns = [f"Year {col}" for col in pnl_pivoted.columns]
            
            expense_rows = [
                "Vacancy Loss", "Property Tax", "Condo Fees", "PNO Insurance",
                "Maintenance", "Management Fees", "Airbnb Specific Costs",
                "Total Operating Expenses", "Loan Interest", "Loan Insurance",
                "Depreciation/Amortization", "Income Tax", "Social Contributions", "Total Taxes"
            ]
            
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
            
            pnl_formatted = self.format_financial_table(pnl_pivoted, expense_rows, label_map)
            st.dataframe(self.style_financial_dataframe(pnl_formatted), use_container_width=True, height=700)
            
            # Charts below
            col1, col2 = st.columns(2)
            with col1:
                cumulative_chart = self.visualizer.create_pnl_cumulative_chart(pnl)
                if cumulative_chart:
                    st.plotly_chart(cumulative_chart, use_container_width=True)
            
            with col2:
                sankey_y1 = self.visualizer.create_pnl_sankey(pnl)
                if sankey_y1:
                    st.subheader("Year 1 Flow")
                    st.plotly_chart(sankey_y1, use_container_width=True)

    def display_bs_page(self):
        """Balance Sheet page"""
        st.header("🏦 Balance Sheet")
        
        if st.session_state.model is None:
            st.info("Run simulation from sidebar to see Balance Sheet.")
            return
        
        bs = st.session_state.model.get_balance_sheet()
        params = st.session_state.params
        
        if bs is not None:
            # Get key months: 0, 12, 24, ...
            key_months = [0] + [12 * y for y in range(1, params.holding_period_years + 1)]
            bs_yearly = bs.loc[key_months]
            
            # Transpose
            bs_pivoted = bs_yearly.T
            bs_pivoted.columns = ["Initial"] + [f"Year {i}" for i in range(1, params.holding_period_years + 1)]
            
            # Convert to k€
            bs_pivoted_k = bs_pivoted / 1000.0
            bs_pivoted_k.index.name = "(in €k)"
            
            st.dataframe(self.style_financial_dataframe(bs_pivoted_k), use_container_width=True, height=700)

    def display_cf_page(self):
        """Cash Flow statement page"""
        st.header("💵 Cash Flow Statement")
        
        if st.session_state.model is None:
            st.info("Run simulation from sidebar to see Cash Flow.")
            return
        
        cf = st.session_state.model.get_cash_flow()
        params = st.session_state.params
        
        if cf is not None:
            # Yearly summary
            cf_yearly = cf.groupby("Year").sum()
            
            # Handle Beginning/Ending Cash specially
            for year in range(1, params.holding_period_years + 1):
                year_data = cf[cf["Year"] == year]
                cf_yearly.loc[year, "Beginning Cash Balance"] = year_data["Beginning Cash Balance"].iloc[0]
                cf_yearly.loc[year, "Ending Cash Balance"] = year_data["Ending Cash Balance"].iloc[-1]
            
            cf_pivoted = cf_yearly.T
            cf_pivoted.columns = [f"Year {col}" for col in cf_pivoted.columns]
            
            expense_rows = [
                "Loan Principal Repayment", "Acquisition Costs Outflow"
            ]
            
            label_map = {
                "Net Income": "Net Income",
                "Depreciation/Amortization": "  Depreciation/Amortization",
                "Cash Flow from Operations (CFO)": "Cash Flow from Operations (CFO)",
                "Acquisition Costs Outflow": "  Acquisition Costs Outflow",
                "Cash Flow from Investing (CFI)": "Cash Flow from Investing (CFI)",
                "Loan Proceeds": "Loan Proceeds",
                "Equity Injected": "Equity Injected",
                "Loan Principal Repayment": "  Loan Principal Repayment",
                "Cash Flow from Financing (CFF)": "Cash Flow from Financing (CFF)",
                "Net Change in Cash": "Net Change in Cash",
                "Beginning Cash Balance": "Beginning Cash Balance",
                "Ending Cash Balance": "Ending Cash Balance"
            }
            
            cf_formatted = self.format_financial_table(cf_pivoted, expense_rows, label_map)
            st.dataframe(self.style_financial_dataframe(cf_formatted), use_container_width=True, height=700)

    def display_dvf_page(self):
        """Market analysis page using DVF data"""
        st.header("🗺️ Market Analysis (DVF)")
        
        st.markdown("""
        Analyze real estate transactions in France using official DVF (Demandes de Valeurs Foncières) data.
        Data is automatically loaded from all `.txt` files in the `data/` folder.
        """)
        
        # Initialize analyzer in session state
        if 'dvf_analyzer' not in st.session_state:
            st.session_state.dvf_analyzer = None
        
        # Run analysis button
        if st.button("🚀 Run DVF Analysis", type="primary"):
            try:
                from ._10_dvf_analyzer import DVFAnalyzer
                
                with st.spinner("Running DVF analysis pipeline..."):
                    # Auto-loads from data/ directory
                    analyzer = DVFAnalyzer()
                    analyzer.run_full_pipeline()
                    st.session_state.dvf_analyzer = analyzer
                
                st.success("✅ Analysis complete!")
                
            except FileNotFoundError as e:
                st.error(f"❌ {e}")
                st.info("💡 Place DVF `.txt` files in the `data/` folder and try again.")
                return
            except Exception as e:
                st.error(f"Error during analysis: {e}")
                st.exception(e)
                return
        
        # Display results if available
        analyzer = st.session_state.dvf_analyzer
        
        if analyzer is not None and analyzer.geocoded_data is not None:
            # Display summary stats
            st.subheader("📊 Market Summary")
            stats = analyzer.get_summary_stats()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Transactions", f"{stats['total_transactions']:,}")
            with col2:
                st.metric("Median Price", f"€{stats['median_price']:,.0f}")
            with col3:
                st.metric("Mean Price", f"€{stats['mean_price']:,.0f}")
            with col4:
                st.metric("Total Volume", f"€{stats['total_volume']/1e9:.2f}B")
            
            # Price distribution
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Min Price", f"€{stats['min_price']:,.0f}")
            with col_b:
                st.metric("Max Price", f"€{stats['max_price']:,.0f}")
            
            st.markdown("---")
            
            # 3D Map
            st.subheader("🏙️ 3D Price Heatmap")
            st.markdown("""
            **Height** = Property value | **Color** = Blue (low) → Red (high)
            
            💡 Rotate: Click + drag | Zoom: Scroll | Tilt: Right-click + drag
            """)
            
            # Create PyDeck map
            deck = analyzer.create_3d_map()
            st.pydeck_chart(deck)
            
            # Data table
            with st.expander("📋 View Transaction Data (Top 100)"):
                display_cols = ['adresse_complete', 'valeur_fonciere', 'surface_totale']
                available_cols = [c for c in display_cols if c in analyzer.geocoded_data.columns]
                
                display_df = analyzer.geocoded_data[available_cols].head(100).copy()
                display_df['valeur_fonciere'] = display_df['valeur_fonciere'].apply(lambda x: f"€{x:,.0f}")
                display_df['surface_totale'] = display_df['surface_totale'].apply(lambda x: f"{x:.1f} m²")
                display_df.columns = ['Address', 'Price', 'Surface']
                
                st.dataframe(display_df, use_container_width=True, height=400)
            
            # Files loaded info
            with st.expander("📁 Data Sources"):
                st.write(f"Loaded {len(analyzer.txt_files)} file(s):")
                for f in analyzer.txt_files:
                    import os
                    st.write(f"  • {os.path.basename(f)}")
        
        else:
            st.info("👆 Click 'Run DVF Analysis' to begin")
            
            # Instructions
            with st.expander("ℹ️ How to set up DVF data"):
                st.markdown("""
                1. Visit [data.gouv.fr DVF dataset](https://www.data.gouv.fr/fr/datasets/demandes-de-valeurs-foncieres/)
                2. Download semester files (e.g., `ValeursFoncieres-2025-S1.txt`, `ValeursFoncieres-2024-S2.txt`)
                3. Place all `.txt` files in the `data/` folder
                4. Click 'Run DVF Analysis' above
                
                **The analyzer will automatically load and combine all files.**
                """)

    def run(self):
        """Main app orchestrator"""
        st.title("🏠 Real Estate Financial Model")
        
        # Sidebar inputs
        default_params = ModelParameters()
        user_widget_values = self.display_sidebar_inputs(default_params)
        selected_lease = user_widget_values.pop("lease_type_choice", "furnished_1yr")
        
        try:
            current_params = ModelParameters(**user_widget_values)
        except TypeError as e:
            st.error(f"Error creating parameters: {e}")
            st.stop()
        
        # Run simulation button
        if st.sidebar.button("🚀 Run Simulation", type="primary"):
            with st.spinner("Running simulation..."):
                model = FinancialModel(current_params)
                try:
                    model.run_simulation(lease_type=selected_lease)
                    st.session_state.model = model
                    st.session_state.params = current_params
                    st.sidebar.success("✅ Simulation complete!")
                except Exception as e:
                    st.error(f"Simulation error: {e}")
                    st.exception(e)
        
        # Navigation
        st.sidebar.markdown("---")
        page = st.sidebar.radio("Navigate", ["Dashboard", "P&L Statement", "Balance Sheet", "Cash Flow", "DVF"])
        
        # Display selected page
        if page == "Dashboard":
            self.display_dashboard()
        elif page == "P&L Statement":
            self.display_pnl_page()
        elif page == "Balance Sheet":
            self.display_bs_page()
        elif page == "Cash Flow":
            self.display_cf_page()
        elif page == "DVF":
            self.display_dvf_page()