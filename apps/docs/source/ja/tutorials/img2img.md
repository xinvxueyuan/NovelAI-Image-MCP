# チュートリアル: 画像から画像

`image_to_image` ツールで、新しいプロンプトを使って既存の画像を変換します。細部の
調整、スタイルの変更、ゼロからの作り直しなしでの構図の反復に最適です。

## 1. 入力画像を読み込む

`image_to_image` は入力を base64 でエンコードされた PNG/JPEG 文字列として期待します。
Python でスクリプトを書く場合は次のようにします:

```python
import base64
from pathlib import Path

image_b64 = base64.b64encode(Path("input.png").read_bytes()).decode("ascii")
```

CLI はファイルパスを直接受け取るため、手動での base64 変換は不要です。

## 2. image-to-image を実行する

```python
result = await ctx.session.call_tool("image_to_image", {
    "prompt": "1girl, masterpiece, smiling, golden hour lighting",
    "image": image_b64,
    "strength": 0.4,
    "noise": 0.05,
    "seed": 42,
})
```

## 3. `strength` を調整する

`strength` (0.01–0.99) が最も重要なパラメーターです:

| `strength` | 効果 |
|---|---|
| 0.1–0.3 | 微妙な調整 — 細部を修正し、構図を保ちます。 |
| 0.4–0.6 | バランス型 — スタイル / ライティングの変化が目に見え、アイデンティティは保たれます。 |
| 0.7–0.9 | 大幅 — 新規の text-to-image に近づき、入力はほとんど見えなくなります。 |

:::{tip}
`0.5` から始めます。結果が入力に似すぎている場合は `0.6` に上げ、入力の
アイデンティティが失われている場合は `0.4` に下げてください。
:::

## 4. 制御されたノイズを加える

`noise` (0–0.99) は入力画像の *上に* 追加のランダム性を注入します。`strength` を
変えずにばらつきを加えたいときに使います:

```python
result = await ctx.session.call_tool("image_to_image", {
    "prompt": "1girl, masterpiece",
    "image": image_b64,
    "strength": 0.5,
    "noise": 0.2,        # 20% noise
    "extra_noise_seed": 99,  # separate seed for the noise (defaults to `seed`)
})
```

## 5. Python API を使う

MCP ホストなしでスクリプトを書く場合は、基盤となるクライアントを直接呼び出します:

:::{note}
直接 API を使う例では `create_http_client()` を使います — `httpx.AsyncClient()` を
手書きで **しないでください**。NovelAI の Cloudflare WAF は TLS スタック (JA3/JA4) を
指紋照合し、ブラウザ以外の接続を無言でリセットします。`create_http_client()` は
Chrome を偽装するもので、`image.novelai.net` でサポートされる唯一のトランスポートです。
:::

```python
import asyncio
import base64
from pathlib import Path

from novelai_image_mcp.nai import (
    Action, GenerationRequest, Model, create_novelai_client,
)
from novelai_image_mcp.nai.http import create_http_client
from novelai_image_mcp.settings import NovelAISettings

async def main():
    settings = NovelAISettings(token="pst-...")
    image_b64 = base64.b64encode(Path("input.png").read_bytes()).decode("ascii")
    async with create_http_client(timeout=settings.timeout) as http_client:
        client = create_novelai_client(settings, http_client=http_client)
        try:
            request = GenerationRequest(
                prompt="1girl, masterpiece, smiling",
                action=Action.IMG2IMG,
                model=Model.V4_5,
                image=image_b64,
                strength=0.4, noise=0.05, seed=42,
            )
            images = await client.generate(request)
        finally:
            await client.aclose()

asyncio.run(main())
```

## 次のステップ

- [Inpainting](inpaint.md) — 特定の領域を再描画する
- [アップスケール](upscale.md) — 解像度を上げる
- [`image_to_image` リファレンス](../tools/generate.md#image_to_image)
