import assert from 'node:assert/strict';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { parseSegments, renderTranslationFile } from '../scripts/render-translation.mjs';

const sample = `# Translation
<!-- segment
id: intro-001
heading: Introduction
source: PDF p. 2
-->
::: original
An observed result.
:::
::: zh
一个观测结果。
:::
`;

test('parses paired segments and renders a side-by-side HTML reader', async () => {
  const segments = parseSegments(sample);
  assert.equal(segments.length, 1);
  assert.equal(segments[0].source, 'PDF p. 2');
  const root = await mkdtemp(path.join(os.tmpdir(), 'paperlearning-translation-'));
  try {
    const input = path.join(root, '02-translation.md');
    await writeFile(input, sample);
    const result = await renderTranslationFile(input);
    const html = await readFile(result.destination, 'utf8');
    assert.match(html, /grid-template-columns:1fr 1fr/);
    assert.match(html, /An observed result/);
    assert.match(html, /一个观测结果/);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test('rejects duplicate segment ids', () => {
  assert.throws(() => parseSegments(`${sample}\n${sample}`), /Duplicate translation segment id/);
});
