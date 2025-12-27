'use client';
import { createContext, useContext, useState, ReactNode } from 'react';

type Language = 'fr' | 'en';

interface LanguageContextType {
  lang: Language;
  setLang: (lang: Language) => void;
}

const LanguageContext = createContext<LanguageContextType>({
  lang: 'fr',
  setLang: () => {},
});

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Language>('fr');
  
  return (
    <LanguageContext.Provider value={{ lang, setLang }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  return useContext(LanguageContext);
}

// Alias for backward compatibility with existing pages
export function useI18n() {
  const { lang, setLang } = useContext(LanguageContext);
  return { lang, setLang, t: (key: string) => key };
}

export function LanguageToggle() {
  const { lang, setLang } = useLanguage();
  
  return (
    <button
      onClick={() => setLang(lang === 'fr' ? 'en' : 'fr')}
      className="px-3 py-1 text-sm bg-gray-700 hover:bg-gray-600 rounded-lg transition"
    >
      {lang === 'fr' ? '🇬🇧 EN' : '🇫🇷 FR'}
    </button>
  );
}