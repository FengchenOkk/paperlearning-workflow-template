import { constants } from 'node:fs';
import { access, copyFile, mkdir, readFile, readdir, rename, rm, stat, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { renderTranslationFile } from '../../F-002-literature-pipeline/scripts/render-translation.mjs';

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url));
const featureRoot = path.resolve(scriptDirectory, '..');
const projectRoot = path.resolve(featureRoot, '..', '..');
const defaultConfigPath = path.join(featureRoot, 'config', 'collections.local.json');
const defaultLibraryRoot = path.join(projectRoot, 'research', 'literature');
const templateRoot = path.join(projectRoot, 'features', 'F-002-literature-pipeline', 'templates');
const templateNames = [
  '00-status.md', '01-bibliography.md', '02-translation.md', '03-deep-reading.md',
  '04-evidence.csv', '05-concepts.md', '06-related-literature.md', '07-review.md',
  '08-reader-summary.md',
];
const stateDirectories = ['10-queue', '20-active', '30-review', '40-library', '90-hold'];

function parseArguments(argv) {
  const options = {
    mode: 'sync', configPath: defaultConfigPath, libraryRoot: defaultLibraryRoot,
    apiBase: null, dryRun: false,
  };
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === '--check') options.mode = 'check';
    else if (argument === '--sync') options.mode = 'sync';
    else if (argument === '--dry-run') options.dryRun = true;
    else if (['--config', '--root', '--api-base'].includes(argument)) {
      const value = argv[index + 1];
      if (!value) throw new Error(`${argument} requires a value`);
      if (argument === '--config') options.configPath = path.resolve(value);
      else if (argument === '--root') options.libraryRoot = path.resolve(value);
      else options.apiBase = value;
      index += 1;
    } else throw new Error(`Unknown argument: ${argument}`);
  }
  return options;
}

function endpoint(apiBase, library, suffix) {
  return `${apiBase.replace(/\/$/, '')}/${library.replace(/^\//, '').replace(/\/$/, '')}/${suffix.replace(/^\//, '')}`;
}

async function fetchJson(url, fetchImpl = fetch) {
  let response;
  try {
    response = await fetchImpl(url, { headers: { 'Zotero-API-Version': '3' } });
  } catch (error) {
    throw new Error(`Cannot reach Zotero local API at ${url}: ${error.message}`);
  }
  if (!response.ok) throw new Error(`Zotero API ${response.status} ${response.statusText} for ${url}`);
  return { body: await response.json(), headers: response.headers };
}

async function fetchAll(url, fetchImpl = fetch) {
  const all = [];
  const separator = url.includes('?') ? '&' : '?';
  for (let start = 0; ; start += 100) {
    const { body } = await fetchJson(`${url}${separator}limit=100&start=${start}`, fetchImpl);
    if (!Array.isArray(body)) throw new Error(`Expected an array from ${url}`);
    all.push(...body);
    if (body.length < 100) return all;
  }
}

function creatorName(creator) {
  if (creator.name) return creator.name;
  return [creator.firstName, creator.lastName].filter(Boolean).join(' ');
}

function filePathFromAttachment(attachment) {
  const href = attachment.links?.enclosure?.href;
  if (!href?.startsWith('file:')) return null;
  try { return fileURLToPath(href); } catch { return null; }
}

async function pathExists(target) {
  if (!target) return false;
  try { await access(target); return true; }
  catch (error) { if (error.code === 'ENOENT') return false; throw error; }
}

function portableAttachment(attachment) {
  return {
    key: attachment.key,
    title: attachment.data?.title ?? '',
    filename: attachment.data?.filename ?? attachment.links?.enclosure?.title ?? '',
    content_type: attachment.data?.contentType ?? '',
    link_mode: attachment.data?.linkMode ?? '',
    md5: attachment.data?.md5 ?? null,
    bytes: attachment.links?.enclosure?.length ?? null,
    zotero_open_url: `zotero://open-pdf/library/items/${attachment.key}`,
  };
}

async function readCollection(config, mapping, fetchImpl) {
  const collectionUrl = endpoint(config.api_base, config.library, `collections/${mapping.key}`);
  const { body: collection } = await fetchJson(collectionUrl, fetchImpl);
  if (collection.data?.name !== mapping.name) {
    throw new Error(`Collection ${mapping.key} is named "${collection.data?.name}", expected "${mapping.name}"`);
  }
  const topItems = await fetchAll(`${collectionUrl}/items/top`, fetchImpl);
  const items = [];
  for (const item of topItems) {
    const children = item.meta?.numChildren
      ? await fetchAll(endpoint(config.api_base, config.library, `items/${item.key}/children`), fetchImpl)
      : [];
    const pdfs = children.filter((child) => child.data?.itemType === 'attachment'
      && child.data?.contentType === 'application/pdf');
    items.push({ item, pdfs });
  }
  return { collection, items };
}

function mergeItem(target, incoming, mapping) {
  if (!target) {
    const data = incoming.item.data ?? {};
    target = {
      item_key: incoming.item.key,
      item_version: incoming.item.version,
      item_type: data.itemType,
      title: data.title || '(untitled)',
      creators: (data.creators ?? []).map(creatorName).filter(Boolean),
      date: data.date ?? '',
      publication_title: data.publicationTitle ?? data.proceedingsTitle ?? '',
      volume: data.volume ?? '', issue: data.issue ?? '', pages: data.pages ?? '',
      doi: data.DOI ?? '', url: data.url ?? '', abstract: data.abstractNote ?? '',
      language: data.language ?? '', tags: (data.tags ?? []).map((tag) => tag.tag).filter(Boolean),
      zotero_select_url: `zotero://select/library/items/${incoming.item.key}`,
      collection_keys: [], collection_names: [], workstreams: [], topics: [], attachments: [],
    };
  }
  if (!target.collection_keys.includes(mapping.key)) target.collection_keys.push(mapping.key);
  if (!target.collection_names.includes(mapping.name)) target.collection_names.push(mapping.name);
  if (mapping.workstream && !target.workstreams.includes(mapping.workstream)) target.workstreams.push(mapping.workstream);
  if (mapping.topic && !target.topics.includes(mapping.topic)) target.topics.push(mapping.topic);
  for (const attachment of incoming.pdfs.map(portableAttachment)) {
    if (!target.attachments.some((existing) => existing.key === attachment.key)) target.attachments.push(attachment);
  }
  return target;
}

function slugify(value) {
  const slug = value.normalize('NFKC').toLowerCase()
    .replace(/[^\p{Letter}\p{Number}]+/gu, '-').replace(/^-+|-+$/g, '').slice(0, 72);
  return slug || 'paper';
}

async function findManifests(directory) {
  const found = [];
  let entries;
  try { entries = await readdir(directory, { withFileTypes: true }); }
  catch (error) { if (error.code === 'ENOENT') return found; throw error; }
  for (const entry of entries) {
    const entryPath = path.join(directory, entry.name);
    if (entry.isDirectory()) found.push(...await findManifests(entryPath));
    else if (entry.isFile() && entry.name === 'manifest.json') found.push(entryPath);
  }
  return found;
}

async function existingPackets(libraryRoot) {
  const packets = new Map();
  for (const stateDirectory of stateDirectories) {
    for (const manifestPath of await findManifests(path.join(libraryRoot, stateDirectory))) {
      const manifest = JSON.parse(await readFile(manifestPath, 'utf8'));
      const key = manifest.zotero?.item_key;
      if (!key) continue;
      if (packets.has(key)) throw new Error(`Duplicate reading packets for Zotero item ${key}`);
      packets.set(key, { manifestPath, manifest });
    }
  }
  return packets;
}

function buildManifest(item, previous = {}) {
  return {
    ...previous,
    schema_version: 2,
    paper_id: previous.paper_id ?? `zotero-${item.item_key}`,
    state: previous.state ?? 'queued',
    workstreams: item.workstreams,
    topics: item.topics,
    source_provenance: 'zotero-local-api',
    bibliographic_metadata_verified: previous.bibliographic_metadata_verified ?? false,
    zotero: {
      item_key: item.item_key,
      item_version: item.item_version,
      item_type: item.item_type,
      title: item.title,
      creators: item.creators,
      date: item.date,
      publication_title: item.publication_title,
      doi: item.doi,
      url: item.url,
      select_url: item.zotero_select_url,
      collection_keys: item.collection_keys,
      collection_names: item.collection_names,
      pdf_attachments: item.attachments,
      synced_at: new Date().toISOString(),
    },
  };
}

async function createPacket(libraryRoot, item) {
  const queueRoot = path.join(libraryRoot, '10-queue');
  const packetName = `${slugify(item.title)}--${item.item_key}`;
  const finalPacket = path.join(queueRoot, packetName);
  if (await pathExists(finalPacket)) throw new Error(`Packet path already exists: ${finalPacket}`);
  const temporaryPacket = path.join(queueRoot, `.sync-${packetName}-${process.pid}-${Date.now()}`);
  try {
    await mkdir(temporaryPacket, { recursive: true });
    for (const name of templateNames) {
      await copyFile(path.join(templateRoot, name), path.join(temporaryPacket, name), constants.COPYFILE_EXCL);
    }
    await writeFile(path.join(temporaryPacket, 'manifest.json'), `${JSON.stringify(buildManifest(item), null, 2)}\n`, { flag: 'wx' });
    await renderTranslationFile(path.join(temporaryPacket, '02-translation.md'));
    await rename(temporaryPacket, finalPacket);
    return finalPacket;
  } catch (error) {
    await rm(temporaryPacket, { recursive: true, force: true });
    throw error;
  }
}

function markdownCell(value) {
  return String(value ?? '').replace(/\|/g, '\\|').replace(/\r?\n/g, ' ');
}

function catalogMarkdown(items, generatedAt, packetIndex, libraryRoot) {
  const lines = [
    '# Zotero 文献索引', '',
    `生成时间：${generatedAt}`, '',
    '> 本文件由 `npm run zotero:sync` 生成。论文原件和主元数据在 Zotero 中管理。', '',
    '| Zotero | 标题 | 年份/日期 | 工作流 | PDF | 阅读包 | DOI |',
    '| --- | --- | --- | --- | ---: | --- | --- |',
  ];
  for (const item of items) {
    const packet = packetIndex.get(item.item_key);
    const relativeReader = packet
      ? path.relative(path.join(libraryRoot, '00-index'), path.join(path.dirname(packet.manifestPath), '02-translation.html')).replace(/\\/g, '/')
      : null;
    const readerLink = relativeReader ? `[对照阅读](${relativeReader})` : '—';
    lines.push(`| [${item.item_key}](${item.zotero_select_url}) | ${markdownCell(item.title)} | ${markdownCell(item.date)} | ${item.workstreams.join(', ')} | ${item.attachments.length} | ${readerLink} | ${markdownCell(item.doi)} |`);
  }
  if (items.length === 0) lines.push('| — | 当前映射集合尚无条目 | — | — | 0 | — | — |');
  lines.push('');
  return lines.join('\n');
}

export async function syncZotero({ configPath = defaultConfigPath, libraryRoot = defaultLibraryRoot, apiBase, dryRun = false, checkOnly = false, fetchImpl = fetch } = {}) {
  let configText;
  try { configText = await readFile(configPath, 'utf8'); }
  catch (error) {
    if (error.code === 'ENOENT') throw new Error(`Missing local Zotero config: ${configPath}. Run "npm run setup" and edit collections.local.json.`);
    throw error;
  }
  const config = JSON.parse(configText);
  if (apiBase) config.api_base = apiBase;
  if (!Array.isArray(config.collections) || config.collections.length === 0) throw new Error('No Zotero collections configured');
  const merged = new Map();
  const resolved = {};
  const checkedCollections = [];
  for (const mapping of config.collections) {
    const result = await readCollection(config, mapping, fetchImpl);
    checkedCollections.push({ key: mapping.key, name: mapping.name, item_count: result.items.length });
    for (const incoming of result.items) {
      const current = mergeItem(merged.get(incoming.item.key), incoming, mapping);
      merged.set(incoming.item.key, current);
      for (const attachment of incoming.pdfs) {
        const localPath = filePathFromAttachment(attachment);
        resolved[attachment.key] = {
          item_key: incoming.item.key,
          filename: attachment.data?.filename ?? '',
          local_path: localPath,
          exists: await pathExists(localPath),
        };
      }
    }
  }
  const items = [...merged.values()].sort((left, right) => left.title.localeCompare(right.title));
  if (checkOnly || dryRun) return { checkedCollections, items, created: [], updated: [], resolved };

  await Promise.all([
    mkdir(path.join(libraryRoot, '00-index'), { recursive: true }),
    mkdir(path.join(libraryRoot, '.local'), { recursive: true }),
    ...stateDirectories.map((directory) => mkdir(path.join(libraryRoot, directory), { recursive: true })),
  ]);
  const packets = await existingPackets(libraryRoot);
  const created = [];
  const updated = [];
  for (const item of items) {
    const existing = packets.get(item.item_key);
    if (existing) {
      await writeFile(existing.manifestPath, `${JSON.stringify(buildManifest(item, existing.manifest), null, 2)}\n`);
      updated.push(path.dirname(existing.manifestPath));
    } else created.push(await createPacket(libraryRoot, item));
  }
  const generatedAt = new Date().toISOString();
  const catalog = { schema_version: 1, generated_at: generatedAt, source: 'zotero-local-api', collections: checkedCollections, items };
  const refreshedPackets = await existingPackets(libraryRoot);
  await writeFile(path.join(libraryRoot, '00-index', 'catalog.json'), `${JSON.stringify(catalog, null, 2)}\n`);
  await writeFile(path.join(libraryRoot, '00-index', 'catalog.md'), catalogMarkdown(items, generatedAt, refreshedPackets, libraryRoot));
  await writeFile(path.join(libraryRoot, '.local', 'zotero-resolved.json'), `${JSON.stringify({ generated_at: generatedAt, attachments: resolved }, null, 2)}\n`);
  return { checkedCollections, items, created, updated, resolved };
}

function report(result, mode) {
  console.log(`Zotero ${mode} OK: ${result.checkedCollections.length} mapped collections, ${result.items.length} unique items.`);
  for (const collection of result.checkedCollections) console.log(`  ${collection.key} ${collection.name}: ${collection.item_count} items`);
  if (mode === 'sync') console.log(`Reading packets: ${result.created.length} created, ${result.updated.length} refreshed.`);
  const missingPdf = result.items.filter((item) => item.attachments.length === 0);
  const missingFiles = Object.values(result.resolved).filter((attachment) => !attachment.exists);
  if (missingPdf.length) console.warn(`WARNING: ${missingPdf.length} items have no PDF attachment.`);
  if (missingFiles.length) console.warn(`WARNING: ${missingFiles.length} PDF attachments are not present locally.`);
}

async function main() {
  const options = parseArguments(process.argv.slice(2));
  const result = await syncZotero({
    configPath: options.configPath,
    libraryRoot: options.libraryRoot,
    apiBase: options.apiBase,
    dryRun: options.dryRun,
    checkOnly: options.mode === 'check',
  });
  report(result, options.mode === 'check' || options.dryRun ? 'check' : 'sync');
}

const invokedAsScript = process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href;
if (invokedAsScript) main().catch((error) => { console.error(error.stack ?? error.message); process.exitCode = 1; });
