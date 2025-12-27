'use client';
import { useState, useEffect } from 'react';
import { getLocations, getLocationDefaults, ExpertSimulationRequest, LeaseType } from '@/lib/api';
import { useLanguage } from '@/lib/i18n';

interface Props {
  onSubmit: (data: ExpertSimulationRequest) => void;
  loading: boolean;
}

const t = {
  fr: {
    // Sections
    property: 'Bien immobilier',
    financing: 'Financement',
    rental: 'Location',
    expenses: 'Charges',
    fiscal: 'Fiscalité',
    exit: 'Sortie',
    
    // Property
    location: 'Ville',
    price: 'Prix d\'achat (€)',
    surface: 'Surface (m²)',
    agencyFees: 'Frais d\'agence (%)',
    notaryFees: 'Frais de notaire (%)',
    renovation: 'Travaux (€)',
    furnishing: 'Ameublement (€)',
    
    // Financing
    apport: 'Apport (€)',
    loanRate: 'Taux d\'emprunt (%)',
    loanDuration: 'Durée (années)',
    loanInsurance: 'Assurance emprunteur (%)',
    
    // Rental
    leaseType: 'Type de bail',
    furnished1yr: 'Meublé 1 an',
    unfurnished3yr: 'Nu 3 ans',
    airbnb: 'Airbnb',
    monthlyRent: 'Loyer mensuel (€)',
    dailyRate: 'Tarif journalier (€)',
    vacancy: 'Vacance locative (%)',
    occupancy: 'Taux d\'occupation (%)',
    rentGrowth: 'Croissance loyer (%/an)',
    
    // Expenses
    propertyTax: 'Taxe foncière (€/an)',
    condoFees: 'Charges copro (€/mois)',
    insurance: 'Assurance PNO (€/an)',
    maintenance: 'Entretien (% loyer)',
    management: 'Gestion locative (%)',
    
    // Fiscal
    tmi: 'TMI (%)',
    
    // Exit
    holdingYears: 'Durée détention (ans)',
    priceGrowth: 'Croissance prix (%/an)',
    exitFees: 'Frais de vente (%)',
    
    // Actions
    analyze: 'Analyser',
    analyzing: 'Calcul en cours...',
  },
  en: {
    property: 'Property',
    financing: 'Financing',
    rental: 'Rental',
    expenses: 'Expenses',
    fiscal: 'Tax',
    exit: 'Exit',
    
    location: 'City',
    price: 'Purchase price (€)',
    surface: 'Surface (m²)',
    agencyFees: 'Agency fees (%)',
    notaryFees: 'Notary fees (%)',
    renovation: 'Renovation (€)',
    furnishing: 'Furnishing (€)',
    
    apport: 'Down payment (€)',
    loanRate: 'Loan rate (%)',
    loanDuration: 'Duration (years)',
    loanInsurance: 'Loan insurance (%)',
    
    leaseType: 'Lease type',
    furnished1yr: 'Furnished 1yr',
    unfurnished3yr: 'Unfurnished 3yr',
    airbnb: 'Airbnb',
    monthlyRent: 'Monthly rent (€)',
    dailyRate: 'Daily rate (€)',
    vacancy: 'Vacancy rate (%)',
    occupancy: 'Occupancy rate (%)',
    rentGrowth: 'Rent growth (%/yr)',
    
    propertyTax: 'Property tax (€/yr)',
    condoFees: 'Condo fees (€/mo)',
    insurance: 'PNO insurance (€/yr)',
    maintenance: 'Maintenance (% rent)',
    management: 'Management fee (%)',
    
    tmi: 'Tax bracket (%)',
    
    holdingYears: 'Holding period (yrs)',
    priceGrowth: 'Price growth (%/yr)',
    exitFees: 'Selling fees (%)',
    
    analyze: 'Analyze',
    analyzing: 'Calculating...',
  }
};

export default function ExpertSimulatorForm({ onSubmit, loading }: Props) {
  const { lang } = useLanguage();
  const labels = t[lang];
  
  const [locations, setLocations] = useState<string[]>([]);
  const [form, setForm] = useState<ExpertSimulationRequest>({
    location: 'Lyon',
    property_price: 250000,
    surface_sqm: 45,
    agency_fees_pct: 0,
    notary_fees_pct: 0.08,
    initial_renovation: 0,
    furnishing_costs: 9000,
    apport: 50000,
    loan_rate: 0.035,
    loan_duration_years: 20,
    loan_insurance_rate: 0.003,
    lease_type: 'furnished_1yr',
    monthly_rent: 900,
    daily_rate: 80,
    vacancy_rate: 0.05,
    occupancy_rate: 0.70,
    rent_growth_rate: 0.015,
    property_tax_yearly: 800,
    condo_fees_monthly: 100,
    pno_insurance_yearly: 150,
    maintenance_pct: 0.05,
    management_fee_pct: 0.07,
    tmi: 0.30,
    holding_years: 10,
    property_growth_rate: 0.02,
    exit_fees_pct: 0.05,
  });

  useEffect(() => {
    getLocations().then(setLocations).catch(console.error);
  }, []);

  // Update defaults when location changes
  useEffect(() => {
    getLocationDefaults(form.location).then((defaults) => {
      if (defaults && !('error' in defaults)) {
        setForm(prev => ({
          ...prev,
          notary_fees_pct: defaults.notary_pct || prev.notary_fees_pct,
          property_tax_yearly: (defaults.property_tax_per_sqm || 0) * prev.surface_sqm,
          condo_fees_monthly: (defaults.condo_fees_per_sqm || 0) * prev.surface_sqm,
          pno_insurance_yearly: defaults.pno_insurance || prev.pno_insurance_yearly,
          vacancy_rate: defaults.vacancy_rate || prev.vacancy_rate,
          property_growth_rate: defaults.price_growth || prev.property_growth_rate,
          management_fee_pct: defaults.management_fee_pct || prev.management_fee_pct,
        }));
      }
    }).catch(console.error);
  }, [form.location]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(form);
  };

  const update = <K extends keyof ExpertSimulationRequest>(
    field: K, 
    value: ExpertSimulationRequest[K]
  ) => {
    setForm(prev => ({ ...prev, [field]: value }));
  };

  const inputClass = "w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500";
  const labelClass = "block text-gray-400 text-sm mb-1";
  const sectionClass = "space-y-3";
  const sectionHeaderClass = "text-lg font-semibold text-blue-400 border-b border-gray-700 pb-2 mb-3";

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* PROPERTY */}
      <div className={sectionClass}>
        <h3 className={sectionHeaderClass}>🏠 {labels.property}</h3>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className={labelClass}>{labels.location}</label>
            <select
              value={form.location}
              onChange={(e) => update('location', e.target.value)}
              className={inputClass}
            >
              {locations.map(loc => (
                <option key={loc} value={loc}>{loc}</option>
              ))}
            </select>
          </div>
          <div>
            <label className={labelClass}>{labels.price}</label>
            <input
              type="number"
              value={form.property_price}
              onChange={(e) => update('property_price', +e.target.value)}
              className={inputClass}
            />
          </div>
          <div>
            <label className={labelClass}>{labels.surface}</label>
            <input
              type="number"
              value={form.surface_sqm}
              onChange={(e) => update('surface_sqm', +e.target.value)}
              className={inputClass}
            />
          </div>
          <div>
            <label className={labelClass}>{labels.notaryFees}</label>
            <input
              type="number"
              step="0.01"
              value={(form.notary_fees_pct || 0) * 100}
              onChange={(e) => update('notary_fees_pct', +e.target.value / 100)}
              className={inputClass}
            />
          </div>
          <div>
            <label className={labelClass}>{labels.renovation}</label>
            <input
              type="number"
              value={form.initial_renovation}
              onChange={(e) => update('initial_renovation', +e.target.value)}
              className={inputClass}
            />
          </div>
          <div>
            <label className={labelClass}>{labels.furnishing}</label>
            <input
              type="number"
              value={form.furnishing_costs}
              onChange={(e) => update('furnishing_costs', +e.target.value)}
              className={inputClass}
            />
          </div>
        </div>
      </div>

      {/* FINANCING */}
      <div className={sectionClass}>
        <h3 className={sectionHeaderClass}>💰 {labels.financing}</h3>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className={labelClass}>{labels.apport}</label>
            <input
              type="number"
              value={form.apport}
              onChange={(e) => update('apport', +e.target.value)}
              className={inputClass}
            />
          </div>
          <div>
            <label className={labelClass}>{labels.loanRate}</label>
            <input
              type="number"
              step="0.1"
              value={(form.loan_rate || 0) * 100}
              onChange={(e) => update('loan_rate', +e.target.value / 100)}
              className={inputClass}
            />
          </div>
          <div>
            <label className={labelClass}>{labels.loanDuration}</label>
            <input
              type="number"
              value={form.loan_duration_years}
              onChange={(e) => update('loan_duration_years', +e.target.value)}
              className={inputClass}
            />
          </div>
          <div>
            <label className={labelClass}>{labels.loanInsurance}</label>
            <input
              type="number"
              step="0.01"
              value={(form.loan_insurance_rate || 0) * 100}
              onChange={(e) => update('loan_insurance_rate', +e.target.value / 100)}
              className={inputClass}
            />
          </div>
        </div>
      </div>

      {/* RENTAL */}
      <div className={sectionClass}>
        <h3 className={sectionHeaderClass}>🔑 {labels.rental}</h3>
        <div className="grid grid-cols-2 gap-3">
          <div className="col-span-2">
            <label className={labelClass}>{labels.leaseType}</label>
            <div className="flex gap-2">
              {(['furnished_1yr', 'unfurnished_3yr', 'airbnb'] as LeaseType[]).map((type) => (
                <button
                  key={type}
                  type="button"
                  onClick={() => update('lease_type', type)}
                  className={`flex-1 py-2 px-3 rounded-lg text-sm transition ${
                    form.lease_type === type
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  {type === 'furnished_1yr' ? labels.furnished1yr : 
                   type === 'unfurnished_3yr' ? labels.unfurnished3yr : labels.airbnb}
                </button>
              ))}
            </div>
          </div>
          
          {form.lease_type === 'airbnb' ? (
            <>
              <div>
                <label className={labelClass}>{labels.dailyRate}</label>
                <input
                  type="number"
                  value={form.daily_rate}
                  onChange={(e) => update('daily_rate', +e.target.value)}
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>{labels.occupancy}</label>
                <input
                  type="number"
                  step="1"
                  value={(form.occupancy_rate || 0.7) * 100}
                  onChange={(e) => update('occupancy_rate', +e.target.value / 100)}
                  className={inputClass}
                />
              </div>
            </>
          ) : (
            <>
              <div>
                <label className={labelClass}>{labels.monthlyRent}</label>
                <input
                  type="number"
                  value={form.monthly_rent}
                  onChange={(e) => update('monthly_rent', +e.target.value)}
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>{labels.vacancy}</label>
                <input
                  type="number"
                  step="1"
                  value={(form.vacancy_rate || 0.05) * 100}
                  onChange={(e) => update('vacancy_rate', +e.target.value / 100)}
                  className={inputClass}
                />
              </div>
            </>
          )}
          <div>
            <label className={labelClass}>{labels.rentGrowth}</label>
            <input
              type="number"
              step="0.1"
              value={(form.rent_growth_rate || 0) * 100}
              onChange={(e) => update('rent_growth_rate', +e.target.value / 100)}
              className={inputClass}
            />
          </div>
        </div>
      </div>

      {/* EXPENSES */}
      <div className={sectionClass}>
        <h3 className={sectionHeaderClass}>📋 {labels.expenses}</h3>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className={labelClass}>{labels.propertyTax}</label>
            <input
              type="number"
              value={form.property_tax_yearly}
              onChange={(e) => update('property_tax_yearly', +e.target.value)}
              className={inputClass}
            />
          </div>
          <div>
            <label className={labelClass}>{labels.condoFees}</label>
            <input
              type="number"
              value={form.condo_fees_monthly}
              onChange={(e) => update('condo_fees_monthly', +e.target.value)}
              className={inputClass}
            />
          </div>
          <div>
            <label className={labelClass}>{labels.insurance}</label>
            <input
              type="number"
              value={form.pno_insurance_yearly}
              onChange={(e) => update('pno_insurance_yearly', +e.target.value)}
              className={inputClass}
            />
          </div>
          <div>
            <label className={labelClass}>{labels.maintenance}</label>
            <input
              type="number"
              step="1"
              value={(form.maintenance_pct || 0) * 100}
              onChange={(e) => update('maintenance_pct', +e.target.value / 100)}
              className={inputClass}
            />
          </div>
          <div>
            <label className={labelClass}>{labels.management}</label>
            <input
              type="number"
              step="1"
              value={(form.management_fee_pct || 0) * 100}
              onChange={(e) => update('management_fee_pct', +e.target.value / 100)}
              className={inputClass}
            />
          </div>
        </div>
      </div>

      {/* FISCAL + EXIT */}
      <div className="grid grid-cols-2 gap-6">
        <div className={sectionClass}>
          <h3 className={sectionHeaderClass}>🧾 {labels.fiscal}</h3>
          <div>
            <label className={labelClass}>{labels.tmi}</label>
            <select
              value={form.tmi}
              onChange={(e) => update('tmi', +e.target.value)}
              className={inputClass}
            >
              <option value={0}>0%</option>
              <option value={0.11}>11%</option>
              <option value={0.30}>30%</option>
              <option value={0.41}>41%</option>
              <option value={0.45}>45%</option>
            </select>
          </div>
        </div>

        <div className={sectionClass}>
          <h3 className={sectionHeaderClass}>🚪 {labels.exit}</h3>
          <div className="space-y-3">
            <div>
              <label className={labelClass}>{labels.holdingYears}</label>
              <input
                type="number"
                value={form.holding_years}
                onChange={(e) => update('holding_years', +e.target.value)}
                className={inputClass}
              />
            </div>
            <div>
              <label className={labelClass}>{labels.priceGrowth}</label>
              <input
                type="number"
                step="0.1"
                value={(form.property_growth_rate || 0) * 100}
                onChange={(e) => update('property_growth_rate', +e.target.value / 100)}
                className={inputClass}
              />
            </div>
          </div>
        </div>
      </div>

      <button
        type="submit"
        disabled={loading}
        className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 disabled:cursor-not-allowed py-3 rounded-lg font-medium transition"
      >
        {loading ? labels.analyzing : `🔍 ${labels.analyze}`}
      </button>
    </form>
  );
}
