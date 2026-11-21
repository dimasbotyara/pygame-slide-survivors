import { strict as assert } from 'node:assert';
import { readFile, stat } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';

const source = fileURLToPath(new URL('../../screenshots/', import.meta.url));
const output = fileURLToPath(new URL('../dist/site/browser/screenshots/', import.meta.url));
const template = await readFile(new URL('../src/app.html', import.meta.url), 'utf8');
const component = await readFile(new URL('../src/main.ts', import.meta.url), 'utf8');
const names = ['ingame', 'mainmenu', 'selecthero', 'bestiary', 'achievements', 'settings', 'pausemenu', 'gameover'];
for (const name of names) {
  assert.ok(component.includes(`file: '${name}'`), `Missing gallery entry: ${name}`);
  for (const lang of ['en', 'ru']) {
    const filename = `${name}-${lang}.png`;
    const original = await readFile(`${source}/${filename}`);
    const built = await readFile(`${output}/${filename}`);
    assert.deepEqual(built, original, `Published screenshot differs: ${filename}`);
    const readme = await readFile(new URL(`../../${lang === 'ru' ? 'README.ru.md' : 'README.md'}`, import.meta.url), 'utf8');
    assert.ok(readme.includes(`screenshots/${filename}`), `README missing ${filename}`);
  }
}
assert.ok(template.includes("'screenshots/ingame-' + language() + '.png'"));
assert.ok(template.includes("shot.file + '-' + language() + '.png'"));
for (const fake of ['gameplay.png', 'gameplay-en.png']) {
  await assert.rejects(stat(new URL(`../dist/site/browser/${fake}`, import.meta.url)), { code: 'ENOENT' });
}
console.log('Screenshots verified: both languages, gallery, README and build assets.');
