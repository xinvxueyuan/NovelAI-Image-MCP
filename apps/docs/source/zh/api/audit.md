# `audit`

按路由区分的工具调用所使用的 append-only JSONL 审计轨迹：`build_record`、
`append_record`、`artifact_paths` 与 `resolve_audit_path`，以及让 prompt、图像载荷与凭据
不进入轨迹的脱敏辅助函数。

:::{admonition} 参见
:class: tip

[Insiders 头、分路与审计](../development/insiders-and-routing.md)
了解记录在何时写入，以及
[配置](../configuration.md) 中的 `MCP_AUDIT_LOG_PATH`。
:::

```{eval-rst}
.. automodule:: novelai_image_mcp.audit
   :members:
   :undoc-members:
   :show-inheritance:
```

## 记录何时写入

审计轨迹是 insiders 接口面的一部分：`ToolCallLoggingMiddleware`
**每次工具调用追加一条记录，且仅在 `model-routing` 生效期间**。不发送 opt-in 头的
请求不会写入任何内容。

`resolve_audit_path` 选择目标位置 —— 显式的
`MCP_AUDIT_LOG_PATH` 优先，否则取
`NOVELAI_OUTPUT_DIR` 下的 `audit.jsonl`。

## 记录字段

`build_record` 每次调用产出一个扁平的、可 JSON 序列化的对象：

| 字段 | 内容 |
|---|---|
| `ts` | UTC 时间戳，ISO-8601。 |
| `route` | 净化后的 route。 |
| `model` / `agent` / `client` / `session` | 提取出的路由值，或 `null`。 |
| `tool` | 工具名。 |
| `duration_ms` | 墙上时钟耗时，四舍五入到三位小数。 |
| `outcome` | `ok`、`error` 或 `rejected`。 |
| `features` | 当前生效的 insiders 特性的排序后名字。 |
| `artifacts` | 结果中提到的 `*.png` 路径，已排序。 |
| `unknown_keys` | insiders 头中无法识别的键，已排序。 |
| `malformed` | insiders 头中不可用的条目，已排序。 |
| `headers` | 净化后的路由头快照，上限为 `MAX_RECORDED_HEADERS`（32）个条目、每个至多 `MAX_RECORDED_HEADER_LENGTH`（256）个字符，按键名小写后的字典序排列。 |
| `arguments` | 摘要化后的调用参数 —— 见下文。 |

`features`、`artifacts`、`unknown_keys` 与 `malformed` 会被排序，因此描述同一状态的
两条记录逐字节相同。

## 脱敏

`summarise_arguments` 会在任何参数进入文件之前先将其缩减：

- **形如 prompt 的**参数（`prompt`、`prompts`、`negative_prompt`、
  `negativeprompt`）经 `digest_text` 变为 `{"length": n, "sha256": "<first 16 hex
  characters>"}`。prompt 文本永远不会被写入。
- **形如图像的**参数（`image`、`images`、`init_image`、`mask`、
  `reference`、`references`、`base64`）变为字面量
  `[redacted image]`。
- **任何**长度超过 `MAX_ARGUMENT_LENGTH`（256）的字符串都会被
  摘要化而不是直接写入，因此一个 base64 blob 无法借某个
  意料之外的参数名溜过去。
- 映射被缩减为 `{"keys": n}`；列表、元组与集合被缩减为
  `{"items": n}`；任何其他对象缩减为其类型名。`None`、布尔值、整数
  与浮点数按原样记录。

携带凭据的头会由
`routing._recorded` 在上游移除，因此本模块所限制的快照从一开始就不含
`authorization`、`cookie`、`set-cookie`、`proxy-authorization` 或任何
`*-token` / `*-secret` / `*-password` / `*-key` / `*-credential`
头。

## 并发与持久性

`append_record` 先序列化记录，然后用**恰好一次 `os.write`** 写入到
以 `O_APPEND` 打开的描述符（模式 `0o600`，
必要时创建父目录）。因此并发写入者追加的是
完整行，而不会把同一行从中间交错：写入中途崩溃可能丢掉一行，
但不会破坏已经写好的行。

## 失败行为

可观测性永远不会成为业务路径的依赖。
`append_record` 捕获自身的 `OSError` / `TypeError` / `ValueError`，
用 `logger.error` 记录该失败，并返回 `False` —— 它从不抛出，因此
不存在任何一条代码路径会让不可写的审计文件变成
工具调用失败。

## 参见

- [Insiders 头、分路与审计](../development/insiders-and-routing.md) —— 头语法与 route 解析
- [`middleware`](middleware.md) —— 追加这些记录的调用方
- [`routing`](routing.md) —— 本模块所限制的头快照
