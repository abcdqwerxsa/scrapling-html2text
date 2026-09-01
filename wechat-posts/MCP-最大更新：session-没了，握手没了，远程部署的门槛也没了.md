# MCP 最大更新：session 没了，握手没了，远程部署的门槛也没了

**作者**: AI工程化
**发布时间**: 2026-07-30 10:02
**原文链接**: https://mp.weixin.qq.com/s/qOz91FYx1QdZ2YX5uCrF-w

---

MCP 新版本刚刚发布，这是协议诞生以来最大的一次更新。官方博客用了一个词：**stateless core** 。

不是小修小补。是整个协议的内核从双向有状态变成了请求/响应的无状态模型。

具体来说，以前 MCP 需要客户端先发 `initialize`，服务器回 `initialized`，然后靠 `Mcp-Session-Id` 头维持会话。现在这些全没了。每个请求自己带着协议版本、客户端身份和能力信息（放在 `_meta` 字段里），可以落在任何一台服务器实例上，后面挂个普通的 round-robin 负载均衡就行。

![](https://r2.jeanjan.kdns.fr/pictures/img-462a857901.jpeg)

如果你还是想提前知道服务器有什么能力，可以用新的 `server/discover` RPC。但它是可选的，不是必须的。

这对运维意味着什么？部署远程 MCP 服务器不再需要共享存储来维持会话状态。拿起来就能跑，水平扩展门槛大幅降低。

当然，协议层面无状态不强迫你的应用也无状态。如果你的工具确实需要跨调用保持状态，官方建议的做法是：让工具自己生成一个 handle，让模型把它当参数传来传去。好处是模型能"看到"这个状态，比藏在传输层里的 session 透明得多。

除了无状态，这次还有几个值得关注的变化：

**Multi Round-Trip Requests (MRTR)**

以前服务端要向客户端发请求（比如 elicitation 让用户确认操作、sampling 调模型、roots 列根目录），必须维持一条双向流。现在 MRTR 用了一种更聪明的做法：服务器返回 `resultType: "input_required"`，附带需要用户回答的问题，客户端收到后带着答案重试原始调用。全程不需要常驻连接。

这对 Supabase 这种本来就跑在无状态架构上的 MCP 服务是直接利好——他们之前想做 elicitation 一直做不了，MRTR 直接解了这个问题。

**Header-based routing**

Streamable HTTP 请求现在必须带 `Mcp-Method` 和 `Mcp-Name` 头。网关、限流器、WAF 可以直接在 HTTP 头层面做路由和计量，不需要解析 JSON body。

**列表结果可缓存**

`tools/list`、`prompts/list`、`resources/list`、`resources/read` 的响应现在带 `ttlMs` 和 `cacheScope`。客户端可以缓存工具目录，重连时不用反复拉取。

**授权强化**

授权是过去一年开发者花最多时间集成的地方。这次做了几件事：

  * 要求授权服务器返回 `iss` 参数（RFC 9207），客户端兑换 token 前必须验证，堵住了授权服务器混用的漏洞
  * 动态客户端注册（DCR）正式弃用，转向 Client ID Metadata Documents（CIMD）。DCR 还能用，但未来会被移除
  * 客户端凭证绑定到签发它的授权服务器，不能跨服务器复用

**Tasks 正式成为扩展**

Tasks 从实验性核心移出，成为 `io.modelcontextprotocol/tasks` 扩展。改成基于轮询的 `tasks/get` 加新的 `tasks/update`。变更通知也不再走 HTTP GET 端点，统一到 `subscriptions/listen` 流。

**正式弃用政策**

Roots、Sampling、Logging 三个旧功能被标记弃用。HTTP+SSE 传输方式也被弃用。但都给了至少 12 个月的缓冲期，不是突然砍掉。

SDK 方面，TypeScript、Python、Go、C# 四个 Tier 1 SDK 已全部支持新规范。Rust SDK 也在 beta 阶段。

有网友 Evan Kirstel 说得挺到位：

> 无状态是一种不起眼的修复，但它让这套协议能在真实公司内部真正部署起来。没人会为它发推，但每个运维团队都能感受到。这才是最好的发布。

另一位网友 Chad Justice 也提到了实际场景：

> 在同一代码库上并行跑多个 Claude Code 实例时，服务端任何有状态的东西都会迅速变成协调噩梦。

如果你之前因为远程 MCP 服务器部署复杂而观望，现在可以重新评估了。MCP 正在从 demo 变成真正的基础设施。

  * MCP 发布公告 (https://claude.com/blog/bringing-mcp-2026-07-28-to-claude)
  * MCP 官方博客 (https://blog.modelcontextprotocol.io/posts/2026-07-28/)
  * 新规范文档 (https://modelcontextprotocol.io/specification/2026-07-28)

  

  

关注公众号回复“进群”入群讨论

