# 工具参考

服务器在 [`FastMCP`](../api/server.md) 实例上注册了 **11 个 MCP 工具**。每个工具
都是 `async` 的，并从 MCP 请求上下文的 lifespan 状态中读取依赖
（`NovelAIClient` 与 `NovelAISettings`）。

## 工具索引

| 工具 | 分组 | 说明 |
|---|---|---|
| [`generate_image`](generate.md#generate_image) | generation | 文生图（V3 / V4 / V4.5 / V5、角色提示词、vibe） |
| [`image_to_image`](generate.md#image_to_image) | generation | 带 strength / noise 的图生图 |
| [`inpaint`](generate.md#inpaint) | generation | 局部重绘（需要 inpaint 模型 + 蒙版） |
| [`upscale_image`](upscale.md#upscale_image) | enhance | 4× 放大（V5 模型） |
| [`director_tool`](director.md#director_tool) | enhance | 线稿 / 素描 / 背景移除 / declutter / 上色 / 表情 |
| [`annotate_image`](annotate.md#annotate_image) | enhance | ControlNet 预处理（hed、midas、fake_scribble、mlsd、uniformer） |
| [`suggest_tags`](tags.md#suggest_tags) | tags | 提示词标签推荐 |
| [`encode_vibe`](vibe.md#encode_vibe) | tags | 把参考图编码为 vibe token |
| [`get_subscription`](account.md#get_subscription) | account | 账户订阅 + Anlas 余额 |
| [`get_user_data`](account.md#get_user_data) | account | 账户用户数据 |
| [`estimate_anlas_cost`](account.md#estimate_anlas_cost) | account | 不调用 API 估算 Anlas 消耗 |

## 通用约定

### 返回结构

每个产出图像的工具都返回一个 MCP 内容块列表：

```python
[
    Image(data=b"...png bytes...", format="png"),  # agent sees the image
    f"Saved 1 image(s): ['outputs/generate-...png']"  # text path for follow-up
]
```

智能体既可以内联查看图像（base64 `Image` 块），也可以从文本块里读出路径，
传给后续工具。

### 图像参数

接收 `str` 的图像参数（`image`、`mask`、`reference`、`references`）期望的是
**base64 编码的 PNG 或 JPEG** 字符串，而不是文件路径。要转换本地文件：

```python
import base64
from pathlib import Path

image_b64 = base64.b64encode(Path("input.png").read_bytes()).decode("ascii")
```

CLI 会自动完成这一步 —— `upscale`、`director` 与 `annotate` 都把输入文件作为
位置参数（例如 `upscale ./input.png`）。

### 校验

工具会尽早校验输入：当枚举式参数（`model`、`tool`、`emotion`、
`controlnet model`、`action`）不匹配时，抛出带合法选项列表的 `ValueError`。
MCP 运行时会把它们呈现为工具调用错误，智能体可以读取并自行纠正。

## 各工具页面

```{toctree}
:maxdepth: 1
:hidden:

generate
upscale
director
annotate
tags
vibe
account
```

## 另请参见

- [教程](../tutorials/index.md) —— 组合多个工具的端到端工作流
- [Agent 技能](../skills.md) —— `novelai-mcp-tools` 技能把这份参考打包给 AI 智能体
- [API 参考](../api/index.md) —— 底层 `NovelAIClient` 的 autodoc
- [配置](../configuration.md) —— 省略参数时套用的默认值
