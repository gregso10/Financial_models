'use client';
import { createContext, useContext, useState, ReactNode } from 'react';

type Lang = 'fr' | 'en';

const translations = {
  // Navigation & Headers
  app_title: { fr: '🏠 Immo Invest', en: '🏠 Immo Invest' },
  simulator_title: { fr: 'Simulateur Investissement Locatif', en: 'Rental Investment Simulator' },
  landing_subtitle: { fr: 'Analysez la rentabilité de vos investissements immobiliers en quelques clics', en: 'Analyze the profitability of your real estate investments in a few clicks' },
  start_analysis: { fr: "Commencer l'analyse →", en: 'Start analysis →' },
  
  // Form Labels
  parameters: { fr: 'Paramètres', en: 'Parameters' },
  results: { fr: 'Résultats', en: 'Results' },
  location: { fr: 'Localisation', en: 'Location' },
  purchase_price: { fr: "Prix d'achat (€)", en: 'Purchase Price (€)' },
  surface: { fr: 'Surface (m²)', en: 'Surface (sqm)' },
  monthly_rent: { fr: 'Loyer mensuel (€)', en: 'Monthly Rent (€)' },
  down_payment: { fr: 'Apport (€)', en: 'Down Payment (€)' },
  loan_rate: { fr: "Taux d'emprunt (%)", en: 'Loan Rate (%)' },
  analyze: { fr: '🔍 Analyser', en: '🔍 Analyze' },
  calculating: { fr: 'Calcul en cours...', en: 'Calculating...' },
  fill_form: { fr: 'Remplissez le formulaire et cliquez Analyser', en: 'Fill the form and click Analyze' },
  
  // Results
  good_investment: { fr: '✅ Bon investissement', en: '✅ Good investment' },
  poor_return: { fr: '⚠️ Rentabilité faible', en: '⚠️ Poor return' },
  irr: { fr: 'TRI (IRR)', en: 'IRR' },
  npv: { fr: 'VAN (NPV)', en: 'NPV' },
  monthly_cashflow: { fr: 'Cash-flow mensuel', en: 'Monthly Cash Flow' },
  equity_multiple: { fr: 'Multiple', en: 'Multiple' },
  cash_on_cash: { fr: 'Cash-on-Cash (A1)', en: 'Cash-on-Cash (Y1)' },
  
  // Exit Scenario
  exit_scenario: { fr: 'Scénario de sortie', en: 'Exit Scenario' },
  years: { fr: 'ans', en: 'years' },
  exit_value: { fr: 'Valeur de revente', en: 'Exit Value' },
  capital_gain: { fr: 'Plus-value', en: 'Capital Gain' },
  selling_costs: { fr: 'Frais de vente', en: 'Selling Costs' },
  capital_gains_tax: { fr: 'Impôt plus-value', en: 'Capital Gains Tax' },
  remaining_loan: { fr: 'Emprunt restant', en: 'Remaining Loan' },
  net_proceeds: { fr: 'Produit net', en: 'Net Proceeds' },
  
  // Charts
  annual_cashflow: { fr: 'Cash-flow annuel', en: 'Annual Cash Flow' },
  cumulative_cashflow: { fr: 'Cash-flow cumulé', en: 'Cumulative Cash Flow' },
  year: { fr: 'Année', en: 'Year' },
  
  // Fiscal
  fiscal_optimization: { fr: '📋 Optimisation Fiscale', en: '📋 Tax Optimization' },
  recommended_regime: { fr: 'Régime recommandé', en: 'Recommended Regime' },
  taxable_income: { fr: 'Revenu imposable', en: 'Taxable Income' },
  total_tax: { fr: 'Impôt total', en: 'Total Tax' },
  annual_savings: { fr: 'Économie annuelle', en: 'Annual Savings' },
  
  // Alerts
  alerts: { fr: '🚦 Alertes', en: '🚦 Alerts' },
  
  // Errors
  connection_error: { fr: 'Erreur de connexion au serveur', en: 'Server connection error' },
  unknown_error: { fr: 'Erreur inconnue', en: 'Unknown error' },
};

type TranslationKey = keyof typeof translations;

interface I18nContextType {
  lang: Lang;
  setLang: (lang: Lang) => void;
  t: (key: TranslationKey) => string;
}

const I18nContext = createContext<I18nContextType | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>('fr');
  
  const t = (key: TranslationKey): string => {
    return translations[key]?.[lang] || key;
  };
  
  return (
    <I18nContext.Provider value={{ lang, setLang, t }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  const context = useContext(I18nContext);
  if (!context) throw new Error('useI18n must be used within I18nProvider');
  return context;
}

export function LanguageToggle() {
  const { lang, setLang } = useI18n();
  return (
    <button
      onClick={() => setLang(lang === 'fr' ? 'en' : 'fr')}
      className="px-3 py-1 text-sm bg-gray-700 hover:bg-gray-600 rounded-lg transition"
    >
      {lang === 'fr' ? '🇬🇧 EN' : '🇫🇷 FR'}
    </button>
  );
}