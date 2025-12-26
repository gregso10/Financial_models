'use client';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { YearlyCashFlow } from '@/lib/api';
import { useI18n } from '@/lib/i18n';

interface Props {
  data: YearlyCashFlow[];
}

export default function CumulativeCashFlowChart({ data }: Props) {
  const { t, lang } = useI18n();
  
  const chartData = data.map(d => ({
    name: `${lang === 'fr' ? 'A' : 'Y'}${d.year}`,
    value: d.cumulative,
  }));
  
  // Find breakeven year
  const breakevenYear = data.find((d, i) => i > 0 && data[i-1].cumulative < 0 && d.cumulative >= 0)?.year;
  
  const formatValue = (value: number) => {
    return new Intl.NumberFormat(lang === 'fr' ? 'fr-FR' : 'en-US', {
      style: 'currency',
      currency: 'EUR',
      maximumFractionDigits: 0,
    }).format(value);
  };
  
  return (
    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
      <div className="flex justify-between items-center mb-3">
        <h3 className="text-sm font-medium text-gray-400">{t('cumulative_cashflow')}</h3>
        {breakevenYear && (
          <span className="text-xs text-green-400 bg-green-900/30 px-2 py-1 rounded">
            Breakeven: {lang === 'fr' ? 'A' : 'Y'}{breakevenYear}
          </span>
        )}
      </div>
      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
          <defs>
            <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
            </linearGradient>
          </defs>
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
            contentStyle={{ backgroundColor: '#f1f7ffff', border: '1px solid #374151', borderRadius: '8px' }}
            labelStyle={{ color: '#9ca3af' }}
            formatter={(value: number) => [formatValue(value), t('cumulative_cashflow')]}
          />
          <ReferenceLine y={0} stroke="#4b5563" strokeDasharray="3 3" />
          <Area 
            type="monotone" 
            dataKey="value" 
            stroke="#3b82f6" 
            strokeWidth={2}
            fill="url(#colorValue)" 
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}