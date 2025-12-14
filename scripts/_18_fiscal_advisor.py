# scripts/_18_fiscal_advisor.py
"""
Fiscal Advisor Module.
Compares tax regimes (Micro vs Réel, LMNP vs LMP) and provides recommendations.
"""

from dataclasses import dataclass
from typing import Dict, Tuple, Optional
from enum import Enum


class LeaseType(Enum):
    FURNISHED = "furnished"      # Meublé classique
    UNFURNISHED = "unfurnished"  # Nu (location vide)
    AIRBNB = "airbnb"           # Meublé tourisme


class FiscalRegime(Enum):
    MICRO_BIC = "Micro-BIC"           # Meublé < 77 700€
    MICRO_FONCIER = "Micro-Foncier"   # Nu < 15 000€
    LMNP_REEL = "LMNP Réel"           # Meublé réel
    REVENU_FONCIER = "Revenu Foncier" # Nu réel
    LMP = "LMP"                        # Loueur Meublé Professionnel


@dataclass
class FiscalScenario:
    """Results for one fiscal regime."""
    regime: str
    gross_revenue: float
    taxable_income: float
    income_tax: float
    social_contributions: float
    total_tax: float
    net_after_tax: float
    effective_rate: float  # Total tax / Gross revenue


@dataclass
class FiscalComparison:
    """Comparison between two regimes."""
    recommended: str
    micro: FiscalScenario
    reel: FiscalScenario
    annual_savings: float
    savings_over_period: float
    recommendation_reason: str


class FiscalAdvisor:
    """
    Analyzes and compares French rental tax regimes.
    """
    
    # Tax constants
    SOCIAL_CONTRIBUTIONS_RATE = 0.172  # 17.2% CSG/CRDS
    
    # Micro regime thresholds
    MICRO_BIC_THRESHOLD = 77700       # Meublé
    MICRO_FONCIER_THRESHOLD = 15000   # Nu
    
    # Micro abatements
    MICRO_BIC_ABATEMENT = 0.50        # 50% for standard furnished
    MICRO_BIC_TOURISM_ABATEMENT = 0.71  # 71% for classified tourism
    MICRO_FONCIER_ABATEMENT = 0.30    # 30% for unfurnished
    
    # LMP thresholds
    LMP_REVENUE_THRESHOLD = 23000     # 23k€ recettes annuelles
    
    def __init__(
        self,
        tmi: float = 0.30,  # Tranche Marginale d'Imposition
        other_household_income: float = 0.0,  # For LMP test
    ):
        self.tmi = tmi
        self.other_income = other_household_income
    
    def calculate_micro_tax(
        self,
        gross_revenue: float,
        lease_type: LeaseType,
        is_classified_tourism: bool = False
    ) -> FiscalScenario:
        """Calculate tax under Micro regime."""
        
        # Determine abatement rate
        if lease_type == LeaseType.UNFURNISHED:
            abatement = self.MICRO_FONCIER_ABATEMENT
            regime_name = FiscalRegime.MICRO_FONCIER.value
        elif lease_type == LeaseType.AIRBNB and is_classified_tourism:
            abatement = self.MICRO_BIC_TOURISM_ABATEMENT
            regime_name = "Micro-BIC (Tourisme)"
        else:
            abatement = self.MICRO_BIC_ABATEMENT
            regime_name = FiscalRegime.MICRO_BIC.value
        
        # Taxable income after abatement
        taxable_income = gross_revenue * (1 - abatement)
        
        # Taxes (only if positive)
        taxable_base = max(0, taxable_income)
        income_tax = taxable_base * self.tmi
        social_contributions = taxable_base * self.SOCIAL_CONTRIBUTIONS_RATE
        total_tax = income_tax + social_contributions
        
        net_after_tax = gross_revenue - total_tax
        effective_rate = (total_tax / gross_revenue * 100) if gross_revenue > 0 else 0
        
        return FiscalScenario(
            regime=regime_name,
            gross_revenue=gross_revenue,
            taxable_income=taxable_income,
            income_tax=income_tax,
            social_contributions=social_contributions,
            total_tax=total_tax,
            net_after_tax=net_after_tax,
            effective_rate=effective_rate
        )
    
    def calculate_reel_tax(
        self,
        gross_revenue: float,
        deductible_expenses: float,
        depreciation: float,
        lease_type: LeaseType
    ) -> FiscalScenario:
        """Calculate tax under Réel regime."""
        
        if lease_type == LeaseType.UNFURNISHED:
            regime_name = FiscalRegime.REVENU_FONCIER.value
            # Nu: no depreciation, deficit can offset other income (up to 10,700€)
            taxable_income = gross_revenue - deductible_expenses
            # Deficit foncier rules simplified here
        else:
            regime_name = FiscalRegime.LMNP_REEL.value
            # LMNP: depreciation cannot create deficit
            net_before_depreciation = gross_revenue - deductible_expenses
            if net_before_depreciation > 0:
                taxable_income = max(0, net_before_depreciation - depreciation)
            else:
                taxable_income = net_before_depreciation  # Already negative, depreciation not used
        
        # Taxes
        taxable_base = max(0, taxable_income)
        income_tax = taxable_base * self.tmi
        social_contributions = taxable_base * self.SOCIAL_CONTRIBUTIONS_RATE
        total_tax = income_tax + social_contributions
        
        net_after_tax = gross_revenue - deductible_expenses - total_tax
        effective_rate = (total_tax / gross_revenue * 100) if gross_revenue > 0 else 0
        
        return FiscalScenario(
            regime=regime_name,
            gross_revenue=gross_revenue,
            taxable_income=taxable_income,
            income_tax=income_tax,
            social_contributions=social_contributions,
            total_tax=total_tax,
            net_after_tax=net_after_tax,
            effective_rate=effective_rate
        )
    
    def compare_regimes(
        self,
        gross_revenue: float,
        deductible_expenses: float,
        depreciation: float,
        lease_type: LeaseType,
        holding_years: int = 10,
        is_classified_tourism: bool = False
    ) -> FiscalComparison:
        """
        Compare Micro vs Réel regimes.
        
        Args:
            gross_revenue: Annual rental income
            deductible_expenses: Annual deductible costs (interest, fees, taxes, etc.)
            depreciation: Annual depreciation (property + furnishing)
            lease_type: Type of rental
            holding_years: Investment duration
            is_classified_tourism: For Airbnb - classified tourism rental
        
        Returns:
            FiscalComparison with recommendation
        """
        
        micro = self.calculate_micro_tax(gross_revenue, lease_type, is_classified_tourism)
        reel = self.calculate_reel_tax(gross_revenue, deductible_expenses, depreciation, lease_type)
        
        # Determine recommendation
        annual_savings = micro.total_tax - reel.total_tax
        savings_over_period = annual_savings * holding_years
        
        if annual_savings > 0:
            recommended = reel.regime
            reason = self._get_reel_reason(micro, reel, lease_type)
        elif annual_savings < -100:  # Micro significantly better
            recommended = micro.regime
            reason = self._get_micro_reason(micro, reel, lease_type)
        else:
            # Similar - recommend Micro for simplicity
            recommended = micro.regime
            reason = self._get_similar_reason(lease_type)
        
        return FiscalComparison(
            recommended=recommended,
            micro=micro,
            reel=reel,
            annual_savings=abs(annual_savings),
            savings_over_period=abs(savings_over_period),
            recommendation_reason=reason
        )
    
    def _get_reel_reason(self, micro: FiscalScenario, reel: FiscalScenario, lease_type: LeaseType) -> str:
        """Generate reason for Réel recommendation."""
        if lease_type == LeaseType.UNFURNISHED:
            return "reel_deductions_higher"
        else:
            if reel.taxable_income == 0:
                return "reel_zero_tax_depreciation"
            else:
                return "reel_lower_tax"
    
    def _get_micro_reason(self, micro: FiscalScenario, reel: FiscalScenario, lease_type: LeaseType) -> str:
        """Generate reason for Micro recommendation."""
        if lease_type == LeaseType.UNFURNISHED:
            return "micro_foncier_simple"
        else:
            return "micro_bic_abatement_sufficient"
    
    def _get_similar_reason(self, lease_type: LeaseType) -> str:
        """Generate reason when regimes are similar."""
        return "micro_simpler_similar_result"
    
    def check_lmp_status(self, annual_revenue: float) -> Dict:
        """
        Check if qualifies as LMP (Loueur Meublé Professionnel).
        
        LMP conditions (cumulative):
        1. Recettes > 23 000€/an
        2. Recettes > autres revenus du foyer
        
        Returns:
            Dict with status and implications
        """
        condition_1 = annual_revenue > self.LMP_REVENUE_THRESHOLD
        condition_2 = annual_revenue > self.other_income if self.other_income > 0 else False
        
        is_lmp = condition_1 and condition_2
        
        return {
            "is_lmp": is_lmp,
            "revenue_threshold_met": condition_1,
            "income_condition_met": condition_2,
            "annual_revenue": annual_revenue,
            "threshold": self.LMP_REVENUE_THRESHOLD,
            "implications": self._get_lmp_implications(is_lmp)
        }
    
    def _get_lmp_implications(self, is_lmp: bool) -> Dict:
        """Get LMP vs LMNP implications."""
        if is_lmp:
            return {
                "social_charges": "Cotisations SSI (~40% du bénéfice)",
                "deficit": "Imputable sur revenu global sans limite",
                "plus_value": "Régime pro (exonération possible si >5 ans)",
                "ifi": "Exonéré si activité principale",
            }
        else:
            return {
                "social_charges": "Prélèvements sociaux 17.2%",
                "deficit": "Reportable sur BIC meublés uniquement",
                "plus_value": "Régime particuliers (abattements durée)",
                "ifi": "Inclus dans l'assiette IFI",
            }
    
    def check_micro_eligibility(self, annual_revenue: float, lease_type: LeaseType) -> Dict:
        """Check if Micro regime is available."""
        if lease_type == LeaseType.UNFURNISHED:
            threshold = self.MICRO_FONCIER_THRESHOLD
            regime = "Micro-Foncier"
        else:
            threshold = self.MICRO_BIC_THRESHOLD
            regime = "Micro-BIC"
        
        eligible = annual_revenue <= threshold
        
        return {
            "eligible": eligible,
            "regime": regime,
            "threshold": threshold,
            "annual_revenue": annual_revenue,
            "margin": threshold - annual_revenue if eligible else 0
        }


# === DISPLAY HELPERS ===

def get_regime_recommendation_text(comparison: FiscalComparison, lang: str = "fr") -> Dict:
    """Get formatted recommendation text."""
    
    reasons = {
        "reel_zero_tax_depreciation": {
            "fr": "L'amortissement LMNP permet de réduire l'impôt à zéro",
            "en": "LMNP depreciation reduces tax to zero"
        },
        "reel_lower_tax": {
            "fr": "Les charges réelles dépassent l'abattement forfaitaire",
            "en": "Actual expenses exceed flat-rate deduction"
        },
        "reel_deductions_higher": {
            "fr": "Les déductions réelles sont plus avantageuses",
            "en": "Real deductions are more advantageous"
        },
        "micro_bic_abatement_sufficient": {
            "fr": "L'abattement de 50% couvre vos charges",
            "en": "The 50% deduction covers your expenses"
        },
        "micro_foncier_simple": {
            "fr": "Micro-Foncier plus simple, résultat similaire",
            "en": "Micro-Foncier simpler, similar result"
        },
        "micro_simpler_similar_result": {
            "fr": "Régimes équivalents - Micro plus simple",
            "en": "Similar regimes - Micro is simpler"
        },
    }
    
    reason_key = comparison.recommendation_reason
    reason_text = reasons.get(reason_key, {}).get(lang, reason_key)
    
    return {
        "recommended": comparison.recommended,
        "reason": reason_text,
        "annual_savings": comparison.annual_savings,
        "total_savings": comparison.savings_over_period,
    }


def get_lmp_alert(lmp_status: Dict, lang: str = "fr") -> Optional[Dict]:
    """Get LMP status alert if relevant."""
    
    if not lmp_status["revenue_threshold_met"]:
        return None  # Not even close to LMP
    
    if lmp_status["is_lmp"]:
        return {
            "type": "warning",
            "icon": "⚠️",
            "title": "Statut LMP" if lang == "fr" else "LMP Status",
            "message": (
                "Vous êtes Loueur Meublé Professionnel. Cotisations SSI applicables (~40% du bénéfice)."
                if lang == "fr" else
                "You qualify as Professional Furnished Landlord. SSI contributions apply (~40% of profit)."
            )
        }
    else:
        margin = lmp_status["threshold"] - lmp_status["annual_revenue"]
        if margin < 5000:
            return {
                "type": "info",
                "icon": "ℹ️",
                "title": "Proche du seuil LMP" if lang == "fr" else "Near LMP threshold",
                "message": (
                    f"Vous êtes à {margin:,.0f}€ du seuil LMP (23 000€). Surveillez vos recettes."
                    if lang == "fr" else
                    f"You are €{margin:,.0f} from LMP threshold (€23,000). Monitor your revenue."
                )
            }
    
    return None
