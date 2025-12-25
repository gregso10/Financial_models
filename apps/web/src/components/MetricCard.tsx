interface MetricCardProps {
  label: string;
  value: string;
  subtitle?: string;
  positive?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export default function MetricCard({ label, value, subtitle, positive, size = 'md' }: MetricCardProps) {
  const sizeClasses = {
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-5',
  };
  const valueClasses = {
    sm: 'text-lg',
    md: 'text-2xl',
    lg: 'text-3xl',
  };
  
  return (
    <div className={`bg-gray-800 rounded-lg ${sizeClasses[size]} border border-gray-700`}>
      <p className="text-gray-400 text-sm">{label}</p>
      <p className={`${valueClasses[size]} font-bold ${
        positive === undefined ? 'text-white' :
        positive ? 'text-green-400' : 'text-red-400'
      }`}>
        {value}
      </p>
      {subtitle && <p className="text-gray-500 text-xs mt-1">{subtitle}</p>}
    </div>
  );
}