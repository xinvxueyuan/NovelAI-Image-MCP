# エージェントスキル

NovelAI Image MCP は 3 つの相補的な方法で操作できます。いずれも同じ非同期の
`NovelAIClient` を包んでおり、違いは呼び出し方だけです。

| モード | 最適な用途 | エージェントから見えるか | 同時接続 |
|---|---|---|---|
| **MCP ツール** — [ツールリファレンス](tools/index.md) | 対話的なエージェントセッション (Claude Desktop、Cline など) | はい — base64 の `Image` コンテンツブロック | トランスポートごとに単一クライアント |
| **CLI** — `novelai-image-mcp generate …` | シェルスクリプト、CI ジョブ、単発コマンド | いいえ — PNG をディスクに保存し、パスを出力 | 呼び出しごとにプロセス |
| **エージェントスキル** — このページ | AI エージェントに CLI や MCP ツールの *使い方* を教える可搬な指示 | 基盤となるモードを継承 | 基盤となるモードを継承 |

エージェントスキルは [skills.sh][skills-sh] のパッケージです — AI エージェント
(Claude Code、Codex、GitHub Copilot、Cursor など) が実行時に読み取り、
プロジェクト固有のワークフローを学ぶ markdown の指示ファイルです。CLI や MCP ツールを
置き換えるものではなく、いつ、どのように使うかをエージェントに *導く* ものです。

[skills-sh]: https://skills.sh

---

## スキルをインストールする

```bash
# Install all three skills globally (Claude Code, Codex, Copilot, …)
npx skills add --yes --global xinvxueyuan/NovelAI-Image-MCP
```

`--yes` フラグは対話的な選択プロンプトをスキップし、`--global` は `~/.agents/skills/` に
インストールするため、マシン上のすべてのプロジェクトが恩恵を受けます。`--global` を
省略すると、現在のプロジェクトの `.agents/skills/` にインストールされます。

インストールを検証します:

```bash
ls ~/.agents/skills/
# novelai-cli  novelai-mcp-tools  novelai-workflows
```

---

## 3 つのスキル

### novelai-cli

**グループ**: CLI

Typer CLI のシェルレベルの使い方 — `serve`、`generate`、`upscale`、`director`、
`annotate`、`info`。インストール (`pip install` / `uvx`)、認証情報の設定、出力の
挙動を扱います。MCP ホストの外で画像ワークフローをスクリプト化したり、画像を
バッチ生成したりするときに使います。

### novelai-mcp-tools

**グループ**: MCP Tools

サーバーが公開する 11 個の MCP ツールのリファレンスです。モデルの選択
(V3 / V4 / V4.5 / Furry)、パラメーターの調整 (steps、scale、sampler、seed)、
`ImageContent` の戻り値の形、Anlas コストへの配慮を扱います。CLI ではなく MCP ホスト
経由で画像を生成・変換するときに使います。

### novelai-workflows

**グループ**: Workflows

複数のツールを連鎖させるエンドツーエンドの創作パイプライン: txt2img → upscale、
annotate → img2img、Director による編集、そして本番向けの一連のフロー。
複数ステップの画像ワークフローのレシピやパイプラインを組み立てるよう求められたときに
使います。

---

## どれをいつ使うか

```{mermaid}
graph TD
    Q{How will you use NovelAI?}
    Q -->|"Interactive session with Claude Desktop / Cline"| A[MCP tools<br/>see Tools reference]
    Q -->|"Shell script, CI job, one-off command"| B[CLI<br/>novelai-image-mcp generate …]
    Q -->|"Want an AI agent to drive either of the above"| C[Agent skills<br/>npx skills add …]
    C -->|"Agent picks CLI or MCP based on context"| A
    C --> B
```

スキルと CLI / MCP ツールは **二者択一ではありません**:

- **CLI + スキル**: `novelai-cli` スキルをインストールすると、AI コーディングエージェント
  (Claude Code、Codex など) がドキュメントを貼り付けなくても CLI コマンドを理解します。
- **MCP + スキル**: `novelai-mcp-tools` スキルをインストールすると、エージェントが
  11 個の MCP ツールのパラメーターとモデル選択のヒューリスティクスを理解します。
- **ワークフロー**: `novelai-workflows` をインストールすると、エージェントがツールを
  複数ステップのパイプライン (txt2img → upscale → Director 編集 など) に連鎖できます。

3 つともインストールできます — それぞれ必要なときに必要な指針を配布するもので、
互いの中核的な内容を重複させていません。

---

## 関連項目

- [ツールリファレンス](tools/index.md) — 11 個の MCP ツール、パラメーター、例
- [チュートリアル](tutorials/index.md) — エンドツーエンドのワークフロー
- [トランスポート](transports/index.md) — stdio と streamable-http
- [skills.sh ページ](https://skills.sh/xinvxueyuan/NovelAI-Image-MCP) — インストール / セキュリティ評価
- [エージェントホストの設定](transports/agent-hosts.md) — Claude Desktop、Cline、Cursor など
