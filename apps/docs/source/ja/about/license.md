# ライセンス

NovelAI Image MCP は **MIT ライセンス** の下で提供されています — 全文は
[`LICENSE`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/LICENSE)
を参照してください。

## ファイルごとの SPDX アノテーション

正規の `LICENSE` ファイルに加えて、すべてのソースファイルが
[`REUSE.toml`](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/REUSE.toml)
で宣言された SPDX の `copyright` / `license` ヘッダーを備えています。
ファイル種別ごとのライセンスは次のとおりです。

| ファイル種別 | ライセンス |
|---|---|
| ソフトウェアコード (`*.py`、`conf.py`) | MIT |
| ドキュメント (`*.md`、`*.mdx`) | MIT |
| 視覚要素 (`*.png`、`*.svg`、`*.jpg`、…) | CC0-1.0 |
| インフラストラクチャ / 設定 (`*.toml`、`*.yml`、`*.json`、`Dockerfile`、…) | CC0-1.0 |
| ビルド成果物 (`*.pyc`、`node_modules/`、キャッシュ) | CC0-1.0 |

CC0-1.0 (パブリックドメインへの献呈) は、非クリエイティブなコンテンツ
(設定、インフラストラクチャ、生成された成果物) に使用されており、
下流の利用者に帰属表示の義務を課しません。

## コンプライアンスの検証

このリポジトリは [REUSE 3.0](https://reuse.software/) に準拠しています。
以下を実行してください。

```bash
uv run reuse lint
```

CI ワークフローは、すべての PR で同じチェックを実行します。

## サードパーティライセンス

このプロジェクトは以下に依存しています。

| 依存関係 | ライセンス |
|---|---|
| [mcp](https://pypi.org/project/mcp/) | MIT |
| [httpx](https://www.python-httpx.org/) | BSD-3-Clause |
| [pydantic](https://docs.pydantic.dev/) | MIT |
| [pydantic-settings](https://docs.pydantic.dev/latest/usage/settings/) | MIT |
| [typer](https://typer.tiangolo.com/) | MIT |
| [argon2-cffi](https://argon2-cffi.readthedocs.io/) | MIT |
| [msgpack](https://msgpack-python.readthedocs.io/) | Apache-2.0 |
| [Sphinx](https://www.sphinx-doc.org/) | BSD-2-Clause |
| [Furo](https://pradyunsg.me/furo/) | MIT |
| [MyST Parser](https://myst-parser.readthedocs.io/) | MIT |

推移的依存関係を含む依存関係ツリー全体を確認するには `uv tree` を実行して
ください。

## 関連項目

- [ライセンス全文](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/LICENSE)
- [REUSE.toml](https://github.com/xinvxueyuan/NovelAI-Image-MCP/blob/main/REUSE.toml)
- [FSFE REUSE 仕様](https://reuse.software/spec/)
