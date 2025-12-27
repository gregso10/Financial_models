'use client';
import { useLanguage } from '@/lib/i18n';

interface LMPStatusType {
  is_lmp: boolean;
  revenue_threshold_met: boolean;
  income_condition_met: boolean;
  annual_revenue: number;
  threshold: number;
  implications?: Record<string, string>;
  implications_fr?: Record<string, string>;
  implications_en?: Record<string, string>;
}

interface Props {
  status: LMPStatusType;
}

const t = {
  fr: {
    title: 'Statut LMP',
    lmp: 'Loueur Meublé Professionnel',
    lmnp: 'Loueur Meublé Non Professionnel',
    revenue: 'Revenus locatifs',
    threshold: 'Seuil LMP',
    conditions: 'Conditions',
    revenueCondition: 'Recettes > 23 000 €',
    incomeCondition: 'Recettes > autres revenus',
    implications: 'Implications fiscales',
    socialCharges: 'Cotisations sociales',
    deficit: 'Déficit',
    capitalGains: 'Plus-values',
    ifi: 'IFI',
  },
  en: {
    title: 'LMP Status',
    lmp: 'Professional Furnished Landlord',
    lmnp: 'Non-Professional Furnished Landlord',
    revenue: 'Rental revenue',
    threshold: 'LMP threshold',
    conditions: 'Conditions',
    revenueCondition: 'Revenue > €23,000',
    incomeCondition: 'Revenue > other income',
    implications: 'Tax implications',
    socialCharges: 'Social contributions',
    deficit: 'Deficit',
    capitalGains: 'Capital gains',
    ifi: 'Wealth tax (IFI)',
  }
};

export default function LMPStatus({ status }: Props) {
  const { lang } = useLanguage();
  const labels = t[lang];
  
  // Handle different API response formats
  const implications = 
    (lang === 'fr' ? status.implications_fr : status.implications_en) 
    || status.implications 
    || {};
  
  const fmt = (n: number) => new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 0 }).format(n);

  return (
    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
      <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
        {status.is_lmp ? '🏢' : '🏠'} {labels.title}
      </h3>
      
      {/* Status Badge */}
      <div className={`inline-block px-3 py-1 rounded-full text-sm font-medium mb-4 ${
        status.is_lmp 
          ? 'bg-orange-900/50 text-orange-300 border border-orange-700'
          : 'bg-blue-900/50 text-blue-300 border border-blue-700'
      }`}>
        {status.is_lmp ? labels.lmp : labels.lmnp}
      </div>
      
      {/* Revenue Info */}
      <div className="grid grid-cols-2 gap-3 mb-4 text-sm">
        <div>
          <span className="text-gray-400">{labels.revenue}:</span>
          <span className="text-white ml-2 font-medium">{fmt(status.annual_revenue)} €</span>
        </div>
        <div>
          <span className="text-gray-400">{labels.threshold}:</span>
          <span className="text-white ml-2 font-medium">{fmt(status.threshold)} €</span>
        </div>
      </div>
      
      {/* Conditions */}
      <div className="mb-4">
        <p className="text-gray-400 text-sm mb-2">{labels.conditions}:</p>
        <div className="flex gap-4 text-sm">
          <div className="flex items-center gap-2">
            {status.revenue_threshold_met ? (
              <span className="text-green-400">✓</span>
            ) : (
              <span className="text-gray-500">✗</span>
            )}
            <span className={status.revenue_threshold_met ? 'text-green-300' : 'text-gray-500'}>
              {labels.revenueCondition}
            </span>
          </div>
          <div className="flex items-center gap-2">
            {status.income_condition_met ? (
              <span className="text-green-400">✓</span>
            ) : (
              <span className="text-gray-500">✗</span>
            )}
            <span className={status.income_condition_met ? 'text-green-300' : 'text-gray-500'}>
              {labels.incomeCondition}
            </span>
          </div>
        </div>
      </div>
      
      {/* Implications */}
      {Object.keys(implications).length > 0 && (
        <div>
          <p className="text-gray-400 text-sm mb-2">{labels.implications}:</p>
          <div className="space-y-2 text-sm">
            {Object.entries(implications).map(([key, value]) => (
              <div key={key} className="flex justify-between">
                <span className="text-gray-400 capitalize">
                  {key === 'social_charges' ? labels.socialCharges :
                   key === 'deficit' ? labels.deficit :
                   key === 'plus_value' ? labels.capitalGains :
                   key === 'ifi' ? labels.ifi : key}
                </span>
                <span className="text-gray-200 text-right max-w-[60%]">{value}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}