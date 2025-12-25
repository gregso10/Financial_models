'use client';
import { SimulationMetrics } from '@/lib/api';
import { useI18n } from '@/lib/i18n';

interface Props {
  metrics: SimulationMetrics;
  holdingYears?: number;
}

export default function ExitScenario({ metrics, holdingYears = 10 }: Props) {
  const { t, lang } = useI18n();
  
  const fmt = (n: number) => new Intl.NumberFormat(lang === 'fr' ? 'fr-FR' : 'en-US', {
    style: 'currency',
    currency: 'EUR',
    maximumFractionDigits: 0,
  }).format(n);
  
  const rows = [
    { label: t('exit_value'), value: metrics.exit_property_value },
    { label: t('capital_gain'), value: metrics.capital_gain },
    { label: t('selling_costs'), value: -metrics.selling_costs },
    { label: t('capital_gains_tax'), value: -metrics.capital_gains_tax },
    { label: t('remaining_loan'), value: -metrics.remaining_loan },
  ];
  
  return (
    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
      <h3 className="text-sm font-medium text-gray-400 mb-3">
        {t('exit_scenario')} ({holdingYears} {t('years')})
      </h3>
      
      <div className="space-y-2 text-sm">
        {rows.map((row, i) => (
          <div key={i} className="flex justify-between">
            <span className="text-gray-400">{row.label}</span>
            <span className={row.value >= 0 ? 'text-white' : 'text-red-400'}>
              {fmt(row.value)}
            </span>
          </div>
        ))}
        
        <div className="flex justify-between pt-2 border-t border-gray-700 font-medium">
          <span className="text-gray-300">{t('net_proceeds')}</span>
          <span className="text-green-400">{fmt(metrics.net_exit_proceeds)}</span>
        </div>
      </div>
    </div>
  );
}