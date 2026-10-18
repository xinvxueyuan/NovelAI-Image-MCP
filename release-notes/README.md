# Release notes (JSON)

## Languages

Project overview in your language (this page remains in English).

| English | 简体中文 | 日本語 |
|---|---|---|
| [English](../README.md) | [简体中文](../.github/docs/README-zh.md) | [日本語](../.github/docs/README-ja.md) |

One file per release: `<version>.json` (no `v` prefix), committed on `main`
**before** the release tag is pushed. The `🚀 Release` workflow validates and
renders it with
[`apps/server/scripts/release_notes.py`](../apps/server/scripts/release_notes.py)
and publishes the result as the GitHub Release body; a tag without a matching
document fails validation before anything is published.

## Format

`version`, `date` and `summary` are required. `highlights`, `sections`,
`upgrade_notes`, `contributors` and `footer` are optional. An **unknown key is
an error**, so a typo can never silently drop part of an announcement.

```json
{
  "version": "0.5.2",
  "date": "2026-10-13",
  "summary": "One paragraph summarising the release.",
  "highlights": [
    { "title": "Headline", "body": "Markdown body for the callout." }
  ],
  "sections": [
    { "title": "🛡️ Security", "items": ["Bullet one", "Bullet two"] },
    { "title": "📝 Notes", "items": "A section is also allowed to be prose." }
  ],
  "upgrade_notes": "Anything an operator must do before upgrading.",
  "contributors": ["@someone"],
  "footer": "Optional closing Markdown."
}
```

`release-notes/` is the only place release announcements live; `CHANGELOG.md`
remains the human-curated, cumulative changelog of the repository.

## Preview locally

```bash
uv run --directory apps/server poe release-notes --version 0.5.2
```

## Relationship to `CHANGELOG.md`

They answer different questions and are both required for a release:

| File | Audience | Shape |
|---|---|---|
| `release-notes/<version>.json` | the GitHub Release announcement | short, structured, grouped |
| [`CHANGELOG.md`](../CHANGELOG.md) | people reading the repository history | cumulative, prose-heavy, Keep a Changelog |
