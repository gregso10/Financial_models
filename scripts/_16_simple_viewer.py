# scripts/_16_simple_viewer.py
"""
Simplified investment simulator for retail investors.
5-7 inputs → visual dashboard with key metrics.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, Tuple

from ._1_model_params import ModelParameters
from ._0_financial_model import FinancialModel
from ._14_translations import t, get_language, fmt_currency, fmt_number
from ._15_city_defaults import get_location_defaults, get_selectable_locations, FIXED_DEFAULTS
from ._17_dvf_comparison import DVFComparison, generate_profitability_alerts, get_market_assessment_text
from ._18_fiscal_advisor import FiscalAdvisor, LeaseType, get_regime_recommendation_text, get_lmp_alert


class SimpleViewer:
    """Simplified interface for quick investment analysis."""
    
    def __init__(self):
        if 'simple_results' not in st.session_state:
            st.session_state.simple_results = None
    
    def get_score_color(self, irr: float, risk_free: float, discount: float) -> Tuple[str, str, str]:
        """
        Returns (color, emoji, label) based on IRR vs thresholds.
        🟢 IRR > discount_rate : Good investment
        🟡 risk_free < IRR ≤ discount : Acceptable
        🔴 IRR ≤ risk_free : Poor
        """
        if irr > discount:
            if get_language() == "fr":
                return "#22c55e", "🟢", "Bon investissement"
            return "#22c55e", "🟢", "Good investment"
        elif irr > risk_free:
            if get_language() == "fr":
                return "#eab308", "🟡", "Acceptable"
            return "#eab308", "🟡", "Acceptable"
        else:
            if get_language() == "fr":
                return "#ef4444", "🔴", "Peu rentable"
            return "#ef4444", "🔴", "Poor return"
    
    def create_cashflow_chart(self, cf_df: pd.DataFrame) -> go.Figure:
        """Simple annual cash flow bar chart."""
        cf_yearly = cf_df.groupby("Year")["Net Change in Cash"].sum()
        
        colors = ["#22c55e" if v >= 0 else "#ef4444" for v in cf_yearly.values]
        
        fig = go.Figure(data=[
            go.Bar(
                x=[f"Y{y}" for y in cf_yearly.index],
                y=cf_yearly.values,
                marker_color=colors,
                text=[fmt_currency(v, 0) for v in cf_yearly.values],
                textposition='outside',
                textfont=dict(size=10)
            )
        ])
        
        title = "Cash-flow annuel" if get_language() == "fr" else "Annual Cash Flow"
        
        fig.update_layout(
            title=title,
            template="plotly_dark",
            height=250,
            margin=dict(l=20, r=20, t=40, b=20),
            yaxis_title="€",
            showlegend=False
        )
        
        return fig
    
    def create_score_gauge(self, irr: float, risk_free: float, discount: float) -> go.Figure:
        """Visual gauge showing investment quality."""
        color, emoji, label = self.get_score_color(irr, risk_free, discount)
        
        # Gauge from 0% to 15%
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=irr * 100,
            number={'suffix': '%', 'font': {'size': 40}},
            title={'text': label, 'font': {'size': 16}},
            gauge={
                'axis': {'range': [0, 15], 'ticksuffix': '%'},
                'bar': {'color': color},
                'steps': [
                    {'range': [0, risk_free * 100], 'color': '#fee2e2'},
                    {'range': [risk_free * 100, discount * 100], 'color': '#fef3c7'},
                    {'range': [discount * 100, 15], 'color': '#dcfce7'},
                ],
                'threshold': {
                    'line': {'color': 'white', 'width': 2},
                    'thickness': 0.8,
                    'value': irr * 100
                }
            }
        ))
        
        fig.update_layout(
            height=200,
            margin=dict(l=20, r=20, t=30, b=10),
            template="plotly_dark"
        )
        
        return fig
    
    def display_dvf_comparison(self, city: str, price: float, surface: float):
        """Display DVF market comparison widget."""
        lang = get_language()
        
        dvf = DVFComparison()
        comparison = dvf.get_market_comparison(city, price, surface)
        
        if comparison is None:
            # No data available - show placeholder
            st.info("📊 " + ("Données de marché non disponibles pour cette zone" if lang == "fr" else "Market data not available for this area"))
            return
        
        # Header
        st.markdown("### 📊 " + ("Comparaison Marché" if lang == "fr" else "Market Comparison"))
        
        # Assessment badge
        assessment_text, assessment_color = get_market_assessment_text(comparison["assessment"], lang)
        
        user_price_sqm = comparison["user_price_sqm"]
        median_price_sqm = comparison["median_price_sqm"]
        diff_pct = comparison["diff_vs_median_pct"]
        
        # Main comparison
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                "Votre prix/m²" if lang == "fr" else "Your price/sqm",
                fmt_currency(user_price_sqm, 0),
            )
        
        with col2:
            diff_str = f"+{diff_pct:.1f}%" if diff_pct > 0 else f"{diff_pct:.1f}%"
            st.metric(
                "Médiane quartier" if lang == "fr" else "Area median",
                fmt_currency(median_price_sqm, 0),
                delta=diff_str,
                delta_color="inverse" if diff_pct > 0 else "normal"
            )
        
        # Assessment banner
        st.markdown(
            f'<div style="background-color:{assessment_color}20; border-left:4px solid {assessment_color}; '
            f'padding:10px; border-radius:4px; margin:10px 0;">'
            f'<span style="color:{assessment_color}; font-weight:bold;">{assessment_text}</span>'
            f'</div>',
            unsafe_allow_html=True
        )
        
        # Stats details
        with st.expander("📈 " + ("Détails du marché" if lang == "fr" else "Market details")):
            st.write(f"• " + ("Transactions similaires" if lang == "fr" else "Similar transactions") + f": {comparison['transaction_count']}")
            if comparison["radius_km"]:
                st.write(f"• " + ("Rayon" if lang == "fr" else "Radius") + f": {comparison['radius_km']} km")
            st.write(f"• " + ("Fourchette" if lang == "fr" else "Range") + f": {fmt_currency(comparison['min_price_sqm'], 0)} - {fmt_currency(comparison['max_price_sqm'], 0)}/m²")
            st.write(f"• Q25-Q75: {fmt_currency(comparison['q25_price_sqm'], 0)} - {fmt_currency(comparison['q75_price_sqm'], 0)}/m²")
            st.write(f"• " + ("Votre percentile" if lang == "fr" else "Your percentile") + f": {comparison['user_percentile']:.0f}%")
            years_str = ", ".join(map(str, comparison["years_covered"][-3:]))
            st.caption(f"📅 " + ("Années" if lang == "fr" else "Years") + f": {years_str}")
    
    def display_profitability_alerts(self, metrics: dict, params):
        """Display profitability alerts."""
        lang = get_language()
        
        cf_df = st.session_state.simple_results["model"].get_cash_flow()
        monthly_cf = cf_df["Net Change in Cash"].sum() / (params.holding_period_years * 12)
        
        alerts = generate_profitability_alerts(
            irr=metrics.get('irr', 0),
            monthly_cashflow=monthly_cf,
            cash_on_cash=metrics.get('cash_on_cash', 0),
            equity_multiple=metrics.get('equity_multiple', 0),
            risk_free_rate=FIXED_DEFAULTS["risk_free_rate"],
            lang=lang
        )
        
        if not alerts:
            return
        
        st.markdown("### " + ("🚦 Alertes" if lang == "fr" else "🚦 Alerts"))
        
        for alert in alerts:
            icon = alert["icon"]
            msg = alert["message"]
            alert_type = alert["type"]
            
            if alert_type == "success":
                bg_color = "#22c55e20"
                border_color = "#22c55e"
            elif alert_type == "warning":
                bg_color = "#eab30820"
                border_color = "#eab308"
            else:
                bg_color = "#ef444420"
                border_color = "#ef4444"
            
            st.markdown(
                f'<div style="background-color:{bg_color}; border-left:4px solid {border_color}; '
                f'padding:8px 12px; border-radius:4px; margin:4px 0;">'
                f'{icon} {msg}</div>',
                unsafe_allow_html=True
            )
    
    def display_fiscal_comparison(self, params, model):
        """Display fiscal regime comparison widget."""
        lang = get_language()
        
        st.markdown("### 📋 " + ("Optimisation Fiscale" if lang == "fr" else "Tax Optimization"))
        
        # Get annual figures from model
        pnl_df = model.get_pnl()
        pnl_year1 = pnl_df[pnl_df["Year"] == 1]
        
        gross_revenue = pnl_year1["Gross Operating Income"].sum()
        
        # Deductible expenses (excluding depreciation)
        deductible = (
            pnl_year1["Property Tax"].sum() +
            pnl_year1["Condo Fees"].sum() +
            pnl_year1["PNO Insurance"].sum() +
            pnl_year1["Maintenance"].sum() +
            pnl_year1["Management Fees"].sum() +
            pnl_year1["Loan Interest"].sum() +
            pnl_year1["Loan Insurance"].sum()
        )
        deductible = abs(deductible)  # Make positive
        
        depreciation = abs(pnl_year1["Depreciation/Amortization"].sum())
        
        # Create advisor
        advisor = FiscalAdvisor(tmi=params.personal_income_tax_bracket)
        
        # Compare regimes (assuming furnished)
        comparison = advisor.compare_regimes(
            gross_revenue=gross_revenue,
            deductible_expenses=deductible,
            depreciation=depreciation,
            lease_type=LeaseType.FURNISHED,
            holding_years=params.holding_period_years
        )
        
        # Get recommendation text
        rec = get_regime_recommendation_text(comparison, lang)
        
        # Recommendation banner
        is_reel = "Réel" in rec["recommended"] or "Reel" in rec["recommended"]
        rec_color = "#22c55e" if is_reel else "#3b82f6"
        
        st.markdown(
            f'<div style="background-color:{rec_color}20; border:2px solid {rec_color}; '
            f'padding:12px; border-radius:8px; text-align:center;">'
            f'<span style="font-size:1.2em; font-weight:bold;">✨ {rec["recommended"]}</span><br/>'
            f'<span style="color:#888;">{rec["reason"]}</span>'
            f'</div>',
            unsafe_allow_html=True
        )
        
        st.markdown("")
        
        # Comparison table
        col1, col2 = st.columns(2)
        
        with col1:
            micro = comparison.micro
            st.markdown(f"**{micro.regime}**")
            st.write(f"• " + ("Revenu imposable" if lang == "fr" else "Taxable income") + f": {fmt_currency(micro.taxable_income, 0)}")
            st.write(f"• " + ("Impôt total" if lang == "fr" else "Total tax") + f": {fmt_currency(micro.total_tax, 0)}")
            st.write(f"• " + ("Taux effectif" if lang == "fr" else "Effective rate") + f": {micro.effective_rate:.1f}%")
        
        with col2:
            reel = comparison.reel
            st.markdown(f"**{reel.regime}**")
            st.write(f"• " + ("Revenu imposable" if lang == "fr" else "Taxable income") + f": {fmt_currency(reel.taxable_income, 0)}")
            st.write(f"• " + ("Impôt total" if lang == "fr" else "Total tax") + f": {fmt_currency(reel.total_tax, 0)}")
            st.write(f"• " + ("Taux effectif" if lang == "fr" else "Effective rate") + f": {reel.effective_rate:.1f}%")
        
        # Savings highlight
        if rec["annual_savings"] > 100:
            savings_text = (
                f"💰 Économie: {fmt_currency(rec['annual_savings'], 0)}/an "
                f"({fmt_currency(rec['total_savings'], 0)} sur {params.holding_period_years} ans)"
                if lang == "fr" else
                f"💰 Savings: {fmt_currency(rec['annual_savings'], 0)}/year "
                f"({fmt_currency(rec['total_savings'], 0)} over {params.holding_period_years} years)"
            )
            st.success(savings_text)
        
        # LMP warning if applicable
        lmp_status = advisor.check_lmp_status(gross_revenue)
        lmp_alert = get_lmp_alert(lmp_status, lang)
        
        if lmp_alert:
            if lmp_alert["type"] == "warning":
                st.warning(f"{lmp_alert['icon']} **{lmp_alert['title']}**: {lmp_alert['message']}")
            else:
                st.info(f"{lmp_alert['icon']} **{lmp_alert['title']}**: {lmp_alert['message']}")
        
        # Pro teaser
        with st.expander("🔒 " + ("Fonctionnalités Pro" if lang == "fr" else "Pro Features")):
            st.markdown(
                ("**Passez en Pro pour accéder à:**\n"
                 "- Simulation déficit foncier\n"
                 "- Comparaison Meublé vs Nu vs Airbnb\n"
                 "- Optimisation SCI / Nom propre\n"
                 "- Export fiscal détaillé")
                if lang == "fr" else
                ("**Upgrade to Pro for:**\n"
                 "- Deficit foncier simulation\n"
                 "- Furnished vs Unfurnished vs Airbnb comparison\n"
                 "- SCI vs Individual optimization\n"
                 "- Detailed tax export")
            )
            st.button("⭐ " + ("Passer Pro" if lang == "fr" else "Go Pro"), disabled=True, help="Coming soon")
    
    def build_params_from_simple_inputs(self, inputs: Dict) -> ModelParameters:
        """Convert simple inputs to full ModelParameters using defaults."""
        location = inputs["location"]
        loc_defaults = get_location_defaults(location)
        
        # Calculate derived values
        sqm = inputs["surface_sqm"]
        
        params = ModelParameters(
            property_address_city=location,
            property_price=inputs["price"],
            property_size_sqm=sqm,
            
            # From location defaults
            agency_fees_percentage=0.0,  # Assume price is net
            notary_fees_percentage_estimate=loc_defaults["notary_pct"],
            
            # Financing
            loan_percentage=(inputs["price"] - inputs["apport"]) / inputs["price"] if inputs["price"] > 0 else 0.8,
            loan_interest_rate=inputs["loan_rate"],
            loan_duration_years=FIXED_DEFAULTS["loan_duration_years"],
            loan_insurance_rate=FIXED_DEFAULTS["loan_insurance_rate"],
            
            # Rental - use furnished defaults
            rental_assumptions={
                "furnished_1yr": {
                    "monthly_rent_sqm": inputs["monthly_rent"] / sqm if sqm > 0 else 0,
                    "vacancy_rate": loc_defaults["vacancy_rate"],
                    "rent_growth_rate": FIXED_DEFAULTS["rent_growth"],
                },
                "unfurnished_3yr": {
                    "monthly_rent_sqm": inputs["monthly_rent"] / sqm * 0.8 if sqm > 0 else 0,
                    "vacancy_rate": loc_defaults["vacancy_rate"],
                    "rent_growth_rate": FIXED_DEFAULTS["rent_growth"],
                },
                "airbnb": {
                    "daily_rate": inputs["monthly_rent"] / 20,  # Rough estimate
                    "occupancy_rate": 0.7,
                    "rent_growth_rate": FIXED_DEFAULTS["rent_growth"],
                    "monthly_seasonality": [1.0] * 12,
                },
            },
            
            # Operating expenses from defaults
            property_tax_yearly=loc_defaults["property_tax_per_sqm"] * sqm,
            condo_fees_monthly=loc_defaults["condo_fees_per_sqm"] * sqm,
            pno_insurance_yearly=loc_defaults["pno_insurance"],
            maintenance_percentage_rent=FIXED_DEFAULTS["maintenance_pct"],
            management_fees_percentage_rent={
                "airbnb": 0.20,
                "furnished_1yr": loc_defaults["management_fee_pct"],
                "unfurnished_3yr": loc_defaults["management_fee_pct"],
            },
            expenses_growth_rate=FIXED_DEFAULTS["expenses_growth"],
            
            # Fiscal
            fiscal_regime="LMNP Réel",
            personal_income_tax_bracket=FIXED_DEFAULTS["tmi"],
            social_contributions_rate=FIXED_DEFAULTS["social_contributions"],
            
            # Exit
            holding_period_years=FIXED_DEFAULTS["holding_period_years"],
            property_value_growth_rate=loc_defaults["price_growth"],
            exit_selling_fees_percentage=0.05,
            
            # Analysis
            risk_free_rate=FIXED_DEFAULTS["risk_free_rate"],
            discount_rate=FIXED_DEFAULTS["discount_rate"],
            
            # Furnishing estimate
            furnishing_costs=sqm * 200,  # ~200€/m² for basic furnishing
            initial_renovation_costs=0,
        )
        
        return params
    
    def display(self):
        """Render simplified interface."""
        lang = get_language()
        
        # Title
        if lang == "fr":
            st.header("🏠 Simulateur Investissement Locatif")
            st.caption("Entrez les informations clés pour évaluer votre investissement")
        else:
            st.header("🏠 Rental Investment Simulator")
            st.caption("Enter key information to evaluate your investment")
        
        # === INPUT FORM ===
        col_input, col_results = st.columns([1, 2])
        
        with col_input:
            with st.form("simple_form"):
                # Location
                locations = get_selectable_locations()
                location = st.selectbox(
                    "📍 " + (t("city") if lang == "en" else "Localisation"),
                    locations,
                    index=locations.index("Lyon") if "Lyon" in locations else 0
                )
                
                # Get defaults for selected location
                loc_defaults = get_location_defaults(location)
                
                # Price
                price = st.number_input(
                    "💰 " + ("Prix d'achat (€)" if lang == "fr" else "Purchase Price (€)"),
                    value=250000,
                    step=10000,
                    format="%d"
                )
                
                # Surface
                surface = st.number_input(
                    "📐 " + ("Surface (m²)" if lang == "fr" else "Surface (sqm)"),
                    value=45,
                    step=5,
                    format="%d"
                )
                
                # Suggested rent based on location
                suggested_rent = int(loc_defaults["rent_per_sqm_furnished"] * surface)
                rent = st.number_input(
                    "🏷️ " + ("Loyer mensuel (€)" if lang == "fr" else "Monthly Rent (€)"),
                    value=suggested_rent,
                    step=50,
                    format="%d",
                    help=f"Suggestion: {fmt_currency(suggested_rent)}" if lang == "en" else f"Suggestion: {fmt_currency(suggested_rent)}"
                )
                
                # Down payment
                apport = st.number_input(
                    "💳 " + ("Apport personnel (€)" if lang == "fr" else "Down Payment (€)"),
                    value=50000,
                    step=5000,
                    format="%d"
                )
                
                # Loan rate
                loan_rate = st.slider(
                    "📊 " + ("Taux d'emprunt (%)" if lang == "fr" else "Loan Rate (%)"),
                    min_value=1.0,
                    max_value=6.0,
                    value=3.5,
                    step=0.1,
                    format="%.1f%%"
                ) / 100
                
                # Submit
                submitted = st.form_submit_button(
                    "🔍 " + ("Analyser" if lang == "fr" else "Analyze"),
                    use_container_width=True,
                    type="primary"
                )
                
                if submitted:
                    inputs = {
                        "location": location,
                        "price": price,
                        "surface_sqm": surface,
                        "monthly_rent": rent,
                        "apport": apport,
                        "loan_rate": loan_rate,
                    }
                    
                    # Build params and run model
                    params = self.build_params_from_simple_inputs(inputs)
                    model = FinancialModel(params)
                    model.run_simulation("furnished_1yr")
                    
                    st.session_state.simple_results = {
                        "model": model,
                        "params": params,
                        "inputs": inputs,
                    }
        
        # === RESULTS ===
        with col_results:
            if st.session_state.simple_results is None:
                st.info("👈 " + ("Remplissez le formulaire et cliquez Analyser" if lang == "fr" else "Fill the form and click Analyze"))
                return
            
            results = st.session_state.simple_results
            model = results["model"]
            params = results["params"]
            metrics = model.get_investment_metrics()
            cf_df = model.get_cash_flow()
            
            if metrics is None:
                st.error("Erreur de calcul" if lang == "fr" else "Calculation error")
                return
            
            # Key metrics
            irr = metrics.get('irr', 0)
            npv = metrics.get('npv', 0)
            monthly_cf = cf_df["Net Change in Cash"].sum() / (params.holding_period_years * 12)
            total_gain = metrics.get('net_exit_proceeds', 0) + cf_df["Net Change in Cash"].sum() - params.property_price * (1 - params.loan_percentage)
            
            risk_free = FIXED_DEFAULTS["risk_free_rate"]
            discount = FIXED_DEFAULTS["discount_rate"]
            color, emoji, label = self.get_score_color(irr, risk_free, discount)
            
            # === ROW 1: Score + Main Metric ===
            st.markdown(f"### {emoji} {label}")
            
            col_m1, col_m2, col_m3 = st.columns(3)
            
            with col_m1:
                irr_display = f"{irr*100:.1f}".replace(".", ",") + "%" if lang == "fr" else f"{irr*100:.1f}%"
                st.metric(
                    "Rendement annuel" if lang == "fr" else "Annual Return",
                    irr_display,
                    help="TRI (Taux de Rendement Interne)" if lang == "fr" else "IRR (Internal Rate of Return)"
                )
            
            with col_m2:
                cf_display = f"{monthly_cf:+,.0f}".replace(",", " ") + " €" if lang == "fr" else f"€{monthly_cf:+,.0f}"
                delta_color = "normal" if monthly_cf >= 0 else "inverse"
                st.metric(
                    "Cash-flow mensuel" if lang == "fr" else "Monthly Cash Flow",
                    cf_display,
                )
            
            with col_m3:
                gain_display = fmt_currency(total_gain, 0)
                st.metric(
                    f"Gain total ({params.holding_period_years} ans)" if lang == "fr" else f"Total Gain ({params.holding_period_years} yrs)",
                    gain_display,
                )
            
            st.markdown("---")
            
            # === ROW 2: Alerts + DVF Comparison ===
            col_alerts, col_dvf = st.columns([1, 1])
            
            with col_alerts:
                self.display_profitability_alerts(metrics, params)
            
            with col_dvf:
                self.display_dvf_comparison(
                    results["inputs"]["location"],
                    results["inputs"]["price"],
                    results["inputs"]["surface_sqm"]
                )
            
            st.markdown("---")
            
            # === ROW 3: Gauge + Chart ===
            col_g, col_c = st.columns([1, 2])
            
            with col_g:
                gauge = self.create_score_gauge(irr, risk_free, discount)
                st.plotly_chart(gauge, use_container_width=True)
            
            with col_c:
                chart = self.create_cashflow_chart(cf_df)
                st.plotly_chart(chart, use_container_width=True)
            
            st.markdown("---")
            
            # === ROW 4: Fiscal Optimization ===
            self.display_fiscal_comparison(params, model)
            
            st.markdown("---")
            
            # === ROW 5: Details expander ===
            with st.expander("📋 " + ("Détails du calcul" if lang == "fr" else "Calculation Details")):
                col_d1, col_d2 = st.columns(2)
                
                with col_d1:
                    st.markdown("**" + ("Financement" if lang == "fr" else "Financing") + "**")
                    loan_amount = params.property_price * params.loan_percentage
                    st.write(f"• " + ("Emprunt" if lang == "fr" else "Loan") + f": {fmt_currency(loan_amount)}")
                    st.write(f"• " + ("Apport" if lang == "fr" else "Down payment") + f": {fmt_currency(results['inputs']['apport'])}")
                    st.write(f"• " + ("Mensualité prêt" if lang == "fr" else "Monthly payment") + f": ~{fmt_currency(loan_amount * 0.005)}")
                
                with col_d2:
                    st.markdown("**" + ("Charges estimées" if lang == "fr" else "Estimated Costs") + "**")
                    st.write(f"• " + ("Taxe foncière" if lang == "fr" else "Property tax") + f": {fmt_currency(params.property_tax_yearly)}/an")
                    st.write(f"• " + ("Charges copro" if lang == "fr" else "Condo fees") + f": {fmt_currency(params.condo_fees_monthly)}/mois")
                    st.write(f"• " + ("Assurance PNO" if lang == "fr" else "PNO Insurance") + f": {fmt_currency(params.pno_insurance_yearly)}/an")
                
                st.caption("💡 " + ("Ces estimations sont basées sur les moyennes de la zone. Passez en mode Expert pour affiner." if lang == "fr" else "These estimates are based on area averages. Switch to Expert mode to refine."))
