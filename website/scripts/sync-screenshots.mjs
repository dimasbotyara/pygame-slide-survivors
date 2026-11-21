// Angular only copies assets from within its workspace. Keep the repository's
// screenshots as the single source of truth and stage them for site builds.
import { cp, mkdir, readdir, rm } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';

const source = fileURLToPath(new URL('../../screenshots/', import.meta.url));
const destination = fileURLToPath(new URL('../public/screenshots/', import.meta.url));
const entries = await readdir(source);
await rm(destination, { recursive: true, force: true });
await mkdir(destination, { recursive: true });
for (const file of entries) {
  if (file.endsWith('.png')) await cp(`${source}/${file}`, `${destination}/${file}`);
}
