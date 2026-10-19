# `audit`

ルーティングされたツール呼び出しのための追記専用 JSONL 監査トレイルです: `build_record`、
`append_record`、`artifact_paths`、`resolve_audit_path` を提供し、さらにプロンプト・画像
ペイロード・認証情報をトレイルに残さないための秘匿化ヘルパーを備えます。

:::{admonition} 関連項目
:class: tip

レコードがいつ書かれるかは
[Insiders ヘッダー、ルーティング、監査](../development/insiders-and-routing.md) を、
`MCP_AUDIT_LOG_PATH` は [設定](../configuration.md) を参照してください。
:::

```{eval-rst}
.. automodule:: novelai_image_mcp.audit
   :members:
   :undoc-members:
   :show-inheritance:
```

## レコードが書かれるとき

監査トレイルは insiders サーフェスの一部です: `ToolCallLoggingMiddleware` は
**ツール呼び出しごとに 1 レコードを、`model-routing` が有効な間だけ** 追記します。
opt-in ヘッダーを送らないリクエストは何も書き込みません。

`resolve_audit_path` が出力先を選びます — 明示的な `MCP_AUDIT_LOG_PATH` が優先され、
なければ `NOVELAI_OUTPUT_DIR` 内の `audit.jsonl` になります。

## レコードのフィールド

`build_record` は呼び出しごとに、JSON にシリアライズ可能なフラットなオブジェクトを
1 つ生成します:

| フィールド | 内容 |
|---|---|
| `ts` | UTC タイムスタンプ (ISO-8601)。 |
| `route` | サニタイズ済みのルート。 |
| `model` / `agent` / `client` / `session` | 抽出されたルーティング値、または `null`。 |
| `tool` | ツール名。 |
| `duration_ms` | 実時間 (小数第 3 位に丸め)。 |
| `outcome` | `ok`、`error`、`rejected` のいずれか。 |
| `features` | 有効な insiders 機能名 (ソート済み)。 |
| `artifacts` | 結果が言及した `*.png` パス (ソート済み)。 |
| `unknown_keys` | insiders ヘッダーの未認識キー (ソート済み)。 |
| `malformed` | insiders ヘッダーの使用不能な項目 (ソート済み)。 |
| `headers` | サニタイズ済みルーティングヘッダーのスナップショット。`MAX_RECORDED_HEADERS` (32) 件、各値 `MAX_RECORDED_HEADER_LENGTH` (256) 文字までで、小文字化した名前の辞書順に並びます。 |
| `arguments` | 要約された呼び出し引数 — 下記参照。 |

`features`、`artifacts`、`unknown_keys`、`malformed` はソートされるため、同じ状態を表す
2 つのレコードはバイト単位で同一になります。

## 秘匿化

`summarise_arguments` は、あらゆる引数をファイルに到達し得る前に縮約します:

- **プロンプト形式** の引数 (`prompt`、`prompts`、`negative_prompt`、
  `negativeprompt`) は `digest_text` により
  `{"length": n, "sha256": "<first 16 hex characters>"}` になります。プロンプト本文が
  書かれることはありません。
- **画像形式** の引数 (`image`、`images`、`init_image`、`mask`、
  `reference`、`references`、`base64`) はリテラルの
  `[redacted image]` になります。
- `MAX_ARGUMENT_LENGTH` (256) 文字を超える **すべての** 文字列は、書かずに
  ダイジェスト化されます。予期しない引数名で base64 ブロブがすり抜けることは
  ありません。
- マッピングは `{"keys": n}` に、リスト・タプル・集合は `{"items": n}` に、その他の
  オブジェクトは型名に縮約されます。`None`、真偽値、整数、浮動小数点数はそのまま
  記録されます。

認証情報を含むヘッダーは上流の `routing._recorded` で除去されるため、このモジュールが
上限を設けるスナップショットには、そもそも `authorization`、`cookie`、`set-cookie`、
`proxy-authorization`、および `*-token` / `*-secret` / `*-password` / `*-key` /
`*-credential` ヘッダーが含まれません。

## 並行性と耐久性

`append_record` はまずレコードをシリアライズし、次に `O_APPEND` で開いたディスクリプタ
(モード `0o600`、必要なら親ディレクトリを作成) に対して **厳密に 1 回の `os.write`** で
書き込みます。したがって並行ライターは、1 行の半分同士を混在させるのではなく行全体を
追記します。書き込み途中のクラッシュで行が失われることはあり得ますが、すでに書かれた行が
壊れることはありません。

## 失敗時の挙動

可観測性が業務パスの依存になることはありません。`append_record` は自身の `OSError` /
`TypeError` / `ValueError` を捕捉し、`logger.error` で失敗を記録して `False` を返します —
決して例外を送出しないため、監査ファイルが書けないことがツール呼び出しの失敗に変わる
コードパスは存在しません。

## 関連項目

- [Insiders ヘッダー、ルーティング、監査](../development/insiders-and-routing.md) — ヘッダーの文法とルート解決
- [`middleware`](middleware.md) — レコードを追記する呼び出し元
- [`routing`](routing.md) — このモジュールが上限を設けるヘッダースナップショット
