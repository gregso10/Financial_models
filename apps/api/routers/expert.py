"""
Expert Mode Router - Premium features
"""
from fastapi import APIRouter
import json

from immo_core import ModelParameters, FinancialModel
from immo_core.data import get_location_defaults, FIXED_DEFAULTS
from immo_core.fiscal import FiscalAdvisor, LeaseType

from ..schemas import (
    ExpertSimulationRequest,
    ExpertSimulationResponse,
    SimulationMetrics,
    FiscalComparison,
    FiscalScenario,
    YearlyCashFlow,
    Alert,
    FiscalComparisonRequest,
    FiscalComparisonResponse,
    LMPCheckRequest,
    LMPCheckResponse,
    SensitivityRequest,
    SensitivityResponse,
    SensitivityPoint,
    LeaseTypeEnum,
)

router = APIRouter(prefix="/expert", tags=["expert"])


# === HELPERS ===

def _map_lease_enum_to_type(lease_enum: LeaseTypeEnum) -> LeaseType:
    """Map API enum to fiscal LeaseType."""
    mapping = {
        LeaseTypeEnum.FURNISHED_1YR: LeaseType.FURNISHED,
        LeaseTypeEnum.UNFURNISHED_3YR: LeaseType.UNFURNISHED,
        LeaseTypeEnum.AIRBNB: LeaseType.AIRBNB,
    }
    return mapping.get(lease_enum, LeaseType.FURNISHED)


def _build_params_from_expert_request(req: ExpertSimulationRequest) -> ModelParameters:
    """Build ModelParameters from expert request."""
    loc = get_location_defaults(req.location)
    sqm = req.surface_sqm
    
    # Calculate loan percentage
    total_cost = req.property_price * (1 + req.notary_fees_pct + req.agency_fees_pct)
    loan_pct = (total_cost - req.apport) / total_cost if total_cost > 0 else 0.8
    loan_pct = max(0, min(1, loan_pct))
    
    # Rental assumptions
    rent_sqm = req.monthly_rent / sqm if req.monthly_rent and sqm > 0 else loc["rent_per_sqm_furnished"]
    
    rental_assumptions = {
        "furnished_1yr": {
            "monthly_rent_sqm": rent_sqm,
            "vacancy_rate": req.vacancy_rate,
            "rent_growth_rate": req.rent_growth_rate,
        },
        "unfurnished_3yr": {
            "monthly_rent_sqm": rent_sqm * 0.8,
            "vacancy_rate": req.vacancy_rate,
            "rent_growth_rate": req.rent_growth_rate,
        },
        "airbnb": {
            "daily_rate": req.daily_rate or (rent_sqm * sqm / 20),
            "occupancy_rate": req.occupancy_rate or 0.70,
            "rent_growth_rate": req.rent_growth_rate,
            "monthly_seasonality": [1.0] * 12,
        },
    }
    
    return ModelParameters(
        property_address_city=req.location,
        property_price=req.property_price,
        property_size_sqm=sqm,
        agency_fees_percentage=req.agency_fees_pct,
        notary_fees_percentage_estimate=req.notary_fees_pct,
        initial_renovation_costs=req.initial_renovation,
        furnishing_costs=req.furnishing_costs,
        loan_percentage=loan_pct,
        loan_interest_rate=req.loan_rate,
        loan_duration_years=req.loan_duration_years,
        loan_insurance_rate=req.loan_insurance_rate,
        rental_assumptions=rental_assumptions,
        property_tax_yearly=req.property_tax_yearly or loc["property_tax_per_sqm"] * sqm,
        condo_fees_monthly=req.condo_fees_monthly or loc["condo_fees_per_sqm"] * sqm,
        pno_insurance_yearly=req.pno_insurance_yearly,
        maintenance_percentage_rent=req.maintenance_pct,
        management_fees_percentage_rent={
            "airbnb": 0.20,
            "furnished_1yr": req.management_fee_pct,
            "unfurnished_3yr": req.management_fee_pct,
        },
        expenses_growth_rate=FIXED_DEFAULTS["expenses_growth"],
        fiscal_regime="LMNP Réel",
        personal_income_tax_bracket=req.tmi,
        social_contributions_rate=FIXED_DEFAULTS["social_contributions"],
        holding_period_years=req.holding_years,
        property_value_growth_rate=req.property_growth_rate,
        exit_selling_fees_percentage=req.exit_fees_pct,
        risk_free_rate=FIXED_DEFAULTS["risk_free_rate"],
        discount_rate=req.discount_rate,
    )


def _generate_alerts(irr: float, monthly_cf: float, equity_multiple: float, risk_free: float = 0.035) -> list[Alert]:
    """Generate profitability alerts."""
    alerts = []
    
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
    elif irr < 0.03:
        alerts.append(Alert(
            type="error", icon="🔴",
            message_fr="Rendement < Livret A (3%)",
            message_en="Return < Livret A (3%)"
        ))
    
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


FISCAL_REASONS = {
    "reel_zero_tax_depreciation": ("L'amortissement LMNP permet de réduire l'impôt à zéro", "LMNP depreciation reduces tax to zero"),
    "reel_lower_tax": ("Les charges réelles dépassent l'abattement forfaitaire", "Actual expenses exceed flat-rate deduction"),
    "reel_deductions_higher": ("Les déductions réelles sont plus avantageuses", "Real deductions are more advantageous"),
    "micro_bic_abatement_sufficient": ("L'abattement de 50% couvre vos charges", "The 50% deduction covers your expenses"),
    "micro_foncier_simple": ("Micro-Foncier plus simple, résultat similaire", "Micro-Foncier simpler, similar result"),
    "micro_simpler_similar_result": ("Régimes équivalents - Micro plus simple", "Similar regimes - Micro is simpler"),
}


# === ENDPOINTS ===

@router.post("/simulate", response_model=ExpertSimulationResponse)
async def simulate_expert(req: ExpertSimulationRequest):
    """Run full expert simulation with all parameters."""
    try:
        params = _build_params_from_expert_request(req)
        model = FinancialModel(params)
        model.run_simulation(req.lease_type.value)
        
        m = model.get_investment_metrics()
        cf = model.get_cash_flow()
        pnl = model.get_pnl()
        
        if not m:
            return ExpertSimulationResponse(success=False, error="Metrics calculation failed")
        
        # Monthly cashflow
        monthly_cf = cf["Net Change in Cash"].sum() / (req.holding_years * 12)
        
        # Yearly cashflows
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
        
        advisor = FiscalAdvisor(tmi=req.tmi)
        comparison = advisor.compare_regimes(
            gross_revenue=gross_revenue,
            deductible_expenses=deductible,
            depreciation=depreciation,
            lease_type=_map_lease_enum_to_type(req.lease_type),
            holding_years=req.holding_years
        )
        
        reason_fr, reason_en = FISCAL_REASONS.get(
            comparison.recommendation_reason, 
            (comparison.recommendation_reason, comparison.recommendation_reason)
        )
        
        fiscal_data = FiscalComparison(
            recommended=comparison.recommended,
            reason=reason_fr,
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
        
        # LMP check
        lmp_raw = advisor.check_lmp_status(gross_revenue)
        lmp_status = json.loads(json.dumps(lmp_raw, default=str))
        
        # Alerts
        alerts = _generate_alerts(
            irr=m.get("irr", 0),
            monthly_cf=monthly_cf,
            equity_multiple=m.get("equity_multiple", 0)
        )
        
        return ExpertSimulationResponse(
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
            alerts=alerts,
            lmp_status=lmp_status,
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return ExpertSimulationResponse(success=False, error=str(e))


@router.post("/fiscal/compare", response_model=FiscalComparisonResponse)
async def compare_fiscal_regimes(req: FiscalComparisonRequest):
    """Compare Micro vs Réel tax regimes."""
    try:
        advisor = FiscalAdvisor(tmi=req.tmi)
        comparison = advisor.compare_regimes(
            gross_revenue=req.gross_revenue,
            deductible_expenses=req.deductible_expenses,
            depreciation=req.depreciation,
            lease_type=_map_lease_enum_to_type(req.lease_type),
            holding_years=req.holding_years,
        )
        
        reason_fr, reason_en = FISCAL_REASONS.get(
            comparison.recommendation_reason,
            (comparison.recommendation_reason, comparison.recommendation_reason)
        )
        
        return FiscalComparisonResponse(
            recommended=comparison.recommended,
            reason_fr=reason_fr,
            reason_en=reason_en,
            annual_savings=abs(comparison.annual_savings),
            total_savings=abs(comparison.savings_over_period),
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
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise


@router.post("/fiscal/lmp-check", response_model=LMPCheckResponse)
async def check_lmp_status(req: LMPCheckRequest):
    """Check if qualifies as LMP (Loueur Meublé Professionnel)."""
    advisor = FiscalAdvisor(other_household_income=req.other_income)
    result = advisor.check_lmp_status(req.annual_revenue)
    
    # Translate implications
    implications_fr = result["implications"]
    implications_en = {
        "social_charges": "SSI contributions (~40% of profit)" if result["is_lmp"] else "Social contributions 17.2%",
        "deficit": "Deductible from all income" if result["is_lmp"] else "Carryforward on furnished rental income only",
        "plus_value": "Professional regime (possible exemption after 5 years)" if result["is_lmp"] else "Individual regime (duration-based deductions)",
        "ifi": "Exempt if main activity" if result["is_lmp"] else "Included in IFI base",
    }
    
    return LMPCheckResponse(
        is_lmp=result["is_lmp"],
        revenue_threshold_met=result["revenue_threshold_met"],
        income_condition_met=result["income_condition_met"],
        annual_revenue=result["annual_revenue"],
        threshold=result["threshold"],
        implications_fr=implications_fr,
        implications_en=implications_en,
    )


@router.post("/sensitivity", response_model=SensitivityResponse)
async def run_sensitivity_analysis(req: SensitivityRequest):
    """Run sensitivity analysis on a single variable."""
    try:
        import numpy as np
        
        base_params = _build_params_from_expert_request(req.base_params)
        
        # Get base value
        if req.variable == "loan_rate":
            base_value = req.base_params.loan_rate
        elif req.variable == "property_growth_rate":
            base_value = req.base_params.property_growth_rate
        else:
            return SensitivityResponse(success=False, error=f"Unknown variable: {req.variable}")
        
        # Generate range
        values = np.linspace(
            base_value + req.range_min,
            base_value + req.range_max,
            req.steps
        )
        
        points = []
        for val in values:
            # Modify parameter
            if req.variable == "loan_rate":
                base_params.loan_interest_rate = float(val)
            elif req.variable == "property_growth_rate":
                base_params.property_value_growth_rate = float(val)
            
            # Run simulation
            model = FinancialModel(base_params)
            model.run_simulation(req.base_params.lease_type.value)
            
            m = model.get_investment_metrics()
            cf = model.get_cash_flow()
            monthly_cf = cf["Net Change in Cash"].sum() / (req.base_params.holding_years * 12)
            
            points.append(SensitivityPoint(
                value=float(val),
                irr=m.get("irr", 0),
                npv=m.get("npv", 0),
                monthly_cashflow=monthly_cf
            ))
        
        return SensitivityResponse(
            success=True,
            variable=req.variable,
            base_value=base_value,
            points=points
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return SensitivityResponse(success=False, error=str(e))