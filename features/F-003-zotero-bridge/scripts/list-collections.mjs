import { pathToFileURL } from 'node:url';
import path from 'node:path';

function parseArguments(argv) {
  let apiBase = 'http://127.0.0.1:23119/api';
  let library = 'users/0';
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === '--api-base' || argument === '--library') {
      const value = argv[index + 1];
      if (!value) throw new Error(`${argument} requires a value`);
      if (argument === '--api-base') apiBase = value;
      else library = value;
      index += 1;
    } else throw new Error(`Unknown argument: ${argument}`);
  }
  return { apiBase, library };
}

async function fetchPage(url) {
  let response;
  try { response = await fetch(url, { headers: { 'Zotero-API-Version': '3' } }); }
  catch (error) { throw new Error(`Cannot reach Zotero local API: ${error.message}`); }
  if (!response.ok) throw new Error(`Zotero API ${response.status} ${response.statusText}`);
  return response.json();
}

export async function listCollections({ apiBase = 'http://127.0.0.1:23119/api', library = 'users/0' } = {}) {
  const base = `${apiBase.replace(/\/$/, '')}/${library.replace(/^\//, '').replace(/\/$/, '')}/collections`;
  const collections = [];
  for (let start = 0; ; start += 100) {
    const page = await fetchPage(`${base}?limit=100&start=${start}`);
    if (!Array.isArray(page)) throw new Error('Expected an array from Zotero collections API');
    collections.push(...page);
    if (page.length < 100) break;
  }
  return collections.map((entry) => ({
    key: entry.key,
    name: entry.data?.name ?? '',
    parent: entry.data?.parentCollection || null,
    items: entry.meta?.numItems ?? null,
  }));
}

async function main() {
  const collections = await listCollections(parseArguments(process.argv.slice(2)));
  if (collections.length === 0) { console.log('No Zotero collections found.'); return; }
  console.table(collections);
}

const invokedAsScript = process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href;
if (invokedAsScript) main().catch((error) => { console.error(error.stack ?? error.message); process.exitCode = 1; });
