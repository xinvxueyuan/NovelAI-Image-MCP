# リリース

本ページではリリースプロセスを説明します: バージョンの更新、リリースノートの
作成、PyPI + GHCR + GitHub Releases + MCP Registry への公開です。バージョン
タグをプッシュするとパイプライン全体が実行されます。トリガーはタグだけです。

## バージョニング

本プロジェクトは [セマンティック バージョニング](https://semver.org/spec/v2.0.0.html) に従います:

- `MAJOR.MINOR.PATCH`
- `MAJOR`: 破壊的な API 変更
- `MINOR`: 後方互換な新機能
- `PATCH`: 後方互換なバグ修正

### 唯一の信頼できる情報源

正規のバージョンは
[`apps/server/pyproject.toml`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/server/pyproject.toml)
の `[project] version` フィールドにあります。バージョンを持つ他のすべての場所は
そこから**導出**され、1 つのコマンドがそれらすべてを書き込みます:

```bash
uv run --directory apps/server poe sync-versions    # write
uv run --directory apps/server poe check-versions   # verify only (what CI runs)
```

| 場所 | 同期のされ方 |
|---|---|
| `apps/server/pyproject.toml` | **ここを編集** (正規)。 |
| `package.json`、`apps/server/package.json`、`apps/docs/package.json` | `poe sync-versions` がトップレベルの `version` を書き込みます。 |
| `server.json` (MCP レジストリマニフェスト) | `poe sync-versions` がトップレベルの `.version`、PyPI エントリの `version`、OCI エントリの `identifier` タグを書き込みます。 |
| `apps/server/src/novelai_image_mcp/__init__.py` (`__version__`) | インポート時に、`pyproject.toml` から生成されたインストール済み wheel の METADATA から解決されます。編集は不要です。 |
| `apps/docs/source/conf.py` (`release`) | Sphinx ビルド時に、インストール済みパッケージのメタデータから解決されます。未同期のチェックアウト向けに `0.0.0` のフォールバックがあります。 |
| `apps/server/Dockerfile` (`ARG VERSION`) | ビルド時に `validate.outputs.version` から注入されます。 |
| Docker イメージラベル (`org.opencontainers.image.version`) | `docker/metadata-action` 経由で `validate.outputs.version` から注入されます。 |
| Git タグ、PyPI バージョン、GitHub Release | すべて実行をトリガーしたタグを情報源とします。 |

:::{important}
リリースワークフローはこれらのファイルを**検証する**だけで、決して書き込み
ません。リリースの実行中にリポジトリへ書き戻されるものは何もないため、公開
された成果物が、それがビルドされたコミットと食い違うことは決してありません。
タグを打つ*前に* `poe sync-versions` を実行してコミットしてください —
そうしないと `poe check-versions` が実行を失敗させます。
:::

## リリースノートは JSON で作成する

各リリースは
[`release-notes/<version>.json`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/tree/main/release-notes)
に告知文を含めます:

```json
{
  "version": "0.5.2",
  "date": "2026-10-13",
  "summary": "One paragraph summarising the release.",
  "highlights": [{ "title": "Headline", "body": "Markdown body" }],
  "sections": [{ "title": "🛡️ Security", "items": ["Bullet one"] }],
  "upgrade_notes": "Anything an operator must do.",
  "contributors": ["@someone"],
  "footer": "Optional closing Markdown."
}
```

`version`、`date`、`summary` は必須です。残りのキーは任意であり、**未知のキーは
エラー**になるため、タイプミスで告知の一部が黙って欠落することはありません。
`🚀 Release` ワークフローは
[`apps/server/scripts/release_notes.py`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/apps/server/scripts/release_notes.py)
でドキュメントをレンダリングし、その結果を GitHub Release の本文として公開し、
その下に自動生成されたコミット一覧 (`.github/release.yml` でグループ化) を
追加します。

```bash
# preview exactly what the release page will show
uv run --directory apps/server poe release-notes --version 0.5.2
```

`CHANGELOG.md` は引き続きリポジトリの累積的で人手による変更履歴であり、JSON
ドキュメントはリリースページに表示される短い告知です。リリースには両方が
必要です。

## リリース前チェックリスト

タグをプッシュする前に:

- [ ] `main` ですべての CI チェックが通り、`main` がプッシュされている。
- [ ] `apps/server/pyproject.toml` の `version` が更新されている (手で編集する
      **唯一の**バージョン文字列)。
- [ ] `CHANGELOG.md` に新バージョンのセクションがある (`## [Unreleased]` を
      `## [X.Y.Z] - YYYY-MM-DD` に改名し、新しい `[Unreleased]` を追加)。
- [ ] `release-notes/X.Y.Z.json` が存在し、レンダリングできる。
- [ ] `poe sync-versions` を実行してコミット済み (3 つの `package.json` と
      `server.json`)。
- [ ] `uv lock` が最新 (`uv lock`)。
- [ ] `poe check`、`uv run reuse lint`、`poe check-versions` がグリーン。
- [ ] 以前のバージョンの機能セットを引用しているチュートリアルが更新されている。

## リリースのトリガー

### オプション A: タグをプッシュする (通常の経路)

タグがリリースの決定です。タグはすでに `main` 上にあるコミットを指している
必要があります — `validate` ジョブが祖先関係をチェックし、ベースライン上に
ないタグを拒否します:

```bash
git tag -a v0.5.2 -m "v0.5.2"
git push origin v0.5.2
```

ワークフローはタグ名からバージョンを解決し、そのコミットに対してパイプライン
全体を実行します。

### オプション B: workflow_dispatch (既存タグの再実行)

GitHub Actions UI (または CLI) から手動でトリガーし、**既存の**タグを再ビルド
して再公開します — 一時的な失敗の後や、リリースノートを更新したい場合に
便利です:

```bash
gh workflow run release.yml -f version=0.5.2
```

タグはすでに存在している必要があります。この経路がタグを書き換えることは
ありません。

## リリースパイプライン

`release.yml` ワークフローは以下のジョブを実行します:

```{mermaid}
graph TD
    A[validate] --> B[build]
    B --> C[publish-pypi]
    B --> D[publish-ghcr]
    C --> E[github-release]
    D --> E
    C --> F[publish-mcp]
    D --> F
```

### 1. Validate

- タグ (または dispatch 入力) からバージョンを解決し、`X.Y.Z` 以外を拒否します。
- タグが存在し、そのコミットが `origin/main` の祖先であることを確認します。
- `apps/server/pyproject.toml` がタグのバージョンを持っていることを確認します。
- `apps/server/scripts/sync_versions.py --check` を実行します: すべての派生
  マニフェストがすでに一致している必要があります (検証のみ — 何も書き込まれ
  ません)。
- `CHANGELOG.md` がそのバージョンを記載していることを確認します。
- `release-notes/<version>.json` をレンダリングし、`release-notes` 成果物と
  してアップロードします。

### 2. Build

- `uv build --package novelai-image-mcp` が wheel + sdist を生成します。
- それらを CI 成果物 (`python-distributions`) としてアップロードします。

### 3. Publish to PyPI

- **OIDC トラステッドパブリッシング**を使用します (API トークンなし)。
- PyPI 側でトラステッドパブリッシング用に GitHub 環境 `pypi` が設定されて
  いる必要があります。

### 4. Publish to GHCR

- Docker イメージをビルドします (Buildx によるマルチプラットフォーム)。
- `ghcr.io/<owner>/<repo>:<version>`、`:<major>.<minor>`、`:<major>`、
  `:sha-<short>` にプッシュします。
- **cosign でイメージに署名します** (keyless、OIDC 経由)。

### 5. GitHub Release

- JSON リリースノートをレンダリングし、自動生成されたコミット一覧を追加します。
- **既存の**タグに対して GitHub Release を作成し (`--verify-tag`)、wheel + sdist
  を添付します。再実行時は失敗する代わりに、ノートを更新してアセットを
  再アップロードします。

### 6. Publish to MCP Registry

- PyPI と GHCR が公開された後に実行されます
  (`needs: [validate, publish-pypi, publish-ghcr]`)。
- `mcp-publisher` をインストールし、`server.json` をレジストリスキーマに対して
  検証し、GitHub OIDC でログインして公開し、その後
  `registry.modelcontextprotocol.io` にサーバーが掲載されていることを確認します。
- 1 回のタグプッシュですべてをアトミックに公開するため、独立したタグトリガー
  ワークフローではなくインライン化されています。スタンドアロンの
  `publish-mcp.yml` は、`server.json` の修正後の手動再公開用として引き続き
  利用できます。

## リリースを切る

完全なリリースを最初から最後まで:

```bash
# 1. Make sure main is green and current
git checkout main
git pull
uv run --directory apps/server poe check

# 2. Bump the canonical version (the ONLY version string you edit)
#    apps/server/pyproject.toml: version = "0.5.2"

# 3. Close the changelog section
#    CHANGELOG.md: rename [Unreleased] to [0.5.2] - 2026-10-13,
#    add a fresh empty [Unreleased]

# 4. Author the announcement
#    release-notes/0.5.2.json  (see the format above)

# 5. Propagate the version and re-lock
uv run --directory apps/server poe sync-versions
uv lock

# 6. Verify everything the workflow will verify, then commit and push
uv run --directory apps/server poe check
uv run --directory apps/server poe check-versions
uv run reuse lint
git add apps/server/pyproject.toml CHANGELOG.md release-notes/0.5.2.json \
        package.json apps/server/package.json apps/docs/package.json \
        server.json uv.lock
git commit -m "🏷️ chore(release): 0.5.2"
git push

# 7. Tag the release commit and push the tag — this triggers the pipeline
git tag -a v0.5.2 -m "v0.5.2"
git push origin v0.5.2

# 8. Watch it
gh run watch
```

## リリース後

- PyPI でパッケージを確認: <https://pypi.org/project/novelai-image-mcp/>
- GHCR でイメージを確認: `docker pull ghcr.io/<owner>/<repo>:0.5.2`
- GitHub Release を確認: <https://github.com/xinvxueyuan/NovelAI-Image-MCP/releases>
- MCP Registry の掲載を確認 (`publish-mcp` ジョブにより自動):
  <https://registry.modelcontextprotocol.io/>
- プロジェクトのディスカッション / チャットで告知します。

## ロールバック

リリースが壊れている場合:

1. **PyPI に同じバージョンを再公開しないでください** (PyPI は再アップロードを
   許可していません)。壊れたリリースは PyPI の Web UI から yank します。
2. 修正を含むパッチリリースを切ります (`0.5.3`)。
3. 壊れたリリースを GitHub 上でプレリリース / yank 済みとしてマークします。

## 履歴

0.5.1 まで (0.5.1 を含む) のリリースは `releases/X.Y.Z` ブランチのプッシュに
よってトリガーされ、ワークフローは同期されたマニフェストをそのブランチに
書き戻していました。タグフローが導入された後にブランチは削除されました。
歴史的な `vX.Y.Z` タグは残っており、それらのリリースの記録となっています。

## 関連項目

- [CHANGELOG](../about/changelog.md) — 各リリースでの変更点
- [`release-notes/README.md`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/release-notes/README.md) — JSON ノートの形式
- [`release.yml`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/.github/workflows/release.yml)
- [`.github/release.yml`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/.github/release.yml) — 追加されるコミット一覧のグループ化
- [PyPI トラステッドパブリッシングのセットアップ](https://docs.pypi.org/trusted-publishers/)
