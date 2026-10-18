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
const MAX_README_BYTES = 2 * 1024 * 1024;

function read(file) {
  const stat = fs.lstatSync(file);
  if (stat.isSymbolicLink()) throw new Error(`refuses symbolic link ${file}`);
  if (!stat.isFile()) throw new Error(`refuses non-regular file ${file}`);
  if (stat.size > MAX_README_BYTES) {
    throw new Error(`file exceeds ${MAX_README_BYTES} byte limit: ${file}`);
  }
  let fd;
  try {
    // NOFOLLOW prevents symlink replacement; NONBLOCK avoids a swapped FIFO hanging open().
    const flags = fs.constants.O_RDONLY | (fs.constants.O_NOFOLLOW ?? 0) | (fs.constants.O_NONBLOCK ?? 0);
    fd = fs.openSync(file, flags);
    const opened = fs.fstatSync(fd);
    if (!opened.isFile() || opened.size > MAX_README_BYTES || opened.dev !== stat.dev || opened.ino !== stat.ino) {
      throw new Error(`file changed to an unsafe or oversized file: ${file}`);
    }
    const buffer = Buffer.alloc(opened.size);
    let offset = 0;
    while (offset < buffer.length) {
      const count = fs.readSync(fd, buffer, offset, buffer.length - offset, null);
      if (!count) break;
      offset += count;
    }
    if (offset !== opened.size) throw new Error(`short read while reading ${file}`);
    return buffer.toString('utf8');
  } finally {
    if (fd !== undefined) fs.closeSync(fd);
  }
}

function safeRead(file, root) {
  try {
    return { text: read(file), errors: [] };
  } catch (error) {
    return { text: '', errors: [`${relative(root, file)}: ${error.message}`] };
  }
}

function relative(root, file) {
  return path.relative(root, file).split(path.sep).join('/');
}

function exists(file) {
  try {
    fs.lstatSync(file);
    return true;
  } catch {
    return false;
  }
}

export function discoverReadmes(root) {
  let names;
  try {
    names = execFileSync('git', ['-C', root, 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] });
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
  // lstat keeps dangling README symlinks visible to the safety check, but ignores deleted files.
  return names.split('\0').filter(Boolean).map((name) => path.join(root, name))
    .filter((file) => README_RE.test(relative(root, file)) && exists(file)).sort();
}

function cells(line) {
  return line.trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map((cell) => cell.trim());
}

function isSeparator(line) {
  const row = cells(line);
  return row.length > 0 && row.every((cell) => /^:?-{3,}:?$/.test(cell));
}

function parseFences(text) {
  const lines = text.match(/[^\n]*\n|[^\n]+$/g) ?? [];
  const blocks = [];
  const masked = new Set();
  let open = null;
  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i].replace(/\r?\n$/, '');
    if (!open) {
      const match = line.match(/^ {0,3}(`{3,}|~{3,})([^\r\n]*)$/);
      // Backtick fence info strings cannot themselves contain backticks.
      if (match && !(match[1][0] === '`' && match[2].includes('`'))) {
        open = { char: match[1][0], length: match[1].length, language: match[2].trim(), contentStart: i + 1 };
        masked.add(i);
      }
      continue;
    }
    masked.add(i);
    const close = line.match(/^ {0,3}(`{3,}|~{3,})[ \t]*$/);
    if (close && close[1][0] === open.char && close[1].length >= open.length) {
      blocks.push({ language: open.language, content: lines.slice(open.contentStart, i).join('') });
      open = null;
    }
  }
  // CommonMark closes an unterminated fence at EOF without rescanning opening lines.
  if (open) blocks.push({ language: open.language, content: lines.slice(open.contentStart).join('') });
  return { lines, blocks, masked };
}

export function extractCode(text) {
  return parseFences(text).blocks;
}

function href(cell) {
  return cell.match(/!?\[[^\]]*\]\(([^)]+)\)/)?.[1] ?? null;
}

function stripQueryFragment(raw) {
  const clean = raw.replace(/^<|>$/g, '');
  const cut = clean.search(/[?#]/);
  return cut < 0 ? clean : clean.slice(0, cut);
}

function decodeLocal(raw) {
  try {
    return { target: decodeURIComponent(stripQueryFragment(raw)) };
  } catch {
    return { error: `malformed URI in local Markdown path ${raw}` };
  }
}

function selectorTable(text) {
  const lines = text.split(/\r?\n/);
  for (let i = 0; i < lines.length - 2; i += 1) {
    if (cells(lines[i]).join('|') === 'English|简体中文|日本語' && isSeparator(lines[i + 1])) {
      return { row: lines[i + 2] };
    }
  }
  return null;
}

export function validateSelector(file, root) {
  const loaded = safeRead(file, root);
  if (loaded.errors.length) return loaded.errors;
  const display = relative(root, file);
  const table = selectorTable(loaded.text);
  const errors = [];
  if (!table) return [`${display}: missing language selector table (English | 简体中文 | 日本語)`];
  const row = cells(table.row);
  if (row.length !== 3) errors.push(`${display}: selector must be exactly a 3-column language table`);
  if (table.row.includes('![')) errors.push(`${display}: selector table must not contain images`);
  for (const [index, label] of Object.keys(SELECTOR_TARGETS).entries()) {
    const raw = href(row[index] ?? '');
    if (!raw) {
      errors.push(`${display}: selector ${label} has no Markdown link`);
      continue;
    }
    let normalized;
    if (/^https?:\/\//i.test(raw)) {
      if (!raw.startsWith(REPOSITORY_BLOB_PREFIX)) {
        errors.push(`${display}: selector ${label} must use the repository GitHub blob/main URL`);
        continue;
      }
      normalized = stripQueryFragment(raw).slice(REPOSITORY_BLOB_PREFIX.length);
    } else {
      const decoded = decodeLocal(raw);
      if (decoded.error) {
        errors.push(`${display}: ${decoded.error}`);
        continue;
      }
      normalized = relative(root, path.resolve(path.dirname(file), decoded.target));
    }
    if (normalized !== SELECTOR_TARGETS[label]) errors.push(`${display}: selector ${label} must link to ${SELECTOR_TARGETS[label]}`);
    if (display === 'apps/server/README.md' && !raw.startsWith(REPOSITORY_BLOB_PREFIX)) {
      errors.push(`${display}: selector links must use absolute github blob/main URLs`);
    }
  }
  return errors;
}

export function validateLocalLinks(file, root) {
  const loaded = safeRead(file, root);
  if (loaded.errors.length) return loaded.errors;
  const errors = [];
  const links = [];
  for (const match of loaded.text.matchAll(/!?\[[^\]]*\]\(([^)]+)\)/g)) links.push(match[1]);
  for (const match of loaded.text.matchAll(/^\s*\[[^\]]+\]:\s*(\S+)/gm)) links.push(match[1]);
  for (const raw of links) {
    // External URLs are not local paths and must not be decoded by the local-file checker.
    if (/^(?:[a-z][a-z0-9+.-]*:|\/\/)/i.test(raw.replace(/^</, ''))) continue;
    const decoded = decodeLocal(raw);
    if (decoded.error) {
      errors.push(`${relative(root, file)}: ${decoded.error}`);
      continue;
    }
    if (!decoded.target) continue;
    const resolved = path.resolve(path.dirname(file), decoded.target);
    if (!fs.existsSync(resolved)) errors.push(`${relative(root, file)}: broken local Markdown link ${raw}`);
  }
  return errors;
}

function markdownTables(text) {
  const { lines, masked } = parseFences(text);
  const tables = [];
  for (let i = 0; i + 1 < lines.length;) {
    if (masked.has(i) || masked.has(i + 1) || !lines[i].includes('|') || !isSeparator(lines[i + 1])) {
      i += 1;
      continue;
    }
    const rows = [];
    let j = i + 2;
    while (j < lines.length && !masked.has(j) && lines[j].includes('|') && lines[j].trim()) {
      rows.push(cells(lines[j]));
      j += 1;
    }
    tables.push({ header: cells(lines[i]), rows });
    i = j;
  }
  return tables;
}

function rowKey(row) {
  // Combined settings such as `NOVELAI_USERNAME` / `NOVELAI_PASSWORD` form one required row.
  return [...(row[0] ?? '').matchAll(/`([^`]+)`/g)].map((match) => match[1]).join(' / ');
}

function validateTables(source, target, display) {
  const errors = [];
  const sourceTables = markdownTables(source);
  const targetTables = markdownTables(target);
  for (const [index, expected] of sourceTables.entries()) {
    const identifiers = expected.rows.map(rowKey).filter(Boolean);
    if (!identifiers.length) continue;
    const actual = targetTables[index];
    if (!actual) {
      errors.push(`${display}: missing table ${index + 1}`);
      continue;
    }
    if (expected.header.length !== actual.header.length) errors.push(`${display}: table ${index + 1} has inconsistent column count`);
    const byIdentifier = new Map();
    for (const row of actual.rows) {
      const key = rowKey(row);
      if (row.length !== expected.header.length) errors.push(`${display}: table ${index + 1} has inconsistent column count`);
      if (row.slice(1).some((cell) => !cell)) errors.push(`${display}: table ${index + 1} has an empty description/default cell`);
      if (byIdentifier.has(key)) errors.push(`${display}: duplicate table row ${key}`);
      byIdentifier.set(key, row);
    }
    const missing = identifiers.filter((id) => !byIdentifier.has(id));
    const unexpected = [...byIdentifier.keys()].filter((id) => !identifiers.includes(id));
    if (missing.length || unexpected.length || actual.rows.length !== expected.rows.length) {
      errors.push(`${display}: table ${index + 1} rows do not match English identifiers: missing ${missing.join(', ')}; unexpected ${unexpected.join(', ')}`);
    }
    // Description prose is translated freely; configuration defaults are literal values.
    if (expected.header.length >= 3) {
      for (const row of expected.rows) {
        const translated = byIdentifier.get(rowKey(row));
        if (translated && translated[1] !== row[1]) errors.push(`${display}: configuration default value changed for ${rowKey(row)}`);
      }
    }
  }
  return errors;
}

export function validateTranslations(root) {
  const english = path.join(root, 'README.md');
  const translations = [path.join(root, '.github/docs/README-zh.md'), path.join(root, '.github/docs/README-ja.md')];
  const sourceLoaded = safeRead(english, root);
  if (sourceLoaded.errors.length) return sourceLoaded.errors;
  const sourceCode = extractCode(sourceLoaded.text);
  const errors = [];
  for (const file of translations) {
    const display = relative(root, file);
    if (!exists(file)) {
      errors.push(`${display}: translation file is missing`);
      continue;
    }
    const loaded = safeRead(file, root);
    if (loaded.errors.length) {
      errors.push(...loaded.errors);
      continue;
    }
    const actual = extractCode(loaded.text);
    if (sourceCode.length !== actual.length || sourceCode.some((block, i) => block.language !== actual[i]?.language || block.content !== actual[i]?.content)) {
      errors.push(`${display}: code blocks (including fence language and content) must match README.md exactly`);
    }
    errors.push(...validateTables(sourceLoaded.text, loaded.text, display));
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
