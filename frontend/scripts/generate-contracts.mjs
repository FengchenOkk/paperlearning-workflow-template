import { compile } from 'json-schema-to-typescript';
import { readFile, writeFile } from 'node:fs/promises';
import { format } from 'prettier';

const schema = JSON.parse(
  await readFile(new URL('../../packages/schemas/domain.schema.json', import.meta.url), 'utf8'),
);
const definitions = schema.$defs;
// Compile once: independent compiles can assign the same alias to different field types.
const output = await format(
  '/* Generated from Pydantic; do not edit. */\n' +
    (await compile(
      {
        title: 'PaperGraphContracts',
        type: 'object',
        additionalProperties: false,
        properties: Object.fromEntries(
          Object.keys(definitions).map((name) => [name, { $ref: `#/$defs/${name}` }]),
        ),
        required: Object.keys(definitions),
        $defs: definitions,
      },
      'PaperGraphContracts',
      {
        bannerComment: '',
        additionalProperties: false,
        enableConstEnums: false,
        unknownAny: false,
      },
    )),
  { parser: 'typescript' },
);
const target = new URL('../src/contracts.ts', import.meta.url);
if (process.argv.includes('--check')) {
  if ((await readFile(target, 'utf8')) !== output) throw new Error('Generated contracts are stale');
} else await writeFile(target, output, 'utf8');
