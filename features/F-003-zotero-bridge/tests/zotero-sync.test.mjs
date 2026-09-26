import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { once } from 'node:events';
import { mkdtemp, readFile, readdir, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { pathToFileURL } from 'node:url';
import { syncZotero } from '../scripts/zotero-sync.mjs';

test('syncs Zotero metadata, resolves the PDF, and creates one source-free reading packet', async () => {
  const root = await mkdtemp(path.join(os.tmpdir(), 'paperlearning-zotero-'));
  const pdf = path.join(root, 'paper.pdf');
  await writeFile(pdf, 'fake pdf');
  const server = createServer((request, response) => {
    response.setHeader('Content-Type', 'application/json');
    const pathname = new URL(request.url, 'http://localhost').pathname;
    if (pathname === '/api/users/0/collections/COLL0001') {
      response.end(JSON.stringify({ key: 'COLL0001', data: { name: '测试集合' } }));
    } else if (pathname === '/api/users/0/collections/COLL0001/items/top') {
      response.end(JSON.stringify([{ key: 'ITEM0001', version: 4, meta: { numChildren: 1 }, data: {
        itemType: 'journalArticle', title: 'Example Research', date: '2026', publicationTitle: 'Journal',
        DOI: '10.0000/example', creators: [{ firstName: 'Ada', lastName: 'Lovelace' }], tags: [],
      } }]));
    } else if (pathname === '/api/users/0/items/ITEM0001/children') {
      response.end(JSON.stringify([{ key: 'PDF00001', data: { itemType: 'attachment', title: 'PDF',
        filename: 'paper.pdf', contentType: 'application/pdf', linkMode: 'imported_file', md5: 'abc' },
      links: { enclosure: { href: pathToFileURL(pdf).href, title: 'paper.pdf', length: 8 } } }]));
    } else { response.statusCode = 404; response.end(JSON.stringify({ error: 'not found' })); }
  });
  server.listen(0, '127.0.0.1');
  await once(server, 'listening');
  const port = server.address().port;
  const configPath = path.join(root, 'config.json');
  const literatureRoot = path.join(root, 'literature');
  await writeFile(configPath, JSON.stringify({ schema_version: 1, api_base: `http://127.0.0.1:${port}/api`,
    library: 'users/0', collections: [{ key: 'COLL0001', name: '测试集合', workstream: 'WS-999', topic: 'test' }] }));
  try {
    const result = await syncZotero({ configPath, libraryRoot: literatureRoot });
    assert.equal(result.created.length, 1);
    assert.equal(result.items[0].item_key, 'ITEM0001');
    assert.equal(result.resolved.PDF00001.exists, true);
    const packet = result.created[0];
    const manifest = JSON.parse(await readFile(path.join(packet, 'manifest.json'), 'utf8'));
    assert.equal(manifest.zotero.item_key, 'ITEM0001');
    assert.equal(manifest.zotero.pdf_attachments[0].key, 'PDF00001');
    assert.equal((await readdir(packet)).includes('source'), false);
    assert.match(await readFile(path.join(packet, '02-translation.html'), 'utf8'), /中文翻译/);
    const catalog = JSON.parse(await readFile(path.join(literatureRoot, '00-index', 'catalog.json'), 'utf8'));
    assert.equal(catalog.items.length, 1);
    assert.match(await readFile(path.join(literatureRoot, '00-index', 'catalog.md'), 'utf8'), /\[对照阅读\]/);
    const second = await syncZotero({ configPath, libraryRoot: literatureRoot });
    assert.equal(second.created.length, 0);
    assert.equal(second.updated.length, 1);
  } finally {
    server.close();
    await once(server, 'close');
    await rm(root, { recursive: true, force: true });
  }
});
