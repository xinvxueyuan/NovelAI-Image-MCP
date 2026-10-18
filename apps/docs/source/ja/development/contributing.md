# コントリビュート

NovelAI Image MCP の改善に関心をお寄せいただきありがとうございます！本ページでは
実務的なワークフローを説明します。プロジェクトの行動規範については
[`CODE_OF_CONDUCT.md`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/CODE_OF_CONDUCT.md)
を参照してください。

## はじめる前に

1. 提案する変更を説明する **Issue を作成** してください。特に新機能や API 変更
   では重要です — コードに時間を費やす前に、スコープと設計について議論します。
2. 関連する進行中の作業がないか、**[Issue トラッカー](https://github.com/xinvxueyuan/NovelAI-Image-MCP/issues) を確認** してください。

## 開発環境のセットアップ

```bash
git clone https://github.com/xinvxueyuan/NovelAI-Image-MCP.git
cd NovelAI-Image-MCP

# Sync the workspace virtualenv (server + docs + dev tools)
uv sync

# (Optional) Install Node-side tooling for husky + markdownlint + turbo
corepack enable pnpm
pnpm install --frozen-lockfile
```

最初の `uv sync` は推移的依存関係をすべてダウンロードします。2 回目以降は
瞬時に完了します。

## ワークフロー

```bash
# 1. Branch off main
git checkout -b feat/my-feature

# 2. Implement your change.
#    - Source under apps/server/src/
#    - Tests under apps/server/tests/
#    - Docs under apps/docs/source/ (if user-facing)

# 3. Run all checks locally before pushing.
uv run --directory apps/server poe check
# Equivalent to: ruff format-check + ruff check + pyright + pytest

# 4. (If you touched docs) verify the build:
uv run --package novelai-image-mcp-docs sphinx-build -b html apps/docs/source apps/docs/_build/html -W --keep-going

# 5. (If you touched markdown) verify markdownlint:
pnpm exec markdownlint-cli2

# 6. (If you touched licensing) verify REUSE compliance:
uv run reuse lint

# 7. Commit using Conventional Commits + gitmoji:
git commit -m "✨ feat: add support for V5 model ids"

# 8. Push and open a PR:
git push -u origin feat/my-feature
gh pr create --title "..." --body "..."
```

## pre-commit フック

pnpm の依存関係をインストール済みの場合、`.husky/pre-commit` フックが
`git commit` のたびに自動実行されます:

1. **prek** — ruff `--fix`、ruff-format、および一般的なフック
   (trailing-whitespace、end-of-file-fixer など)。
2. **markdownlint** — `.md` ファイルがステージされた場合のみ。
3. **pyright** — `.py` ファイルがステージされた場合のみ。
4. **pytest** — `.py` ファイルがステージされた場合のみ (最も遅いフェーズ)。

prek がファイルを変更した場合、フックはそれらを再ステージして 1 回だけ
リトライします。いずれかのフェーズが失敗すると、コミットは明確なメッセージと
ともに中止されます。

WIP コミットでバイパスする場合 (使用は控えめに):

```bash
git commit --no-verify -m "wip: ..."
```

:::{warning}
CI はフックと同じチェックを実行します。`--no-verify` によるコミットは
それでも CI で失敗します — バイパスは、PR を開く前に rebase する本当に
WIP な作業に限ってください。
:::

## コーディング標準

### Python

- **スタイル**: `ruff` (preview モード) によって強制されます。ルールセットは
  `apps/server/pyproject.toml` を参照してください。自動整形には
  `uv run --directory apps/server ruff format` を実行します。
- **型**: `pyright` (standard モード) によって強制されます。型チェックが
  通る必要があります。
- **docstring**: Google スタイル (本プロジェクトの pydocstyle 規約)。
  公開 API では必須、プライベートヘルパーでは任意です。
- **インポート**: すべてのモジュールの先頭で `from __future__ import annotations`
  が必須です (PEP 563 + Ruff の `TC` ルール)。
- **非同期**: ツールは非同期です。HTTP には `httpx.AsyncClient`、テストには
  `pytest-asyncio` (`asyncio_mode=auto`) を使用します。

### Markdown

- MyST Markdown (ドキュメントサイトのパーサー) を使用します。
- 行長の制限はありません (`MD013` は無効)。
- 見出しは `.,;:!` で終えてはいけません (`MD026`)。
- コールアウト / details 用にインライン HTML を使用できます (`MD033` は無効)。
- ほとんどの問題は `pnpm exec markdownlint-cli2 --fix` で自動修正できます。

### ライセンス

- すべてのファイルに SPDX ライセンスヘッダーが必要です。`REUSE.toml` が
  それらを glob で宣言しているため、通常は手動で追加する必要はありません。
- 準拠を検証するには `uv run reuse lint` を実行します。
- ソフトウェアコード: MIT。ドキュメント: MIT。視覚要素 + インフラストラクチャ:
  CC0-1.0。

## テストカバレッジ

- カバレッジの下限: **70%** (`--cov-fail-under=70` で強制)。
- テストは `apps/server/tests/` にあり、`pytest-asyncio` +
  `respx` (HTTP モック) を使用します。
- 新しい公開関数には、少なくとも 1 つのテストが必要です。
- バグには回帰テストを含めるべきです。

テストの構成とフィクスチャ戦略については [テスト](testing.md) を参照してください。

## ドキュメント

ユーザーに影響する変更 (新しいツール、新しいパラメーター、挙動の変更) は
ドキュメントを更新する必要があります:

- ツール → `apps/docs/source/tools/<tool>.md`
- チュートリアル → `apps/docs/source/tutorials/<tutorial>.md`
- 設定 → `apps/docs/source/configuration.md`
- API → docstring から `sphinx.ext.autodoc` によって自動生成

ドキュメントをローカルでプレビューするには:

```bash
uv run --package novelai-image-mcp-docs sphinx-autobuild apps/docs/source apps/docs/_build/html --open-browser
```

### スキルのコントリビュート

エージェントスキルは `skills/<name>/SKILL.md` に配置され、リポジトリルートの
`skills.sh.json` に登録されます。新しいスキルを追加するには:

1. `npx skills init <name>` を実行して、`SKILL.md` の frontmatter
   (`name` + `description` のみ、`metadata` ブロックなし) と
   `## When to use` → `## Instructions` の本文構造をスキャフォールドします。
2. 内容を記入します — ガイダンスは必要に応じて配分し、他のスキルがすでに
   カバーしている内容を重複させないでください。
3. 適切なグルーピング (CLI / MCP Tools / Workflows) の下で
   `skills.sh.json` にスキルを追加します。
4. ユーザーに公開されるスキルの場合は、[エージェントスキル](../skills.md)
   ドキュメントページと README のスキル表を更新します。

完全なスキャフォールド規約 (frontmatter のルール、H1 = スキル名、description は
200 文字未満、YAML 特殊文字の引用ルール) については、`AGENTS.md` →
「Agent Skills (skills.sh)」を参照してください。

## ドキュメントの翻訳

ドキュメントサイトは、言語ごとのソースツリーによって多言語をサポートします。
英語は `apps/docs/source/` のルートにあり、追加の各言語は
`apps/docs/source/<lang-code>/` (例: `source/zh/`、`source/ja/`) に配置されます。
すべての言語は同じ `conf.py` を共有します。

### ルール

1. **完全な翻訳のみ — スタブは禁止。** 翻訳ページは英語ソース全体を
   カバーする必要があります。コードブロックは変更せず、散文のみを翻訳します。
   「翻訳中」のプレースホルダーページを作成しないでください — ビルドの `-W`
   警告ゲートを壊し、ユーザーを混乱させます。

2. **toctree のスコープ = 翻訳済みページのみ。** 各言語ディレクトリの
   `index.md` の toctree は、その言語ディレクトリ配下に実在するページのみを
   参照する必要があります。あるセクション (例: `tools/`、`tutorials/`) が
   未翻訳の場合、翻訳版 toctree からは省略してください — 未翻訳のセクションは
   ユーザーが英語に切り替えて参照します。

3. **MyST ディレクティブを保持する。** すべての MyST 構文 (`:::tip`、
   `=== "Unix"` タブ、`{toctree}`、`{image}` など) をそのまま維持します。
   ディレクティブ内の散文のみを翻訳してください。

4. **見出しの CJK 句読点。** `MD026` は見出し末尾の `.,;:!` を禁止します —
   代わりに `。、！？` を使用してください。(`MD013` の行長制限は無効なので、
   長い CJK 行は問題ありません。)

### 新しい言語の追加

1. 少なくとも `index.md` を含む `apps/docs/source/<code>/` を作成します。
2. `apps/docs/source/conf.py` の `AVAILABLE_LANGUAGES` に言語を追加します
   (`(code, label, base_path)` のタプル)。
3. `.github/workflows/docs.yml` の matrix に言語を追加します。
4. ローカルでビルドし、警告がゼロであることを確認します:

   ```bash
   uv run --package novelai-image-mcp-docs sphinx-build -b html \
     apps/docs/source/<code> apps/docs/_build/<code>/html \
     -c apps/docs/source -D language=<code> -W --keep-going
   ```

### リポジトリの README

正規のプロジェクト概要は `README.md` (英語) です。その完全な翻訳は
`.github/docs/README-zh.md` (簡体字中国語) と `.github/docs/README-ja.md`
(日本語) に、Sphinx ソースツリーとは別に配置されています。ルートの
`README-zh.md` は互換性のためのエントリーポイントであり、維持すべき
2 つ目の翻訳ではありません。

すべての README には、3 つのプロジェクト概要すべてにリンクするテキストのみの
Markdown テーブルが含まれ、列名は `English`、`简体中文`、`日本語` です。
ファイルのディレクトリに応じた相対リンクを使用してください。公開される
`apps/server/README.md` は、PyPI でもリンクが機能するように絶対 GitHub URL を
使用します。パッケージおよびリリースノートの README は、これらをパッケージや
リリースノートガイド自体の翻訳ではなく、プロジェクト概要へのリンクとして
位置づけています。

3 つの完全な概要すべてで、すべてのセクション、ツール / 設定テーブル、
フェンス付きの例を同期させてください。翻訳するのは散文であり、実行可能な例
ではありません。`.github/docs/` 用にローカルファイルリンクを貼り替えて
ください。サーバーパッケージの `mcp-name:` マーカーは保持してください。
提出前に `pnpm readme:check`、`pnpm readme:test`、
`pnpm exec markdownlint-cli2` を実行してください。CI とローカルの
pre-commit フックは同じ README チェッカーを実行します。

### 翻訳の同期を保つ

英語ソースが変更された場合、可能であれば同じ PR で翻訳ページを更新してください。
ひどく同期がずれた翻訳ページは、古いまま残すのではなく削除すべきです —
翻訳が欠けている方が、誤解を招く翻訳よりましです。

## コミットメッセージ

[Conventional Commits](https://www.conventionalcommits.org/) +
[gitmoji](https://gitmoji.dev/) に従ってください:

```text
<emoji> <type>: <subject>

<body>
```

| 種類 | 用途 |
|---|---|
| `feat` | 新機能 |
| `fix` | バグ修正 |
| `docs` | ドキュメントのみ |
| `style` | 整形、空白、コード変更なし |
| `refactor` | コード再構成、挙動の変更なし |
| `perf` | パフォーマンス改善 |
| `test` | テストの追加 / 修正 |
| `build` | ビルドシステム、依存関係、CI |
| `ci` | CI 設定の変更 |
| `chore` | その他のメンテナンス |

一般的な絵文字:

| 絵文字 | 種類 |
|---|---|
| ✨ | feat |
| 🐛 | fix |
| 📝 | docs |
| 🎨 | style |
| ♻️ | refactor |
| ⚡️ | perf |
| ✅ | test |
| 🏗️ | build |
| 🔧 | chore |

## プルリクエスト

- 論理的な変更ごとに 1 つの PR。
- タイトル: Conventional Commit 形式 (`feat:`、`fix:` など)。
- 説明: Issue をリンクし、変更を要約し、破壊的変更を列挙します。
- マージ前にすべての CI チェックを通過する必要があります。
- `main` (デフォルトブランチ) へ squash-and-merge します。

## バグの報告

[バグレポート Issue](https://github.com/xinvxueyuan/NovelAI-Image-MCP/issues/new?template=bug_report.md) を作成してください。
以下を含めます:

- 実行した正確なコマンド。
- 完全なエラー出力 (Python の場合はスタックトレース)。
- サーバーのバージョン (`uv run python -c "import novelai_image_mcp; print(novelai_image_mcp.__version__)"` で確認)。
- OS、Python のバージョン、uv のバージョン。
- 最小限の再現 (スクリプトまたは手順)。

## セキュリティ問題の報告

**セキュリティ脆弱性について公開 Issue を作成しないでください。** 非公開の
開示プロセスについては
[`SECURITY.md`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/SECURITY.md)
を参照してください。

## 関連項目

- [テスト](testing.md)
- [アーキテクチャ](architecture.md)
- [リリース](releasing.md)
