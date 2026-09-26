import { spawn } from 'node:child_process';
import { randomUUID } from 'node:crypto';
import { createWriteStream } from 'node:fs';
import { mkdir, readFile, realpath, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const featureRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const projectRoot = path.resolve(featureRoot, '..', '..');
const modelPatch = path.join(featureRoot, 'config', 'dsh.patch.yml');

function usage() {
  console.error('Usage: node features/F-001-deepseek-worker/scripts/dsh-task.mjs --check | --task-file <project-relative UTF-8 file>');
  process.exitCode = 2;
}

async function dshEntry() {
  const packageDir = path.join(projectRoot, 'node_modules', '@deepseek-ai', 'dsh');
  let metadata;
  try {
    metadata = JSON.parse(await readFile(path.join(packageDir, 'package.json'), 'utf8'));
  } catch {
    throw new Error('DSH is not installed. Run npm install in the project directory.');
  }
  const bin = typeof metadata.bin === 'string' ? metadata.bin : metadata.bin?.dsh;
  if (!bin) throw new Error('The installed DSH package has no dsh executable.');
  return { entry: path.resolve(packageDir, bin), version: metadata.version };
}

function run(entry, args, options = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [entry, ...args], {
      cwd: projectRoot,
      env: { ...process.env, DSH_HOME: path.join(featureRoot, '.dsh-home') },
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    let stdout = '';
    let stderr = '';
    child.stdout.setEncoding('utf8');
    child.stderr.setEncoding('utf8');
    child.stdout.on('data', chunk => {
      if (options.onStdout) options.onStdout(chunk);
      else stdout += chunk;
    });
    child.stderr.on('data', chunk => {
      if (options.onStderr) options.onStderr(chunk);
      else stderr += chunk;
    });
    child.stdin.on('error', error => {
      if (error.code !== 'EPIPE') reject(error);
    });
    child.once('error', reject);
    child.once('close', code => resolve({ code, stdout, stderr }));
    child.stdin.end(options.stdin ?? '');
  });
}

async function main() {
  const args = process.argv.slice(2);
  if (!(args.length === 1 && args[0] === '--check') &&
      !(args.length === 2 && args[0] === '--task-file')) {
    usage();
    return;
  }

  const { entry, version } = await dshEntry();
  if (args[0] === '--check') {
    const result = await run(entry, ['--profile', 'headless', '--patch', modelPatch, '--help']);
    if (result.code !== 0) throw new Error(result.stderr.trim() || 'DSH headless profile check failed.');
    console.log(`DSH headless profile ready: ${version}; model: deepseek-flash`);
    console.log('No API request was made. A real task still requires a valid DeepSeek credential.');
    return;
  }

  const taskPath = await realpath(path.resolve(projectRoot, args[1]));
  const relative = path.relative(projectRoot, taskPath);
  if (relative.startsWith('..') || path.isAbsolute(relative)) {
    throw new Error('Task file must be inside this project.');
  }
  const task = await readFile(taskPath, 'utf8');
  if (!task.trim()) throw new Error('Task file is empty.');

  const runId = `${new Date().toISOString().replace(/[:.]/g, '-')}-${randomUUID().slice(0, 8)}`;
  const runDir = path.join(featureRoot, '.runtime', 'runs', runId);
  await mkdir(runDir, { recursive: true });
  await writeFile(path.join(runDir, 'task.txt'), task, 'utf8');

  const events = createWriteStream(path.join(runDir, 'events.jsonl'), { encoding: 'utf8' });
  const diagnostics = createWriteStream(path.join(runDir, 'stderr.log'), { encoding: 'utf8' });
  let pending = '';
  let finalText;
  let sessionId;
  let invalidLines = 0;
  const ingest = line => {
    if (!line.trim()) return;
    events.write(`${line}\n`);
    try {
      const event = JSON.parse(line);
      if (event.type === 'session') sessionId = event.sessionId;
      if (event.type === 'final') finalText = event.text;
    } catch {
      invalidLines += 1;
    }
  };

  const startedAt = new Date().toISOString();
  let result;
  try {
    result = await run(entry, ['--profile', 'headless', '--patch', modelPatch, '--json', '-'], {
      stdin: task,
      onStdout(chunk) {
        pending += chunk;
        let newline;
        while ((newline = pending.indexOf('\n')) >= 0) {
          ingest(pending.slice(0, newline));
          pending = pending.slice(newline + 1);
        }
      },
      onStderr(chunk) { diagnostics.write(chunk); },
    });
    if (pending) ingest(pending);
  } finally {
    await Promise.all([
      new Promise(resolve => events.end(resolve)),
      new Promise(resolve => diagnostics.end(resolve)),
    ]);
  }

  if (typeof finalText === 'string') {
    await writeFile(path.join(runDir, 'answer.md'), finalText, 'utf8');
  }
  const success = result.code === 0 && typeof finalText === 'string' && invalidLines === 0;
  await writeFile(path.join(runDir, 'run.json'), JSON.stringify({
    status: success ? 'completed' : 'failed',
    dshVersion: version,
    sessionId,
    startedAt,
    endedAt: new Date().toISOString(),
    exitCode: result.code,
    invalidEventLines: invalidLines,
    taskFile: relative,
  }, null, 2) + '\n', 'utf8');
  console.log(`Run directory: ${runDir}`);
  if (!success) {
    throw new Error(`DSH did not complete successfully. Inspect run.json, events.jsonl, and stderr.log in ${runDir}.`);
  }
  console.log(`Answer: ${path.join(runDir, 'answer.md')}`);
}

main().catch(error => {
  console.error(error.message);
  process.exitCode = 1;
});
