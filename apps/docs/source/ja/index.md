# NovelAI Image MCP

```{image} ../_static/logo.svg
:alt: NovelAI Image MCP
:width: 120px
:align: center
```

[MCP (Model Context Protocol)][mcp] サーバーであり、**NovelAI 画像生成**を
AI エージェント向けツールとして公開するものです — Claude Desktop、Cline、
自作エージェント、リモートクライアントなどで利用できます。

FastMCP 4（MCP SDK v2 `mcp>=2.3.0` 上の fastmcp フレームワーク）上に構築され、
エージェントは標準の MCP ツールインターフェースを通じて、画像生成（txt2img / img2img /
inpaint）、アップスケール、Director ツールの実行（ラインアート、エモーション、
背景除去など）、ControlNet によるアノテーション、タグ補完、vibe のエンコード、
アカウントサブスクリプションの照会を行えます。

[mcp]: https://modelcontextprotocol.io/

---

## 主な特徴

- **11 個の MCP ツール** — NovelAI 画像 API の全機能を網羅。
- **2 種類のトランスポート** — stdio（ローカルエージェント向け）と streamable-http（リモート / マルチクライアント向け）。
- **デュアルな戻り値** — base64 の `Image` コンテンツブロック（エージェントが画像を *認識* できる）**と** ディスクに保存された PNG（パスはテキストで返却）。
- **非同期 + 同期** — 非同期ツールハンドラーと、直接呼び出し向けの `typer` CLI。
- **エージェントスキル** — AI エージェントに CLI と MCP ツールの使い方を教える 3 つの [skills.sh](https://skills.sh) パッケージ（`novelai-cli`、`novelai-mcp-tools`、`novelai-workflows`）。
- **uv 管理のモノレポ** — MIT ライセンス、Docker 対応、GitHub Pages でドキュメントを提供。

---

## はじめに

```{toctree}
:maxdepth: 2
:caption: はじめに
:hidden:

installation
quickstart
configuration
```

```{toctree}
:maxdepth: 2
:caption: ツールリファレンス
:hidden:

tools/index
```

```{toctree}
:maxdepth: 1
:caption: チュートリアル
:hidden:

tutorials/index
```

```{toctree}
:maxdepth: 1
:caption: トランスポート
:hidden:

transports/index
```

```{toctree}
:maxdepth: 1
:caption: スキル
:hidden:

skills
```

```{toctree}
:maxdepth: 1
:caption: 開発
:hidden:

development/index
```

```{toctree}
:maxdepth: 1
:caption: API リファレンス
:hidden:

api/index
```

```{toctree}
:maxdepth: 1
:caption: について
:hidden:

about/license
about/changelog
about/tool-validation
```

---

## クイックリンク

- [クイックスタート](quickstart.md) — インストール、設定、最初の 1 枚を生成するまで
- [ツールリファレンス](tools/index.md) — すべての MCP ツール、パラメータ、例
- [トランスポート](transports/index.md) — stdio と streamable-http
- [エージェントスキル](skills.md) — AI エージェントに CLI と MCP ツールを教える skills.sh パッケージ
- [エージェントホストの設定](transports/agent-hosts.md) — Claude Desktop、Cline、Cursor、Continue、Windsurf、Codex CLI
- [API リファレンス](api/index.md) — autodoc 生成の Python API
- [コントリビュート](development/contributing.md) — サーバーを改造するには

---

## プロジェクトリンク

- **ソースコード**: <https://github.com/xinvxueyuan/NovelAI-Image-MCP>
- **Issue**: <https://github.com/xinvxueyuan/NovelAI-Image-MCP/issues>
- **ライセンス**: [MIT](about/license.md)
- **変更履歴**: [Keep a Changelog](about/changelog.md)
- **NovelAI API ドキュメント**: <https://image.novelai.net/docs/index.html>
