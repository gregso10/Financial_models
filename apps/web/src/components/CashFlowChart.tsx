'use client';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine, Cell } from 'recharts';
import { YearlyCashFlow } from '@/lib/api';
import { useI18n } from '@/lib/i18n';

interface Props {
  data: YearlyCashFlow[];
}

export default function CashFlowChart({ data }: Props) {
  const { t, lang } = useI18n();
  
  const chartData = data.map(d => ({
    name: `${lang === 'fr' ? 'A' : 'Y'}${d.year}`,
    value: d.net_change,
    cumulative: d.cumulative,
  }));
  
  const formatValue = (value: number) => {
    return new Intl.NumberFormat(lang === 'fr' ? 'fr-FR' : 'en-US', {
      style: 'currency',
      currency: 'EUR',
      maximumFractionDigits: 0,
    }).format(value);
  };
  
  return (
    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
      <h3 className="text-sm font-medium text-gray-400 mb-3">{t('annual_cashflow')}</h3>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
          <XAxis 
            dataKey="name" 
            axisLine={false} 
            tickLine={false}
            tick={{ fill: '#9ca3af', fontSize: 11 }}
          />
          <YAxis 
            axisLine={false} 
            tickLine={false}
            tick={{ fill: '#9ca3af', fontSize: 11 }}
            tickFormatter={(v) => `${(v/1000).toFixed(0)}k`}
          />
          <Tooltip
            contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
            labelStyle={{ color: '#9ca3af' }}
            formatter={(value: number) => [formatValue(value), t('annual_cashflow')]}
          />
          <ReferenceLine y={0} stroke="#4b5563" />
          <Bar dataKey="value" radius={[4, 4, 0, 0]}>
            {chartData.map((entry, index) => (
              <Cell key={index} fill={entry.value >= 0 ? '#22c55e' : '#ef4444'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}