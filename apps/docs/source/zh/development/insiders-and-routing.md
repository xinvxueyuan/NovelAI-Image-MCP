# Insiders 头、分路与审计

insiders 接口面让 HTTP 客户端可以 opt-in 实验性行为，并
声明一个请求属于*哪条* route、model、agent 与 session。本页
记录该头的契约、路由由此推导出什么、它产生的审计
轨迹，以及该特性在已发布形态下的边界。

没有该头时这里的一切都不生效：不发送该头的请求
行为与路由存在之前完全一致，只有一个刻意的例外，
见[向后兼容](#向后兼容)。

## 信任模型

路由头是**客户端提供、因而可伪造的**。它们不是
认证机制，也不得被当作身份。

请把 opt-in 视为你授予一个已在信任边界内的调用方的能力。
在依赖该头所说的任何内容之前，请把服务器放在能认证调用方的
网关后面（或让 `MCP_HOST` 保持 localhost）。头*确实*参与安全决策的
唯一地方是[按路由绑定的 token](#按路由绑定的-token)，在那里
不匹配会 fail closed。

route 值是攻击者可控的字符串，最终会进入文件系统路径与
日志行。因此每条 route 在使用前都要经过白名单；见
[Route 净化](#route-净化)。

## X-MCP-Insiders 头

该头名默认为 `X-MCP-Insiders`，可用
`MCP_INSIDERS_HEADER` 改名。查找是大小写不敏感的，因为 HTTP 头名
本就如此。

### 语法

其值是以逗号分隔的列表。每个问题都会被*上报*并忽略 ——
一个笔误永远不会让请求失败。

| 值 | 效果 |
|---|---|
| *（头缺失）* | 关闭 |
| *（空或仅空白）* | 关闭 |
| `false`、`0`、`off`、`no` | 关闭 |
| `true`、`1`、`on`、`yes` | 开启，每个已注册特性取默认值 |
| `model-routing=false` | 开启，`model-routing` 被强制关闭 |
| `model-routing` | 开启，`model-routing` 被强制开启（裸键） |
| `k=v, k2=v2` | 开启，每个已注册键被逐项覆盖 |

附加规则：

- 键名大小写不敏感，且把 `-` 与 `_` 视为同一字符，
  因此 `Model_Routing` 与 `model-routing` 指向同一个特性。
- 未注册的键会被收集到 `unknown_keys` 并忽略。
  客户端永远无法激活服务器不知道的特性。
- 无法解析的值（例如 `model-routing=maybe`）会被收集到
  `malformed`，该键被丢弃。
- 超过 4096 字符的头会关闭整个头，并在 `malformed` 中记录
  `header-too-long`。

### 已注册特性

| 特性 | 默认 | 生效时的效果 |
|---|---|---|
| `model-routing` | 开 | 该请求的 route、model、agent、client 与 session 由路由头解析得出，并且每次工具调用追加一条审计记录 |
| `experimental-tools` | 开 | 带 insiders tag 的工具会被列出且可调用，`director_tool` 接受其实验性 `emotion` / `emotion_level` 参数 |

"默认开"描述的是**接口面被启用之后**特性的状态。发送
`X-MCP-Insiders: true` 会把两者都打开；完全不发送头则什么都不打开。

优先级，由弱到强：

1. 注册时的默认值，
2. 头中的按请求覆盖，
3. `MCP_INSIDERS_DISABLED_FEATURES` —— 运维侧的强制关闭开关，优先于
   客户端发送的任何内容。

被关闭的头会得到空特性集，无论另外两者如何。

## 声明 route

当 `model-routing` 生效时，路由会读取一组候选头。每个
分组都是有序列表，**第一个携带非空值的头**胜出。

| 字段 | 默认候选 | 环境变量覆盖 |
|---|---|---|
| model | `X-MCP-Model`、`X-MCP-Model-Name` | `MCP_MODEL_HEADERS` |
| agent | `X-MCP-Agent-ID`、`X-MCP-Agent`、`X-MCP-Agent-Source` | `MCP_AGENT_HEADERS` |
| client | `X-MCP-Client`、`X-MCP-Client-Session-Id` | `MCP_CLIENT_HEADERS` |
| session | 名字含 `session` 的第一个 client 候选 | -- |

三个列表变量都是 JSON，例如
`MCP_AGENT_HEADERS='["X-MCP-Agent-ID","X-MCP-Agent"]'`。逗号分隔的
值是 settings 错误，不是列表。

### Route 优先级

route 取以下第一个可用者：

1. 第一个非空的 **agent** 候选，
2. 第一个非空的 **client** 候选，
3. MCP 客户端自报的名字（`client_info.name`），
4. 请求不是经由 HTTP 到达时取 `stdio`，否则取 `unknown`。

### Route 净化

无论 route 来自哪里，它都必须先通过白名单，才能被用作
目录名或写入日志行：

- 允许的字符：`A-Za-z0-9._-`
- 长度：1 到 64 个字符
- 拒绝：路径分隔符（`/`、`\`）、上跳（`.`、`..`）、空白、
  非 ASCII 文本、空字符串，以及任何超过 64 字符的值

被拒绝的值会变成 `unknown`。注意只有 *route* 会被这样净化；
提取出的 `model`、`agent`、`client` 与 `session` 字段保留
原始值，以便运维人员看到客户端实际发送了什么。

## 按路由的日志与审计轨迹

### 日志记录

每次工具调用都会向名为
`novelai_image_mcp.audit.<route>` 的 logger 输出一行，携带工具名、route、model、agent、
client、session、耗时、结果与当前生效的特性。由于 logger
名中包含 route，运维人员可以用标准日志配置按团队分流或过滤。

### 审计记录

**仅在 `model-routing` 生效期间**，审计记录才会被追加到
一个 append-only 的 JSONL 文件。目标位置在设置时取 `MCP_AUDIT_LOG_PATH`，
否则取 `NOVELAI_OUTPUT_DIR` 下的 `audit.jsonl`。

该文件以 `O_APPEND` 打开，每条记录用单次
`os.write` 写入，因此并发写入者追加的是完整行，而不会把同一行
从中间交错。写入中途崩溃可能丢掉一行；但不会破坏
已经写好的行。

| 字段 | 内容 |
|---|---|
| `ts` | UTC 时间戳，ISO-8601 |
| `route` | 净化后的 route |
| `model` / `agent` / `client` / `session` | 提取出的值，或 `null` |
| `tool` | 工具名 |
| `duration_ms` | 墙上时钟耗时，四舍五入到三位小数 |
| `outcome` | `ok`、`error` 或 `rejected` |
| `features` | 当前生效特性的排序后名字 |
| `artifacts` | 结果中提到的 `*.png` 路径，已排序 |
| `unknown_keys` | 头中无法识别的键，已排序 |
| `malformed` | 头中不可用的条目，已排序 |
| `headers` | 净化后的路由头快照，上限 32 个条目、每个至多 256 个字符 |
| `arguments` | 调用参数的摘要（见下） |

### 脱敏

该轨迹的设计保证载荷无法泄漏进去：

- 形如 prompt 的参数（`prompt`、`negative_prompt`、……）会变成
  `{"length": n, "sha256": "<first 16 hex characters>"}`。prompt 文本
  永远不会被写入。
- 形如图像的参数（`image`、`mask`、`images`、`init_image`、
  `references`、`base64`）会变成字面量 `[redacted image]`。
- **任何**超过 256 字符的字符串都会被摘要化而不是直接写入，因此
  一个 base64 blob 无法借某个意料之外的参数名溜过去。
- 容器会被缩减为其大小；未知对象缩减为其类型名。
- 携带凭据的头 —— `authorization`、`cookie`、`set-cookie`、
  `proxy-authorization`，以及任何以 `-token`、`-secret`、
  `-password`、`-passwd`、`-key` 或 `-credential(s)` 结尾的头 —— 会在
  记录之前从头部快照中移除，并且永远不会被写日志。

### 失败行为

审计绝不能破坏它所观察的对象。如果审计文件无法
创建或写入，该失败会以 `ERROR` 级别记录，工具调用仍然
返回正常结果。不存在任何一条代码路径会让审计问题
变成工具调用失败。

## 按路由隔离的输出

当路由生效**且** `MCP_ROUTE_SCOPED_OUTPUT` 为 true（默认值）时，
生成的图像会写入按路由划分的子目录：

```text
<NOVELAI_OUTPUT_DIR>/<sanitised route>/<name>-<timestamp>-<hex>.png
```

`novelai://outputs/{name}` 资源在同一个目录中解析名字，因此
客户端读回的正是它写入的内容。目录名来自上面所述的
同一份白名单，因此恶意 route 无法逃出输出
目录。

路由关闭时，或 `MCP_ROUTE_SCOPED_OUTPUT=false` 时，每个路径都是
路由存在之前服务器所生成的那个路径。

## 按路由绑定的 token

`MCP_AUTH_TOKEN` 保持其原有含义：HTTP 传输使用的一个静态 bearer token，
在任何 MCP 请求被服务之前由 FastMCP 校验。

`MCP_ROUTE_TOKENS` 在此之上增加*按路由绑定*的 token。它是一个把
route 映射到其 token 的 JSON 对象：

```bash
MCP_AUTH_TOKEN=static-token
MCP_ROUTE_TOKENS='{"team-a":"token-for-team-a","team-b":"token-for-team-b"}'
```

路由 token 以它自己的 route 身份认证；当同一个请求通过路由头
声明了一个*不同*的 route 时会被拒绝。不匹配会让
校验器拒绝该请求，bearer 中间件再把它变成带
`WWW-Authenticate` challenge 的 `401` —— 而不是 `ToolError`。两条 route 都会以
`WARNING` 级别记录，因此该拒绝保持可审计。

值得了解的细节：

- **没有可用声明 route** 的请求 —— 完全没有路由头，或
  一个净化后为 `unknown` 的值 —— 会被接受，并归属到该 token 自身的
  route。只有两个*不同*且都存在 route 时才 fail closed。
- 静态 token 从不参与 route 检查，因此无论是否配置了
  路由 token，其语义都不变。
- 某个条目无法被兑现时会被跳过并给出警告：空的
  token、与 `MCP_AUTH_TOKEN` 相同的 token（静态 token 胜出）、未通过
  白名单的 route 名（该 token 根本不会被注册，因此
  永远无法认证），或绑定到两条 route 的 token（排序后
  第一条 route 胜出）。
- 两个设置都未配置时，不会安装任何认证中间件，
  端点行为与之前完全一致。

## 向后兼容

不发送 insiders 头的请求看到的是今天的服务器，只有一个
刻意的例外：

- 工具、资源、prompt 与 schema 不变。
- 没有任何工具被新增或移除。已发布的工具都不带 `insiders` tag，因此
  列表过滤器永远不会对未 opt-in 的客户端隐藏任何东西。
- 生成的图像保持扁平的 `NOVELAI_OUTPUT_DIR` 布局。
- 不会写入审计文件。
- `MCP_AUTH_TOKEN` 行为与之前完全一致。

:::{warning}
**`director_tool` 的 `emotion` 与 `emotion_level` 参数现在受门控。**
在没有 `experimental-tools` opt-in 的情况下传任一个都会以
`ToolError` 失败。这是刻意的行为变更，已记录在
CHANGELOG 的 `Changed` 段。仅一个非默认的 `emotion_level` 也算
传参，因此默认调用形态不受影响。
:::

## 扩展点

- **新增一个平级特性。** 在
  `apps/server/src/novelai_image_mcp/features.py` 的 `INSIDERS_FEATURES` 中加入一个条目，包含其名字、
  `default_enabled` 与一行摘要。头解析器、中间件
  与每个工具都会自动接住它，无需其他改动。
- **门控一个新工具。** 用 `tags={"insiders"}` 注册它。列表过滤器
  与按名拒绝都从该 tag 派生。**不要**把该 tag 加到
  现有工具上：那会让每个不发送该头的客户端都失去该工具。
- **给现有工具门控一个新参数。** 读取
  `features: frozenset[str] = Depends(get_effective_features)`，并在
  `EXPERIMENTAL_TOOLS` 缺失时从工具体内抛出 `ToolError`，就像
  `director_tool` 那样。

## v1 边界

- **工具 schema 是静态的。** FastMCP 在服务器启动时就发布工具的参数 schema，
  因此 schema 无法按请求变化。实验性
  参数因此仍留在 schema 中，opt-in 改为在
  工具体内强制执行。做 schema 内省的客户端能看到该参数，
  但没有该头就无法使用它。
- **路由是按请求的，不是按连接的。** 该头从携带工具调用的
  HTTP 请求中读取。
- **该头不是认证。** 见[信任模型](#信任模型)。

## 参见

- [HTTP 传输](../transports/http.md)
- [配置](../configuration.md)
- [director_tool](../tools/director.md)
