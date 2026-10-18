# チュートリアル: Inpainting

`inpaint` ツールで画像の特定の領域を再描画します。用途: 解剖学的な修正、オブジェクトの
削除、背景の変更、顔の差し替え。

## 前提条件

- `*_inpainting` モデル。標準の V4.5 inpaint モデルは
  `nai-diffusion-4-5-full-inpainting` です。
- **マスク** — 不透明 (alpha > 0) のピクセルが再生成する領域を示す PNG。

## 1. マスクを作成する

マスクは入力画像と同じ寸法でなければなりません。任意の画像エディター
(Photoshop、GIMP、Krita など) で作成するか、プログラムで作成できます:

```python
from PIL import Image, ImageDraw

# Open the source image to get its dimensions
src = Image.open("input.png")
mask = Image.new("RGBA", src.size, (0, 0, 0, 0))  # fully transparent

# Draw a region to redraw (e.g. the face area)
draw = ImageDraw.Draw(mask)
draw.ellipse(
    (src.width // 3, src.height // 4, src.width * 2 // 3, src.height // 2),
    fill=(255, 255, 255, 255),  # opaque white = redraw
)
mask.save("mask.png")
```

## 2. inpaint を実行する

```python
import base64
from pathlib import Path

image_b64 = base64.b64encode(Path("input.png").read_bytes()).decode("ascii")
mask_b64 = base64.b64encode(Path("mask.png").read_bytes()).decode("ascii")

result = await ctx.session.call_tool("inpaint", {
    "prompt": "1girl, masterpiece, smiling",
    "image": image_b64,
    "mask": mask_b64,
    "model": "nai-diffusion-4-5-full-inpainting",
    "strength": 0.5,
    "seed": 42,
})
```

## 3. `strength` を調整する

`image_to_image` と同様に、`strength` は再描画された領域が元の画像からどれだけ
離れるかを制御します:

- `0.2–0.3` — アイデンティティを保ち、軽微な問題を修正する
- `0.5` — バランス型で、多くの場合最適な値
- `0.7+` — 大きな変更で、周囲のピクセルとの継ぎ目が生じるリスクがある

## 4. ワークフロー: 反復的な調整

Inpaint は反復的に行うのが最も効果的です。生成し、確認し、マスクを洗練させ、
繰り返します:

```python
# Step 1: coarse redraw with high strength
result = await ctx.session.call_tool("inpaint", {
    "prompt": "1girl, smiling",
    "image": image_b64,
    "mask": coarse_mask_b64,
    "strength": 0.7,
})

# Step 2: refine with a tighter mask and lower strength
result = await ctx.session.call_tool("inpaint", {
    "prompt": "1girl, smiling, perfect teeth",
    "image": result_image_b64,  # use the previous result
    "mask": fine_mask_b64,
    "strength": 0.3,
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
    mask_b64 = base64.b64encode(Path("mask.png").read_bytes()).decode("ascii")
    async with create_http_client(timeout=settings.timeout) as http_client:
        client = create_novelai_client(settings, http_client=http_client)
        try:
            request = GenerationRequest(
                prompt="1girl, masterpiece, smiling",
                action=Action.INPAINT,
                model=Model.V4_5_INPAINT,
                image=image_b64, mask=mask_b64,
                strength=0.5, seed=42,
            )
            images = await client.generate(request)
        finally:
            await client.aclose()

asyncio.run(main())
```

## よくある落とし穴

:::{warning}
**モデルの不一致。** Inpaint には inpaint モデルが必要です。inpaint 以外のモデルで
`inpaint` を呼び出すと `NovelAIValidationError` が発生します。次のように確認します:

```python
from novelai_image_mcp.nai import is_inpaint_model, Model
is_inpaint_model(Model.V4_5_INPAINT)  # True
is_inpaint_model(Model.V4_5)           # False
```
:::

:::{warning}
**マスクの寸法。** マスクは入力画像の寸法と *正確に* 一致しなければなりません。
832×1216 の画像には 832×1216 のマスクが必要です。一致しないマスクは
`NovelAIValidationError` を発生させます。
:::

:::{tip}
**マスクをぼかす。** 硬いマスクの縁は目に見える継ぎ目を生みます。マスクの alpha を
ガウスぼかし (半径 5–10 px) で柔らかくすると、遷移が滑らかになります。
:::

## 次のステップ

- [画像から画像](img2img.md) — 画像全体の変換
- [アップスケール](upscale.md) — より高い解像度で仕上げる
- [`inpaint` リファレンス](../tools/generate.md#inpaint)
