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
from ._19_address_widget import address_autocomplete, address_input_simple, create_dvf_map
from ._17_dvf_comparison import DVFComparison

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
        
        from ._19_address_widget import _fetch_suggestions, _geocode_address

        # Language toggle at top of sidebar
        st.sidebar.header(t("simulation_params"))
        
        inputs: Dict[str, Any] = {} 

        # --- Property & Acquisition ---
        st.sidebar.subheader(t("property_acquisition"))

        # ADDRESS AUTOCOMPLETE
        address_key = "property_address"
        if f"{address_key}_selected" not in st.session_state:
            st.session_state[f"{address_key}_selected"] = None
        
        address_input = st.sidebar.text_input(
            "📍 " + ("Adresse du bien" if get_language() == "fr" else "Property Address"),
            key=address_key,
            placeholder="Ex: 15 rue de la Paix, 75002 Paris",
            help="Entrez l'adresse complète pour une comparaison marché précise" if get_language() == "fr" else "Enter full address for precise market comparison"
        )
        
        # Show suggestions
        if address_input and len(address_input) >= 5 and not st.session_state[f"{address_key}_selected"]:
            suggestions = _fetch_suggestions(address_input)
            if suggestions:
                st.sidebar.caption("Suggestions:")
                for i, sug in enumerate(suggestions[:4]):
                    if st.sidebar.button(f"📍 {sug['label']}", key=f"sug_{i}", use_container_width=True):
                        st.session_state[f"{address_key}_selected"] = sug
                        st.rerun()
        
        # Display selected address
        selected_address = st.session_state[f"{address_key}_selected"]
        if selected_address:
            st.sidebar.success(f"✅ {selected_address['label']}")
            inputs["property_address"] = selected_address['label']
            inputs["property_lat"] = selected_address['lat']
            inputs["property_lon"] = selected_address['lon']
            inputs["property_address_city"] = selected_address['city']
            
            col1, col2 = st.sidebar.columns([3, 1])
            with col2:
                if st.button("🔄", key="clear_addr", help="Changer"):
                    st.session_state[f"{address_key}_selected"] = None
                    st.rerun()
        else:
            # Fallback to city dropdown
            inputs["property_address_city"] = st.sidebar.selectbox(
                t("city"),
                ["Paris", "Lyon", "Marseille", "Bordeaux", "Nantes", "Toulouse", "Nice", "Lille", "Strasbourg"],
                index=0
            )
            inputs["property_lat"] = None
            inputs["property_lon"] = None
            inputs["property_address"] = None

        
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
        """Dashboard page with summary metrics and charts - streamlined version"""
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
            
            # Explanation expanders
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
            
            # Exit scenario expander (kept)
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
        
        # === ROW 2: CASH FLOW VISUALIZATION ===
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Monthly cash curve with breakeven
            st.subheader("📈 " + ("Évolution Trésorerie" if get_language() == "fr" else "Cash Position"))
            
            # Breakeven metric
            breakeven = self.visualizer.calculate_breakeven_month(cf)
            if breakeven:
                years = breakeven // 12
                months = breakeven % 12
                if get_language() == "fr":
                    be_text = f"Seuil de rentabilité: Mois {breakeven} ({years}a {months}m)"
                else:
                    be_text = f"Breakeven: Month {breakeven} ({years}y {months}m)"
                st.success(f"✅ {be_text}")
            else:
                if cf is not None and cf['Ending Cash Balance'].iloc[-1] < 0:
                    st.warning("⚠️ " + ("Pas de breakeven sur la période" if get_language() == "fr" else "No breakeven within period"))
                else:
                    st.success("✅ " + ("Positif dès le départ" if get_language() == "fr" else "Positive from start"))
            
            cash_curve = self.visualizer.create_monthly_cash_curve(cf)
            if cash_curve:
                st.plotly_chart(cash_curve, use_container_width=True)
        
        with col2:
            # Waterfall chart (replaces Sankey)
            st.subheader("💧 " + ("Cascade Revenus → Cash (hors exit)" if get_language() == "fr" else "Revenue to Cash Waterfall (excl. exit)"))
            waterfall = self.visualizer.create_revenue_to_cash_waterfall(pnl, cf)
            if waterfall:
                st.plotly_chart(waterfall, use_container_width=True)
        
        st.markdown("---")
        
        # === ROW 3: DVF MARKET COMPARISON ===
        if params.property_price > 0 and params.property_size_sqm > 0:
            self.display_dvf_map_comparison(params, params.property_price, params.property_size_sqm)
            st.markdown("---")

        # === ROW 4: LOAN ANALYSIS (kept) ===
        if loan_schedule is not None and len(loan_schedule) > 0:
            st.subheader(t("loan_analysis"))
            col_loan1, col_loan2 = st.columns([1, 1])
            
            with col_loan1:
                st.markdown(f"**{t('amortization_yearly')}**")
                loan_table = self.visualizer.format_loan_schedule_table(loan_schedule)
                if loan_table is not None:
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
        
        # === ROW 5: INVESTMENT RETURN SENSITIVITY (kept) ===
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
        """P&L statement page with table and waterfall chart"""
        st.header(t("pnl_title"))
        
        if st.session_state.model is None:
            st.info(t("run_simulation_pnl"))
            return
        
        pnl = st.session_state.model.get_pnl()
        cf = st.session_state.model.get_cash_flow()
        params = st.session_state.params
        metrics = st.session_state.model.get_investment_metrics()
        
        if pnl is None:
            return
        
        # === TABLE ===
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
        st.dataframe(self.style_financial_dataframe(pnl_formatted), use_container_width=True, height=600)
        
        st.markdown("---")
        
        # === WATERFALL: Investment Journey ===
        st.subheader("📊 " + ("Parcours de l'Investissement" if get_language() == "fr" else "Investment Journey"))
        
        # Calculate breakeven
        breakeven_month = self.visualizer.calculate_breakeven_month(cf)
        holding_months = params.holding_period_years * 12
        
        # Build waterfall data
        initial_equity = getattr(params, 'initial_equity', 0)
        
        if breakeven_month and breakeven_month < holding_months:
            # Has breakeven: Purchase → Breakeven → Exit
            cf_to_breakeven = cf.loc[1:breakeven_month, 'Net Change in Cash'].sum()
            cf_breakeven_to_exit = cf.loc[breakeven_month+1:holding_months, 'Net Change in Cash'].sum()
            exit_proceeds = metrics.get('net_exit_proceeds', 0) if metrics else 0
            
            labels = [
                "Apport initial" if get_language() == "fr" else "Initial Equity",
                f"Cash-flows M1-M{breakeven_month}",
                "Seuil rentabilité" if get_language() == "fr" else "Breakeven",
                f"Cash-flows M{breakeven_month+1}-M{holding_months}",
                "Produit de sortie" if get_language() == "fr" else "Exit Proceeds",
                "Valeur finale" if get_language() == "fr" else "Final Value"
            ]
            values = [
                -initial_equity,
                cf_to_breakeven,
                0,  # Breakeven marker (relative measure will show cumulative)
                cf_breakeven_to_exit,
                exit_proceeds,
                0  # Total
            ]
            measures = ["absolute", "relative", "total", "relative", "relative", "total"]
            
        else:
            # No breakeven: Purchase → Exit
            total_cf = cf['Net Change in Cash'].sum()
            exit_proceeds = metrics.get('net_exit_proceeds', 0) if metrics else 0
            
            labels = [
                "Apport initial" if get_language() == "fr" else "Initial Equity",
                "Cash-flows opérationnels" if get_language() == "fr" else "Operating Cash Flows",
                "Produit de sortie" if get_language() == "fr" else "Exit Proceeds",
                "Valeur finale" if get_language() == "fr" else "Final Value"
            ]
            values = [-initial_equity, total_cf, exit_proceeds, 0]
            measures = ["absolute", "relative", "relative", "total"]
        
        # Create waterfall
        import plotly.graph_objects as go
        
        fig = go.Figure(go.Waterfall(
            orientation="v",
            measure=measures,
            x=labels,
            y=values,
            connector={"line": {"color": "rgba(255,255,255,0.3)"}},
            decreasing={"marker": {"color": "#ef4444"}},
            increasing={"marker": {"color": "#22c55e"}},
            totals={"marker": {"color": "#3b82f6"}},
            textposition="outside",
            text=[self._fmt_k_currency(abs(v)) if v != 0 else "" for v in values],
            textfont={"size": 11}
        ))
        
        fig.update_layout(
            template="plotly_dark",
            height=400,
            margin=dict(l=40, r=40, t=40, b=60),
            yaxis_title="€",
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Summary metrics
        final_value = -initial_equity + cf['Net Change in Cash'].sum() + (metrics.get('net_exit_proceeds', 0) if metrics else 0)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Apport initial" if get_language() == "fr" else "Initial Equity", self._fmt_k_currency(initial_equity))
        with col2:
            if breakeven_month:
                years = breakeven_month // 12
                months = breakeven_month % 12
                be_text = f"{years}a {months}m" if get_language() == "fr" else f"{years}y {months}m"
                st.metric("Seuil rentabilité" if get_language() == "fr" else "Breakeven", be_text)
            else:
                st.metric("Seuil rentabilité" if get_language() == "fr" else "Breakeven", "N/A")
        with col3:
            st.metric("Valeur finale" if get_language() == "fr" else "Final Value", self._fmt_k_currency(final_value))
        
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
        """Cash Flow statement page with cleaner table and charts"""
        st.header(t("cf_title"))
        
        if st.session_state.model is None:
            st.info(t("run_simulation_cf"))
            return
        
        cf = st.session_state.model.get_cash_flow()
        params = st.session_state.params
        
        if cf is None:
            return
        
        # === CLEAN TABLE (remove zero columns) ===
        cf_yearly = cf.groupby("Year").sum()
        
        # Get beginning/ending cash per year
        for year in range(1, params.holding_period_years + 1):
            year_data = cf[cf["Year"] == year]
            cf_yearly.loc[year, "Beginning Cash Balance"] = year_data["Beginning Cash Balance"].iloc[0]
            cf_yearly.loc[year, "Ending Cash Balance"] = year_data["Ending Cash Balance"].iloc[-1]
        
        cf_pivoted = cf_yearly.T
        cf_pivoted.columns = [f"{t('year')} {col}" for col in cf_pivoted.columns]
        
        # Remove rows that are all zeros (except first year for one-time items)
        rows_to_keep = []
        for idx, row in cf_pivoted.iterrows():
            if row.abs().sum() > 0.01:  # Keep if any non-zero value
                rows_to_keep.append(idx)
        cf_pivoted = cf_pivoted.loc[rows_to_keep]
        
        expense_rows = ["Loan Principal Repayment", "Acquisition Costs Outflow"]
        label_map = get_cf_label_map()
        
        cf_formatted = self.format_financial_table(cf_pivoted, expense_rows, label_map)
        st.dataframe(self.style_financial_dataframe(cf_formatted), use_container_width=True, height=500)
        
        st.markdown("---")
        
        # === MONTHLY CASH CURVE ===
        st.subheader("📈 " + ("Évolution Trésorerie Mensuelle" if get_language() == "fr" else "Monthly Cash Position"))
        
        cash_curve = self.visualizer.create_monthly_cash_curve(cf)
        if cash_curve:
            st.plotly_chart(cash_curve, use_container_width=True)
        
        st.markdown("---")
        
        # === MONTHLY CASH FLOW BARS (Purchase → Breakeven → Exit) ===
        st.subheader("📊 " + ("Cash-flows Mensuels" if get_language() == "fr" else "Monthly Cash Flows"))
        
        breakeven_month = self.visualizer.calculate_breakeven_month(cf)
        holding_months = params.holding_period_years * 12
        
        import plotly.graph_objects as go
        
        months = list(range(1, holding_months + 1))
        monthly_cf = cf['Net Change in Cash'].values
        
        # Color bars based on phase
        if breakeven_month and breakeven_month < holding_months:
            colors = []
            for m in months:
                if m <= breakeven_month:
                    colors.append("#f59e0b")  # Orange: pre-breakeven
                else:
                    colors.append("#22c55e")  # Green: post-breakeven
            
            phase1_label = f"Pré-seuil (M1-M{breakeven_month})" if get_language() == "fr" else f"Pre-breakeven (M1-M{breakeven_month})"
            phase2_label = f"Post-seuil (M{breakeven_month+1}-M{holding_months})" if get_language() == "fr" else f"Post-breakeven (M{breakeven_month+1}-M{holding_months})"
        else:
            colors = ["#3b82f6" if v >= 0 else "#ef4444" for v in monthly_cf]
            phase1_label = None
            phase2_label = None
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=months,
            y=monthly_cf,
            marker_color=colors,
            name="Cash-flow mensuel" if get_language() == "fr" else "Monthly Cash Flow"
        ))
        
        # Add breakeven line if exists
        if breakeven_month and breakeven_month < holding_months:
            fig.add_vline(x=breakeven_month, line_dash="dash", line_color="#22c55e", line_width=2)
            fig.add_annotation(
                x=breakeven_month, y=max(monthly_cf) * 0.9,
                text="Breakeven",
                showarrow=False,
                font=dict(color="#22c55e", size=12)
            )
        
        fig.update_layout(
            template="plotly_dark",
            height=350,
            margin=dict(l=40, r=20, t=40, b=40),
            xaxis_title="Mois" if get_language() == "fr" else "Month",
            yaxis_title="€",
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Phase summary metrics
        if breakeven_month and breakeven_month < holding_months:
            col1, col2, col3 = st.columns(3)
            
            cf_phase1 = cf.loc[1:breakeven_month, 'Net Change in Cash'].sum()
            cf_phase2 = cf.loc[breakeven_month+1:holding_months, 'Net Change in Cash'].sum()
            avg_monthly_phase1 = cf_phase1 / breakeven_month
            avg_monthly_phase2 = cf_phase2 / (holding_months - breakeven_month) if holding_months > breakeven_month else 0
            
            with col1:
                st.metric(
                    phase1_label,
                    self._fmt_k_currency(cf_phase1),
                    delta=f"Ø {fmt_currency(avg_monthly_phase1, 0)}/mois" if get_language() == "fr" else f"Avg {fmt_currency(avg_monthly_phase1, 0)}/mo"
                )
            with col2:
                st.metric(
                    phase2_label,
                    self._fmt_k_currency(cf_phase2),
                    delta=f"Ø {fmt_currency(avg_monthly_phase2, 0)}/mois" if get_language() == "fr" else f"Avg {fmt_currency(avg_monthly_phase2, 0)}/mo"
                )
            with col3:
                total_cf = cf['Net Change in Cash'].sum()
                st.metric(
                    "Total cash-flows" if get_language() == "fr" else "Total Cash Flows",
                    self._fmt_k_currency(total_cf)
                )
        else:
            col1, col2 = st.columns(2)
            total_cf = cf['Net Change in Cash'].sum()
            avg_monthly = total_cf / holding_months
            
            with col1:
                st.metric(
                    "Total cash-flows" if get_language() == "fr" else "Total Cash Flows",
                    self._fmt_k_currency(total_cf)
                )
            with col2:
                st.metric(
                    "Moyenne mensuelle" if get_language() == "fr" else "Monthly Average",
                    fmt_currency(avg_monthly, 0)
                )

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
    
    # === ADD NEW METHOD FOR DVF MAP ON DASHBOARD ===
    def display_dvf_map_comparison(self, params, price: float, surface: float):
        """Display DVF map comparison for expert mode."""
        from ._17_dvf_comparison import DVFComparison, get_market_assessment_text, get_dvf_disclaimer
        from ._19_address_widget import create_dvf_map
        
        lang = get_language()
        
        lat = getattr(params, 'property_lat', None)
        lon = getattr(params, 'property_lon', None)
        city = params.property_address_city
        
        st.subheader("🗺️ " + ("Comparaison Marché Local" if lang == "fr" else "Local Market Comparison"))
        
        # Radius slider (only show if we have coordinates)
        if lat and lon:
            radius_km = st.slider(
                "🎯 " + ("Rayon de recherche" if lang == "fr" else "Search radius"),
                min_value=0.2,
                max_value=10.0,
                value=0.5,
                step=0.1,
                format="%.1f km"
            )
            
            dvf = DVFComparison()
            comparison = dvf.get_market_comparison_geo(lat, lon, price, surface, radius_km)
            
            if comparison and comparison.get("transactions"):
                # Stats row
                col1, col2, col3, col4 = st.columns(4)
                
                assessment_text, assessment_color = get_market_assessment_text(comparison["assessment"], lang)
                
                with col1:
                    st.metric("Votre prix/m²" if lang == "fr" else "Your €/m²", 
                            f"€{comparison['user_price_sqm']:,.0f}")
                with col2:
                    diff = comparison['diff_vs_median_pct']
                    st.metric("Médiane zone" if lang == "fr" else "Area median",
                            f"€{comparison['median_price_sqm']:,.0f}",
                            delta=f"{diff:+.1f}%",
                            delta_color="inverse" if diff > 0 else "normal")
                with col3:
                    st.metric("Transactions", comparison['transaction_count'])
                with col4:
                    st.markdown(
                        f'<div style="background:{assessment_color}; padding:8px; border-radius:4px; text-align:center;">'
                        f'<b style="color:white;">{assessment_text}</b></div>',
                        unsafe_allow_html=True
                    )
                
                # Map
                deck = create_dvf_map(
                    lat, lon,
                    comparison["transactions"],
                    comparison["user_price_sqm"],
                    radius_km
                )
                st.pydeck_chart(deck, use_container_width=True)
                
                st.caption(f"🔵 Similaire | 🟢 Moins cher | 🔴 Plus cher • Rayon: {radius_km*1000:.0f}m • " + get_dvf_disclaimer(lang))
            else:
                st.info("📊 " + ("Pas assez de données dans cette zone. Essayez un rayon plus large." if lang == "fr" else "Not enough data in this area. Try a larger radius."))
        else:
            # City-level fallback (no slider needed)
            dvf = DVFComparison()
            comparison = dvf.get_market_comparison_simple(city, price, surface)
            if comparison:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Votre prix/m²" if lang == "fr" else "Your €/m²",
                            f"€{comparison['user_price_sqm']:,.0f}")
                with col2:
                    st.metric("Médiane " + city,
                            f"€{comparison['median_price_sqm']:,.0f}",
                            delta=f"{comparison['diff_vs_median_pct']:+.1f}%",
                            delta_color="inverse" if comparison['diff_vs_median_pct'] > 0 else "normal")
                
                st.info("💡 " + ("Entrez une adresse précise pour voir la carte des transactions" if lang == "fr" else "Enter a precise address to see the transactions map"))
            else:
                st.info("📊 " + ("Données de marché non disponibles" if lang == "fr" else "Market data not available"))

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
        
        property_lat = user_widget_values.pop("property_lat", None)
        property_lon = user_widget_values.pop("property_lon", None)
        property_address = user_widget_values.pop("property_address", None)

        try:
            current_params = ModelParameters(**user_widget_values)
            # Store geo data on params for DVF comparison (optional)
            current_params.property_lat = property_lat
            current_params.property_lon = property_lon
            current_params.property_address = property_address
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
        nav_options = [t("dashboard"), t("pnl_statement"), t("balance_sheet"), t("cash_flow")]
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
