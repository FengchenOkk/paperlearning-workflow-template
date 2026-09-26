import assert from 'node:assert/strict';
import { mkdtemp, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { initializeLocalWorkspace } from '../scripts/setup-local.mjs';

test('creates private local files from examples without overwriting them', async () => {
  const root = await mkdtemp(path.join(os.tmpdir(), 'paperlearning-setup-'));
  try {
    await mkdir(path.join(root, 'planning'), { recursive: true });
    await mkdir(path.join(root, 'features/F-003-zotero-bridge/config'), { recursive: true });
    await writeFile(path.join(root, 'PROJECT.example.md'), 'project example');
    await writeFile(path.join(root, 'planning/BACKLOG.example.md'), 'backlog example');
    await writeFile(path.join(root, 'planning/DECISIONS.example.md'), 'decisions example');
    await writeFile(path.join(root, 'planning/ROADMAP.example.md'), 'roadmap example');
    await writeFile(path.join(root, 'features/F-003-zotero-bridge/config/collections.example.json'), '{}');
    const first = await initializeLocalWorkspace(root);
    assert.equal(first.every((entry) => entry.status === 'created'), true);
    await writeFile(path.join(root, 'PROJECT.md'), 'private content');
    const second = await initializeLocalWorkspace(root);
    assert.equal(second.every((entry) => entry.status === 'kept'), true);
    assert.equal(await readFile(path.join(root, 'PROJECT.md'), 'utf8'), 'private content');
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
