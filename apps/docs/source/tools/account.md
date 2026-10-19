# Account tools

Three tools that read account state and estimate costs without making
image-generation API calls. They're safe to call frequently — they don't
consume Anlas.

---

## `get_subscription`

Return the account's subscription details and Anlas balance.

### Parameters

None.

### Returns

`dict` mirroring NovelAI's `/user/subscription` response. The keys and
types below were observed on a live account:

| Key | Type | Notes |
|---|---|---|
| `tier` | `int` | 0 = free, 1 = starter, 2 = ..., 3 = Opus. |
| `active` | `bool` | Whether the subscription is currently active. |
| `accountType` | `int` | Account kind reported by NovelAI. |
| `expiresAt` | `int` | Subscription expiry, as returned by the API. |
| `isGracePeriod` | `bool` | Whether the subscription is in a grace period. |
| `isNewCustomer` | `bool` | Whether the account is a first-time subscriber. |
| `isPaypal` | `bool` | Whether the account pays through PayPal. |
| `paymentProcessor` | `str` | Payment processor id. |
| `paymentProcessorData` | `null` | Was `null` on the account probed; its real type is not established, so do not depend on it. |
| `perks` | `object` | Tier feature flags. |
| `perks.maxPriorityActions` | `int` | Max-priority actions included with the tier. |
| `perks.startPriority` | `int` | Queue priority the tier starts at. |
| `perks.contextTokens` | `int` | Context-token allowance. |
| `perks.unlimitedMaxPriority` | `bool` | Whether max priority is unlimited. |
| `perks.moduleTrainingSteps` | `int` | Module training steps included. |
| `trainingStepsLeft` | `object` | Remaining Anlas-equivalent steps. |
| `trainingStepsLeft.fixedTrainingStepsLeft` | `int` | Fixed (non-purchased) steps remaining. |
| `trainingStepsLeft.purchasedTrainingSteps` | `int` | Purchased steps remaining. |

### Example

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

Return the authenticated account's user data. Useful to confirm which
account the server is authenticated as before issuing generation commands.

### Parameters

None.

### Returns

`dict` with:

| Key | Type | Notes |
|---|---|---|
| `email` | `str` | The account's registered email. |
| `accountChain` | `str` | Registration source (e.g. `google`, `x`, `direct`). |
| `priority` | `int` | Internal epoch. |

### Example

```python
user = await ctx.session.call_tool("get_user_data", {})
print(f"Authenticated as: {user['email']}")
```

---

## `estimate_anlas_cost`

Estimate the Anlas cost of a generation **without** calling the API.
Mirrors NovelAI's public web-client cost formula.

### Parameters

| Name | Type | Default | Notes |
|---|---|---|---|
| `width` | `int` | *required* | Image width (px). |
| `height` | `int` | *required* | Image height (px). |
| `steps` | `int` | *required* | Sampler steps. |
| `n_samples` | `int` | `1` | Number of images. |
| `model` | `str` | `"nai-diffusion-4-5-full"` | Target model. |
| `action` | `str` | `"generate"` | `generate`, `img2img`, or `infill` (inpaint). |
| `strength` | `float \| None` | `None` | Required for `img2img` / `infill` (0.01–0.99). |
| `smea` | `bool \| None` | `None` | SMEA enabled. |
| `smea_dynamic` | `bool \| None` | `None` | Dynamic SMEA enabled. |
| `auto_smea` | `bool` | `False` | Auto SMEA. |
| `opus` | `bool` | `False` | Apply Opus-tier free-sample rules. |

### Returns

`dict` with:

| Key | Type | Notes |
|---|---|---|
| `anlas` | `int` | Estimated Anlas cost. |
| `opus_free_sample` | `bool` | `True` if Opus free-sample applies (no Anlas charged). |

### Example

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

### Cost table (typical)

For reference — single sample, `nai-diffusion-4-5-full`, 28 steps. Measured
with this tool.

**txt2img** (`action="generate"`)

| Resolution | `opus=False` | `opus=True` |
|---|---|---|
| 512 × 768 | 8 | 0 |
| 832 × 1216 | 20 | 0 |
| 1024 × 1024 | 20 | 0 |
| 1536 × 1024 | 30 | 30 |

**img2img** (`action="img2img"`, `strength=0.5`)

| Resolution | `opus=False` | `opus=True` |
|---|---|---|
| 512 × 768 | 4 | 0 |
| 832 × 1216 | 10 | 0 |
| 1024 × 1024 | 10 | 0 |
| 1536 × 1024 | 15 | 15 |

:::{note}
Opus-tier subscribers get **free samples** for small generations (≤1024²,
≤28 steps): inside that window `opus=True` returns `anlas: 0` and
`opus_free_sample: true`. Outside it, `opus` does not change the estimate.
:::

`infill` (inpaint) is priced like `generate`: 832 × 1216 at 28 steps with
`strength=0.5` is 20 Anlas.

Costs scale linearly with `n_samples` — the example above (4 samples at
832 × 1216) is `4 × 20 = 80`.

:::{warning}
On **V5 models**, Opus free generations are capped by NovelAI's refillable
usage limit and the API **silently bills Anlas** once exhausted. Check
`get_subscription`'s `trainingStepsLeft` before costly V5 runs — the
subscription response carries no separate `usage` field.
:::

## See also

- [`estimate_anlas_cost` API reference](../api/tools.md)
- [NovelAI Anlas documentation](https://docs.novelai.net/image/anlas.html)
- [Configuration](../configuration.md) — set generation defaults to control cost
