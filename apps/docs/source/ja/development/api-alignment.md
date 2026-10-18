# API サーフェスの整合

このサーバーを NovelAI が公開している API ドキュメントと照合した監査結果です。
実際のエンドポイントに対する **ライブ検証** も含みます。生成リクエストが検証
エラーで失敗し始めたとき、NovelAI が API 変更を告知したとき、または `nai/` に
触れるリリースの前に再実行してください。

## 公式ドキュメントの実態

| URL | 提供している内容 |
|---|---|
| `https://image.novelai.net/docs/index.html` | Swagger UI。インライン設定が `doc.json` を指しています。 |
| `https://image.novelai.net/docs/doc.json` | **これが実際のスペック**: Swagger 2.0、27 パス、57 定義、タイトルは "Omegalaser API"。 |
| `https://text.novelai.net/docs/doc.json` | 同じスペックのバイト単位で同一のコピー。 |
| `https://api.novelai.net/docs/` | Swagger UI ですが、その `swagger-initializer.js` は依然として `https://petstore.swagger.io/v2/swagger.json` を指しています — **実際のスペックではありません**。情報源として使わないでください。 |
| `https://text.novelai.net/openapi.json` | "Observability API" (エラートラッキング) であり、画像生成とは無関係です。 |
| `https://docs.novelai.net/en/...` | 製品ガイド (194 ページ)。*機能と UI 設定* を説明するもので、エンドポイントやフィールド名は扱いません。`nai-diffusion-*` の ID や `/ai/*` パスには一切言及していません。 |

プロジェクト自身のブラウザフィンガープリント付きクライアントでスペックを取得します
(Cloudflare は素のクライアントをブロックします):

```python
from novelai_image_mcp.nai.http import create_http_client

async with create_http_client(timeout=60) as client:
    spec = (await client.get("https://image.novelai.net/docs/doc.json")).json()
```

### スペックはフィールドのホワイトリストではない

`image.RequestParameters` は、このクライアントが送信し API が受け付けるフィールドを
省略しています — `characterPrompts`、`autoSmea`、`ucPresetId`、`qualityPresetId` (V5)、
`normalize_reference_strength_multiple`、`inpaintImg2ImgStrength`、
`legacy_uc`、パラメーター単位の `use_coords` です — さらに `model`、
`sampler`、`noise_schedule` を列挙なしの素の文字列として型付けしています。
スペックは **どのパスが存在するか** と **レスポンスの形** について権威あるものとして扱い、
**どのフィールドが機能するか** についてはライブ API を権威あるものとして扱ってください。

## パスの一覧 (27 件を文書化)

2026-10-10 に実アカウントで検証済み (Anlas の消費前後を記録)。

| 文書化されているパス | このサーバー | ライブ結果 |
|---|---|---|
| `POST /ai/generate-image` | V3 / Furry の ZIP パス (`Endpoint.IMAGE`) | `nai-diffusion-3` で 200 (ZIP) |
| `POST /ai/generate-image-stream` | V4 / V4.5 / V5 の msgpack パス | 200 (`application/msgpack`) |
| `POST /ai/generate-image/suggest-tags` | `suggest_tags` ツール | 200、`{"tags": [{"tag", "count", "confidence"}]}` |
| `POST /ai/upscale` | `upscale_image` ツール | このホストでは **V5 モデルのみ** 200。旧 `api.novelai.net` パスは 404 |
| `POST /ai/augment-image` | `director_tool` | `lineart`、`sketch`、`bg-removal`、`declutter`、`colorize` で 200 |
| `POST /ai/encode-vibe` | `encode_vibe` ツール | 200 (バイナリの vibe ファイル。クライアントが base64 エンコード) |
| `GET /user/subscription` | `get_subscription` ツール | 200 |
| `GET /user/data` | `get_user_data` ツール | 200 |
| `GET /user/information` | — | 200 (メール / 認証 / BAN ステータス) |
| `GET /user/priority` | — | 200 (priority の再補充) |
| `GET /user/giftkeys` | — | 永続トークンでは **401** |
| `GET/PUT /user/clientsettings` | — | 永続トークンでは **401** |
| `POST /ai/generate`, `POST /ai/generate-stream` | — | テキスト生成。この画像サーバーの対象外 |
| `/oa/v1/*` (completions, chat, token-count, models) | — | OpenAI 互換のテキスト API。`GET /oa/v1/models` はこのアカウントでは空の `data` を返します |
| `/user/keystore`, `/user/consent`, `/user/create-persistent-token`, `/user/objects/*`, `/user/subscription/bind`, `/user/resend-email-verification` | — | アカウント / 製品エンドポイント。変更操作とプライベートデータはこの監査では決して呼び出しません |
| `/ai/annotate-image` | `annotate_image` ツール | **このスペックには含まれません。** `hed`、`midas`、`fake_scribble`、`mlsd`、`uniformer` に対して `api.novelai.net` でライブ 200 — 唯一移行しなかったエンドポイントです |

## このコードベースを変更させた知見

1. **`/ai/upscale` は移行済みで、V5 専用です。** エンドポイントは
   `image.novelai.net` 上にあり、`{image, model, declared_blur_sigma}` を受け取り、
   V3/V4/V4.5 のすべてのモデルを *"model ... doesn't support standalone
   upscaling"* で拒否します。以前の実装は `{image, width, height,
   scale}` を `api.novelai.net/ai/upscale` に POST しており、これは現在 **404** を
   返します — ツールは壊れていました。``upscale()`` で修正しました: 画像ホストに
   POST し、文書化されたボディを送信し、モデルの既定値を
   `NOVELAI_UPSCALE_MODEL` (`nai-diffusion-5-full`) にし、4× ステップ以外を
   拒否します (API は係数を公開していません)。
2. **`suggest_tags` は `{tag, count, confidence}` を返します** —
   ドキュメントが主張していた `{description, text, count}` の形ではありません。
   `schemas.TagSuggestion` はワイヤーフィールドを反映するようになりました
   (上流の追加が残るよう `extra="allow"` 付き)。
3. **`/ai/generate-image` (ZIP) は V4/V4.5 モデルで 500 を返します** —
   これらのモデルは `/ai/generate-image-stream` を使う必要があります。クライアントは
   すでにモデルファミリー (`is_v4_model()`) でルーティングしているため、変更は不要でした。

## 意図的に未検証

- `emotion` Director ツール: 顔のない合成画像ではリクエストが 500 を返します。
  他の 5 つの `req_type` 値は 200 を返します。確認にはポートレートが必要です。
- アカウント状態を変更するもの (`/user/consent`、`subscription/bind`、
  `create-persistent-token`、`objects/*` の削除) — 設計上対象外です。
- `/user/giftkeys` と `/user/clientsettings` は永続トークンでは 401 を返します。
  形を文書化するにはセッショントークンが必要です。

## 関連項目

- [アーキテクチャ](architecture.md) — `nai/` が API にどう対応するか
- [設定](../configuration.md) — エンドポイントとモデルの設定
- [トランスポート](../transports/index.md)
