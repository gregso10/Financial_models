import { SimulationMetrics } from '@/lib/api';
import MetricCard from './MetricCard';

interface Props {
  metrics: SimulationMetrics;
}

export default function ResultsDashboard({ metrics }: Props) {
  const fmt = (n: number) => new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 0 }).format(n);
  const fmtPct = (n: number) => `${(n * 100).toFixed(2)}%`;

  const isGoodIRR = metrics.irr > 0.05;

  return (
    <div className="space-y-4">
      <div className={`p-4 rounded-lg text-center ${isGoodIRR ? 'bg-green-900/50 border border-green-700' : 'bg-red-900/50 border border-red-700'}`}>
        <p className="text-lg">{isGoodIRR ? '✅ Bon investissement' : '⚠️ Rentabilité faible'}</p>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <MetricCard label="TRI (IRR)" value={fmtPct(metrics.irr)} positive={metrics.irr > 0.03} />
        <MetricCard label="VAN (NPV)" value={`${fmt(metrics.npv)} €`} positive={metrics.npv > 0} />
        <MetricCard label="Cash-flow mensuel" value={`${fmt(metrics.monthly_cashflow)} €`} positive={metrics.monthly_cashflow >= 0} />
        <MetricCard label="Multiple" value={`${metrics.equity_multiple.toFixed(2)}x`} />
      </div>

      <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
        <p className="text-gray-400 text-sm mb-2">Scénario de sortie (10 ans)</p>
        <div className="space-y-1 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-400">Valeur de revente</span>
            <span className="text-white">{fmt(metrics.exit_property_value)} €</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Impôt plus-value</span>
            <span className="text-white">{fmt(metrics.capital_gains_tax)} €</span>
          </div>
          <div className="flex justify-between font-medium pt-2 border-t border-gray-700">
            <span className="text-gray-300">Produit net</span>
            <span className="text-green-400">{fmt(metrics.net_exit_proceeds)} €</span>
          </div>
        </div>
      </div>
    </div>
  );
}