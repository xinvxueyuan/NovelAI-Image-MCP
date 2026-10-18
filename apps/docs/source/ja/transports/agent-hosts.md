# エージェントホスト

主要なエージェントホスト向けの、コピー&ペーストできる MCP 設定スニペットです。
すべてのスニペットは標準の stdio 形式 — `command` + `args` + `env` — を使います。
`uvx` は *コマンド* (Astral の `uv` パッケージランナー) であり、トランスポートでは
ないからです。MCP 仕様が定義するトランスポートは `stdio` と `Streamable HTTP` の
2 つだけで、`command` がある場合、ホストは暗黙に stdio を選びます。

## 概要

| ホスト | 設定ファイル | 形式 | シークレットの注入 |
|---|---|---|---|
| [Claude Desktop](#claude-desktop) | `claude_desktop_config.json` | JSON | `env` のリテラル、`${input:…}` |
| [Cline](#cline) | `cline_mcp_settings.json` / `~/.cline/mcp.json` | JSON | `env` のリテラル |
| [Cursor](#cursor) | `mcp.json` (グローバルまたはプロジェクト) | JSON | `env` のリテラル、`auth` (OAuth) |
| [Continue](#continue) | `config.yaml` / `config.json` | YAML または JSON | `env` のリテラル、`${{ secrets.X }}` |
| [Windsurf](#windsurf) | `mcp_config.json` | JSON | `${env:VAR}`、`${file:/path}` |
| [Codex CLI](#codex-cli) | `config.toml` | TOML | `env_vars`、`bearer_token_env_var` |
| [Generic stdio](#generic-stdio) | (ホスト固有) | JSON | `env` のリテラル |

## Claude Desktop

### 設定ファイルのパス

| OS | パス |
|---|---|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| Linux (非公式ビルド) | `~/.config/Claude/claude_desktop_config.json` |

macOS のパスは Settings → Developer → **Edit Config** からも到達でき、ファイルが
なければ作成されます。

### スニペット

```json
{
  "mcpServers": {
    "novelai-image": {
      "command": "uvx",
      "args": ["novelai-image-mcp", "serve"],
      "env": { "NOVELAI_TOKEN": "${input:novelai_token}" }
    }
  }
}
```

単発のテストでは、`${input:…}` 参照の代わりにリテラルのトークン
(`"pst-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"`) を直接書いてください。

### シークレットの注入

Claude Desktop は `env` オブジェクトからシークレットをリテラル文字列として読み取るか、
`${input:…}` 参照をホスト自身が管理するシークレット UI 経由で解決します。公式スキーマに
`${env:VAR}` のようなシェル補間はありません。

### ホスト固有のフィールド

Claude Desktop は MCP 仕様そのままの stdio 形式を使います — `type` も `disabled` も
`autoApprove` もありません。リモートサーバーでは `command` + `args` の代わりに
`url` + `headers` を使います。

### 参考リンク

- [docs.open.cx/mcp/clients/claude-desktop](https://docs.open.cx/mcp/clients/claude-desktop)
- [github.com/mcp-finder/claude-mcp-config-examples](https://github.com/mcp-finder/claude-mcp-config-examples)
- [modelcontextprotocol.io/docs/develop/connect-local-servers](https://modelcontextprotocol.io/docs/develop/connect-local-servers)

## Cline

### 設定ファイルのパス

| スコープ | パス |
|---|---|
| VS Code 拡張 | MCP Servers アイコン → Configure タブ → **Configure MCP Servers** から開く |
| Cline CLI | `~/.cline/mcp.json` |

拡張機能の設定ファイルのディスク上の位置はバージョン間で移動しています。信頼できる
経路は **Configure MCP Servers** ボタンです。古いインストールでは VS Code の
`globalStorage/saoudrizwan.claude-dev/settings/` に置かれていました — ⚠ 現在の
拡張バージョンが今もそこに書き込むかは未検証です。

### スニペット

```json
{
  "mcpServers": {
    "novelai-image": {
      "command": "uvx",
      "args": ["novelai-image-mcp", "serve"],
      "env": { "NOVELAI_TOKEN": "pst-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

### シークレットの注入

Cline はシークレットを `env` オブジェクト内のリテラル文字列として読み取ります
(リモートサーバーでは `headers`)。公式スキーマに `${env:VAR}` 補間の記載はありません。

### ホスト固有のフィールド

- `disabled` (boolean) — 設定を削除せずにサーバーを無効化します。
- `autoApprove` (string array) — サーバーごとのツール許可リスト。`alwaysAllow` では
  **ありません** (それは Roo Code フォークの綴りです)。
- リモートサーバー用の `type` — `streamableHttp` (camelCase) または `sse` を受け付けます。
  `type` を省略するとレガシーの `sse` が既定になるため、推奨トランスポートを使う場合は
  明示的に設定してください。

### 参考リンク

- [docs.cline.bot/mcp/mcp-overview](https://docs.cline.bot/mcp/mcp-overview)
- [policylayer.com/integrations/cline](https://policylayer.com/integrations/cline)

## Cursor

### 設定ファイルのパス

| スコープ | パス |
|---|---|
| グローバル | `~/.cursor/mcp.json` (macOS/Linux)、`%USERPROFILE%\.cursor\mcp.json` (Windows) |
| プロジェクト固有 | プロジェクトルートの `.cursor/mcp.json` |

プロジェクトレベルの設定はグローバルのファイルとマージされます (⚠ 公式ドキュメントに対する
マージの意味論は未検証)。

### スニペット

```json
{
  "mcpServers": {
    "novelai-image": {
      "command": "uvx",
      "args": ["novelai-image-mcp", "serve"],
      "env": { "NOVELAI_TOKEN": "pst-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" }
    }
  }
}
```

### シークレットの注入

stdio のシークレットは `env` 内のリテラル文字列です。リモートサーバーのシークレットは
`headers` (例: `"Authorization": "Bearer …"`) に置くか、`auth` オブジェクト経由の
OAuth で取得します。JSON スキーマに `${env:VAR}` 置換の記載はありません。

### ホスト固有のフィールド

- `auth` — 静的 OAuth のリモートサーバー用に `CLIENT_ID` (必須)、`CLIENT_SECRET`、
  `scopes` を持つオブジェクト。
- `envFile` — ファイルから環境変数を読み込むために一部のサードパーティガイドで言及
  されています。⚠ 公式ドキュメントに対して未検証。
- `type`/`transport` フィールドはありません — Cursor はフィールドの形からトランスポートを
  自動判別します (`command` → stdio、`url` → SSE または Streamable HTTP)。

### 参考リンク

- [cursor.com/docs/mcp](https://cursor.com/docs/mcp)

## Continue

### 設定ファイルのパス

| OS | パス |
|---|---|
| macOS / Linux | `~/.continue/config.yaml` (または `config.json`) |
| Windows | `%USERPROFILE%\.continue\config.yaml` (または `config.json`) |
| プロジェクトスコープ | ワークスペースの `.continue/config.yaml` |
| スタンドアロンの MCP ブロック | `.continue/mcpServers/<name>.yaml` または `.json` |

### スニペット

```yaml
mcpServers:
  - name: novelai-image
    command: uvx
    args:
      - "novelai-image-mcp"
      - "serve"
    env:
      NOVELAI_TOKEN: "pst-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

:::{warning}
Continue の `mcpServers` は、明示的な `name` フィールドを持つオブジェクトの **配列** です
— サーバー名をキーにしたオブジェクトではありません。Claude Desktop / Cursor / Cline の
JSON 設定をそのままコピーしても動作しません。(Continue は移行用に、Claude Desktop 形式の
JSON を `.continue/mcpServers/` に置くことは受け付けます。)
:::

### シークレットの注入

3 つの仕組みがあります: `env` のリテラル値、Continue Mission Control のホスト型
シークレットストアから取得する `${{ secrets.NAME }}` プレースホルダー、そして OAuth
(Continue がユーザーの認可のためにブラウザタブを開きます)。

### ホスト固有のフィールド

- `name` (必須) — サーバーの表示名 (他のホストが使うオブジェクトキーの慣習を置き換えます)。
- `type` — `stdio` (既定)、`sse`、`streamable-http` (kebab-case。Cline の camelCase な
  `streamableHttp` とは対照的です)。
- `env` / `args` における `${{ secrets.X }}` 置換。

:::{note}
MCP は Continue の **エージェントモード** でのみ動作します — チャットモードや
オートコンプリートモードでは動作しません。
:::

### 参考リンク

- [docs.continue.dev/customize/deep-dives/mcp](https://docs.continue.dev/customize/deep-dives/mcp)
- [docs.continue.dev/reference](https://docs.continue.dev/reference)

## Windsurf

### 設定ファイルのパス

| OS | パス |
|---|---|
| macOS / Linux | `~/.codeium/windsurf/mcp_config.json` |
| Windows | `%USERPROFILE%\.codeium\windsurf\mcp_config.json` |

⚠ **相違点:** 公式 Windsurf ドキュメント
[docs.windsurf.com/windsurf/cascade/mcp](https://docs.windsurf.com/windsurf/cascade/mcp) は
今も `windsurf/` セグメント *なし* の `~/.codeium/mcp_config.json` を示しています。
独立した 6 つのサードパーティ情報源 (open.cx、policylayer、quadratichq、toolcog、
GitHub MCP Server のインストールガイド、mcp.directory の Windsurf バリデーター) は
いずれも `windsurf/` サブディレクトリを参照しています — 公式ドキュメントのページは
この点で古いようです。設定はグローバルのみで、プロジェクトごとのファイルはありません。

### スニペット

```json
{
  "mcpServers": {
    "novelai-image": {
      "command": "uvx",
      "args": ["novelai-image-mcp", "serve"],
      "env": { "NOVELAI_TOKEN": "${env:NOVELAI_TOKEN}" }
    }
  }
}
```

Windsurf を起動する前にシェルで `NOVELAI_TOKEN` をエクスポートしてください —
`${env:VAR}` 形式ならリテラルのトークンを設定ファイルに残さずに済みます。

### シークレットの注入

文書化された 3 つの仕組み: `env`/`headers` のリテラル文字列、ユーザーのシェル環境から
取得する `${env:VAR}` 補間、ファイルの 1 行目を読む `${file:/absolute/path}` です。
3 つとも `command`、`args`、`env`、`serverUrl`、`url`、`headers` で動作します。

### ホスト固有のフィールド

- `serverUrl` — `url` に対する Windsurf 固有の別名です (素の `url` も受け付けます)。
- 任意の文字列フィールドにおける `${env:VAR}` と `${file:/path}` の補間。
- `disabledTools` — サーバーごとに抑制するツール名の配列 (⚠ 公式ドキュメントに対して
  未検証)。
- `type` フィールドはありません — トランスポートは自動判別されます。

:::{warning}
Windsurf は起動時にのみ `mcp_config.json` を読み取ります。Cascade を再起動せずに
ファイルを編集することが、最もよくある静かな失敗です。
:::

### 参考リンク

- [docs.windsurf.com/windsurf/cascade/mcp](https://docs.windsurf.com/windsurf/cascade/mcp)
- [docs.codeium.com/plugins/cascade/mcp](https://docs.codeium.com/plugins/cascade/mcp)

## Codex CLI

### 設定ファイルのパス

| スコープ | パス |
|---|---|
| グローバル | `$CODEX_HOME/config.toml` (既定は `~/.codex/config.toml`、Windows では `%USERPROFILE%\.codex\config.toml`) |
| プロジェクトスコープ | `.codex/config.toml` (信頼されたプロジェクトでのみ読み込まれます) |

### スニペット

```toml
[mcp_servers.novelai-image]
command = "uvx"
args = ["novelai-image-mcp", "serve"]
env_vars = ["NOVELAI_TOKEN"]
startup_timeout_sec = 10.0

[mcp_servers.novelai-image.env]
NOVELAI_OUTPUT_DIR = "/tmp/novelai-outputs"
```

シェル (例: `~/.zshrc` や PowerShell プロファイル) で `NOVELAI_TOKEN` をエクスポートして
ください。`env_vars = ["NOVELAI_TOKEN"]` は実行時に親プロセスからそれを転送するため、
リテラルのトークンを設定ファイルに残さずに済みます。

:::{note}
TOML の順序が重要です: `command`、`args`、`env_vars`、`startup_timeout_sec` は
`[mcp_servers.<name>.env]` サブテーブルのヘッダーより *上* に置く必要があります —
それより下は `env` に属します。このリストで TOML を使うのはこのホストだけです。
Claude Desktop / Cursor / Cline の JSON 設定をコピーしても動作しません。
:::

### シークレットの注入

Codex は 7 つのホストの中で最もセキュリティを重視しており、トークンを設定ファイルに
リテラルで書くことは想定されていません。`env_vars` を使って親プロセスから名前付き
環境変数を転送します (`source = "local"` または `source = "remote"` に対応)。HTTP
サーバーでは `bearer_token_env_var` で、Codex が実行時に読み取って
`Authorization: Bearer <token>` として注入する環境変数名を指定します。OAuth も
`codex mcp login` 経由でサポートされています。

### ホスト固有のフィールド

- `env_vars` — 親環境から転送する変数名のリスト (文字列、または
  `{ name = "X", source = "local"|"remote" }`)。
- `bearer_token_env_var` — HTTP サーバー用のベアラートークンを保持する環境変数名を
  指定します。
- `env_http_headers` — 実行時に環境変数から HTTP ヘッダーを設定します。
- `enabled_tools` / `disabled_tools` — サーバーごとのツール許可 / 拒否リスト。
- `startup_timeout_sec` (既定 `10.0`) / `tool_timeout_sec` (既定 `60.0`)。
- `experimental_environment = "remote"` — stdio サーバーの起動をリモート実行者経由に
  します。
- トップレベルの `mcp_oauth_credentials_store` (`auto` | `file` | `keyring`)。

### 参考リンク

- [developers.openai.com/codex/mcp](https://developers.openai.com/codex/mcp)
- [developers.openai.com/codex/config-reference](https://developers.openai.com/codex/config-reference)
- [github.com/openai/codex](https://github.com/openai/codex)

## Generic stdio

MCP 仕様が定義するのはワイヤプロトコルと 2 つのトランスポートだけで、クライアントの
設定ファイル形式は標準化していません。以下の事実上の「generic stdio」形式は、
Claude Desktop、Cursor、Windsurf がそのまま受け付けるものです (Cline は任意の拡張を
付けて受け付けます。Continue と Codex CLI は受け付けません — 上記の各セクションを
参照してください)。

### 設定ファイルのパス

ホスト固有 — ホストごとのセクションを参照してください。

### スニペット

```json
{
  "mcpServers": {
    "novelai-image": {
      "command": "uvx",
      "args": ["novelai-image-mcp", "serve"],
      "env": { "NOVELAI_TOKEN": "pst-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" }
    }
  }
}
```

### シークレットの注入

素の `env` リテラルです。利用できる場合はホスト固有の仕組み (Claude Desktop の
`${input:…}`、Windsurf の `${env:VAR}`、Codex CLI の `env_vars`) に移行してください。

### ホスト固有のフィールド

なし — これは MCP 仕様の正規の stdio 形式です。

### 参考リンク

- [modelcontextprotocol.io/docs/develop/connect-local-servers](https://modelcontextprotocol.io/docs/develop/connect-local-servers)

## よくある落とし穴

- **`uvx` を `type`/`transport` フィールドに書く。** `uvx` はコマンドであり、
  `command` に入れるべきものです。MCP 仕様のトランスポートは `stdio` と
  `Streamable HTTP` (およびレガシーの `sse`) だけで、`command` がある場合、ホストは
  暗黙に stdio を選びます。
- **Claude Desktop の JSON 設定を Codex CLI にコピーする。** Codex は
  `~/.codex/config.toml` (JSON ではなく TOML) を `[mcp_servers.<name>]` テーブルで
  読み取ります。JSON 設定は解析されません。
- **オブジェクトキー形式の設定を Continue にコピーする。** Continue は `mcpServers` を、
  明示的な `name` フィールドを持つオブジェクトの配列として読み取ります — サーバー名を
  キーにしたオブジェクトではありません。
- **Cline で `autoApprove` の代わりに `alwaysAllow` を使う。** `alwaysAllow` は
  Roo Code フォークの綴りで、古いバリデーターに現れます。現在の正式な名前は
  `autoApprove` です。
- **`streamableHttp` と `streamable-http` を混同する。** Cline は camelCase
  (`streamableHttp`)、Continue は kebab-case (`streamable-http`) を使います。
- **設定ファイルを編集した後にホストを再起動し忘れる。** Claude Desktop と Windsurf は
  起動時にのみ設定を読み取ります — ウィンドウを閉じるだけでは不十分です
  (macOS: `Cmd+Q`、Windsurf: Cascade の完全な再起動)。

## 企業プロキシの背後で

企業または地域のファイアウォールの背後にいる場合 (たとえば `novelai.net` に直接
アクセスできない中国本土)、標準のプロキシ環境変数を `env` ブロックに追加します:

```json
"env": {
  "NOVELAI_TOKEN": "pst-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "HTTPS_PROXY": "http://127.0.0.1:10808",
  "HTTP_PROXY": "http://127.0.0.1:10808",
  "NO_PROXY": "localhost,127.0.0.1"
}
```

サーバーは `httpx` を使っており、標準の `HTTP_PROXY` / `HTTPS_PROXY` / `NO_PROXY`
環境変数を尊重します。これらがないと、NovelAI API を呼び出すすべてのツール
(`get_subscription`、`generate_image`、`upscale_image` など) が
`NovelAI request transport failed` エラーで失敗します。

## 関連項目

- [stdio トランスポート](stdio.md)
- [streamable-http トランスポート](http.md)
- [設定](../configuration.md)
