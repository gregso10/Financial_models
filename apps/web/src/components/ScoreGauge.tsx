'use client';
import { useI18n } from '@/lib/i18n';

interface ScoreGaugeProps {
  irr: number;
  riskFreeRate?: number;
  discountRate?: number;
}

export default function ScoreGauge({ irr, riskFreeRate = 0.035, discountRate = 0.05 }: ScoreGaugeProps) {
  const { t } = useI18n();
  
  const getScoreInfo = () => {
    if (irr > discountRate) return { color: '#22c55e', label: t('good_investment'), emoji: '🟢' };
    if (irr > riskFreeRate) return { color: '#eab308', label: '⚠️ Acceptable', emoji: '🟡' };
    return { color: '#ef4444', label: t('poor_return'), emoji: '🔴' };
  };
  
  const { color, label, emoji } = getScoreInfo();
  const percentage = Math.min(Math.max(irr * 100, 0), 15);
  const rotation = (percentage / 15) * 180 - 90;
  
  return (
    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
      <div className="relative w-48 h-24 mx-auto overflow-hidden">
        {/* Background arc */}
        <div className="absolute inset-0">
          <svg viewBox="0 0 200 100" className="w-full h-full">
            {/* Red zone (0-3.5%) */}
            <path
              d="M 20 100 A 80 80 0 0 1 62 32"
              fill="none"
              stroke="#fee2e2"
              strokeWidth="16"
            />
            {/* Yellow zone (3.5-5%) */}
            <path
              d="M 62 32 A 80 80 0 0 1 100 20"
              fill="none"
              stroke="#fef3c7"
              strokeWidth="16"
            />
            {/* Green zone (5-15%) */}
            <path
              d="M 100 20 A 80 80 0 0 1 180 100"
              fill="none"
              stroke="#dcfce7"
              strokeWidth="16"
            />
          </svg>
        </div>
        
        {/* Needle */}
        <div 
          className="absolute bottom-0 left-1/2 w-1 h-16 origin-bottom transition-transform duration-500"
          style={{ 
            transform: `translateX(-50%) rotate(${rotation}deg)`,
            background: `linear-gradient(to top, ${color}, ${color}88)`
          }}
        />
        
        {/* Center point */}
        <div 
          className="absolute bottom-0 left-1/2 w-4 h-4 rounded-full -translate-x-1/2 translate-y-1/2"
          style={{ backgroundColor: color }}
        />
      </div>
      
      {/* Value display */}
      <div className="text-center mt-2">
        <span className="text-3xl font-bold" style={{ color }}>{(irr * 100).toFixed(1)}%</span>
        <p className="text-sm mt-1" style={{ color }}>{label}</p>
      </div>
      
      {/* Scale labels */}
      <div className="flex justify-between text-xs text-gray-500 mt-2">
        <span>0%</span>
        <span>{(riskFreeRate * 100).toFixed(1)}%</span>
        <span>{(discountRate * 100).toFixed(1)}%</span>
        <span>15%</span>
      </div>
    </div>
  );
}