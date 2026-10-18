#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';

export const SELECTOR_TARGETS = {
  English: 'README.md',
  '简体中文': '.github/docs/README-zh.md',
  日本語: '.github/docs/README-ja.md',
};
const README_RE = /(?:^|\/)README.*\.md$/i;
const REPOSITORY_BLOB_PREFIX = 'https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/';
const CODE_RE = /^```([^\r\n]*)\r?\n([\s\S]*?)^```[ \t]*$/gm;

function read(file) {
  return fs.readFileSync(file, 'utf8');
}

function relative(root, file) {
  return path.relative(root, file).split(path.sep).join('/');
}

export function discoverReadmes(root) {
  let names;
  try {
    names = execFileSync(
      'git',
      ['-C', root, 'ls-files', '-z', '--cached', '--others', '--exclude-standard'],
      { encoding: 'utf8' },
    );
  } catch {
    names = '';
  }
  if (!names) {
    const walk = (dir) => fs.readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
      if (entry.name === 'node_modules' || entry.name === '.git') return [];
      const full = path.join(dir, entry.name);
      return entry.isDirectory() ? walk(full) : [full];
    });
    return walk(root).filter((file) => README_RE.test(relative(root, file))).sort();
  }
  return names
    .split('\0')
    .filter(Boolean)
    .map((name) => path.join(root, name))
    .filter((file) => fs.existsSync(file) && README_RE.test(relative(root, file)))
    .sort();
}

function selectorTable(text) {
  const lines = text.split(/\r?\n/);
  for (let i = 0; i < lines.length - 2; i += 1) {
    if (!/^\s*\|.*English.*\|.*简体中文.*\|.*日本語.*\|\s*$/.test(lines[i])) continue;
    if (!/^\s*\|\s*:?-{3,}:?\s*\|\s*:?-{3,}:?\s*\|\s*:?-{3,}:?\s*\|\s*$/.test(lines[i + 1])) continue;
    return { header: lines[i], row: lines[i + 2] };
  }
  return null;
}

function cells(line) {
  return line.trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map((x) => x.trim());
}

function href(cell) {
  return cell.match(/!?(?:\[[^\]]*\])\(([^)]+)\)/)?.[1]?.split(/[?#]/)[0] ?? null;
}

export function validateSelector(file, root) {
  const text = read(file);
  const table = selectorTable(text);
  const errors = [];
  const display = relative(root, file);
  if (!table) return [`${display}: missing language selector table (English | 简体中文 | 日本語)`];
  const heads = cells(table.header);
  const row = cells(table.row);
  if (heads.length !== 3 || heads.join('|') !== 'English|简体中文|日本語' || row.length !== 3) {
    errors.push(`${display}: selector must be exactly a 3-column language table`);
  }
  if (table.row.includes('![')) errors.push(`${display}: selector table must not contain images`);

  for (const [index, label] of Object.keys(SELECTOR_TARGETS).entries()) {
    const link = href(row[index] ?? '');
    if (!link) {
      errors.push(`${display}: selector ${label} has no Markdown link`);
      continue;
    }
    const target = SELECTOR_TARGETS[label];
    let normalized;
    if (link.startsWith('http://') || link.startsWith('https://')) {
      if (!link.startsWith(REPOSITORY_BLOB_PREFIX)) {
        errors.push(`${display}: selector ${label} must use the repository GitHub blob/main URL`);
        continue;
      }
      normalized = link.slice(REPOSITORY_BLOB_PREFIX.length);
    } else {
      normalized = relative(root, path.resolve(path.dirname(file), link));
    }
    if (normalized !== target) errors.push(`${display}: selector ${label} must link to ${target}`);
    if (display === 'apps/server/README.md' && !link.startsWith(REPOSITORY_BLOB_PREFIX)) {
      errors.push(`${display}: selector links must use absolute github blob/main URLs`);
    }
  }
  return errors;
}

export function validateLocalLinks(file, root) {
  const text = read(file);
  const errors = [];
  const links = [];
  for (const match of text.matchAll(/!?(?:\[[^\]]*\])\(([^)]+)\)/g)) links.push(match[1]);
  for (const match of text.matchAll(/^\s*\[[^\]]+\]:\s*(\S+)/gm)) links.push(match[1]);
  for (const raw of links) {
    const target = raw.replace(/^<|>$/g, '').split(/[?#]/)[0];
    if (!target || /^(?:[a-z][a-z0-9+.-]*:|\/\/)/i.test(target)) continue;
    const resolved = path.resolve(path.dirname(file), target);
    if (!fs.existsSync(resolved)) errors.push(`${relative(root, file)}: broken local Markdown link ${raw}`);
  }
  return errors;
}

export function extractCode(text) {
  return [...text.matchAll(CODE_RE)].map((match) => ({ language: match[1], content: match[2] }));
}

export function requiredTokens(text) {
  const tokens = new Set();
  for (const line of text.split(/\r?\n/)) {
    if (!line.includes('|')) continue;
    for (const token of line.matchAll(/`([^`]+)`/g)) tokens.add(token[1]);
  }
  return tokens;
}

export function validateTranslations(root) {
  const english = path.join(root, 'README.md');
  const translations = [path.join(root, '.github/docs/README-zh.md'), path.join(root, '.github/docs/README-ja.md')];
  if (!fs.existsSync(english)) return [];
  const source = read(english);
  const sourceCode = extractCode(source);
  const sourceTokens = requiredTokens(source);
  const errors = [];
  for (const file of translations) {
    const display = relative(root, file);
    if (!fs.existsSync(file)) {
      errors.push(`${display}: translation file is missing`);
      continue;
    }
    const translated = read(file);
    const actualCode = extractCode(translated);
    if (sourceCode.length !== actualCode.length || sourceCode.some((block, i) => block.language !== actualCode[i]?.language || block.content !== actualCode[i]?.content)) {
      errors.push(`${display}: code blocks (including fence language and content) must match README.md exactly`);
    }
    const missing = [...sourceTokens].filter((token) => !requiredTokens(translated).has(token));
    if (missing.length) errors.push(`${display}: missing tool/config table tokens: ${missing.join(', ')}`);
  }
  return errors;
}

export function validateRepository(root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..')) {
  const files = discoverReadmes(root);
  const errors = files.flatMap((file) => [...validateSelector(file, root), ...validateLocalLinks(file, root)]);
  errors.push(...validateTranslations(root));
  return { files: files.map((file) => relative(root, file)), errors };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const result = validateRepository(process.argv[2] ? path.resolve(process.argv[2]) : undefined);
  if (result.errors.length) {
    console.error(result.errors.map((error) => `✖ ${error}`).join('\n'));
    process.exitCode = 1;
  } else {
    console.log(`README checks passed (${result.files.length} files)`);
  }
}
