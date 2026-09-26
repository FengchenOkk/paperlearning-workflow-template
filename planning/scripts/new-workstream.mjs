import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const planningRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const projectRoot = path.resolve(planningRoot, '..');
const [id, slug, ...titleParts] = process.argv.slice(2);
const title = titleParts.join(' ').trim();

if (!/^WS-\d{3}$/.test(id ?? '') || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug ?? '') || !title) {
  console.error('Usage: npm run project:new -- WS-002 short-slug "工作流名称"');
  process.exit(2);
}

const directory = path.join(projectRoot, 'workstreams', `${id}-${slug}`);
const template = await readFile(path.join(planningRoot, 'templates', 'workstream.md'), 'utf8');
const content = template.replace('# WS-### 工作流名称', `# ${id} ${title}`);

try {
  await mkdir(directory, { recursive: false });
  await writeFile(path.join(directory, 'README.md'), content, { encoding: 'utf8', flag: 'wx' });
  console.log(`Created: ${directory}`);
  console.log('Next: add this workstream to PROJECT.md or planning/BACKLOG.md.');
} catch (error) {
  if (error.code === 'EEXIST') {
    console.error(`Workstream already exists: ${directory}`);
    process.exit(1);
  }
  throw error;
}
