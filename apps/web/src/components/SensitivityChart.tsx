'use client';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { SensitivityPoint } from '@/lib/api';
import { useLanguage } from '@/lib/i18n';

interface Props {
  variable: string;
  baseValue: number;
  points: SensitivityPoint[];
  metric?: 'irr' | 'npv' | 'monthly_cashflow';
}

const t = {
  fr: {
    title: 'Analyse de sensibilité',
    loan_rate: 'Taux d\'emprunt',
    property_growth_rate: 'Croissance prix',
    irr: 'TRI',
    npv: 'VAN',
    monthly_cashflow: 'Cash-flow mensuel',
    baseValue: 'Valeur de base',
  },
  en: {
    title: 'Sensitivity Analysis',
    loan_rate: 'Loan rate',
    property_growth_rate: 'Price growth',
    irr: 'IRR',
    npv: 'NPV',
    monthly_cashflow: 'Monthly cash flow',
    baseValue: 'Base value',
  }
};

export default function SensitivityChart({ variable, baseValue, points, metric = 'irr' }: Props) {
  const { lang } = useLanguage();
  const labels = t[lang];
  
  const variableLabel = variable === 'loan_rate' ? labels.loan_rate : labels.property_growth_rate;
  const metricLabel = metric === 'irr' ? labels.irr : metric === 'npv' ? labels.npv : labels.monthly_cashflow;
  
  const data = points.map(p => ({
    x: p.value * 100, // Convert to percentage
    y: metric === 'irr' ? p.irr * 100 : metric === 'npv' ? p.npv : p.monthly_cashflow,
    label: `${(p.value * 100).toFixed(1)}%`
  }));

  const formatY = (value: number) => {
    if (metric === 'irr') return `${value.toFixed(1)}%`;
    if (metric === 'npv') return `${(value / 1000).toFixed(0)}k€`;
    return `${value.toFixed(0)}€`;
  };

  const formatX = (value: number) => `${value.toFixed(1)}%`;

  return (
    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
      <h3 className="text-lg font-semibold mb-4">📊 {labels.title}</h3>
      <p className="text-gray-400 text-sm mb-4">
        {variableLabel} → {metricLabel}
      </p>
      
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 10, right: 30, left: 10, bottom: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis 
              dataKey="x" 
              stroke="#9CA3AF"
              tickFormatter={formatX}
              label={{ 
                value: variableLabel, 
                position: 'bottom', 
                fill: '#9CA3AF',
                offset: -5
              }}
            />
            <YAxis 
              stroke="#9CA3AF"
              tickFormatter={formatY}
              label={{ 
                value: metricLabel, 
                angle: -90, 
                position: 'insideLeft', 
                fill: '#9CA3AF' 
              }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1F2937',
                border: '1px solid #374151',
                borderRadius: '8px',
              }}
              formatter={(value: number) => [formatY(value), metricLabel]}
              labelFormatter={(label) => `${variableLabel}: ${label}%`}
            />
            <ReferenceLine 
              x={baseValue * 100} 
              stroke="#3B82F6" 
              strokeDasharray="5 5"
              label={{ 
                value: labels.baseValue, 
                fill: '#3B82F6', 
                fontSize: 12 
              }}
            />
            <Line 
              type="monotone" 
              dataKey="y" 
              stroke="#10B981" 
              strokeWidth={2}
              dot={{ fill: '#10B981', strokeWidth: 2 }}
              activeDot={{ r: 6, fill: '#10B981' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
