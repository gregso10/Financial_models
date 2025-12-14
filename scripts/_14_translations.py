# In file: scripts/_14_translations.py

"""
Translation system for the Real Estate Financial Model.
Supports English (en) and French (fr).
"""

import streamlit as st
from typing import Dict

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        # === APP TITLE ===
        "app_title": "🏠 Real Estate Financial Model",
        "simulation_params": "Simulation Parameters",
        
        # === SIDEBAR SECTIONS ===
        "property_acquisition": "Property & Acquisition",
        "financing": "Financing",
        "rental_assumptions": "Rental Assumptions",
        "operating_expenses": "Operating Expenses",
        "fiscal_params": "Fiscal Parameters",
        "exit_strategy": "Exit Strategy",
        "investment_analysis": "Investment Analysis",
        "export": "📥 Export",
        "navigate": "Navigate",
        
        # === PROPERTY INPUTS ===
        "city": "City",
        "property_price": "Property Price (€, FAI)",
        "agency_fees": "Agency Fees (%)",
        "notary_fees": "Notary Fees Est. (%)",
        "property_size": "Size (sqm)",
        "initial_renovation": "Initial Renovation (€)",
        "furnishing_costs": "Furnishing (€)",
        
        # === FINANCING INPUTS ===
        "loan_percentage": "Loan Percentage (%)",
        "loan_interest_rate": "Loan Interest Rate (%)",
        "loan_duration": "Loan Duration (Years)",
        "loan_insurance_rate": "Loan Insurance Rate (%)",
        
        # === RENTAL INPUTS ===
        "select_lease_type": "Select Lease Type for Simulation",
        "airbnb_specifics": "Airbnb Specifics:",
        "daily_rate": "Daily Rate (€)",
        "occupancy_rate": "Occupancy Rate",
        "monthly_rent_sqm": "Monthly Rent / sqm (€)",
        "vacancy_rate": "Annual Vacancy Rate",
        
        # === OPERATING EXPENSES INPUTS ===
        "property_tax_yearly": "Property Tax (€/Year)",
        "condo_fees_monthly": "Condo Fees (€/Month)",
        "maintenance_pct": "Maintenance (% of GOI)",
        "pno_insurance": "PNO Insurance (€/Year)",
        "expenses_growth": "Annual Expenses Growth Rate",
        
        # === FISCAL INPUTS ===
        "fiscal_regime": "Fiscal Regime",
        "income_tax_bracket": "Income Tax Bracket (TMI)",
        
        # === EXIT INPUTS ===
        "holding_period": "Holding Period (Years)",
        "property_growth": "Annual Property Value Growth",
        "selling_fees": "Selling Fees (%)",
        
        # === INVESTMENT ANALYSIS INPUTS ===
        "risk_free_rate": "Risk-Free Rate (OAT 20Y)",
        "risk_free_rate_help": "French government bond rate",
        "discount_rate": "Discount Rate",
        "discount_rate_help": "Project discount rate (risk-free + risk premium)",
        
        # === BUTTONS ===
        "run_simulation": "🚀 Run Simulation",
        "simulation_complete": "✅ Simulation complete!",
        "download_excel": "📊 Download Excel Model",
        "export_type": "Export Type",
        "summary": "Summary",
        "full_model": "Full Model",
        "export_summary_help": "Summary: Yearly aggregates | Full Model: Monthly with formulas",
        
        # === NAVIGATION ===
        "dashboard": "Dashboard",
        "pnl_statement": "P&L Statement",
        "balance_sheet": "Balance Sheet",
        "cash_flow": "Cash Flow",
        "dvf": "DVF",
        
        # === DASHBOARD ===
        "investment_dashboard": "📊 Investment Dashboard",
        "run_simulation_prompt": "Run simulation from sidebar to see dashboard.",
        "investment_metrics": "🎯 Investment Performance Metrics",
        "irr": "IRR",
        "irr_help": "Internal Rate of Return - annualized return on equity investment",
        "npv": "NPV",
        "npv_help": "Net Present Value at {rate}% discount rate",
        "cash_on_cash": "Cash-on-Cash (Y1)",
        "cash_on_cash_help": "Year 1 cash flow divided by initial equity invested",
        "equity_multiple": "Equity Multiple",
        "equity_multiple_help": "Total cash returned divided by initial equity",
        "exit_scenario_details": "📤 Exit Scenario Details",
        "exit_property_value": "Exit Property Value",
        "capital_gain": "Capital Gain",
        "selling_costs": "Selling Costs",
        "capital_gains_tax": "Capital Gains Tax",
        "remaining_loan": "Remaining Loan",
        "net_exit_proceeds": "Net Exit Proceeds",
        "consolidated_cf": "Consolidated Cash Flow (Total Period)",
        "pnl_sankey_total": "P&L Sankey (Total Period)",
        "cf_sankey_total": "Cash Flow Sankey (Total Period)",
        "loan_analysis": "📋 Loan Analysis",
        "amortization_yearly": "Amortization Schedule (Yearly)",
        "payment_sensitivity": "Payment Sensitivity Analysis",
        "no_loan": "💰 No loan in this scenario (100% equity financing)",
        "irr_sensitivity": "💎 Investment Return Sensitivity Analysis",
        "irr_sensitivity_heatmap": "IRR Sensitivity Heatmap",
        "npv_sensitivity_heatmap": "NPV Range Analysis",
        "sensitivity_caption": "Varying property value growth rate and loan interest rate",
        "calculating_irr": "Calculating IRR sensitivity... (this may take a moment)",
        "calculating_npv": "Calculating NPV range...",
        "could_not_calculate_irr": "Could not calculate IRR sensitivity",
        "could_not_calculate_npv": "Could not calculate NPV sensitivity",
        
        # === P&L PAGE ===
        "pnl_title": "💰 Profit & Loss Statement",
        "run_simulation_pnl": "Run simulation from sidebar to see P&L.",
        "year_1_flow": "Year 1 Flow",
        
        # === BS PAGE ===
        "bs_title": "🏦 Balance Sheet",
        "run_simulation_bs": "Run simulation from sidebar to see Balance Sheet.",
        
        # === CF PAGE ===
        "cf_title": "💵 Cash Flow Statement",
        "run_simulation_cf": "Run simulation from sidebar to see Cash Flow.",
        
        # === DVF PAGE ===
        "dvf_title": "🗺️ Paris Real Estate Prices (€/m²)",
        "transactions": "Transactions",
        "median_price_sqm": "Median €/m²",
        "mean_price_sqm": "Mean €/m²",
        "max_price_sqm": "Max €/m²",
        "no_paris_data": "No Paris data found. Run geocoding first.",
        "dvf_error": "Error: {error}",
        "dvf_db_info": "Ensure DVF database exists at data/dvf_fresh_local.db",
        
        # === P&L LABELS ===
        "gross_potential_rent": "Gross Potential Rent",
        "vacancy_loss": "Vacancy Loss",
        "occupancy_adj": "Occupancy Adjustment",
        "gross_operating_income": "Gross Operating Income",
        "property_tax": "Property Tax",
        "condo_fees": "Condo Fees",
        "pno_insurance_label": "PNO Insurance",
        "maintenance": "Maintenance",
        "management_fees": "Management Fees",
        "airbnb_costs": "Airbnb Specific Costs",
        "total_opex": "Total Operating Expenses",
        "noi": "Net Operating Income",
        "loan_interest": "Loan Interest",
        "loan_insurance": "Loan Insurance",
        "depreciation": "Depreciation/Amortization",
        "taxable_income": "Taxable Income",
        "income_tax": "Income Tax",
        "social_contributions": "Social Contributions",
        "total_taxes": "Total Taxes",
        "net_income": "Net Income",
        
        # === CF LABELS ===
        "cfo": "Cash Flow from Operations (CFO)",
        "acquisition_costs": "Acquisition Costs Outflow",
        "cfi": "Cash Flow from Investing (CFI)",
        "loan_proceeds": "Loan Proceeds",
        "equity_injected": "Equity Injected",
        "principal_repayment": "Loan Principal Repayment",
        "cff": "Cash Flow from Financing (CFF)",
        "net_change_cash": "Net Change in Cash",
        "beginning_cash": "Beginning Cash Balance",
        "ending_cash": "Ending Cash Balance",
        
        # === BS LABELS ===
        "property_net_value": "Property Net Value",
        "renovation_net_value": "Renovation Net Value",
        "furnishing_net_value": "Furnishing Net Value",
        "total_fixed_assets": "Total Fixed Assets",
        "cash": "Cash",
        "total_assets": "Total Assets",
        "loan_balance": "Loan Balance",
        "total_liabilities": "Total Liabilities",
        "initial_equity": "Initial Equity",
        "retained_earnings": "Retained Earnings",
        "total_equity": "Total Equity",
        "total_le": "Total Liabilities & Equity",
        "balance_check": "Balance Check",
        "initial": "Initial",
        "year": "Year",
        
        # === EXCEL SHEETS ===
        "assumptions": "Assumptions",
        "loan_schedule": "Loan Schedule",
        "investment_metrics_sheet": "Investment Metrics",
        "no_loan_excel": "No loan in this scenario (100% equity)",
        
        # === MISC ===
        "in_k_euros": "(in €k)",
        "simulation_error": "Simulation error: {error}",
        "error_creating_params": "Error creating parameters: {error}",
        
        # === HELP TOOLTIPS ===
        "property_price_help": "Price including agency fees (FAI = Frais d'Agence Inclus). This is the total price you pay to acquire the property, including the agent's commission.",
        "agency_fees_help": "Agency commission as % of net seller price. Already included in FAI price above. Used to calculate notary fees base.",
        "notary_type": "Property Type (Notary Fees)",
        "notary_ancien": "Ancien (existing) - 8%",
        "notary_neuf": "Neuf (new build) - 5.5%",
        "notary_help": "Notary fees are calculated on property price. 'Ancien' (existing properties) = ~8%, 'Neuf' (new builds < 5 years) = ~5.5%",
        
        "loan_amount_label": "Loan Amount (€)",
        "loan_amount_help": "Absolute amount to borrow. The percentage below shows what portion of total acquisition cost this represents.",
        "loan_pct_display": "→ {pct:.1f}% of total acquisition cost (€{total:,.0f})",
        "loan_interest_help": "Annual nominal interest rate (TAEG). Current market rates in France: ~3-4% (2024).",
        "loan_duration_help": "Standard durations: 15, 20, or 25 years. Longer = lower monthly payments but more total interest.",
        "loan_insurance_help": "Borrower insurance (assurance emprunteur). Typically 0.1%-0.4% of initial loan amount per year. Required by French banks.",
        
        "irr_explanation": """**IRR (Internal Rate of Return)** is the annualized return on your equity investment, accounting for the timing of all cash flows.

It answers: "What equivalent annual return did my invested capital generate?"

- **IRR > Discount Rate** → Good investment (creates value)
- **IRR < Discount Rate** → Poor investment (destroys value)
- Includes: rental income, tax savings, property appreciation, and exit proceeds
- Does NOT account for risk - compare to similar investments""",
        
        "npv_explanation": """**NPV (Net Present Value)** is the total value created by the investment in today's euros.

It discounts all future cash flows back to present value using your required return (discount rate).

- **NPV > 0** → Investment creates value above your required return
- **NPV = 0** → Investment exactly meets your required return
- **NPV < 0** → Investment fails to meet your required return

Formula: NPV = -Initial Investment + Σ(Cash Flows / (1 + r)^t)""",
        
        "discount_rate_explanation": """**How to choose a discount rate:**

Discount Rate = Risk-Free Rate + Risk Premium

**Risk-Free Rate** (~3.5%): Return on "safe" investment (French OAT 20-year government bonds)

**Risk Premium** (1-5%): Extra return required for taking real estate risk:
- Liquidity risk (can't sell quickly)
- Vacancy risk
- Maintenance surprises
- Market fluctuations

**Typical ranges:**
- Conservative investor: 7-10%
- Moderate investor: 5-7%
- Aggressive investor: 4-5%

Higher discount rate = more conservative valuation""",
        
        "risk_free_rate_explanation": """**Why French OAT 20-year?**

We use the 20-year French government bond (OAT) because:

1. **Matches investment horizon**: Real estate is typically held 10-25 years
2. **Same currency**: Euro-denominated, no FX risk
3. **Sovereign guarantee**: Closest to "risk-free" in Eurozone
4. **Benchmark**: Standard reference for French real estate valuations

Current OAT 20Y: ~3.5% (as of 2024)

This represents the minimum return you could get with zero risk - your real estate investment must beat this to justify the additional risk.""",

        "occupancy_help": "Percentage of nights booked per year. 70% = ~255 nights/year. Seasonal properties may have 50-60%, prime locations 80%+.",
        "vacancy_help": "Expected vacancy as % of annual rent. 8% ≈ 1 month/year between tenants. Long-term leases typically have lower vacancy.",
        "maintenance_help": "Annual maintenance budget as % of gross rent. 5% is standard, older properties may need 8-10%.",
        "expenses_growth_help": "Annual inflation rate for operating expenses (taxes, fees, insurance). French inflation averages 1.5-2%.",
        "property_growth_help": "Expected annual appreciation of property value. Paris historical average: 3-5%. Provincial cities: 1-3%.",
        "holding_period_help": "Investment duration before sale. Affects: capital gains tax (exemption after 22-30 years), total returns, and IRR calculation.",
    },
    
    "fr": {
        # === APP TITLE ===
        "app_title": "🏠 Modèle Financier Immobilier",
        "simulation_params": "Paramètres de Simulation",
        
        # === SIDEBAR SECTIONS ===
        "property_acquisition": "Bien & Acquisition",
        "financing": "Financement",
        "rental_assumptions": "Hypothèses Locatives",
        "operating_expenses": "Charges d'Exploitation",
        "fiscal_params": "Paramètres Fiscaux",
        "exit_strategy": "Stratégie de Sortie",
        "investment_analysis": "Analyse d'Investissement",
        "export": "📥 Export",
        "navigate": "Navigation",
        
        # === PROPERTY INPUTS ===
        "city": "Ville",
        "property_price": "Prix du bien (€, FAI)",
        "agency_fees": "Frais d'agence (%)",
        "notary_fees": "Frais de notaire est. (%)",
        "property_size": "Surface (m²)",
        "initial_renovation": "Travaux initiaux (€)",
        "furnishing_costs": "Ameublement (€)",
        
        # === FINANCING INPUTS ===
        "loan_percentage": "Pourcentage d'emprunt (%)",
        "loan_interest_rate": "Taux d'intérêt (%)",
        "loan_duration": "Durée du prêt (Années)",
        "loan_insurance_rate": "Taux assurance emprunteur (%)",
        
        # === RENTAL INPUTS ===
        "select_lease_type": "Type de bail pour simulation",
        "airbnb_specifics": "Spécificités Airbnb :",
        "daily_rate": "Tarif journalier (€)",
        "occupancy_rate": "Taux d'occupation",
        "monthly_rent_sqm": "Loyer mensuel / m² (€)",
        "vacancy_rate": "Taux de vacance annuel",
        
        # === OPERATING EXPENSES INPUTS ===
        "property_tax_yearly": "Taxe foncière (€/An)",
        "condo_fees_monthly": "Charges copro (€/Mois)",
        "maintenance_pct": "Entretien (% du GOI)",
        "pno_insurance": "Assurance PNO (€/An)",
        "expenses_growth": "Croissance annuelle des charges",
        
        # === FISCAL INPUTS ===
        "fiscal_regime": "Régime fiscal",
        "income_tax_bracket": "Tranche marginale (TMI)",
        
        # === EXIT INPUTS ===
        "holding_period": "Durée de détention (Années)",
        "property_growth": "Croissance annuelle du bien",
        "selling_fees": "Frais de vente (%)",
        
        # === INVESTMENT ANALYSIS INPUTS ===
        "risk_free_rate": "Taux sans risque (OAT 20A)",
        "risk_free_rate_help": "Taux des obligations d'État françaises",
        "discount_rate": "Taux d'actualisation",
        "discount_rate_help": "Taux d'actualisation projet (sans risque + prime)",
        
        # === BUTTONS ===
        "run_simulation": "🚀 Lancer la simulation",
        "simulation_complete": "✅ Simulation terminée !",
        "download_excel": "📊 Télécharger le modèle Excel",
        "export_type": "Type d'export",
        "summary": "Résumé",
        "full_model": "Modèle complet",
        "export_summary_help": "Résumé : Agrégats annuels | Complet : Mensuel avec formules",
        
        # === NAVIGATION ===
        "dashboard": "Tableau de bord",
        "pnl_statement": "Compte de résultat",
        "balance_sheet": "Bilan",
        "cash_flow": "Flux de trésorerie",
        "dvf": "DVF",
        
        # === DASHBOARD ===
        "investment_dashboard": "📊 Tableau de Bord Investissement",
        "run_simulation_prompt": "Lancez la simulation depuis le menu latéral.",
        "investment_metrics": "🎯 Métriques de Performance",
        "irr": "TRI",
        "irr_help": "Taux de Rentabilité Interne - rendement annualisé sur fonds propres",
        "npv": "VAN",
        "npv_help": "Valeur Actuelle Nette au taux de {rate}%",
        "cash_on_cash": "Cash-on-Cash (A1)",
        "cash_on_cash_help": "Flux de trésorerie année 1 / fonds propres investis",
        "equity_multiple": "Multiple sur fonds propres",
        "equity_multiple_help": "Total cash retourné / fonds propres initiaux",
        "exit_scenario_details": "📤 Détails du Scénario de Sortie",
        "exit_property_value": "Valeur de sortie du bien",
        "capital_gain": "Plus-value",
        "selling_costs": "Frais de vente",
        "capital_gains_tax": "Impôt sur plus-value",
        "remaining_loan": "Emprunt restant",
        "net_exit_proceeds": "Produit net de sortie",
        "consolidated_cf": "Flux de trésorerie consolidé (Période totale)",
        "pnl_sankey_total": "Sankey Résultat (Période totale)",
        "cf_sankey_total": "Sankey Trésorerie (Période totale)",
        "loan_analysis": "📋 Analyse du Prêt",
        "amortization_yearly": "Tableau d'amortissement (Annuel)",
        "payment_sensitivity": "Analyse de sensibilité des mensualités",
        "no_loan": "💰 Pas d'emprunt (financement 100% fonds propres)",
        "irr_sensitivity": "💎 Analyse de Sensibilité du Rendement",
        "irr_sensitivity_heatmap": "Carte de sensibilité TRI",
        "npv_sensitivity_heatmap": "Analyse de sensibilité VAN",
        "sensitivity_caption": "Variation du taux de croissance et du taux d'intérêt",
        "calculating_irr": "Calcul de la sensibilité TRI... (peut prendre un moment)",
        "calculating_npv": "Calcul de la sensibilité VAN...",
        "could_not_calculate_irr": "Impossible de calculer la sensibilité TRI",
        "could_not_calculate_npv": "Impossible de calculer la sensibilité VAN",
        
        # === P&L PAGE ===
        "pnl_title": "💰 Compte de Résultat",
        "run_simulation_pnl": "Lancez la simulation pour voir le compte de résultat.",
        "year_1_flow": "Flux Année 1",
        
        # === BS PAGE ===
        "bs_title": "🏦 Bilan",
        "run_simulation_bs": "Lancez la simulation pour voir le bilan.",
        
        # === CF PAGE ===
        "cf_title": "💵 Tableau des Flux de Trésorerie",
        "run_simulation_cf": "Lancez la simulation pour voir les flux.",
        
        # === DVF PAGE ===
        "dvf_title": "🗺️ Prix Immobiliers Paris (€/m²)",
        "transactions": "Transactions",
        "median_price_sqm": "Médiane €/m²",
        "mean_price_sqm": "Moyenne €/m²",
        "max_price_sqm": "Max €/m²",
        "no_paris_data": "Aucune donnée Paris. Lancez le géocodage d'abord.",
        "dvf_error": "Erreur : {error}",
        "dvf_db_info": "Vérifiez que la base DVF existe dans data/dvf_fresh_local.db",
        
        # === P&L LABELS ===
        "gross_potential_rent": "Loyer potentiel brut",
        "vacancy_loss": "Perte vacance locative",
        "occupancy_adj": "Ajustement occupation",
        "gross_operating_income": "Revenu brut d'exploitation",
        "property_tax": "Taxe foncière",
        "condo_fees": "Charges copropriété",
        "pno_insurance_label": "Assurance PNO",
        "maintenance": "Entretien",
        "management_fees": "Frais de gestion",
        "airbnb_costs": "Coûts spécifiques Airbnb",
        "total_opex": "Total charges d'exploitation",
        "noi": "Résultat net d'exploitation",
        "loan_interest": "Intérêts d'emprunt",
        "loan_insurance": "Assurance emprunteur",
        "depreciation": "Amortissements",
        "taxable_income": "Résultat fiscal",
        "income_tax": "Impôt sur le revenu",
        "social_contributions": "Prélèvements sociaux",
        "total_taxes": "Total impôts",
        "net_income": "Résultat net",
        
        # === CF LABELS ===
        "cfo": "Flux d'exploitation (CFO)",
        "acquisition_costs": "Coûts d'acquisition",
        "cfi": "Flux d'investissement (CFI)",
        "loan_proceeds": "Déblocage emprunt",
        "equity_injected": "Apport fonds propres",
        "principal_repayment": "Remboursement capital",
        "cff": "Flux de financement (CFF)",
        "net_change_cash": "Variation nette de trésorerie",
        "beginning_cash": "Trésorerie début",
        "ending_cash": "Trésorerie fin",
        
        # === BS LABELS ===
        "property_net_value": "Valeur nette bien",
        "renovation_net_value": "Valeur nette travaux",
        "furnishing_net_value": "Valeur nette mobilier",
        "total_fixed_assets": "Total immobilisations",
        "cash": "Trésorerie",
        "total_assets": "Total Actif",
        "loan_balance": "Encours emprunt",
        "total_liabilities": "Total Passif",
        "initial_equity": "Fonds propres initiaux",
        "retained_earnings": "Report à nouveau",
        "total_equity": "Total Capitaux propres",
        "total_le": "Total Passif & Capitaux propres",
        "balance_check": "Contrôle équilibre",
        "initial": "Initial",
        "year": "Année",
        
        # === EXCEL SHEETS ===
        "assumptions": "Hypothèses",
        "loan_schedule": "Tableau amortissement",
        "investment_metrics_sheet": "Métriques investissement",
        "no_loan_excel": "Pas d'emprunt (100% fonds propres)",
        
        # === MISC ===
        "in_k_euros": "(en k€)",
        "simulation_error": "Erreur de simulation : {error}",
        "error_creating_params": "Erreur paramètres : {error}",
        
        # === HELP TOOLTIPS ===
        "property_price_help": "Prix FAI (Frais d'Agence Inclus). C'est le prix total d'acquisition incluant la commission de l'agent immobilier.",
        "agency_fees_help": "Commission d'agence en % du prix net vendeur. Déjà incluse dans le prix FAI ci-dessus. Utilisée pour calculer la base des frais de notaire.",
        "notary_type": "Type de bien (Frais de notaire)",
        "notary_ancien": "Ancien - 8%",
        "notary_neuf": "Neuf (< 5 ans) - 5,5%",
        "notary_help": "Frais de notaire calculés sur le prix du bien. 'Ancien' = ~8%, 'Neuf' (moins de 5 ans) = ~5,5%",
        
        "loan_amount_label": "Montant emprunté (€)",
        "loan_amount_help": "Montant absolu à emprunter. Le pourcentage affiché montre la part du coût total d'acquisition.",
        "loan_pct_display": "→ {pct:.1f}% du coût total d'acquisition (€{total:,.0f})",
        "loan_interest_help": "Taux d'intérêt annuel nominal (TAEG). Taux actuels en France : ~3-4% (2024).",
        "loan_duration_help": "Durées standard : 15, 20 ou 25 ans. Plus long = mensualités plus faibles mais plus d'intérêts totaux.",
        "loan_insurance_help": "Assurance emprunteur. Typiquement 0,1%-0,4% du capital initial par an. Exigée par les banques françaises.",
        
        "irr_explanation": """**TRI (Taux de Rentabilité Interne)** est le rendement annualisé de votre investissement en fonds propres, tenant compte du timing de tous les flux.

Il répond à : "Quel rendement annuel équivalent mon capital investi a-t-il généré ?"

- **TRI > Taux d'actualisation** → Bon investissement (crée de la valeur)
- **TRI < Taux d'actualisation** → Mauvais investissement (détruit de la valeur)
- Inclut : revenus locatifs, économies fiscales, plus-value, produit de revente
- Ne tient PAS compte du risque - comparer à des investissements similaires""",
        
        "npv_explanation": """**VAN (Valeur Actuelle Nette)** est la valeur totale créée par l'investissement en euros d'aujourd'hui.

Elle actualise tous les flux futurs à leur valeur présente en utilisant votre taux de rendement exigé.

- **VAN > 0** → L'investissement crée de la valeur au-delà du rendement exigé
- **VAN = 0** → L'investissement atteint exactement le rendement exigé
- **VAN < 0** → L'investissement n'atteint pas le rendement exigé

Formule : VAN = -Investissement Initial + Σ(Flux / (1 + r)^t)""",
        
        "discount_rate_explanation": """**Comment choisir un taux d'actualisation :**

Taux d'actualisation = Taux sans risque + Prime de risque

**Taux sans risque** (~3,5%) : Rendement d'un placement "sûr" (OAT françaises 20 ans)

**Prime de risque** (1-5%) : Rendement supplémentaire exigé pour le risque immobilier :
- Risque de liquidité (revente lente)
- Risque de vacance
- Imprévus de maintenance
- Fluctuations du marché

**Fourchettes typiques :**
- Investisseur prudent : 7-10%
- Investisseur modéré : 5-7%
- Investisseur dynamique : 4-5%

Taux plus élevé = valorisation plus conservative""",
        
        "risk_free_rate_explanation": """**Pourquoi l'OAT française 20 ans ?**

Nous utilisons l'obligation d'État française à 20 ans (OAT) car :

1. **Correspond à l'horizon d'investissement** : L'immobilier se détient typiquement 10-25 ans
2. **Même devise** : Libellé en euros, pas de risque de change
3. **Garantie souveraine** : Le plus proche du "sans risque" en zone euro
4. **Référence** : Standard pour les valorisations immobilières françaises

OAT 20 ans actuelle : ~3,5% (2024)

Cela représente le rendement minimum avec zéro risque - votre investissement immobilier doit battre ce taux pour justifier le risque supplémentaire.""",

        "occupancy_help": "Pourcentage de nuits réservées par an. 70% = ~255 nuits/an. Biens saisonniers : 50-60%, emplacements premium : 80%+.",
        "vacancy_help": "Vacance attendue en % du loyer annuel. 8% ≈ 1 mois/an entre locataires. Baux longue durée = vacance plus faible.",
        "maintenance_help": "Budget entretien annuel en % du loyer brut. 5% est standard, biens anciens peuvent nécessiter 8-10%.",
        "expenses_growth_help": "Taux d'inflation annuel des charges (taxes, frais, assurance). Inflation française moyenne : 1,5-2%.",
        "property_growth_help": "Appréciation annuelle attendue du bien. Moyenne historique Paris : 3-5%. Villes de province : 1-3%.",
        "holding_period_help": "Durée de l'investissement avant revente. Affecte : impôt sur plus-value (exonération après 22-30 ans), rendements totaux, et calcul du TRI.",
    }
}


def t(key: str, **kwargs) -> str:
    """
    Get translated string for current language.
    
    Args:
        key: Translation key
        **kwargs: Format arguments for string interpolation
        
    Returns:
        Translated string, or key if not found
    """
    lang = st.session_state.get("language", "en")
    text = TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)
    
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass
    
    return text


def get_language() -> str:
    """Get current language code."""
    return st.session_state.get("language", "en")


def set_language(lang: str):
    """Set language code."""
    if lang in TRANSLATIONS:
        st.session_state.language = lang


def toggle_language():
    """Toggle between English and French."""
    current = get_language()
    set_language("fr" if current == "en" else "en")


def get_pnl_label_map() -> Dict[str, str]:
    """Get P&L row label mapping for current language."""
    return {
        "Gross Potential Rent": f"  {t('gross_potential_rent')}",
        "Vacancy Loss": f"    {t('vacancy_loss')}",
        "Gross Operating Income": t('gross_operating_income'),
        "Property Tax": f"    {t('property_tax')}",
        "Condo Fees": f"    {t('condo_fees')}",
        "PNO Insurance": f"    {t('pno_insurance_label')}",
        "Maintenance": f"    {t('maintenance')}",
        "Management Fees": f"    {t('management_fees')}",
        "Airbnb Specific Costs": f"    {t('airbnb_costs')}",
        "Total Operating Expenses": t('total_opex'),
        "Net Operating Income": t('noi'),
        "Loan Interest": f"    {t('loan_interest')}",
        "Loan Insurance": f"    {t('loan_insurance')}",
        "Depreciation/Amortization": f"    {t('depreciation')}",
        "Taxable Income": t('taxable_income'),
        "Income Tax": f"    {t('income_tax')}",
        "Social Contributions": f"    {t('social_contributions')}",
        "Total Taxes": t('total_taxes'),
        "Net Income": t('net_income'),
    }


def fmt_number(value: float, decimals: int = 0) -> str:
    """
    Format number according to current language locale.
    - EN: 1,000,000.50
    - FR: 1 000 000,50
    """
    lang = get_language()
    
    if decimals > 0:
        formatted = f"{value:,.{decimals}f}"
    else:
        formatted = f"{value:,.0f}"
    
    if lang == "fr":
        # Replace comma with space, then period with comma
        # Step 1: temp replace comma -> @
        formatted = formatted.replace(",", " ")
        # Step 2: replace period -> comma
        formatted = formatted.replace(".", ",")
    
    return formatted


def fmt_currency(value: float, decimals: int = 0, symbol: str = "€") -> str:
    """
    Format currency according to current language locale.
    - EN: €1,000,000.50
    - FR: 1 000 000,50 €
    """
    lang = get_language()
    num = fmt_number(value, decimals)
    
    if lang == "fr":
        return f"{num} {symbol}"
    else:
        return f"{symbol}{num}"


def fmt_percent(value: float, decimals: int = 1) -> str:
    """
    Format percentage according to current language locale.
    Value should be in decimal form (0.05 for 5%)
    - EN: 5.0%
    - FR: 5,0%
    """
    lang = get_language()
    pct_value = value * 100
    
    if lang == "fr":
        formatted = f"{pct_value:.{decimals}f}".replace(".", ",")
    else:
        formatted = f"{pct_value:.{decimals}f}"
    
    return f"{formatted}%"


def get_cf_label_map() -> Dict[str, str]:
    """Get Cash Flow row label mapping for current language."""
    return {
        "Net Income": t('net_income'),
        "Depreciation/Amortization": f"  {t('depreciation')}",
        "Cash Flow from Operations (CFO)": t('cfo'),
        "Acquisition Costs Outflow": f"  {t('acquisition_costs')}",
        "Cash Flow from Investing (CFI)": t('cfi'),
        "Loan Proceeds": t('loan_proceeds'),
        "Equity Injected": t('equity_injected'),
        "Loan Principal Repayment": f"  {t('principal_repayment')}",
        "Cash Flow from Financing (CFF)": t('cff'),
        "Net Change in Cash": t('net_change_cash'),
        "Beginning Cash Balance": t('beginning_cash'),
        "Ending Cash Balance": t('ending_cash'),
    }
