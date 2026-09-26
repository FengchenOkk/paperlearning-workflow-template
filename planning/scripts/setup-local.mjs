import { constants } from 'node:fs';
import { copyFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url));
const defaultProjectRoot = path.resolve(scriptDirectory, '..', '..');

async function copyIfMissing(source, destination) {
  await mkdir(path.dirname(destination), { recursive: true });
  try {
    await copyFile(source, destination, constants.COPYFILE_EXCL);
    return 'created';
  } catch (error) {
    if (error.code === 'EEXIST') return 'kept';
    throw error;
  }
}

export async function initializeLocalWorkspace(projectRoot = defaultProjectRoot) {
  const copies = [
    ['PROJECT.example.md', 'PROJECT.md'],
    ['planning/BACKLOG.example.md', 'planning/BACKLOG.md'],
    ['planning/DECISIONS.example.md', 'planning/DECISIONS.md'],
    ['planning/ROADMAP.example.md', 'planning/ROADMAP.md'],
    ['features/F-003-zotero-bridge/config/collections.example.json', 'features/F-003-zotero-bridge/config/collections.local.json'],
  ];
  const results = [];
  for (const [source, destination] of copies) {
    results.push({ destination, status: await copyIfMissing(path.join(projectRoot, source), path.join(projectRoot, destination)) });
  }
  const directories = [
    'research/literature/00-index', 'research/literature/10-queue', 'research/literature/20-active',
    'research/literature/30-review', 'research/literature/40-library', 'research/literature/90-hold',
    'outputs', 'workstreams',
  ];
  await Promise.all(directories.map((directory) => mkdir(path.join(projectRoot, directory), { recursive: true })));
  return results;
}

async function main() {
  const rootArgument = process.argv[2];
  const results = await initializeLocalWorkspace(rootArgument ? path.resolve(rootArgument) : defaultProjectRoot);
  for (const result of results) console.log(`${result.status.toUpperCase()} ${result.destination}`);
  console.log('Local private workspace is ready. Edit collections.local.json before Zotero sync.');
}

const invokedAsScript = process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href;
if (invokedAsScript) main().catch((error) => { console.error(error.stack ?? error.message); process.exitCode = 1; });
