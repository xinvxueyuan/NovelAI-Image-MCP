# API 接口面对齐

对本服务器与 NovelAI 已发布 API 文档的审计，并针对真实端点做了
**在线验证**。当生成请求开始因校验错误而失败、NovelAI 宣布 API 变更，或
发布前涉及 `nai/` 时，请重新运行该审计。

## 官方文档究竟是什么

| URL | 提供的内容 |
|---|---|
| `https://image.novelai.net/docs/index.html` | Swagger UI。其内联配置指向 `doc.json`。 |
| `https://image.novelai.net/docs/doc.json` | **真正的规范**：Swagger 2.0，27 条路径，57 个定义，标题为 "Omegalaser API"。 |
| `https://text.novelai.net/docs/doc.json` | 同一份规范的逐字节相同副本。 |
| `https://api.novelai.net/docs/` | Swagger UI，其 `swagger-initializer.js` 仍指向 `https://petstore.swagger.io/v2/swagger.json` —— **它不是真正的规范**；不要把它当作来源。 |
| `https://text.novelai.net/openapi.json` | "Observability API"（错误追踪），与图像生成无关。 |
| `https://docs.novelai.net/en/...` | 产品指南（194 页）。它们描述的是*功能与 UI 设置*，而不是端点或字段名；从不提及 `nai-diffusion-*` id 或 `/ai/*` 路径。 |

用项目自带的浏览器指纹客户端抓取该规范（Cloudflare
会拦截普通客户端）：

```python
from novelai_image_mcp.nai.http import create_http_client

async with create_http_client(timeout=60) as client:
    spec = (await client.get("https://image.novelai.net/docs/doc.json")).json()
```

### 该规范不是字段白名单

`image.RequestParameters` 省略了本客户端会发送、且 API 会接受的字段 ——
`characterPrompts`、`autoSmea`、`ucPresetId`、`qualityPresetId`（V5）、
`normalize_reference_strength_multiple`、`inpaintImg2ImgStrength`、
`legacy_uc`、参数级 `use_coords` —— 并且把 `model`、
`sampler` 与 `noise_schedule` 标注为不带枚举的普通字符串。请把
该规范视为**存在哪些路径**与**响应结构**的权威，
把在线 API 视为**哪些字段可用**的权威。

## 路径清单（文档中记载 27 条）

2026-10-10 用真实账户验证（记录了 Anlas 前后变化）。

| 文档记载的路径 | 本服务器 | 实测结果 |
|---|---|---|
| `POST /ai/generate-image` | V3 / Furry ZIP 路径（`Endpoint.IMAGE`） | 使用 `nai-diffusion-3` 时 200（ZIP） |
| `POST /ai/generate-image-stream` | V4 / V4.5 / V5 msgpack 路径 | 200（`application/msgpack`） |
| `POST /ai/generate-image/suggest-tags` | `suggest_tags` 工具 | 200，`{"tags": [{"tag", "count", "confidence"}]}` |
| `POST /ai/upscale` | `upscale_image` 工具 | 在本主机上**仅 V5 模型**返回 200；旧的 `api.novelai.net` 路径为 404 |
| `POST /ai/augment-image` | `director_tool` | `lineart`、`sketch`、`bg-removal`、`declutter`、`colorize` 返回 200 |
| `POST /ai/encode-vibe` | `encode_vibe` 工具 | 200（二进制 vibe 文件，由客户端做 base64 编码） |
| `GET /user/subscription` | `get_subscription` 工具 | 200 |
| `GET /user/data` | `get_user_data` 工具 | 200 |
| `GET /user/information` | — | 200（邮箱/验证/封禁状态） |
| `GET /user/priority` | — | 200（priority 补充） |
| `GET /user/giftkeys` | — | 使用 persistent token 时 **401** |
| `GET/PUT /user/clientsettings` | — | 使用 persistent token 时 **401** |
| `POST /ai/generate`、`POST /ai/generate-stream` | — | 文本生成；不在本图像服务器的范围内 |
| `/oa/v1/*`（completions、chat、token-count、models） | — | OpenAI 兼容的文本 API；对本账户 `GET /oa/v1/models` 返回空的 `data` |
| `/user/keystore`、`/user/consent`、`/user/create-persistent-token`、`/user/objects/*`、`/user/subscription/bind`、`/user/resend-email-verification` | — | 账户/产品端点；本审计从不调用其中的变更操作与私有数据 |
| `/ai/annotate-image` | `annotate_image` 工具 | **不在该规范中。** 在 `api.novelai.net` 上对 `hed`、`midas`、`fake_scribble`、`mlsd`、`uniformer` 实测 200 —— 这是唯一从未迁移的端点 |

## 改变本代码库的发现

1. **`/ai/upscale` 已迁移且仅支持 V5。** 该端点在
   `image.novelai.net` 上，接收 `{image, model, declared_blur_sigma}`，并
   对每个 V3/V4/V4.5 模型都以 *"model ... doesn't support standalone
   upscaling"* 拒绝。此前的实现向 `api.novelai.net/ai/upscale` POST
   `{image, width, height, scale}`，该地址现在返回 **404** —— 该
   工具当时是坏的。已通过 ``upscale()`` 修复：它向 image 主机发起请求，
   发送文档记载的请求体，把模型默认为
   `NOVELAI_UPSCALE_MODEL`（`nai-diffusion-5-full`），并拒绝除
   4× 步进之外的任何值（该 API 未暴露 factor）。
2. **`suggest_tags` 返回 `{tag, count, confidence}`**，而不是文档声称的
   `{description, text, count}` 结构。`schemas.TagSuggestion`
   现在与线上字段一致（带 `extra="allow"`，因此上游新增字段可以保留）。
3. **`/ai/generate-image`（ZIP）对 V4/V4.5 模型返回 500** —— 这些模型必须
   使用 `/ai/generate-image-stream`。客户端已按模型家族路由
   （`is_v4_model()`），因此无需改动。

## 有意未验证的内容

- `emotion` Director 工具：对没有人脸的合成图像该请求返回 500；
  其余五个 `req_type` 值返回 200。需要一张人像才能确认。
- 任何会变更账户状态的操作（`/user/consent`、`subscription/bind`、
  `create-persistent-token`、`objects/*` 删除）—— 按设计不在范围内。
- `/user/giftkeys` 与 `/user/clientsettings` 对 persistent
  token 返回 401；要记录其结构需要 session token。

## 参见

- [架构](architecture.md) —— `nai/` 如何映射到 API
- [配置](../configuration.md) —— 端点与模型设置
- [传输方式](../transports/index.md)
