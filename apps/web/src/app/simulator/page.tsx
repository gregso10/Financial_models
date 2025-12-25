'use client';
import { useState } from 'react';
import { useI18n, LanguageToggle } from '@/lib/i18n';
import SimulatorForm from '@/components/SimulatorForm';
import MetricCard from '@/components/MetricCard';
import ScoreGauge from '@/components/ScoreGauge';
import CashFlowChart from '@/components/CashFlowChart';
import CumulativeCashFlowChart from '@/components/CumulativeCashFlowChart';
import FiscalComparison from '@/components/FiscalComparison';
import AlertsList from '@/components/AlertsList';
import ExitScenario from '@/components/ExitScenario';
import { simulateSimple, SimulationResponse, SimulationRequest } from '@/lib/api';

export default function SimulatorPage() {
  const { t, lang } = useI18n();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SimulationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (data: SimulationRequest) => {
    setLoading(true);
    setError(null);
    try {
      const res = await simulateSimple(data);
      if (res.success) {
        setResult(res);
      } else {
        setError(res.error || t('unknown_error'));
      }
    } catch (e) {
      setError(t('connection_error'));
    } finally {
      setLoading(false);
    }
  };

  const fmt = (n: number) => new Intl.NumberFormat(lang === 'fr' ? 'fr-FR' : 'en-US', {
    style: 'currency',
    currency: 'EUR',
    maximumFractionDigits: 0,
  }).format(n);
  
  const fmtPct = (n: number) => `${(n * 100).toFixed(2)}%`;

  return (
    <main className="min-h-screen bg-gray-900 text-white p-4 md:p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold">🏠 {t('simulator_title')}</h1>
          <LanguageToggle />
        </div>
        
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Left Column - Form */}
          <div className="lg:col-span-1">
            <div className="bg-gray-850 p-5 rounded-xl border border-gray-700 sticky top-6">
              <h2 className="text-lg font-medium mb-4">{t('parameters')}</h2>
              <SimulatorForm onSubmit={handleSubmit} loading={loading} />
            </div>
          </div>

          {/* Right Column - Results */}
          <div className="lg:col-span-2 space-y-6">
            {error && (
              <div className="bg-red-900/50 border border-red-700 p-4 rounded-lg text-red-300">
                {error}
              </div>
            )}
            
            {!result?.metrics && !error && (
              <div className="bg-gray-800 p-12 rounded-lg text-center text-gray-500 border border-gray-700">
                {t('fill_form')}
              </div>
            )}
            
            {result?.metrics && (
              <>
                {/* Key Metrics Row */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <MetricCard 
                    label={t('irr')} 
                    value={fmtPct(result.metrics.irr)} 
                    positive={result.metrics.irr > 0.03}
                  />
                  <MetricCard 
                    label={t('npv')} 
                    value={fmt(result.metrics.npv)} 
                    positive={result.metrics.npv > 0}
                  />
                  <MetricCard 
                    label={t('monthly_cashflow')} 
                    value={fmt(result.metrics.monthly_cashflow)} 
                    positive={result.metrics.monthly_cashflow >= 0}
                  />
                  <MetricCard 
                    label={t('equity_multiple')} 
                    value={`${result.metrics.equity_multiple.toFixed(2)}x`}
                    positive={result.metrics.equity_multiple > 1}
                  />
                </div>

                {/* Gauge + Alerts Row */}
                <div className="grid md:grid-cols-2 gap-4">
                  <ScoreGauge irr={result.metrics.irr} />
                  {result.alerts && <AlertsList alerts={result.alerts} />}
                </div>

                {/* Charts Row */}
                <div className="grid md:grid-cols-2 gap-4">
                  {result.yearly_cashflows && (
                    <>
                      <CashFlowChart data={result.yearly_cashflows} />
                      <CumulativeCashFlowChart data={result.yearly_cashflows} />
                    </>
                  )}
                </div>

                {/* Fiscal + Exit Row */}
                <div className="grid md:grid-cols-2 gap-4">
                  {result.fiscal && <FiscalComparison data={result.fiscal} />}
                  <ExitScenario metrics={result.metrics} />
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}