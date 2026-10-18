# トランスポート

MCP サーバーは 2 つのトランスポートをサポートします。使い方に応じて選んでください。

| トランスポート | 用途 | コスト | 同時接続 |
|---|---|---|---|
| [stdio](stdio.md) | ローカルエージェントとの統合 (Claude Desktop、Cline) | 最小 — ネットワークのオーバーヘッドなし | 単一クライアント |
| [streamable-http](http.md) | リモート / マルチクライアント / 本番デプロイ | やや高い (HTTP フレーミング) | 複数クライアント |

## 選択の早見表

```{mermaid}
graph TD
    Q{How will you use the server?}
    Q -->|Local agent on the same machine| A[stdio]
    Q -->|Remote / multi-client / production| B[streamable-http]
    Q -->|Scripting — direct CLI use| C[CLI: novelai-image-mcp generate<br/>uv run python -m ...]
    Q -->|Portable agent instructions| D[Agent skills<br/>npx skills add …]
```

スキルはトランスポートではありません — [skills.sh](https://skills.sh) のパッケージで、
AI エージェントに CLI や MCP ツールの *使い方* を教えるものです。コーディング
エージェント (Claude Code、Codex、Copilot など) に、手動のプロンプトなしで
プロジェクトのコマンドとパラメーターを理解させたいときにインストールします。詳細は
[エージェントスキル](../skills.md) を参照してください。

## トランスポートに依存しない設計

サーバーの `lifespan` が、単一の共有 `httpx.AsyncClient` (コネクションプール) と
1 つの `NovelAIClient` を所有します。すべてのツールはそれらをリクエストコンテキストの
lifespan 状態から取得するため、ツールのコードもシグネチャもトランスポート間で
変わりません。

トランスポートの選択はサーバー起動時に行われます (`MCP_TRANSPORT` または CLI の
`--transport` フラグ):

```bash
# stdio (default)
MCP_TRANSPORT=stdio uv run python -m novelai_image_mcp serve

# streamable-http
MCP_TRANSPORT=streamable-http uv run python -m novelai_image_mcp serve
```

`MCP_*` 変数の完全な一覧は [設定](../configuration.md) を参照してください。

```{toctree}
:maxdepth: 1
:hidden:

stdio
http
agent-hosts
```
