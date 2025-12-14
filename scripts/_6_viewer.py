# In file: scripts/_6_viewer.py

import streamlit as st
import pandas as pd
from typing import Dict, Any
from ._1_model_params import ModelParameters
from ._0_financial_model import FinancialModel 
from ._7_data_visualizer import DataVisualizer
from ._12_excel_exporter import ExcelExporter
from ._13_excel_exporter_full import ExcelExporterFull
from ._14_translations import t, toggle_language, get_language, get_pnl_label_map, get_cf_label_map, fmt_number, fmt_currency, fmt_percent

st.set_page_config(layout="wide", page_title="Real Estate Financial Model")

class ModelViewer:
    """
    Multi-page Streamlit interface for the financial model.
    Pages: Dashboard, P&L, Balance Sheet, Cash Flow
    Supports English/French translation.
    """
    
    def __init__(self):
        self.visualizer = DataVisualizer()
        
        # Initialize session state
        if 'model' not in st.session_state:
            st.session_state.model = None
        if 'params' not in st.session_state:
            st.session_state.params = None
        if 'language' not in st.session_state:
            st.session_state.language = "en"

    def display_sidebar_inputs(self, defaults: ModelParameters) -> Dict[str, Any]:
        """Creates sidebar inputs with translations and improved UX."""
        
        # Language toggle at top of sidebar
        st.sidebar.header(t("simulation_params"))
        
        inputs: Dict[str, Any] = {} 

        # --- Property & Acquisition ---
        st.sidebar.subheader(t("property_acquisition"))
        inputs["property_address_city"] = st.sidebar.text_input(t("city"), value=defaults.property_address_city)
        inputs["property_price"] = st.sidebar.number_input(
            t("property_price"), 
            value=defaults.property_price, 
            step=1000.0, 
            format="%.0f",
            help=t("property_price_help")
        )
        if inputs["property_price"] > 0:
            st.sidebar.caption(f"→ {fmt_currency(inputs['property_price'])}")
        
        # Agency fees as 0-100% display
        inputs["agency_fees_percentage"] = st.sidebar.slider(
            t("agency_fees"), 
            0.0, 15.0, 
            value=defaults.agency_fees_percentage * 100, 
            step=0.5, 
            format="%.1f%%",
            help=t("agency_fees_help")
        ) / 100  # Convert back to decimal
        
        # Notary fees as radio button
        notary_type = st.sidebar.radio(
            t("notary_type"),
            [t("notary_ancien"), t("notary_neuf")],
            index=0,
            help=t("notary_help")
        )
        inputs["notary_fees_percentage_estimate"] = 0.08 if t("notary_ancien") in notary_type else 0.055
        
        inputs["property_size_sqm"] = st.sidebar.number_input(t("property_size"), value=defaults.property_size_sqm, step=1.0, format="%.1f")
        
        inputs["initial_renovation_costs"] = st.sidebar.number_input(t("initial_renovation"), value=defaults.initial_renovation_costs, step=500.0, format="%.0f")
        if inputs["initial_renovation_costs"] > 0:
            st.sidebar.caption(f"→ {fmt_currency(inputs['initial_renovation_costs'])}")
        
        inputs["furnishing_costs"] = st.sidebar.number_input(t("furnishing_costs"), value=defaults.furnishing_costs, step=100.0, format="%.0f")
        if inputs["furnishing_costs"] > 0:
            st.sidebar.caption(f"→ {fmt_currency(inputs['furnishing_costs'])}")

        # --- Calculate estimated total acquisition cost for loan % display ---
        est_notary = inputs["property_price"] * inputs["notary_fees_percentage_estimate"]
        est_total_acq = inputs["property_price"] + est_notary + inputs["initial_renovation_costs"] + inputs["furnishing_costs"]
        
        # Show acquisition cost breakdown
        if inputs["property_price"] > 0:
            st.sidebar.markdown("---")
            if get_language() == "fr":
                st.sidebar.caption(f"**Coût total estimé:** {fmt_currency(est_total_acq)}")
                st.sidebar.caption(f"  • Bien: {fmt_currency(inputs['property_price'])}")
                st.sidebar.caption(f"  • Notaire: {fmt_currency(est_notary)}")
                if inputs["initial_renovation_costs"] > 0:
                    st.sidebar.caption(f"  • Travaux: {fmt_currency(inputs['initial_renovation_costs'])}")
                if inputs["furnishing_costs"] > 0:
                    st.sidebar.caption(f"  • Mobilier: {fmt_currency(inputs['furnishing_costs'])}")
            else:
                st.sidebar.caption(f"**Estimated total cost:** {fmt_currency(est_total_acq)}")
                st.sidebar.caption(f"  • Property: {fmt_currency(inputs['property_price'])}")
                st.sidebar.caption(f"  • Notary: {fmt_currency(est_notary)}")
                if inputs["initial_renovation_costs"] > 0:
                    st.sidebar.caption(f"  • Renovation: {fmt_currency(inputs['initial_renovation_costs'])}")
                if inputs["furnishing_costs"] > 0:
                    st.sidebar.caption(f"  • Furnishing: {fmt_currency(inputs['furnishing_costs'])}")

        # --- Financing ---
        st.sidebar.subheader(t("financing"))
        
        # Loan amount as absolute value
        default_loan_amount = est_total_acq * defaults.loan_percentage
        loan_amount = st.sidebar.number_input(
            t("loan_amount_label"),
            value=default_loan_amount,
            min_value=0.0,
            max_value=est_total_acq * 1.1,  # Allow slight over-financing
            step=1000.0,
            format="%.0f",
            help=t("loan_amount_help")
        )
        
        # Calculate and display induced percentage with formatted values
        if est_total_acq > 0:
            induced_pct = (loan_amount / est_total_acq) * 100
            if get_language() == "fr":
                st.sidebar.caption(f"→ {fmt_currency(loan_amount)} = {induced_pct:.1f}% du coût total ({fmt_currency(est_total_acq)})")
            else:
                st.sidebar.caption(f"→ {fmt_currency(loan_amount)} = {induced_pct:.1f}% of total cost ({fmt_currency(est_total_acq)})")
            inputs["loan_percentage"] = loan_amount / est_total_acq
        else:
            inputs["loan_percentage"] = defaults.loan_percentage
        
        # Interest rate as 0-100% display
        inputs["loan_interest_rate"] = st.sidebar.slider(
            t("loan_interest_rate"), 
            0.0, 8.0, 
            value=defaults.loan_interest_rate * 100, 
            step=0.1, 
            format="%.1f%%",
            help=t("loan_interest_help")
        ) / 100
        
        inputs["loan_duration_years"] = st.sidebar.number_input(
            t("loan_duration"), 
            min_value=1, 
            max_value=30, 
            value=defaults.loan_duration_years, 
            step=1,
            help=t("loan_duration_help")
        )
        
        # Loan insurance as 0-100% display (but smaller range)
        inputs["loan_insurance_rate"] = st.sidebar.slider(
            t("loan_insurance_rate"), 
            0.0, 1.0, 
            value=defaults.loan_insurance_rate * 100, 
            step=0.05, 
            format="%.2f%%",
            help=t("loan_insurance_help")
        ) / 100

        # --- Rental Assumptions ---
        st.sidebar.subheader(t("rental_assumptions"))
        lease_type_choice = st.sidebar.selectbox(
            t("select_lease_type"), list(defaults.rental_assumptions.keys()),
            key="lease_type_selector"
        )
        inputs["lease_type_choice"] = lease_type_choice
        inputs["rental_assumptions"] = defaults.rental_assumptions.copy() 

        if lease_type_choice == "airbnb":
            st.sidebar.write(f"**{t('airbnb_specifics')}**")
            inputs["rental_assumptions"]["airbnb"]["daily_rate"] = st.sidebar.number_input(t("daily_rate"), value=defaults.rental_assumptions["airbnb"]["daily_rate"], step=1.0)
            if inputs["rental_assumptions"]["airbnb"]["daily_rate"] > 0:
                daily = inputs["rental_assumptions"]["airbnb"]["daily_rate"]
                st.sidebar.caption(f"→ {fmt_currency(daily)}/nuit")
            inputs["rental_assumptions"]["airbnb"]["occupancy_rate"] = st.sidebar.slider(
                t("occupancy_rate"), 
                0.0, 100.0, 
                value=defaults.rental_assumptions["airbnb"]["occupancy_rate"] * 100, 
                step=1.0,
                format="%.0f%%",
                help=t("occupancy_help")
            ) / 100
        elif lease_type_choice in ["furnished_1yr", "unfurnished_3yr"]:
            st.sidebar.write(f"**{lease_type_choice}:**")
            inputs["rental_assumptions"][lease_type_choice]["monthly_rent_sqm"] = st.sidebar.number_input(t("monthly_rent_sqm"), value=defaults.rental_assumptions[lease_type_choice]["monthly_rent_sqm"], step=0.5)
            if inputs["rental_assumptions"][lease_type_choice]["monthly_rent_sqm"] > 0 and inputs["property_size_sqm"] > 0:
                rent_sqm = inputs["rental_assumptions"][lease_type_choice]["monthly_rent_sqm"]
                total_monthly = rent_sqm * inputs["property_size_sqm"]
                total_yearly = total_monthly * 12
                st.sidebar.caption(f"→ {fmt_currency(total_monthly)}/mois = {fmt_currency(total_yearly)}/an")
            inputs["rental_assumptions"][lease_type_choice]["vacancy_rate"] = st.sidebar.slider(
                t("vacancy_rate"), 
                0.0, 50.0, 
                value=defaults.rental_assumptions[lease_type_choice]["vacancy_rate"] * 100, 
                step=1.0,
                format="%.0f%%",
                help=t("vacancy_help")
            ) / 100

        # --- Operating Expenses ---
        st.sidebar.subheader(t("operating_expenses"))
        inputs["property_tax_yearly"] = st.sidebar.number_input(t("property_tax_yearly"), value=defaults.property_tax_yearly, step=10.0, format="%.0f")
        if inputs["property_tax_yearly"] > 0:
            st.sidebar.caption(f"→ {fmt_currency(inputs['property_tax_yearly'])}/an")
        
        inputs["condo_fees_monthly"] = st.sidebar.number_input(t("condo_fees_monthly"), value=defaults.condo_fees_monthly, step=5.0, format="%.0f")
        if inputs["condo_fees_monthly"] > 0:
            yearly_condo = inputs["condo_fees_monthly"] * 12
            st.sidebar.caption(f"→ {fmt_currency(inputs['condo_fees_monthly'])}/mois = {fmt_currency(yearly_condo)}/an")
        
        inputs["maintenance_percentage_rent"] = st.sidebar.slider(
            t("maintenance_pct"), 
            0.0, 15.0, 
            value=defaults.maintenance_percentage_rent * 100, 
            step=0.5, 
            format="%.1f%%",
            help=t("maintenance_help")
        ) / 100
        
        inputs["pno_insurance_yearly"] = st.sidebar.number_input(t("pno_insurance"), value=defaults.pno_insurance_yearly, step=5.0, format="%.0f")
        if inputs["pno_insurance_yearly"] > 0:
            st.sidebar.caption(f"→ {fmt_currency(inputs['pno_insurance_yearly'])}/an")
        
        inputs["management_fees_percentage_rent"] = defaults.management_fees_percentage_rent 
        inputs["expenses_growth_rate"] = st.sidebar.slider(
            t("expenses_growth"), 
            0.0, 5.0, 
            value=defaults.expenses_growth_rate * 100, 
            step=0.1, 
            format="%.1f%%",
            help=t("expenses_growth_help")
        ) / 100

        # --- Fiscal Parameters ---     
        if lease_type_choice == "unfurnished_3yr":
            valid_regimes = ["Revenu Foncier Réel", "Micro-Foncier"]
        else:
            valid_regimes = ["LMNP Réel", "Micro-BIC"]
        
        inputs["fiscal_regime"] = st.sidebar.selectbox(t("fiscal_regime"), valid_regimes, index=0)
        inputs["personal_income_tax_bracket"] = st.sidebar.slider(
            t("income_tax_bracket"), 
            0.0, 45.0, 
            value=defaults.personal_income_tax_bracket * 100, 
            step=1.0,
            format="%.0f%%"
        ) / 100

        # --- Exit Parameters ---
        st.sidebar.subheader(t("exit_strategy"))
        inputs["holding_period_years"] = st.sidebar.number_input(
            t("holding_period"), 
            min_value=1, 
            max_value=50, 
            value=defaults.holding_period_years, 
            step=1,
            help=t("holding_period_help")
        )
        inputs["property_value_growth_rate"] = st.sidebar.slider(
            t("property_growth"), 
            0.0, 10.0, 
            value=defaults.property_value_growth_rate * 100, 
            step=0.1, 
            format="%.1f%%",
            help=t("property_growth_help")
        ) / 100
        inputs["exit_selling_fees_percentage"] = st.sidebar.slider(
            t("selling_fees"), 
            0.0, 10.0, 
            value=defaults.exit_selling_fees_percentage * 100, 
            step=0.5, 
            format="%.1f%%"
        ) / 100
        
        # --- Investment Analysis with detailed explanations ---
        st.sidebar.subheader(t("investment_analysis"))
        
        # Risk-free rate with explanation expander
        with st.sidebar.expander("ℹ️ " + t("risk_free_rate")):
            st.markdown(t("risk_free_rate_explanation"))
        inputs["risk_free_rate"] = st.sidebar.slider(
            t("risk_free_rate"), 
            0.0, 10.0, 
            value=getattr(defaults, 'risk_free_rate', 0.035) * 100, 
            step=0.1, 
            format="%.1f%%"
        ) / 100
        
        # Discount rate with explanation expander
        with st.sidebar.expander("ℹ️ " + t("discount_rate")):
            st.markdown(t("discount_rate_explanation"))
        inputs["discount_rate"] = st.sidebar.slider(
            t("discount_rate"), 
            0.0, 15.0, 
            value=getattr(defaults, 'discount_rate', 0.05) * 100, 
            step=0.5, 
            format="%.1f%%"
        ) / 100

        return inputs

    def format_financial_table(self, df: pd.DataFrame, expense_rows: list, label_map: dict) -> pd.DataFrame:
        """Common formatting for financial statements"""
        rows_to_flip = df.index.intersection(expense_rows)
        df.loc[rows_to_flip] *= -1
        df_k = df / 1000.0
        df_k.index.name = t("in_k_euros")
        df_k.index = df_k.index.map(lambda x: label_map.get(x, x))
        return df_k

    def style_financial_dataframe(self, df: pd.DataFrame):
        """Apply styling to financial dataframes with locale-aware formatting"""
        lang = get_language()
        
        def format_k_euros(val):
            if pd.isna(val): return "-"
            try:
                val_int = int(round(val, 0))
                if val_int < 0:
                    # Negative: show in brackets
                    if lang == "fr":
                        return f"({abs(val_int):,})".replace(",", " ")
                    else:
                        return f"({abs(val_int):,})"
                elif val_int == 0:
                    return "0"
                else:
                    if lang == "fr":
                        return f"{val_int:,}".replace(",", " ")
                    else:
                        return f"{val_int:,}"
            except (ValueError, TypeError): 
                return val

        def style_financial_rows(row):
            row_name_clean = row.name.strip()
            styles = [''] * len(row)
            if 'Total' in row_name_clean or 'Net' in row_name_clean or 'Résultat' in row_name_clean:
                styles = ['font-weight: bold'] * len(row)
            separator_rows = [
                t("gross_operating_income"), t("total_opex"), 
                t("noi"), t("taxable_income"), t("total_taxes"), 
                t("net_income"), t("cfo"), t("cfi"), t("cff")
            ]
            if row_name_clean in separator_rows:
                styles = [s + '; border-top: 1px solid #4b5563' for s in styles]
            if row_name_clean == t("net_income"):
                styles = ['background-color: lightgrey; font-weight: bold; color: black; border-top: 2px solid white;'] * len(row)
            return styles

        def style_index_label(label):
            label_clean = label.strip()
            style = 'text-align: left; padding-left: 5px; '
            if 'Total' in label_clean or 'Net' in label_clean or 'Résultat' in label_clean:
                style += 'font-weight: bold; '
            separator_rows = [
                t("gross_operating_income"), t("total_opex"), 
                t("noi"), t("taxable_income"), t("total_taxes"), 
                t("net_income"), t("cfo"), t("cfi"), t("cff")
            ]
            if label_clean in separator_rows:
                style += 'border-top: 1px solid #4b5563; '
            if label_clean == t("net_income"):
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

    def _fmt_k_currency(self, value: float) -> str:
        """Format value in k€ with locale awareness."""
        k_val = value / 1000
        if get_language() == "fr":
            return f"{k_val:,.1f}k €".replace(",", " ").replace(".", ",")
        else:
            return f"€{k_val:,.1f}k"
    
    def _fmt_pct(self, value: float, decimals: int = 2) -> str:
        """Format percentage with locale awareness. Value in decimal (0.05 = 5%)"""
        pct = value * 100
        if get_language() == "fr":
            return f"{pct:.{decimals}f}%".replace(".", ",")
        else:
            return f"{pct:.{decimals}f}%"

    def display_dashboard(self):
        """Dashboard page with summary metrics and charts"""
        st.header(t("investment_dashboard"))
        
        if st.session_state.model is None:
            st.info(t("run_simulation_prompt"))
            return
        
        model = st.session_state.model
        params = st.session_state.params
        pnl = model.get_pnl()
        cf = model.get_cash_flow()
        loan_schedule = model.get_loan_schedule()
        metrics = model.get_investment_metrics()
        
        # === ROW 1: KEY INVESTMENT METRICS ===
        if metrics:
            st.subheader(t("investment_metrics"))
            
            # Explanation expanders for key metrics
            col_exp1, col_exp2 = st.columns(2)
            with col_exp1:
                with st.expander("ℹ️ " + t("irr") + " - " + ("What is IRR?" if get_language() == "en" else "Qu'est-ce que le TRI ?")):
                    st.markdown(t("irr_explanation"))
            with col_exp2:
                with st.expander("ℹ️ " + t("npv") + " - " + ("What is NPV?" if get_language() == "en" else "Qu'est-ce que la VAN ?")):
                    st.markdown(t("npv_explanation"))
            
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            
            with col_m1:
                st.metric(t("irr"), self._fmt_pct(metrics.get('irr', 0)), help=t("irr_help"))
            with col_m2:
                discount_rate = getattr(params, 'discount_rate', 0.05) * 100
                st.metric(t("npv"), self._fmt_k_currency(metrics.get('npv', 0)), help=t("npv_help", rate=f"{discount_rate:.1f}"))
            with col_m3:
                st.metric(t("cash_on_cash"), self._fmt_pct(metrics.get('cash_on_cash', 0)), help=t("cash_on_cash_help"))
            with col_m4:
                em_value = metrics.get('equity_multiple', 0)
                em_display = f"{em_value:.2f}".replace(".", ",") + "x" if get_language() == "fr" else f"{em_value:.2f}x"
                st.metric(t("equity_multiple"), em_display, help=t("equity_multiple_help"))
            
            with st.expander(t("exit_scenario_details")):
                col_e1, col_e2, col_e3 = st.columns(3)
                with col_e1:
                    st.metric(t("exit_property_value"), self._fmt_k_currency(metrics.get('exit_property_value', 0)))
                    st.metric(t("capital_gain"), self._fmt_k_currency(metrics.get('capital_gain', 0)))
                with col_e2:
                    st.metric(t("selling_costs"), self._fmt_k_currency(metrics.get('selling_costs', 0)))
                    st.metric(t("capital_gains_tax"), self._fmt_k_currency(metrics.get('capital_gains_tax', 0)))
                with col_e3:
                    st.metric(t("remaining_loan"), self._fmt_k_currency(metrics.get('remaining_loan_balance', 0)))
                    st.metric(t("net_exit_proceeds"), self._fmt_k_currency(metrics.get('net_exit_proceeds', 0)))
            
            st.markdown("---")
        
        # === ROW 2: CONSOLIDATED CF + SANKEY CHARTS ===
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader(t("consolidated_cf"))
            consolidated_cf = self.visualizer.create_consolidated_cf_table(pnl, cf, params)
            if consolidated_cf is not None:
                st.dataframe(self.style_financial_dataframe(consolidated_cf), use_container_width=True, height=600)
        
        with col2:
            st.subheader(t("pnl_sankey_total"))
            pnl_sankey = self.visualizer.create_pnl_sankey_total(pnl)
            if pnl_sankey:
                st.plotly_chart(pnl_sankey, use_container_width=True)
            
            st.subheader(t("cf_sankey_total"))
            cf_sankey = self.visualizer.create_cf_sankey_total(cf)
            if cf_sankey:
                st.plotly_chart(cf_sankey, use_container_width=True)
        
        st.markdown("---")
        
        # === ROW 3: LOAN ANALYSIS ===
        if loan_schedule is not None and len(loan_schedule) > 0:
            st.subheader(t("loan_analysis"))
            col_loan1, col_loan2 = st.columns([1, 1])
            
            with col_loan1:
                st.markdown(f"**{t('amortization_yearly')}**")
                loan_table = self.visualizer.format_loan_schedule_table(loan_schedule)
                if loan_table is not None:
                    # Locale-aware formatting for loan table
                    if get_language() == "fr":
                        fmt_str = lambda x: f"{x:,.1f}".replace(",", " ").replace(".", ",") if pd.notna(x) else "-"
                    else:
                        fmt_str = "{:,.1f}"
                    st.dataframe(loan_table.style.format(fmt_str), use_container_width=True, height=400)
            
            with col_loan2:
                loan_chart = self.visualizer.create_loan_balance_chart(loan_schedule)
                if loan_chart:
                    st.plotly_chart(loan_chart, use_container_width=True)
            
            st.markdown(f"**{t('payment_sensitivity')}**")
            sensitivity_heatmap = self.visualizer.create_loan_sensitivity_heatmap(params)
            if sensitivity_heatmap:
                st.plotly_chart(sensitivity_heatmap, use_container_width=True)
        else:
            st.info(t("no_loan"))
        
        st.markdown("---")
        
        # === ROW 4: INVESTMENT RETURN SENSITIVITY ===
        if st.session_state.model is None:
            return
        st.subheader(t("irr_sensitivity"))
        
        lease_type_used = getattr(params, 'lease_type_used', 'furnished_1yr')
        setattr(params, 'current_lease_type', lease_type_used)
        
        col_sens1, col_sens2 = st.columns([1, 1])
        
        with col_sens1:
            st.markdown(f"**{t('irr_sensitivity_heatmap')}**")
            st.caption(t("sensitivity_caption"))
            with st.spinner(t("calculating_irr")):
                irr_heatmap = self.visualizer.create_irr_sensitivity_heatmap(params)
                if irr_heatmap:
                    st.plotly_chart(irr_heatmap, use_container_width=True)
                else:
                    st.warning(t("could_not_calculate_irr"))
        
        with col_sens2:
            st.markdown(f"**{t('npv_sensitivity_heatmap')}**")
            st.caption(t("sensitivity_caption"))
            with st.spinner(t("calculating_npv")):
                npv_heatmap = self.visualizer.create_npv_sensitivity_heatmap(params)
                if npv_heatmap:
                    st.plotly_chart(npv_heatmap, use_container_width=True)
                else:
                    st.warning(t("could_not_calculate_npv"))

    def display_pnl_page(self):
        """P&L statement page"""
        st.header(t("pnl_title"))
        
        if st.session_state.model is None:
            st.info(t("run_simulation_pnl"))
            return
        
        pnl = st.session_state.model.get_pnl()
        params = st.session_state.params
        
        if pnl is not None:
            pnl_yearly = pnl.groupby("Year").sum()
            pnl_pivoted = pnl_yearly.T
            pnl_pivoted.columns = [f"{t('year')} {col}" for col in pnl_pivoted.columns]
            
            expense_rows = [
                "Vacancy Loss", "Property Tax", "Condo Fees", "PNO Insurance",
                "Maintenance", "Management Fees", "Airbnb Specific Costs",
                "Total Operating Expenses", "Loan Interest", "Loan Insurance",
                "Depreciation/Amortization", "Income Tax", "Social Contributions", "Total Taxes"
            ]
            
            label_map = get_pnl_label_map()
            
            pnl_formatted = self.format_financial_table(pnl_pivoted, expense_rows, label_map)
            st.dataframe(self.style_financial_dataframe(pnl_formatted), use_container_width=True, height=700)
            
            col1, col2 = st.columns(2)
            with col1:
                cumulative_chart = self.visualizer.create_pnl_cumulative_chart(pnl)
                if cumulative_chart:
                    st.plotly_chart(cumulative_chart, use_container_width=True)
            with col2:
                sankey_y1 = self.visualizer.create_pnl_sankey(pnl)
                if sankey_y1:
                    st.subheader(t("year_1_flow"))
                    st.plotly_chart(sankey_y1, use_container_width=True)

    def display_bs_page(self):
        """Balance Sheet page"""
        st.header(t("bs_title"))
        
        if st.session_state.model is None:
            st.info(t("run_simulation_bs"))
            return
        
        bs = st.session_state.model.get_balance_sheet()
        params = st.session_state.params
        
        if bs is not None:
            key_months = [0] + [12 * y for y in range(1, params.holding_period_years + 1)]
            bs_yearly = bs.loc[key_months]
            bs_pivoted = bs_yearly.T
            bs_pivoted.columns = [t("initial")] + [f"{t('year')} {i}" for i in range(1, params.holding_period_years + 1)]
            bs_pivoted_k = bs_pivoted / 1000.0
            bs_pivoted_k.index.name = t("in_k_euros")
            st.dataframe(self.style_financial_dataframe(bs_pivoted_k), use_container_width=True, height=700)

    def display_cf_page(self):
        """Cash Flow statement page"""
        st.header(t("cf_title"))
        
        if st.session_state.model is None:
            st.info(t("run_simulation_cf"))
            return
        
        cf = st.session_state.model.get_cash_flow()
        params = st.session_state.params
        
        if cf is not None:
            cf_yearly = cf.groupby("Year").sum()
            
            for year in range(1, params.holding_period_years + 1):
                year_data = cf[cf["Year"] == year]
                cf_yearly.loc[year, "Beginning Cash Balance"] = year_data["Beginning Cash Balance"].iloc[0]
                cf_yearly.loc[year, "Ending Cash Balance"] = year_data["Ending Cash Balance"].iloc[-1]
            
            cf_pivoted = cf_yearly.T
            cf_pivoted.columns = [f"{t('year')} {col}" for col in cf_pivoted.columns]
            
            expense_rows = ["Loan Principal Repayment", "Acquisition Costs Outflow"]
            
            label_map = get_cf_label_map()
            
            cf_formatted = self.format_financial_table(cf_pivoted, expense_rows, label_map)
            st.dataframe(self.style_financial_dataframe(cf_formatted), use_container_width=True, height=700)

    def display_dvf_page(self):
        """Paris 3D price map from DVF database."""
        st.header(t("dvf_title"))
        
        import pydeck as pdk
        from ._10_dvf_analyzer_local import DVFAnalyzer
        
        @st.cache_data(ttl=3600)
        def load_paris_data():
            analyzer = DVFAnalyzer()
            return analyzer.get_paris_data(limit=30000)
        
        try:
            df = load_paris_data()
            
            if len(df) == 0:
                st.warning(t("no_paris_data"))
                return
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric(t("transactions"), fmt_number(len(df)))
            col2.metric(t("median_price_sqm"), fmt_currency(df['prix_m2'].median(), 0))
            col3.metric(t("mean_price_sqm"), fmt_currency(df['prix_m2'].mean(), 0))
            col4.metric(t("max_price_sqm"), fmt_currency(df['prix_m2'].max(), 0))
            
            import numpy as np
            df = df.copy()
            log_prices = np.log1p(df['prix_m2'])
            df['normalized'] = (log_prices - log_prices.min()) / (log_prices.max() - log_prices.min())
            
            def get_color(v):
                v = max(0, min(1, v))
                if v < 0.25: return [0, int(v*4*255), 255, 180]
                elif v < 0.5: return [0, 255, int(255-(v-0.25)*4*255), 180]
                elif v < 0.75: return [int((v-0.5)*4*255), 255, 0, 180]
                return [255, int(255-(v-0.75)*4*255), 0, 180]
            
            df['color'] = df['normalized'].apply(get_color)
            
            layer = pdk.Layer(
                "ColumnLayer",
                data=df,
                get_position=["longitude", "latitude"],
                get_elevation="prix_m2",
                elevation_scale=0.5,
                radius=30,
                get_fill_color="color",
                pickable=True,
                extruded=True,
            )
            
            view = pdk.ViewState(
                latitude=48.8566, longitude=2.3522,
                zoom=11, pitch=50, bearing=0
            )
            
            deck = pdk.Deck(
                layers=[layer],
                initial_view_state=view,
                map_style="mapbox://styles/mapbox/dark-v10",
                tooltip={"html": "<b>€{prix_m2:.0f}/m²</b><br>{adresse_complete}"}
            )
            
            st.pydeck_chart(deck, use_container_width=True)
            
        except Exception as e:
            st.error(t("dvf_error", error=str(e)))
            st.info(t("dvf_db_info"))

    def export_to_excel(self, export_type: str = "Summary"):
        """Generate and return Excel file for download."""
        if st.session_state.model is None:
            return None
        
        model = st.session_state.model
        params = st.session_state.params
        
        export_args = {
            "params": params,
            "pnl_df": model.get_pnl(),
            "bs_df": model.get_balance_sheet(),
            "cf_df": model.get_cash_flow(),
            "loan_schedule": model.get_loan_schedule(),
            "investment_metrics": model.get_investment_metrics()
        }
        
        if export_type == t("full_model"):
            exporter = ExcelExporterFull(**export_args)
        else:
            exporter = ExcelExporter(**export_args)
        
        return exporter.export()
    
    def run(self):
        """Main app orchestrator with Simple/Expert mode toggle"""
        st.title(t("app_title"))
        
        # === LANGUAGE TOGGLE (very top) ===
        col_lang, col_space = st.sidebar.columns([1, 1])
        with col_lang:
            if st.button("🌐 FR/EN", key="lang_toggle_main", width=120):
                toggle_language()
                st.rerun()
        
        # === MODE TOGGLE ===
        if 'app_mode' not in st.session_state:
            st.session_state.app_mode = "simple"
        
        mode_label = "🎯 Simple" if get_language() == "fr" else "🎯 Simple"
        expert_label = "⚙️ Expert" if get_language() == "fr" else "⚙️ Expert"
        
        col_mode1, col_mode2 = st.sidebar.columns(2)
        with col_mode1:
            if st.button(mode_label, use_container_width=True, 
                        type="primary" if st.session_state.app_mode == "simple" else "secondary"):
                st.session_state.app_mode = "simple"
                st.rerun()
        with col_mode2:
            if st.button(expert_label, use_container_width=True,
                        type="primary" if st.session_state.app_mode == "expert" else "secondary"):
                st.session_state.app_mode = "expert"
                st.rerun()
        
        st.sidebar.markdown("---")
        
        # === SIMPLE MODE ===
        if st.session_state.app_mode == "simple":
            from ._16_simple_viewer import SimpleViewer
            simple_viewer = SimpleViewer()
            simple_viewer.display()
            return
        
        # === EXPERT MODE (existing code) ===
        # Sidebar inputs
        default_params = ModelParameters()
        user_widget_values = self.display_sidebar_inputs(default_params)
        selected_lease = user_widget_values.pop("lease_type_choice", "furnished_1yr")
        
        try:
            current_params = ModelParameters(**user_widget_values)
        except TypeError as e:
            st.error(t("error_creating_params", error=str(e)))
            st.stop()
        
        # Run simulation button
        if st.sidebar.button(t("run_simulation"), type="primary"):
            with st.spinner("..."):
                model = FinancialModel(current_params)
                try:
                    model.run_simulation(lease_type=selected_lease)
                    st.session_state.model = model
                    st.session_state.params = current_params
                    st.sidebar.success(t("simulation_complete"))
                except Exception as e:
                    st.error(t("simulation_error", error=str(e)))
                    st.exception(e)
        
        # Excel Export Section (only show after simulation)
        if st.session_state.model is not None:
            st.sidebar.markdown("---")
            st.sidebar.subheader(t("export"))
            
            export_type = st.sidebar.radio(t("export_type"), [t("summary"), t("full_model")], 
                                           help=t("export_summary_help"))
            
            excel_data = self.export_to_excel(export_type)
            if excel_data:
                filename = "financial_model_full.xlsx" if export_type == t("full_model") else "financial_model.xlsx"
                st.sidebar.download_button(
                    label=t("download_excel"),
                    data=excel_data,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        
        # Navigation
        st.sidebar.markdown("---")
        nav_options = [t("dashboard"), t("pnl_statement"), t("balance_sheet"), t("cash_flow"), t("dvf")]
        page = st.sidebar.radio(t("navigate"), nav_options)
        
        # Display selected page
        if page == t("dashboard"):
            self.display_dashboard()
        elif page == t("pnl_statement"):
            self.display_pnl_page()
        elif page == t("balance_sheet"):
            self.display_bs_page()
        elif page == t("cash_flow"):
            self.display_cf_page()
        elif page == t("dvf"):
            self.display_dvf_page()
