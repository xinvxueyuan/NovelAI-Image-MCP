# 账户工具

三个读取账户状态、且不调用图像生成 API 就能估算成本的工具。它们可以放心
频繁调用 —— 不会消耗 Anlas。

---

## `get_subscription`

返回账户的订阅详情与 Anlas 余额。

### 参数

无。

### 返回

`dict`，与 NovelAI `/user/subscription` 的响应一致：

| 键 | 类型 | 说明 |
|---|---|---|
| `tier` | `int` | 0 = free，1 = starter，2 = ...，3 = Opus。 |
| `active` | `bool` | 订阅当前是否有效。 |
| `trainingStepsLeft` | `dict` | `{fixed: int, perStepUsage: bool}` —— 剩余的 Anlas 等值步数。 |
| `fixedTrainingStepsLeft` | `int` | 不按次计费的 Anlas 等值步数。 |
| `perStepUsage` | `bool` | 步数是否按每次生成扣减。 |
| `subscriptionId` | `str` | 内部订阅 id。 |

### 示例

```python
sub = await ctx.session.call_tool("get_subscription", {})
print(sub["tier"], sub["trainingStepsLeft"]["fixed"])
```

### CLI

```bash
uv run python -m novelai_image_mcp info
```

---

## `get_user_data`

返回已认证账户的用户数据。在下发生成命令之前，用它确认服务器当前认证的
是哪个账户。

### 参数

无。

### 返回

`dict`，包含：

| 键 | 类型 | 说明 |
|---|---|---|
| `email` | `str` | 账户注册邮箱。 |
| `accountChain` | `str` | 注册来源（例如 `google`、`x`、`direct`）。 |
| `priority` | `int` | 内部 epoch。 |

### 示例

```python
user = await ctx.session.call_tool("get_user_data", {})
print(f"Authenticated as: {user['email']}")
```

---

## `estimate_anlas_cost`

**不**调用 API 就估算一次生成的 Anlas 消耗。与 NovelAI 公开 Web 客户端的
成本公式保持一致。

### 参数

| 名称 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `width` | `int` | *必填* | 图像宽度（像素）。 |
| `height` | `int` | *必填* | 图像高度（像素）。 |
| `steps` | `int` | *必填* | 采样器步数。 |
| `n_samples` | `int` | `1` | 图像数量。 |
| `model` | `str` | `"nai-diffusion-4-5-full"` | 目标模型。 |
| `action` | `str` | `"generate"` | `generate`、`img2img` 或 `infill`（局部重绘）。 |
| `strength` | `float \| None` | `None` | `img2img` / `infill` 必填（0.01–0.99）。 |
| `smea` | `bool \| None` | `None` | 是否启用 SMEA。 |
| `smea_dynamic` | `bool \| None` | `None` | 是否启用动态 SMEA。 |
| `auto_smea` | `bool` | `False` | 自动 SMEA。 |
| `opus` | `bool` | `False` | 套用 Opus 档位的免费样本规则。 |

### 返回

`dict`，包含：

| 键 | 类型 | 说明 |
|---|---|---|
| `anlas` | `int` | 估算的 Anlas 消耗。 |
| `opus_free_sample` | `bool` | 若适用 Opus 免费样本（不计 Anlas）则为 `True`。 |

### 示例

```python
cost = await ctx.session.call_tool("estimate_anlas_cost", {
    "width": 832,
    "height": 1216,
    "steps": 28,
    "n_samples": 4,
    "model": "nai-diffusion-4-5-full",
})
# cost: {"anlas": 20, "opus_free_sample": False}
```

### 成本表（典型值）

供参考 —— 单张样本、Opus 档位、`nai-diffusion-4-5-full`、28 步：

| 分辨率 | Anlas（txt2img） | Anlas（img2img，strength=0.5） |
|---|---|---|
| 512 × 768 | 2 | 1 |
| 832 × 1216 | 5 | 3 |
| 1024 × 1024 | 5 | 3 |
| 1536 × 1024 | 7 | 4 |

:::{note}
Opus 档订阅者对小型生成（≤1024²、≤28 步）享有**免费样本**。设置
`opus=True` 即可按已套用免费样本的方式估算。
:::

:::{warning}
在 **V5 模型**上，Opus 免费生成受 NovelAI 可补充的使用额度上限约束，额度用尽
后 API 会**静默计费 Anlas** —— 在昂贵的 V5 批量运行之前，先检查
`get_subscription` 的 `usage` 字段。
:::

## 另请参见

- [`estimate_anlas_cost` API 参考](../api/tools.md)
- [NovelAI Anlas 文档](https://docs.novelai.net/image/anlas.html)
- [配置](../configuration.md) —— 设置生成默认值以控制成本
