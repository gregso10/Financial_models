'use client';
import { FiscalComparison as FiscalComparisonType } from '@/lib/api';
import { useI18n } from '@/lib/i18n';

interface Props {
  data: FiscalComparisonType;
}

export default function FiscalComparison({ data }: Props) {
  const { t, lang } = useI18n();
  
  const fmt = (n: number) => new Intl.NumberFormat(lang === 'fr' ? 'fr-FR' : 'en-US', {
    style: 'currency',
    currency: 'EUR',
    maximumFractionDigits: 0,
  }).format(n);
  
  const isReel = data.recommended.includes('Réel');
  const recommendedColor = isReel ? '#22c55e' : '#3b82f6';
  
  return (
    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
      <h3 className="text-sm font-medium text-gray-400 mb-3">{t('fiscal_optimization')}</h3>
      
      {/* Recommendation badge */}
      <div 
        className="p-3 rounded-lg text-center mb-4"
        style={{ backgroundColor: `${recommendedColor}20`, border: `2px solid ${recommendedColor}` }}
      >
        <span className="text-lg font-bold" style={{ color: recommendedColor }}>
          ✨ {data.recommended}
        </span>
        <p className="text-xs text-gray-400 mt-1">{data.reason}</p>
      </div>
      
      {/* Comparison table */}
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div className="space-y-2">
          <p className="font-medium text-gray-300">{data.micro.regime}</p>
          <div className="text-gray-400">
            <p>{t('taxable_income')}: <span className="text-white">{fmt(data.micro.taxable_income)}</span></p>
            <p>{t('total_tax')}: <span className="text-white">{fmt(data.micro.total_tax)}</span></p>
          </div>
        </div>
        <div className="space-y-2">
          <p className="font-medium text-gray-300">{data.reel.regime}</p>
          <div className="text-gray-400">
            <p>{t('taxable_income')}: <span className="text-white">{fmt(data.reel.taxable_income)}</span></p>
            <p>{t('total_tax')}: <span className="text-white">{fmt(data.reel.total_tax)}</span></p>
          </div>
        </div>
      </div>
      
      {/* Savings */}
      {data.annual_savings > 100 && (
        <div className="mt-3 p-2 bg-green-900/30 rounded-lg text-center">
          <span className="text-green-400 text-sm font-medium">
            💰 {t('annual_savings')}: {fmt(data.annual_savings)}/{lang === 'fr' ? 'an' : 'year'}
          </span>
        </div>
      )}
    </div>
  );
}