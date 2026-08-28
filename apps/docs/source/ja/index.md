# NovelAI Image MCP

```{image} ../_static/logo.svg
:alt: NovelAI Image MCP
:width: 120px
:align: center
```

[MCP (Model Context Protocol)][mcp] サーバーであり、**NovelAI 画像生成**を
AI エージェント向けツールとして公開するものです — Claude Desktop、Cline、
自作エージェント、リモートクライアントなどで利用できます。

FastMCP 4 (MCP SDK v2 `mcp>=2.0.0` 上の fastmcp フレームワーク) 上に構築され、エージェントは
標準の MCP ツールインターフェースを通じて、画像生成 (txt2img / img2img /
inpaint)、アップスケール、Director ツールの実行 (ラインアート、エモーション、
背景除去など)、ControlNet によるアノテーション、タグ補完、vibe のエンコード、
アカウントサブスクリプションの照会を行えます。

[mcp]: https://modelcontextprotocol.io/

---

## 主な特徴

- **11 個の MCP ツール** — NovelAI 画像 API の全機能を網羅。
- **2 種類のトランスポート** — stdio (ローカルエージェント向け) と streamable-http (リモート / マルチクライアント向け)。
- **デュアルな戻り値** — base64 の `Image` コンテンツブロック (エージェントが画像を *認識* できる) **と** ディスクに保存された PNG (パスはテキストで返却)。
- **非同期 + 同期** — 非同期ツールハンドラーと、直接呼び出し向けの `typer` CLI。
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

---

## クイックリンク

- [クイックスタート](quickstart.md) — インストール、設定、最初の 1 枚を生成するまで
- [設定](configuration.md) — 環境変数による生成デフォルトの調整
- [Docker での運用](installation.md) — 自己完結型の再現性あるデプロイ

---

## プロジェクトリンク

- **ソースコード**: <https://github.com/xinvxueyuan/NovelAI-Image-MCP>
- **Issue**: <https://github.com/xinvxueyuan/NovelAI-Image-MCP/issues>
- **ライセンス**: [MIT](https://xinvxueyuan.github.io/NovelAI-Image-MCP/about/license.html)
- **変更履歴**: [Keep a Changelog](https://xinvxueyuan.github.io/NovelAI-Image-MCP/about/changelog.html)
- **NovelAI API ドキュメント**: <https://image.novelai.net/docs/index.html>

---

## その他のセクション（英語）

ツールリファレンス、チュートリアル、トランスポート、開発ガイド、API リファレンスなどのセクションは現在英語版のみの提供です。以下のリンクから直接ご覧いただけます：

- [ツールリファレンス](https://xinvxueyuan.github.io/NovelAI-Image-MCP/tools/index.html) —— 全 11 個の MCP ツールのパラメータと例
- [チュートリアル](https://xinvxueyuan.github.io/NovelAI-Image-MCP/tutorials/index.html) —— エンドツーエンドのワークフロー（txt2img、img2img、inpaint など）
- [トランスポート](https://xinvxueyuan.github.io/NovelAI-Image-MCP/transports/index.html) —— stdio と streamable-http の比較
- [エージェントスキル](https://xinvxueyuan.github.io/NovelAI-Image-MCP/skills.html) —— AI エージェントに CLI と MCP ツールを教える
- [開発ガイド](https://xinvxueyuan.github.io/NovelAI-Image-MCP/development/index.html) —— アーキテクチャ、貢献、テスト、リリース
- [API リファレンス](https://xinvxueyuan.github.io/NovelAI-Image-MCP/api/index.html) —— autodoc 生成の Python API
- [ライセンス / 変更履歴 / ツール検証](https://xinvxueyuan.github.io/NovelAI-Image-MCP/about/license.html)
