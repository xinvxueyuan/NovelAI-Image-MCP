import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { validateLocalLinks, validateSelector, validateTranslations } from './check-readmes.mjs';

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
  const source = `${rootSelector}\n| Name | Value |\n|---|---|\n| ${tick}TOOL${tick} | enabled |\n| ${tick}MCP_AUTH_TOKEN${tick} | required |`;
  const f = fixture({ 'README.md': source, '.github/docs/README-zh.md': translation('', '| Name | Value |\n|---|---|\n| ${tick}TOOL${tick} | enabled |'), '.github/docs/README-ja.md': translation('') });
  try { assert.ok(validateTranslations(f.root).some((error) => error.includes('MCP_AUTH_TOKEN'))); } finally { f.cleanup(); }
});

test('rejects a missing tool table row even when code mentions the same name', () => {
  const source = `${rootSelector}\n\`\`\`python\nTOOL\n\`\`\`\n| Tool | Description |\n|---|---|\n| ${tick}TOOL${tick} | enabled |`;
  const f = fixture({ 'README.md': source, '.github/docs/README-zh.md': translation('```python\nTOOL\n```', '| Tool | Description |\n|---|---|'), '.github/docs/README-ja.md': translation('```python\nTOOL\n```') });
  try { assert.ok(validateTranslations(f.root).some((error) => error.includes('TOOL'))); } finally { f.cleanup(); }
});

test('accepts complete synchronized English, Chinese, and Japanese READMEs', () => {
  const source = `${rootSelector}\n\`\`\`bash\necho ok\n\`\`\`\n| Name | Value |\n|---|---|\n| ${tick}TOOL${tick} | enabled |\n| ${tick}MCP_AUTH_TOKEN${tick} | required |`;
  const f = fixture({ 'README.md': source, '.github/docs/README-zh.md': translation('```bash\necho ok\n```'), '.github/docs/README-ja.md': translation('```bash\necho ok\n```') });
  try { assert.deepEqual(validateTranslations(f.root), []); } finally { f.cleanup(); }
});
