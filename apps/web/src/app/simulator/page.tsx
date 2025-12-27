'use client';
import { useState } from 'react';
import SimulatorForm from '@/components/SimulatorForm';
import ExpertSimulatorForm from '@/components/ExpertSimulatorForm';
import ResultsDashboard from '@/components/ResultsDashboard';
import LMPStatus from '@/components/LMPStatus';
import SensitivityChart from '@/components/SensitivityChart';
import { 
  simulateSimple, 
  simulateExpert,
  runSensitivityAnalysis,
  SimulationRequest,
  ExpertSimulationRequest,
  SimulationResponse,
  ExpertSimulationResponse,
  SensitivityResponse,
} from '@/lib/api';
import { useLanguage, LanguageToggle } from '@/lib/i18n';

type Mode = 'simple' | 'expert';

const t = {
  fr: {
    title: 'Simulateur Investissement Locatif',
    simple: 'Simple',
    expert: 'Expert',
    simpleDesc: 'Analyse rapide avec les paramètres essentiels',
    expertDesc: 'Contrôle complet de tous les paramètres',
    params: 'Paramètres',
    results: 'Résultats',
    fillForm: 'Remplissez le formulaire et cliquez Analyser',
    runSensitivity: 'Analyse de sensibilité',
    sensitivityLoading: 'Calcul...',
    pro: 'PRO',
  },
  en: {
    title: 'Rental Investment Simulator',
    simple: 'Simple',
    expert: 'Expert',
    simpleDesc: 'Quick analysis with essential parameters',
    expertDesc: 'Full control over all parameters',
    params: 'Parameters',
    results: 'Results',
    fillForm: 'Fill the form and click Analyze',
    runSensitivity: 'Sensitivity Analysis',
    sensitivityLoading: 'Calculating...',
    pro: 'PRO',
  }
};

export default function SimulatorPage() {
  const { lang } = useLanguage();
  const labels = t[lang];
  
  const [mode, setMode] = useState<Mode>('simple');
  const [loading, setLoading] = useState(false);
  const [sensitivityLoading, setSensitivityLoading] = useState(false);
  const [result, setResult] = useState<SimulationResponse | ExpertSimulationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastExpertParams, setLastExpertParams] = useState<ExpertSimulationRequest | null>(null);
  const [sensitivityData, setSensitivityData] = useState<{
    loanRate?: SensitivityResponse;
    growth?: SensitivityResponse;
  }>({});

  const handleSimpleSubmit = async (data: SimulationRequest) => {
    setLoading(true);
    setError(null);
    setSensitivityData({});
    
    try {
      const res = await simulateSimple(data);
      if (res.success) {
        setResult(res);
      } else {
        setError(res.error || 'Unknown error');
      }
    } catch (e) {
      setError('Server connection error');
    } finally {
      setLoading(false);
    }
  };

  const handleExpertSubmit = async (data: ExpertSimulationRequest) => {
    setLoading(true);
    setError(null);
    setSensitivityData({});
    setLastExpertParams(data);
    
    try {
      const res = await simulateExpert(data);
      if (res.success) {
        setResult(res);
      } else {
        setError(res.error || 'Unknown error');
      }
    } catch (e) {
      setError('Server connection error');
    } finally {
      setLoading(false);
    }
  };

  const handleSensitivityAnalysis = async () => {
    if (!lastExpertParams) return;
    
    setSensitivityLoading(true);
    
    try {
      const [loanRateRes, growthRes] = await Promise.all([
        runSensitivityAnalysis({
          base_params: lastExpertParams,
          variable: 'loan_rate',
          range_min: -0.015,
          range_max: 0.015,
          steps: 7,
        }),
        runSensitivityAnalysis({
          base_params: lastExpertParams,
          variable: 'property_growth_rate',
          range_min: -0.02,
          range_max: 0.02,
          steps: 7,
        }),
      ]);
      
      setSensitivityData({
        loanRate: loanRateRes,
        growth: growthRes,
      });
    } catch (e) {
      console.error('Sensitivity analysis failed:', e);
    } finally {
      setSensitivityLoading(false);
    }
  };

  const handleModeChange = (newMode: Mode) => {
    setMode(newMode);
    setResult(null);
    setError(null);
    setSensitivityData({});
  };

  const expertResult = result as ExpertSimulationResponse;

  return (
    <main className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex justify-between items-center mb-4">
            <h1 className="text-2xl font-bold">🏠 {labels.title}</h1>
            <LanguageToggle />
          </div>
          
          {/* Mode Toggle */}
          <div className="flex gap-2">
            <button
              onClick={() => handleModeChange('simple')}
              className={`px-4 py-2 rounded-lg font-medium transition flex items-center gap-2 ${
                mode === 'simple'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              ⚡ {labels.simple}
            </button>
            <button
              onClick={() => handleModeChange('expert')}
              className={`px-4 py-2 rounded-lg font-medium transition flex items-center gap-2 ${
                mode === 'expert'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              🎯 {labels.expert}
              <span className="text-xs bg-amber-500 text-black px-1.5 py-0.5 rounded font-bold">
                {labels.pro}
              </span>
            </button>
          </div>
          <p className="text-gray-400 text-sm mt-2">
            {mode === 'simple' ? labels.simpleDesc : labels.expertDesc}
          </p>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid lg:grid-cols-2 gap-6">
          {/* Left: Form */}
          <div className="bg-gray-850 p-6 rounded-xl border border-gray-700 max-h-[calc(100vh-220px)] overflow-y-auto">
            <h2 className="text-lg font-medium mb-4">{labels.params}</h2>
            {mode === 'simple' ? (
              <SimulatorForm onSubmit={handleSimpleSubmit} loading={loading} />
            ) : (
              <ExpertSimulatorForm onSubmit={handleExpertSubmit} loading={loading} />
            )}
          </div>

          {/* Right: Results */}
          <div className="space-y-4 max-h-[calc(100vh-220px)] overflow-y-auto">
            <h2 className="text-lg font-medium">{labels.results}</h2>
            
            {error && (
              <div className="bg-red-900/50 border border-red-700 p-4 rounded-lg text-red-300">
                {error}
              </div>
            )}
            
            {result?.success && result.metrics ? (
              <div className="space-y-4">
                <ResultsDashboard 
                  metrics={result.metrics} 
                  fiscal={result.fiscal}
                  yearly_cashflows={result.yearly_cashflows}
                  alerts={result.alerts}
                />
                
                {/* Expert-only features */}
                {mode === 'expert' && (
                  <>
                    {/* LMP Status */}
                    {expertResult?.lmp_status && Object.keys(expertResult.lmp_status).length > 0 && (
                      <LMPStatus status={expertResult.lmp_status} />
                    )}
                    
                    {/* Sensitivity Analysis */}
                    <button
                      onClick={handleSensitivityAnalysis}
                      disabled={sensitivityLoading || !lastExpertParams}
                      className="w-full bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:text-gray-500 py-3 rounded-lg font-medium transition flex items-center justify-center gap-2"
                    >
                      {sensitivityLoading ? (
                        <>
                          <span className="animate-spin">⏳</span>
                          {labels.sensitivityLoading}
                        </>
                      ) : (
                        <>📊 {labels.runSensitivity}</>
                      )}
                    </button>
                    
                    {sensitivityData.loanRate?.success && sensitivityData.loanRate.points && (
                      <SensitivityChart
                        variable="loan_rate"
                        baseValue={sensitivityData.loanRate.base_value}
                        points={sensitivityData.loanRate.points}
                        metric="irr"
                      />
                    )}
                    
                    {sensitivityData.growth?.success && sensitivityData.growth.points && (
                      <SensitivityChart
                        variable="property_growth_rate"
                        baseValue={sensitivityData.growth.base_value}
                        points={sensitivityData.growth.points}
                        metric="irr"
                      />
                    )}
                  </>
                )}
              </div>
            ) : (
              <div className="bg-gray-800 p-8 rounded-lg text-center text-gray-500">
                {labels.fillForm}
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}