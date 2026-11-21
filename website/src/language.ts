/** A saved choice wins; otherwise negotiate against the browser's preferences. */
export function resolveLanguage(saved: string | null, browserLanguages: readonly string[]): 'en' | 'ru' {
  if (saved === 'en' || saved === 'ru') return saved;
  for (const language of browserLanguages) {
    const base = language.toLowerCase().split(/[-_]/)[0];
    if (base === 'ru' || base === 'en') return base;
  }
  return 'en';
}
