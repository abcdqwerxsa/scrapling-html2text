# wigolo：给 AI Agent 装一个本地联网大脑，零 API Key，零按次计费

**作者**: AI工程化
**发布时间**: 2026-07-20 08:02
**原文链接**: https://mp.weixin.qq.com/s/HGFVaFsvkJhbhN48L9A5Rw

---

还在给AI配各种搜索API？

按次计费、API Key管理、数据隐私...这些麻烦事，有一个开源项目换了个思路：**wigolo** 。

它把搜索、网页抓取、爬虫、信息提取、缓存、Research全塞进一个本地MCP Server，不需要API Key，不按次数付费，所有数据留在本地机器上。

## 一个命令，搞定所有

wigolo 的安装极其简单，要求 Node ≥ 20 和约 1.5 GB 磁盘空间（用来放浏览器引擎和本地模型）。macOS、Linux、Windows 都支持。
```

npx wigolo init --agents=claude-code  # 自动配置 Claude Code
```

`init` 命令自动下载浏览器引擎、本地模型，并配置好 MCP 客户端。wire 完就能用，搜索、抓取、爬虫、提取、缓存、相似搜索，全都不需要 API Key。

如果你想要更强大的 `research` 和 `agent` 功能，建议配一个免费 Gemini Key（从 aistudio.google.com 免费获取），用来做合成回答。但核心搜索和抓取，完全不需要。

## 能干什么？怎么做到的？

wigolo 提供了 10 个工具。本质上是一个**单 Node 进程** ，通过 MCP 协议（JSON-RPC over stdio）与 AI Agent 通信，所有重活都在本地按需懒加载。

![wigolo architecture](https://r2.jeanjan.kdns.fr/pictures/img-e7442f5a01.svg)

**搜索（`search`）**：同时向 18 个搜索引擎发请求——直接适配器，不走聚合 API。拿到结果后做排序融合（rank fusion），再用本地 ML 模型重排序，最后给每个结果打一个可解释的分数：语义相关性多少、词汇匹配多少、几个引擎共同推荐了它。这意味着你不用为每次搜索付费，重排序和嵌入都跑在本地硬件上。

**抓取（`fetch`）**：有一个分层升级的 fetch router。先尝试普通 HTTP 请求；如果页面是 SPA 壳或触发反爬挑战，自动升级到 headless 浏览器渲染。升级逻辑不靠域名猜测，而是根据实际响应内容判断——看到 SPA 标记就升级，看到 challenge 页面就等待。它还会按域名学习：某个域名被标记为"需要浏览器"后，下次直接走浏览器通道；后续发现不需要了，自动降级。`wigolo tune list` 能看到它学到了什么。翻不过去的墙，返回 `blocked_by_challenge` 标签，不把反爬页面伪装成正文。

**缓存（`cache`）**：所有抓过的页面存在 `~/.wigolo/` 下，带关键词索引和向量索引。同一个问题问第二次，直接从缓存返回，零延迟。嵌入模型和重排序模型也跑在本机——数据不会发送到第三方，除非你主动配了 LLM 做合成。

**研究（`research`）和自主代理（`agent`）**：前者分解问题 → 并行搜索 → 获取源 → 合成带引用的报告；后者是自主循环：规划 → 搜索 → 获取 → 提取 → 合成，带时间预算和输出 Schema。这两个需要 LLM 来写合成回答，配个免费 Gemini Key 或接 Ollama 都行。

其他工具——`crawl`（多页面爬取，遵守 robots.txt 和速率限制）、`extract`（提取结构化数据）、`find_similar`（找相似页面）、`diff` \+ `watch`（监控页面变化推 webhook）——各司其职，也都从终端、交互式 Shell、REST API、TypeScript/Python SDK 多通道可用。

三个设计原则贯穿始终：**能用代码解决的绝不碰 LLM** （规范化、去重、排序融合这些确定性工作全走代码，LLM 只用于合成回答，生成内容会跟原文校验）；**根据可观测信号做路由** （fetch 升级看响应体里有没有 SPA 标记，不是"这个域名看起来像"）；**能读就读，读不了就直说** （缓存过期、抓取失败、后端降级，全在结果里标出来）。

项目作者做了一次实测：用同一个问题同时调用 Claude 内置的 WebSearch、wigolo、Tavily、Exa，四个工具给出了相同的核心答案，但只有 wigolo 返回了带精确源位置的原文片段，并且弱结果被自己标记为"垃圾"。

## 快速上手

  1. 安装 Node.js 20+，然后运行：

```

npx wigolo init --agents=claude-code  # 或 cursor, codex, gemini-cli 等
```

  2. 检查健康：

```

npx wigolo doctor
```

  3. 在 Claude Code 里直接问联网问题，比如"最新 PostgreSQL 16 的发布说明"，它会自动调用 wigolo 搜索并返回结果。

如果想用 research 合成功能，加一个免费 Gemini Key：
```

export WIGOLO_LLM_PROVIDER=gemini  
export GEMINI_API_KEY=<your-free-key>
```

## 小结

本地跑一个浏览器引擎+模型，成本远低于按次计费的 API。而且数据隐私、延迟、可定制性，本地方案都有优势。

当然，它也不是完美。比如一些反爬严格的网站，数据中心 IP 可能不如家庭宽带好用。但 wigolo 会明确标记失败，而不是假装成功。

如果需要做需要联网搜索的任务，不妨试试 wigolo。它不会让你变富，但能让你省下买 API 的钱。

项目地址：https://github.com/KnockOutEZ/wigolo 

关注公众号回复“进群”入群讨论

  


