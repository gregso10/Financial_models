'use client';
import Link from 'next/link';
import { useI18n, LanguageToggle } from '@/lib/i18n';

export default function Home() {
  const { t } = useI18n();
  
  return (
    <main className="min-h-screen bg-gray-900 text-white flex flex-col items-center justify-center p-6">
      <div className="absolute top-4 right-4">
        <LanguageToggle />
      </div>
      
      <h1 className="text-5xl font-bold mb-4">{t('app_title')}</h1>
      <p className="text-gray-400 mb-8 text-center max-w-md">
        {t('landing_subtitle')}
      </p>
      <Link
        href="/simulator"
        className="bg-blue-600 hover:bg-blue-700 px-8 py-3 rounded-lg font-medium transition text-lg"
      >
        {t('start_analysis')}
      </Link>
    </main>
  );
}