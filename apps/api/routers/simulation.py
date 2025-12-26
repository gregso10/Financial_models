from fastapi import APIRouter
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from immo_core import ModelParameters, FinancialModel
from immo_core.data import get_location_defaults, FIXED_DEFAULTS
from immo_core.fiscal import FiscalAdvisor, LeaseType 

from ..schemas import (
    SimpleSimulationRequest, SimulationResponse, SimulationMetrics,
    FiscalComparison, FiscalScenario, YearlyCashFlow, Alert
)

router = APIRouter(prefix="/simulate", tags=["simulation"])


def generate_alerts(irr: float, monthly_cf: float, equity_multiple: float, risk_free: float = 0.035) -> list[Alert]:
    """Generate profitability alerts."""
    alerts = []
    
    # Cash flow alert
    if monthly_cf >= 0:
        alerts.append(Alert(
            type="success", icon="✅",
            message_fr="Cash-flow positif dès le départ",
            message_en="Positive cash flow from day 1"
        ))
    elif monthly_cf >= -100:
        alerts.append(Alert(
            type="warning", icon="⚠️",
            message_fr=f"Effort d'épargne modéré: {abs(monthly_cf):.0f}€/mois",
            message_en=f"Moderate saving effort: €{abs(monthly_cf):.0f}/month"
        ))
    else:
        alerts.append(Alert(
            type="error", icon="🔴",
            message_fr=f"Cash-flow négatif: {monthly_cf:.0f}€/mois",
            message_en=f"Negative cash flow: €{monthly_cf:.0f}/month"
        ))
    
    # IRR alert
    if irr > 0.08:
        alerts.append(Alert(
            type="success", icon="🌟",
            message_fr="Rendement excellent (>8%)",
            message_en="Excellent return (>8%)"
        ))
    elif irr > risk_free:
        alerts.append(Alert(
            type="success", icon="✅",
            message_fr=f"Rendement > taux sans risque ({risk_free*100:.1f}%)",
            message_en=f"Return > risk-free rate ({risk_free*100:.1f}%)"
        ))
    elif irr > 0.03:
        alerts.append(Alert(
            type="warning", icon="⚠️",
            message_fr="Rendement > Livret A mais < obligations",
            message_en="Return > Livret A but < bonds"
        ))
    else:
        alerts.append(Alert(
            type="error", icon="🔴",
            message_fr="Rendement < Livret A (3%)",
            message_en="Return < Livret A (3%)"
        ))
    
    # Equity multiple alert
    if equity_multiple >= 2.0:
        alerts.append(Alert(
            type="success", icon="💰",
            message_fr="Capital doublé sur la période",
            message_en="Capital doubled over period"
        ))
    elif equity_multiple < 1.0:
        alerts.append(Alert(
            type="error", icon="📉",
            message_fr="Perte en capital probable",
            message_en="Likely capital loss"
        ))
    
    return alerts


@router.post("/simple", response_model=SimulationResponse)
async def simulate_simple(req: SimpleSimulationRequest):
    try:
        loc = get_location_defaults(req.location)
        sqm = req.surface_sqm
        loan_pct = (req.price - req.apport) / req.price if req.price > 0 else 0.8
        loan_pct = max(0, min(1, loan_pct))
        
        params = ModelParameters(
            property_address_city=req.location,
            property_price=req.price,
            property_size_sqm=sqm,
            loan_percentage=loan_pct,
            loan_interest_rate=req.loan_rate,
            loan_duration_years=FIXED_DEFAULTS["loan_duration_years"],
            loan_insurance_rate=FIXED_DEFAULTS["loan_insurance_rate"],
            rental_assumptions={
                "furnished_1yr": {
                    "monthly_rent_sqm": req.monthly_rent / sqm,
                    "vacancy_rate": loc["vacancy_rate"],
                    "rent_growth_rate": FIXED_DEFAULTS["rent_growth"],
                },
                "unfurnished_3yr": {"monthly_rent_sqm": 0, "vacancy_rate": 0.04, "rent_growth_rate": 0.015},
                "airbnb": {"daily_rate": 0, "occupancy_rate": 0.7, "rent_growth_rate": 0.02, "monthly_seasonality": [1]*12},
            },
            property_tax_yearly=loc["property_tax_per_sqm"] * sqm,
            condo_fees_monthly=loc["condo_fees_per_sqm"] * sqm,
            pno_insurance_yearly=loc["pno_insurance"],
            maintenance_percentage_rent=FIXED_DEFAULTS["maintenance_pct"],
            management_fees_percentage_rent={
                "airbnb": 0.20,
                "furnished_1yr": loc["management_fee_pct"],
                "unfurnished_3yr": loc["management_fee_pct"],
            },
            personal_income_tax_bracket=FIXED_DEFAULTS["tmi"],
            social_contributions_rate=FIXED_DEFAULTS["social_contributions"],
            holding_period_years=FIXED_DEFAULTS["holding_period_years"],
            property_value_growth_rate=loc["price_growth"],
            exit_selling_fees_percentage=0.05,
            furnishing_costs=sqm * 200,
            initial_renovation_costs=0,
            fiscal_regime="LMNP Réel",
        )
        
        model = FinancialModel(params)
        model.run_simulation("furnished_1yr")
        
        m = model.get_investment_metrics()
        cf = model.get_cash_flow()
        pnl = model.get_pnl()
        
        # Monthly cashflow
        holding_years = FIXED_DEFAULTS["holding_period_years"]
        monthly_cf = cf["Net Change in Cash"].sum() / (holding_years * 12)
        
        # Yearly cashflows for chart
        cf_yearly = cf.groupby("Year")["Net Change in Cash"].sum()
        cumulative = 0
        yearly_cashflows = []
        for year, net_change in cf_yearly.items():
            cumulative += net_change
            yearly_cashflows.append(YearlyCashFlow(
                year=int(year),
                net_change=float(net_change),
                cumulative=float(cumulative)
            ))
        
        # Fiscal comparison
        pnl_year1 = pnl[pnl["Year"] == 1]
        gross_revenue = pnl_year1["Gross Operating Income"].sum()
        deductible = abs(
            pnl_year1["Property Tax"].sum() +
            pnl_year1["Condo Fees"].sum() +
            pnl_year1["PNO Insurance"].sum() +
            pnl_year1["Maintenance"].sum() +
            pnl_year1["Management Fees"].sum() +
            pnl_year1["Loan Interest"].sum() +
            pnl_year1["Loan Insurance"].sum()
        )
        depreciation = abs(pnl_year1["Depreciation/Amortization"].sum())
        
        advisor = FiscalAdvisor(tmi=FIXED_DEFAULTS["tmi"])
        comparison = advisor.compare_regimes(
            gross_revenue=gross_revenue,
            deductible_expenses=deductible,
            depreciation=depreciation,
            lease_type=LeaseType.FURNISHED,
            holding_years=holding_years
        )
        
        # Reason text
        reasons = {
            "reel_zero_tax_depreciation": ("L'amortissement LMNP permet de réduire l'impôt à zéro", "LMNP depreciation reduces tax to zero"),
            "reel_lower_tax": ("Les charges réelles dépassent l'abattement forfaitaire", "Actual expenses exceed flat-rate deduction"),
            "reel_deductions_higher": ("Les déductions réelles sont plus avantageuses", "Real deductions are more advantageous"),
            "micro_bic_abatement_sufficient": ("L'abattement de 50% couvre vos charges", "The 50% deduction covers your expenses"),
            "micro_foncier_simple": ("Micro-Foncier plus simple, résultat similaire", "Micro-Foncier simpler, similar result"),
            "micro_simpler_similar_result": ("Régimes équivalents - Micro plus simple", "Similar regimes - Micro is simpler"),
        }
        reason_fr, reason_en = reasons.get(comparison.recommendation_reason, (comparison.recommendation_reason, comparison.recommendation_reason))
        
        fiscal_data = FiscalComparison(
            recommended=comparison.recommended,
            reason=reason_fr,  # We'll handle translation in frontend
            annual_savings=abs(comparison.annual_savings),
            micro=FiscalScenario(
                regime=comparison.micro.regime,
                gross_revenue=comparison.micro.gross_revenue,
                taxable_income=comparison.micro.taxable_income,
                total_tax=comparison.micro.total_tax,
                effective_rate=comparison.micro.effective_rate
            ),
            reel=FiscalScenario(
                regime=comparison.reel.regime,
                gross_revenue=comparison.reel.gross_revenue,
                taxable_income=comparison.reel.taxable_income,
                total_tax=comparison.reel.total_tax,
                effective_rate=comparison.reel.effective_rate
            )
        )
        
        # Alerts
        alerts = generate_alerts(
            irr=m.get("irr", 0),
            monthly_cf=monthly_cf,
            equity_multiple=m.get("equity_multiple", 0)
        )
        
        return SimulationResponse(
            success=True,
            metrics=SimulationMetrics(
                irr=m.get("irr", 0),
                npv=m.get("npv", 0),
                monthly_cashflow=monthly_cf,
                cash_on_cash=m.get("cash_on_cash", 0),
                equity_multiple=m.get("equity_multiple", 0),
                exit_property_value=m.get("exit_property_value", 0),
                net_exit_proceeds=m.get("net_exit_proceeds", 0),
                capital_gains_tax=m.get("capital_gains_tax", 0),
                capital_gain=m.get("capital_gain", 0),
                remaining_loan=m.get("remaining_loan_balance", 0),
                selling_costs=m.get("selling_costs", 0),
            ),
            fiscal=fiscal_data,
            yearly_cashflows=yearly_cashflows,
            alerts=alerts
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return SimulationResponse(success=False, error=str(e))