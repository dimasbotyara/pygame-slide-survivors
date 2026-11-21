import { strict as assert } from 'node:assert';
import { resolveLanguage } from '../src/language.ts';

assert.equal(resolveLanguage(null, ['ru-RU', 'en-US']), 'ru');
assert.equal(resolveLanguage(null, ['en-GB', 'ru-RU']), 'en');
assert.equal(resolveLanguage(null, ['fr-FR', 'ru']), 'ru');
assert.equal(resolveLanguage(null, ['de-DE']), 'en');
assert.equal(resolveLanguage(null, []), 'en');
assert.equal(resolveLanguage('en', ['ru-RU']), 'en');
assert.equal(resolveLanguage('ru', ['en-US']), 'ru');
assert.equal(resolveLanguage('invalid', ['RU_ru']), 'ru');
console.log('Language preference tests passed.');
