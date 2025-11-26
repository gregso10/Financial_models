# In file: scripts/_11_taxes.py

from dataclasses import dataclass
from typing import Dict
from ._1_model_params import ModelParameters

class Taxes:
    """
    Gère la fiscalité française (revenus locatifs et plus-values).
    Sources: règles_impots.txt et règles générales des plus-values immobilières.
    """

    def __init__(self, params: ModelParameters):
        self.params = params
        self.social_contributions_rate = 0.172  # 17.2% CSG/CRDS

    def _get_micro_abatement_rate(self, lease_type: str) -> float:
        """Retourne le taux d'abattement Micro selon le type de bail."""
        if lease_type == "unfurnished_3yr":
            return 0.30 # Micro-Foncier
        elif lease_type == "airbnb":
            return 0.71 # Meublé Tourisme classé / Chambre d'hôte (hypothèse favorable)
        else:
            return 0.50 # Micro-BIC standard (Meublé à l'année)

    def calculate_tax_details(self, 
                              gross_revenue: float, 
                              deductible_expenses: float, 
                              depreciation: float, 
                              lease_type: str) -> Dict[str, float]:
        """Calcul l'impôt sur les revenus locatifs annuels."""
        regime = self.params.fiscal_regime
        taxable_income = 0.0

        # --- 1. Calcul de l'assiette (Revenus Locatifs) ---
        if "Micro" in regime:
            abatement = self._get_micro_abatement_rate(lease_type)
            taxable_income = gross_revenue * (1 - abatement)
        elif "Réel" in regime:
            # Revenu Net = Loyers - Charges Réelles
            net_operating_result = gross_revenue - deductible_expenses
            
            if "LMNP" in regime:
                # En LMNP Réel, l'amortissement ne peut pas créer de déficit
                # Il réduit le bénéfice jusqu'à 0. L'excédent est reportable (simplifié ici à 0)
                taxable_income = max(0.0, net_operating_result - depreciation)
            else:
                # Revenu Foncier Réel (Nu) : Pas d'amortissement, déficit imputable sur revenu global (limite 10k7)
                taxable_income = net_operating_result

        # --- 2. Calcul des Impôts ---
        # On ne calcule l'impôt à payer que si le résultat est positif
        tax_base = max(0.0, taxable_income)
        
        income_tax = tax_base * self.params.personal_income_tax_bracket
        social_contributions = tax_base * self.social_contributions_rate

        return {
            "taxable_income": taxable_income,
            "income_tax": income_tax,
            "social_contributions": social_contributions,
            "total_taxes": income_tax + social_contributions
        }

    def calculate_capital_gain_tax(self, selling_price: float, purchase_price: float, years_held: int) -> Dict[str, float]:
        """
        Calcul l'impôt sur la plus-value immobilière à la revente.
        Règle Spécifique Utilisateur : Exonération totale si détention >= 25 ans.
        Sinon : Application des abattements légaux standards (IR et PS).
        """
        # Règle utilisateur : Exonération totale après 25 ans
        if years_held >= 25:
            return {
                "gross_capital_gain": max(0, selling_price - purchase_price),
                "net_taxable_gain_ir": 0.0,
                "net_taxable_gain_ps": 0.0,
                "tax_ir": 0.0,
                "tax_ps": 0.0,
                "total_exit_tax": 0.0
            }

        # --- Estimer le prix d'acquisition corrigé ---
        # Forfait travaux 15% (si détenu > 5 ans) + Forfait frais acquisition 7.5%
        acquisition_costs_flat = purchase_price * 0.075
        works_flat = purchase_price * 0.15 if years_held > 5 else 0.0
        
        adjusted_purchase_price = purchase_price + acquisition_costs_flat + works_flat
        gross_capital_gain = max(0, selling_price - adjusted_purchase_price)

        if gross_capital_gain == 0:
             return {"total_exit_tax": 0.0, "gross_capital_gain": 0.0}

        # --- Calcul des Abattements (Durée de détention) ---
        # 1. Impôt sur le Revenu (IR) - Taux 19%
        # 6-21 ans : 6%/an, 22 ans : 4%
        if years_held < 6:
            abatement_ir = 0.0
        elif years_held <= 21:
            abatement_ir = (years_held - 5) * 0.06
        else: 
            abatement_ir = 1.0 # Exonéré IR après 22 ans (règle FR standard)

        # 2. Prélèvements Sociaux (PS) - Taux 17.2%
        # 6-21 ans : 1.65%/an, 22 ans : 1.6%, 23-30 ans : 9%
        if years_held < 6:
            abatement_ps = 0.0
        elif years_held <= 21:
            abatement_ps = (years_held - 5) * 0.0165
        elif years_held == 22:
            abatement_ps = (16 * 0.0165) + 0.0160
        else:
            # Pour < 25 ans (car >= 25 est géré par le if au début)
            abatement_ps = (16 * 0.0165) + 0.0160 + ((years_held - 22) * 0.09)

        # --- Calcul Final ---
        taxable_base_ir = gross_capital_gain * (1 - abatement_ir)
        taxable_base_ps = gross_capital_gain * (1 - abatement_ps)

        tax_ir = taxable_base_ir * 0.19
        tax_ps = taxable_base_ps * self.social_contributions_rate

        return {
            "gross_capital_gain": gross_capital_gain,
            "net_taxable_gain_ir": taxable_base_ir,
            "net_taxable_gain_ps": taxable_base_ps,
            "tax_ir": tax_ir,
            "tax_ps": tax_ps,
            "total_exit_tax": tax_ir + tax_ps
        }