'use client';
import { useState, useEffect } from 'react';
import { getLocations, SimulationRequest } from '@/lib/api';
import { useI18n } from '@/lib/i18n';

interface Props {
  onSubmit: (data: SimulationRequest) => void;
  loading: boolean;
}

export default function SimulatorForm({ onSubmit, loading }: Props) {
  const { t } = useI18n();
  const [locations, setLocations] = useState<string[]>([]);
  const [form, setForm] = useState({
    location: 'Lyon',
    price: 250000,
    surface_sqm: 45,
    monthly_rent: 900,
    apport: 50000,
    loan_rate: 3.5,
  });

  useEffect(() => {
    getLocations().then(setLocations).catch(console.error);
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({ ...form, loan_rate: form.loan_rate / 100 });
  };

  const update = (field: string, value: string | number) => {
    setForm(prev => ({ ...prev, [field]: value }));
  };

  const inputClass = "w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent";

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm text-gray-400 mb-1">{t('location')}</label>
        <select
          value={form.location}
          onChange={e => update('location', e.target.value)}
          className={inputClass}
        >
          {locations.map(loc => (
            <option key={loc} value={loc}>{loc}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm text-gray-400 mb-1">{t('purchase_price')}</label>
        <input
          type="number"
          value={form.price}
          onChange={e => update('price', +e.target.value)}
          className={inputClass}
          step="1000"
        />
      </div>

      <div>
        <label className="block text-sm text-gray-400 mb-1">{t('surface')}</label>
        <input
          type="number"
          value={form.surface_sqm}
          onChange={e => update('surface_sqm', +e.target.value)}
          className={inputClass}
        />
      </div>

      <div>
        <label className="block text-sm text-gray-400 mb-1">{t('monthly_rent')}</label>
        <input
          type="number"
          value={form.monthly_rent}
          onChange={e => update('monthly_rent', +e.target.value)}
          className={inputClass}
          step="50"
        />
      </div>

      <div>
        <label className="block text-sm text-gray-400 mb-1">{t('down_payment')}</label>
        <input
          type="number"
          value={form.apport}
          onChange={e => update('apport', +e.target.value)}
          className={inputClass}
          step="1000"
        />
      </div>

      <div>
        <label className="block text-sm text-gray-400 mb-1">{t('loan_rate')}</label>
        <input
          type="number"
          step="0.1"
          value={form.loan_rate}
          onChange={e => update('loan_rate', +e.target.value)}
          className={inputClass}
        />
      </div>

      <button
        type="submit"
        disabled={loading}
        className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-medium py-3 rounded-lg transition"
      >
        {loading ? t('calculating') : t('analyze')}
      </button>
    </form>
  );
}