'use client';
import { Alert } from '@/lib/api';
import { useI18n } from '@/lib/i18n';

interface Props {
  alerts: Alert[];
}

export default function AlertsList({ alerts }: Props) {
  const { t, lang } = useI18n();
  
  const getAlertStyle = (type: string) => {
    switch (type) {
      case 'success': return { bg: 'bg-green-900/30', border: 'border-green-700', text: 'text-green-400' };
      case 'warning': return { bg: 'bg-yellow-900/30', border: 'border-yellow-700', text: 'text-yellow-400' };
      case 'error': return { bg: 'bg-red-900/30', border: 'border-red-700', text: 'text-red-400' };
      default: return { bg: 'bg-gray-800', border: 'border-gray-700', text: 'text-gray-400' };
    }
  };
  
  return (
    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
      <h3 className="text-sm font-medium text-gray-400 mb-3">{t('alerts')}</h3>
      <div className="space-y-2">
        {alerts.map((alert, i) => {
          const style = getAlertStyle(alert.type);
          const message = lang === 'fr' ? alert.message_fr : alert.message_en;
          return (
            <div 
              key={i}
              className={`${style.bg} border-l-4 ${style.border} px-3 py-2 rounded-r-lg`}
            >
              <span className={style.text}>{alert.icon} {message}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}