import { bootstrapApplication } from '@angular/platform-browser';
import { Component, signal } from '@angular/core';
import { NbButton, NbSurface } from '@ng-brutalism/ui';
import { resolveLanguage } from './language';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [NbButton, NbSurface],
  templateUrl: './app.html',
})
class AppComponent {
  readonly dark = signal(document.documentElement.classList.contains('dark'));
  readonly language = signal<'en' | 'ru'>(this.loadLanguage());
  readonly menuOpen = signal(false);
  readonly copyState = signal<'idle' | 'copied' | 'error'>('idle');
  readonly screenshots = [
    { file: 'ingame', en: 'Gameplay', ru: 'Игровой процесс' },
    { file: 'mainmenu', en: 'Main menu', ru: 'Главное меню' },
    { file: 'selecthero', en: 'Hero selection', ru: 'Выбор героя' },
    { file: 'bestiary', en: 'Bestiary', ru: 'Бестиарий' },
    { file: 'achievements', en: 'Achievements', ru: 'Достижения' },
    { file: 'settings', en: 'Settings', ru: 'Настройки' },
    { file: 'pausemenu', en: 'Pause menu', ru: 'Меню паузы' },
    { file: 'gameover', en: 'Run results', ru: 'Результаты забега' },
  ] as const;

  constructor() { this.updateDocument(); }
  private loadLanguage(): 'en' | 'ru' {
    let saved: string | null = null;
    try { saved = localStorage.getItem('slide-site-language'); } catch { /* use browser preferences */ }
    return resolveLanguage(saved, navigator.languages?.length ? navigator.languages : [navigator.language || 'en']);
  }
  tr(en: string, ru: string): string { return this.language() === 'ru' ? ru : en; }
  toggleLanguage(): void {
    const lang = this.language() === 'en' ? 'ru' : 'en';
    this.language.set(lang);
    try { localStorage.setItem('slide-site-language', lang); } catch { /* works for this visit */ }
    this.updateDocument();
  }
  private updateDocument(): void {
    document.documentElement.lang = this.language();
    document.title = this.tr('Slide Survivors — slide, strike, survive', 'Slide Survivors — скользи, бей, выживай');
    document.querySelector('meta[name="description"]')?.setAttribute('content', this.tr(
      'Slide Survivors is a free Pygame arena roguelike. Slide through hordes, explore biomes and fight bosses.',
      'Slide Survivors — бесплатная аренная игра на Python. Скользи сквозь орды, исследуй биомы и сражайся с боссами.'
    ));
  }
  copyLabel(): string {
    return this.copyState() === 'copied' ? this.tr('COPIED ✓', 'СКОПИРОВАНО ✓') :
      this.copyState() === 'error' ? this.tr('COPY COMMANDS MANUALLY', 'СКОПИРУЙТЕ КОМАНДЫ ВРУЧНУЮ') :
      this.tr('COPY COMMANDS ↗', 'КОПИРОВАТЬ КОМАНДЫ ↗');
  }
  toggleTheme(): void {
    const dark = !this.dark();
    this.dark.set(dark);
    document.documentElement.classList.toggle('dark', dark);
    try { localStorage.setItem('slide-site-theme', dark ? 'dark' : 'light'); } catch { /* theme still works for this visit */ }
  }
  async copyCommand(): Promise<void> {
    try {
      await navigator.clipboard.writeText('python -m pip install -r requirements.txt\npython main.py');
      this.copyState.set('copied');
      setTimeout(() => this.copyState.set('idle'), 2000);
    } catch {
      this.copyState.set('error');
    }
  }
}
bootstrapApplication(AppComponent).catch(console.error);
