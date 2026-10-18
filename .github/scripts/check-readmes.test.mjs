import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { discoverReadmes, extractCode, validateLocalLinks, validateSelector, validateTranslations } from './check-readmes.mjs';

const rootSelector = '| English | 简体中文 | 日本語 |\n|---|---|---|\n| [English](README.md) | [简体中文](.github/docs/README-zh.md) | [日本語](.github/docs/README-ja.md) |';
const tick = String.fromCharCode(96);
const tableTokens = `| Name | Value |\n|---|---|\n| ${tick}TOOL${tick} | enabled |\n| ${tick}MCP_AUTH_TOKEN${tick} | required |`;
const nestedSelector = '| English | 简体中文 | 日本語 |\n|---|---|---|\n| [English](../../README.md) | [简体中文](README-zh.md) | [日本語](README-ja.md) |';

function fixture(files) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'readme-check-'));
  for (const [name, content] of Object.entries(files)) {
    const file = path.join(root, name);
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.writeFileSync(file, content);
  }
  return { root, cleanup: () => fs.rmSync(root, { recursive: true, force: true }) };
}

function translation(code, table = tableTokens) {
  return `${nestedSelector}\n# Translation\n${code}\n${table}\n`;
}

function selectorErrors(files, name = 'README.md') {
  const f = fixture(files);
  try { return validateSelector(path.join(f.root, name), f.root); } finally { f.cleanup(); }
}

test('accepts a valid root selector and local link', () => {
  const f = fixture({ 'README.md': `${rootSelector}\n[guide](guide.md)`, 'guide.md': '# guide', '.github/docs/README-zh.md': '# zh', '.github/docs/README-ja.md': '# ja' });
  try {
    assert.deepEqual(validateSelector(path.join(f.root, 'README.md'), f.root), []);
    assert.deepEqual(validateLocalLinks(path.join(f.root, 'README.md'), f.root), []);
  } finally { f.cleanup(); }
});

test('resolves selector links relative to a nested README directory', () => {
  const f = fixture({ '.github/docs/README-zh.md': nestedSelector, 'README.md': '', '.github/docs/README-ja.md': '' });
  try { assert.deepEqual(validateSelector(path.join(f.root, '.github/docs/README-zh.md'), f.root), []); } finally { f.cleanup(); }
});

test('rejects an absolute selector URL for the wrong owner or repository', () => {
  const selector = rootSelector.replace('README.md)', 'https://github.com/other/project/blob/main/README.md)');
  assert.ok(selectorErrors({ 'README.md': selector }).some((error) => error.includes('repository GitHub')));
});

test('rejects an image selector cell', () => {
  const selector = rootSelector.replace('[English](README.md)', '![English](README.md)');
  assert.ok(selectorErrors({ 'README.md': selector }).some((error) => error.includes('must not contain images')));
});

test('rejects a selector with a missing configuration row', () => {
  const selector = '| English | 简体中文 | 日本語 |\n|---|---|---|\n| [English](README.md) | [简体中文](.github/docs/README-zh.md) | |';
  assert.ok(selectorErrors({ 'README.md': selector }).some((error) => error.includes('日本語 has no Markdown link')));
});

test('rejects a broken local Markdown link', () => {
  const f = fixture({ 'README.md': `${rootSelector}\n[missing](no-such.md)` });
  try { assert.ok(validateLocalLinks(path.join(f.root, 'README.md'), f.root).some((error) => error.includes('no-such.md'))); } finally { f.cleanup(); }
});

test('rejects missing translation files', () => {
  const f = fixture({ 'README.md': rootSelector });
  try { assert.ok(validateTranslations(f.root).some((error) => error.includes('README-zh.md'))); } finally { f.cleanup(); }
});

test('rejects a changed code-fence language', () => {
  const source = `${rootSelector}\n\`\`\`bash\necho ok\n\`\`\`\n| ${tick}TOOL${tick} | enabled |`;
  const f = fixture({ 'README.md': source, '.github/docs/README-zh.md': translation('```shell\necho ok\n```'), '.github/docs/README-ja.md': translation('```bash\necho ok\n```') });
  try { assert.ok(validateTranslations(f.root).some((error) => error.includes('code blocks'))); } finally { f.cleanup(); }
});

test('rejects changed code-fence content byte-for-byte', () => {
  const source = `${rootSelector}\n\`\`\`bash\necho ok\n\`\`\`\n| ${tick}TOOL${tick} | enabled |`;
  const f = fixture({ 'README.md': source, '.github/docs/README-zh.md': translation('```bash\necho  ok\n```'), '.github/docs/README-ja.md': translation('```bash\necho ok\n```') });
  try { assert.ok(validateTranslations(f.root).some((error) => error.includes('code blocks'))); } finally { f.cleanup(); }
});

test('rejects a missing configuration table token', () => {
  const source = `${rootSelector}\n\n| Name | Value |\n|---|---|\n| ${tick}TOOL${tick} | enabled |\n| ${tick}MCP_AUTH_TOKEN${tick} | required |`;
  const f = fixture({ 'README.md': source, '.github/docs/README-zh.md': translation('', `| Name | Value |\n|---|---|\n| ${tick}TOOL${tick} | enabled |`), '.github/docs/README-ja.md': translation('') });
  try { assert.ok(validateTranslations(f.root).some((error) => error.includes('MCP_AUTH_TOKEN'))); } finally { f.cleanup(); }
});

test('rejects a missing tool table row even when code mentions the same name', () => {
  const source = `${rootSelector}\n\`\`\`python\nTOOL\n\`\`\`\n| Tool | Description |\n|---|---|\n| ${tick}TOOL${tick} | enabled |`;
  const f = fixture({ 'README.md': source, '.github/docs/README-zh.md': translation('```python\nTOOL\n```', `| Tool | Description |\n|---|---|`), '.github/docs/README-ja.md': translation('```python\nTOOL\n```') });
  try { assert.ok(validateTranslations(f.root).some((error) => error.includes('TOOL'))); } finally { f.cleanup(); }
});

test('accepts complete synchronized English, Chinese, and Japanese READMEs', () => {
  const source = `${rootSelector}\n\`\`\`bash\necho ok\n\`\`\`\n| Name | Value |\n|---|---|\n| ${tick}TOOL${tick} | enabled |\n| ${tick}MCP_AUTH_TOKEN${tick} | required |`;
  const f = fixture({ 'README.md': source, '.github/docs/README-zh.md': translation('```bash\necho ok\n```'), '.github/docs/README-ja.md': translation('```bash\necho ok\n```') });
  try { assert.deepEqual(validateTranslations(f.root), []); } finally { f.cleanup(); }
});


test('rejects README symlinks and special files without reading them', { skip: process.platform === 'win32' }, () => {
  const f = fixture({ 'README.md': rootSelector });
  try {
    fs.renameSync(path.join(f.root, 'README.md'), path.join(f.root, 'real.md'));
    fs.symlinkSync('real.md', path.join(f.root, 'README.md'));
    assert.ok(validateLocalLinks(path.join(f.root, 'README.md'), f.root).some((error) => error.includes('symbolic link')));
    fs.rmSync(path.join(f.root, 'README.md'));
    execFileSync('mkfifo', [path.join(f.root, 'README.md')]);
    assert.ok(validateLocalLinks(path.join(f.root, 'README.md'), f.root).some((error) => error.includes('non-regular')));
  } finally { f.cleanup(); }
});

test('rejects an oversized README before allocating or reading it', () => {
  const f = fixture({ 'README.md': 'x'.repeat(2 * 1024 * 1024 + 1) });
  try { assert.ok(validateLocalLinks(path.join(f.root, 'README.md'), f.root).some((error) => error.includes('exceeds'))); } finally { f.cleanup(); }
});

test('decodes valid local URI paths and reports malformed URI syntax', () => {
  const f = fixture({ 'README.md': '[space](a%20b.md) [中文](%E4%B8%AD.md) [hash](hash%23name.md) [bad](bad%ZZ.md)', 'a b.md': '', '中.md': '', 'hash#name.md': '' });
  try {
    const errors = validateLocalLinks(path.join(f.root, 'README.md'), f.root);
    assert.equal(errors.filter((error) => error.includes('broken')).length, 0);
    assert.ok(errors.some((error) => error.includes('malformed URI')));
  } finally { f.cleanup(); }
});

test('decodes selector paths before resolving query and fragment', () => {
  const selector = rootSelector.replace('(README.md)', '(README%2Emd?view=1#top)');
  assert.deepEqual(selectorErrors({ 'README.md': selector }), []);
});

test('extracts tilde fences, longer closures, and preserves content bytes', () => {
  const text = '  ~~~~python\r\n a  \r\n~~~~~~ \r\n```js\npipe | stays\n````\n';
  assert.deepEqual(extractCode(text), [{ language: 'python', content: ' a  \r\n' }, { language: 'js', content: 'pipe | stays\n' }]);
});

test('requires matching fence character and leaves a shorter or mixed closure unclosed', () => {
  assert.deepEqual(extractCode('```js\na\n``\n'), [{ language: 'js', content: 'a\n``\n' }]);
  assert.deepEqual(extractCode('~~~js\na\n~`~\n'), [{ language: 'js', content: 'a\n~`~\n' }]);
});

test('does not treat pipe characters inside unclosed code as table rows', () => {
  const code = '~~~text\n| `FAKE` | not a table |\n';
  const source = `${rootSelector}\n\n| Tool | Description |\n|---|---|\n| ${tick}TOOL${tick} | enabled |\n\n${code}`;
  const target = `${nestedSelector}\n\n${code}`;
  const f = fixture({ 'README.md': source, '.github/docs/README-zh.md': target, '.github/docs/README-ja.md': target });
  try { assert.ok(validateTranslations(f.root).some((error) => error.includes('missing table'))); } finally { f.cleanup(); }
});

test('rejects duplicate, missing, empty-description, and changed-default table rows', () => {
  const source = `${rootSelector}\n\n| Variable | Default | Notes |\n|---|---|---|\n| ${tick}A${tick} | one | Alpha |\n| ${tick}B${tick} | two | Beta |`;
  const f = fixture({ 'README.md': source, '.github/docs/README-zh.md': translation('', '| Variable | Default | Notes |\n|---|---|---|\n| `A` | changed | |\n| `A` | changed | duplicate |'), '.github/docs/README-ja.md': translation('', '| Variable | Default | Notes |\n|---|---|---|\n| `A` | changed | |\n| `A` | changed | duplicate |') });
  try { const errors = validateTranslations(f.root); assert.ok(errors.some((error) => error.includes('duplicate') || error.includes('rows do not match'))); assert.ok(errors.length >= 2); assert.ok(errors.some((error) => error.includes('B'))); } finally { f.cleanup(); }
});

test('rejects translated table column-count changes', () => {
  const source = `${rootSelector}\n\n| Tool | Description |\n|---|---|\n| ${tick}TOOL${tick} | enabled |`;
  const f = fixture({ 'README.md': source, '.github/docs/README-zh.md': translation('', '| Tool | Description | Extra |\n|---|---|---|\n| `TOOL` | 可用 | x |'), '.github/docs/README-ja.md': translation('', '| Tool | Description | Extra |\n|---|---|---|\n| `TOOL` | 有効 | x |') });
  try { assert.ok(validateTranslations(f.root).some((error) => error.includes('inconsistent column count') || error.includes('rows do not match'))); } finally { f.cleanup(); }
});

function tableErrors(sourceTable, targetTable) {
  const f = fixture({
    'README.md': `${rootSelector}\n\n${sourceTable}`,
    '.github/docs/README-zh.md': translation('', targetTable),
    '.github/docs/README-ja.md': translation('', sourceTable),
  });
  try { return validateTranslations(f.root); } finally { f.cleanup(); }
}

test('checks combined variable rows independently of repeated identifiers in descriptions', () => {
  const source = '| Variable | Default | Notes |\n|---|---|---|\n| `A` / `B` | — | Login |\n| `C` | out | Output |';
  const target = '| Variable | Default | Notes |\n|---|---|---|\n| `C` | out | See `A` / `B` |';
  assert.ok(tableErrors(source, target).some((error) => error.includes('missing A / B')));
});

test('checks default values by identifier even when configuration rows are reordered', () => {
  const source = '| Variable | Default | Notes |\n|---|---|---|\n| `A` / `B` | — | Login |\n| `C` | out | Output |';
  const target = '| Variable | Default | Notes |\n|---|---|---|\n| `C` | out | 输出 |\n| `A` / `B` | changed | 登录 |';
  assert.ok(tableErrors(source, target).some((error) => error.includes('default value changed for A / B')));
  assert.deepEqual(tableErrors(source, target.replace('| changed |', '| — |')), []);
});

test('accepts translated table descriptions without equating prose across languages', () => {
  const source = '| Tool | Description |\n|---|---|\n| `TOOL` | Generate an image |';
  const target = '| 工具 | 说明 |\n|---|---|\n| `TOOL` | 生成图像 |';
  assert.deepEqual(tableErrors(source, target), []);
});

test('rejects a table row replaced with another row that merely mentions its identifier', () => {
  const source = '| Tool | Description |\n|---|---|\n| `A` | First |\n| `B` | Second |';
  const target = '| Tool | Description |\n|---|---|\n| `A` | Mentions `B` |';
  assert.ok(tableErrors(source, target).some((error) => error.includes('missing B')));
});

test('rejects directories as README input without opening them', () => {
  const f = fixture({});
  try {
    fs.mkdirSync(path.join(f.root, 'README.md'));
    assert.ok(validateLocalLinks(path.join(f.root, 'README.md'), f.root).some((error) => error.includes('non-regular')));
  } finally { f.cleanup(); }
});

test('discovers dangling README symlinks and rejects device symlinks before reading', { skip: process.platform === 'win32' }, () => {
  const f = fixture({});
  try {
    fs.symlinkSync('missing.md', path.join(f.root, 'README.md'));
    assert.ok(discoverReadmes(f.root).includes(path.join(f.root, 'README.md')));
    assert.ok(validateLocalLinks(path.join(f.root, 'README.md'), f.root).some((error) => error.includes('symbolic link')));
    fs.rmSync(path.join(f.root, 'README.md'));
    fs.symlinkSync('/dev/zero', path.join(f.root, 'README.md'));
    assert.ok(validateLocalLinks(path.join(f.root, 'README.md'), f.root).some((error) => error.includes('symbolic link')));
  } finally { f.cleanup(); }
});

test('processes many opening fence lines as a single unterminated block', () => {
  const content = '```python\n'.repeat(10000);
  const blocks = extractCode(content);
  assert.equal(blocks.length, 1);
  assert.equal(blocks[0].content, '```python\n'.repeat(9999));
});

test('requires only whitespace after a closing fence and compares full info strings', () => {
  assert.deepEqual(extractCode('~~~python\na\n~~~ trailing\nb\n~~~~\n'), [
    { language: 'python', content: 'a\n~~~ trailing\nb\n' },
  ]);
  assert.equal(extractCode('```python title=example\na\n```')[0].language, 'python title=example');
});

test('detects different code in tilde fences in translations', () => {
  const f = fixture({
    'README.md': `${rootSelector}\n~~~bash\necho ok\n~~~`,
    '.github/docs/README-zh.md': translation('~~~bash\necho wrong\n~~~', ''),
    '.github/docs/README-ja.md': translation('~~~bash\necho ok\n~~~', ''),
  });
  try { assert.ok(validateTranslations(f.root).some((error) => error.includes('code blocks'))); } finally { f.cleanup(); }
});
