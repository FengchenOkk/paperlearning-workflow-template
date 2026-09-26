import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

function escapeHtml(value) {
  return value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function renderPlainMarkdown(value) {
  const escaped = escapeHtml(value.trim());
  return escaped.split(/\n\s*\n/).map((paragraph) => `<p>${paragraph.replace(/\n/g, '<br>')}</p>`).join('\n');
}

function parseMetadata(block) {
  const metadata = {};
  for (const line of block.trim().split(/\r?\n/)) {
    const separator = line.indexOf(':');
    if (separator === -1) continue;
    metadata[line.slice(0, separator).trim()] = line.slice(separator + 1).trim();
  }
  return metadata;
}

export function parseSegments(markdown) {
  const expression = /<!--\s*segment\s*\r?\n([\s\S]*?)-->\s*\r?\n::: original\s*\r?\n([\s\S]*?)\r?\n:::\s*\r?\n::: zh\s*\r?\n([\s\S]*?)\r?\n:::/g;
  const segments = [];
  let match;
  while ((match = expression.exec(markdown)) !== null) {
    const metadata = parseMetadata(match[1]);
    if (!metadata.id) throw new Error('Every translation segment requires an id');
    segments.push({ id: metadata.id, heading: metadata.heading || metadata.id,
      source: metadata.source || '位置待核验', original: match[2].trim(), translation: match[3].trim() });
  }
  if (segments.length === 0) throw new Error('No structured translation segments found');
  const ids = new Set();
  for (const segment of segments) {
    if (ids.has(segment.id)) throw new Error(`Duplicate translation segment id: ${segment.id}`);
    ids.add(segment.id);
  }
  return segments;
}

function documentHtml(segments, title) {
  const navigation = segments.map((segment) => `<a href="#${escapeHtml(segment.id)}">${escapeHtml(segment.heading)}</a>`).join('');
  const rows = segments.map((segment) => `
    <section class="segment" id="${escapeHtml(segment.id)}">
      <header><h2>${escapeHtml(segment.heading)}</h2><span>${escapeHtml(segment.source)}</span></header>
      <div class="pair">
        <article lang="en"><h3>Original</h3>${renderPlainMarkdown(segment.original)}</article>
        <article lang="zh-CN"><h3>中文翻译</h3>${renderPlainMarkdown(segment.translation)}</article>
      </div>
    </section>`).join('\n');
  return `<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${escapeHtml(title)} · 双语对照</title>
<style>
:root{color-scheme:light dark;--bg:#f5f2eb;--panel:#fffdfa;--ink:#1f2933;--muted:#667085;--line:#d5d0c7;--accent:#005f73}
@media(prefers-color-scheme:dark){:root{--bg:#14181c;--panel:#1e252b;--ink:#edf2f4;--muted:#a9b4bd;--line:#3b4650;--accent:#76c7d5}}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.7 system-ui,-apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
nav{position:sticky;top:0;z-index:2;display:flex;gap:.5rem;overflow:auto;padding:.75rem max(1rem,calc((100vw - 1280px)/2));background:color-mix(in srgb,var(--panel) 94%,transparent);border-bottom:1px solid var(--line);backdrop-filter:blur(10px)}
nav a{flex:none;color:var(--accent);text-decoration:none;padding:.25rem .6rem;border:1px solid var(--line);border-radius:999px}main{max-width:1280px;margin:auto;padding:1.25rem}
h1{font-size:clamp(1.5rem,3vw,2.25rem);margin:.5rem 0 1.5rem}.segment{margin:0 0 1.5rem;background:var(--panel);border:1px solid var(--line);border-radius:14px;overflow:hidden;box-shadow:0 8px 28px rgb(0 0 0/.05)}
.segment>header{display:flex;align-items:baseline;justify-content:space-between;gap:1rem;padding:.8rem 1rem;border-bottom:1px solid var(--line)}h2,h3{margin:0}.segment>header span,h3{color:var(--muted);font-size:.88rem;font-weight:600}
.pair{display:grid;grid-template-columns:1fr 1fr}.pair article{min-width:0;padding:1rem 1.15rem}.pair article+article{border-left:1px solid var(--line)}p{margin:.65rem 0;white-space:normal;overflow-wrap:anywhere}
@media(max-width:760px){.pair{grid-template-columns:1fr}.pair article+article{border-left:0;border-top:1px solid var(--line)}}
@media print{nav{display:none}body{background:white;color:black}.segment{break-inside:avoid;box-shadow:none}.pair{grid-template-columns:1fr 1fr}}
</style></head><body><nav>${navigation}</nav><main><h1>${escapeHtml(title)} · 双语对照</h1>${rows}</main></body></html>\n`;
}

export async function renderTranslationFile(inputPath, outputPath = null) {
  const markdown = await readFile(inputPath, 'utf8');
  const segments = parseSegments(markdown);
  const destination = outputPath ?? path.join(path.dirname(inputPath), `${path.basename(inputPath, path.extname(inputPath))}.html`);
  const packetName = path.basename(path.dirname(inputPath));
  await writeFile(destination, documentHtml(segments, packetName));
  return { destination, segmentCount: segments.length };
}

async function main() {
  const input = process.argv[2];
  if (!input) throw new Error('Usage: node render-translation.mjs <02-translation.md> [output.html]');
  const result = await renderTranslationFile(path.resolve(input), process.argv[3] ? path.resolve(process.argv[3]) : null);
  console.log(`Rendered ${result.segmentCount} segments -> ${result.destination}`);
}

const invokedAsScript = process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href;
if (invokedAsScript) main().catch((error) => { console.error(error.stack ?? error.message); process.exitCode = 1; });
