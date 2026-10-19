# 账户工具

三个读取账户状态、且不调用图像生成 API 就能估算成本的工具。它们可以放心
频繁调用 —— 不会消耗 Anlas。

---

## `get_subscription`

返回账户的订阅详情与 Anlas 余额。

### 参数

无。

### 返回

`dict`，与 NovelAI `/user/subscription` 的响应一致。下表的键与类型均在真实
账户上观测得到：

| 键 | 类型 | 说明 |
|---|---|---|
| `tier` | `int` | 0 = free，1 = starter，2 = ...，3 = Opus。 |
| `active` | `bool` | 订阅当前是否有效。 |
| `accountType` | `int` | NovelAI 报告的账户类型。 |
| `expiresAt` | `int` | 订阅到期时间，按 API 返回的原样。 |
| `isGracePeriod` | `bool` | 订阅是否处于宽限期。 |
| `isNewCustomer` | `bool` | 账户是否为首次订阅者。 |
| `isPaypal` | `bool` | 账户是否通过 PayPal 付款。 |
| `paymentProcessor` | `str` | 支付处理方 id。 |
| `paymentProcessorData` | `null` | 在所探测的账户上为 `null`；其真实类型尚未确定，因此不要依赖它。 |
| `perks` | `object` | 档位功能标志。 |
| `perks.maxPriorityActions` | `int` | 该档位包含的最高优先级操作数。 |
| `perks.startPriority` | `int` | 该档位起始的队列优先级。 |
| `perks.contextTokens` | `int` | 上下文 token 配额。 |
| `perks.unlimitedMaxPriority` | `bool` | 最高优先级是否不限量。 |
| `perks.moduleTrainingSteps` | `int` | 包含的模块训练步数。 |
| `trainingStepsLeft` | `object` | 剩余的 Anlas 等值步数。 |
| `trainingStepsLeft.fixedTrainingStepsLeft` | `int` | 剩余的固定（非购买）步数。 |
| `trainingStepsLeft.purchasedTrainingSteps` | `int` | 剩余的已购买步数。 |

### 示例

```python
sub = await ctx.session.call_tool("get_subscription", {})
print(sub["tier"], sub["trainingStepsLeft"]["fixedTrainingStepsLeft"])
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
# cost: {"anlas": 80, "opus_free_sample": False}
```

### 成本表（典型值）

供参考 —— 单张样本、`nai-diffusion-4-5-full`、28 步。使用本工具
实测。

**txt2img**（`action="generate"`）

| 分辨率 | `opus=False` | `opus=True` |
|---|---|---|
| 512 × 768 | 8 | 0 |
| 832 × 1216 | 20 | 0 |
| 1024 × 1024 | 20 | 0 |
| 1536 × 1024 | 30 | 30 |

**img2img**（`action="img2img"`、`strength=0.5`）

| 分辨率 | `opus=False` | `opus=True` |
|---|---|---|
| 512 × 768 | 4 | 0 |
| 832 × 1216 | 10 | 0 |
| 1024 × 1024 | 10 | 0 |
| 1536 × 1024 | 15 | 15 |

:::{note}
Opus 档订阅者对小型生成（≤1024²、≤28 步）享有**免费样本**：在该窗口内
`opus=True` 返回 `anlas: 0` 与 `opus_free_sample: true`。超出该窗口时，
`opus` 不改变估算结果。
:::

`infill`（局部重绘）的计价与 `generate` 相同：832 × 1216、28 步、
`strength=0.5` 时为 20 Anlas。

成本随 `n_samples` 线性增长 —— 上面的示例（832 × 1216 的 4 张样本）为
`4 × 20 = 80`。

:::{warning}
在 **V5 模型**上，Opus 免费生成受 NovelAI 可补充的使用额度上限约束，额度用尽
后 API 会**静默计费 Anlas**。在昂贵的 V5 批量运行之前，先检查
`get_subscription` 的 `trainingStepsLeft` —— 订阅响应中没有单独的
`usage` 字段。
:::

## 另请参见

- [`estimate_anlas_cost` API 参考](../api/tools.md)
- [NovelAI Anlas 文档](https://docs.novelai.net/image/anlas.html)
- [配置](../configuration.md) —— 设置生成默认值以控制成本
