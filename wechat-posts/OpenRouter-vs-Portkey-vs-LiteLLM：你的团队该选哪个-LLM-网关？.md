# OpenRouter vs Portkey vs LiteLLM：你的团队该选哪个 LLM 网关？

**作者**: 随野录
**发布时间**: 2026-06-20 10:44
**原文链接**: https://mp.weixin.qq.com/s/q1cW-4hh6Q2M_Dj2S09kuA

---

导读LLM 网关是团队调用大模型的基础设施，选错代价很高。OpenRouter 目前最流行的托管选择，但 Portkey、LiteLLM 各有明确的优势区间。本文聚焦两个核心问题：OpenRouter vs Portkey 怎么选、OpenRouter vs LiteLLM 怎么选，给出按实际场景的决策框架。LLM网关OpenRouterPortkeyLiteLLM成本选型01你的团队需要一个 LLM 网关吗  
很多团队早期直接调 OpenAI API，跑得挺顺。但规模上来就头疼——模型太多、密钥管理乱、切换成本高、没有统一的用量观测。LLM 网关做的事，就是把这件事变简单。三个核心价值：• 统一路由：一个 API 入口背后对接多家模型商，不需要每家单独集成• 成本管理：统一计费、预算控制、用量拆分到项目或团队• 可观测性：请求日志、延迟分布、错误率，按模型、按项目分别统计市面上海量的方案，但最终进决赛的通常是三个：OpenRouter、Portkey、LiteLLM。简单说：OpenRouter 是托管路由，Portkey 是治理层，LiteLLM 是自己部署的开源网关。![](https://r2.jeanjan.kdns.fr/pictures/img-0e6b639101.png)  
  
  
  
  
02OpenRouter：开箱即用的路由网络  
OpenRouter 的核心逻辑很简单：它是一个托管在 Cloudflare 边缘的路由层，接入了 70+ 家模型供应商。你用一套 API，可以切换到任意一家模型——Anthropic、Google、DeepSeek、开源模型都行。70+模型供应商5.5%平台费率100万首免费Token费率结构也很直接：每家模型供应商定价不同，OpenRouter 在此基础上加 5.5% 平台费。新用户有 100 万免费 token 额度，够跑很多实验了。技术实现上，OpenRouter 替你处理了各家 API 的差异——认证方式不同、rate limit 不同、响应格式不同，你只需要跟它的统一接口打交道。路由策略支持按模型、按延迟、按成本自动选择。适用场景很明确：小团队不想运维、想快速接入多模型、需要开箱即用的方案。第一版产品或概念验证阶段，用 OpenRouter 成本最低。  
  
  
  
  
03Portkey：企业级治理与可观测性  
Portkey 在 2025 年被 Palo Alto Networks 收购了，定位变成了企业安全背景下的 AI 网关。它的核心不是路由，而是 治理 和 可观测性。Portkey 的计费模式是按日志量计费——你用多少记录，它收多少费。这和 OpenRouter 的token抽成完全不同。适合的场景是：需要详细审计日志、合规要求高、团队规模较大的企业。Portkey 支持对接 OpenRouter，也可以直连各模型供应商。它的价值在于在你已有的多模型架构上加了一层统一的治理层——虚拟密钥管理、预算分配、访问策略、完整的请求追踪。选 Portkey 而不是 OpenRouter 的核心信号：• 有合规要求：日志必须保留、访问需要审批、数据不能出特定区域• 多团队多项目：需要把用量拆分到BU、拆分到环境、拆分到模型• 已有 OpenRouter：Portkey 可以叠在 OpenRouter 上面做治理，不是非此即彼  
  
  
  
  
04LiteLLM：开源自部署的网关方案  
LiteLLM 思路完全不同：你自己的机器上跑，网关开源免费，依赖 Docker、PostgreSQL、Redis。它的定位是把所有模型 API 统一成 OpenAI 格式——原来用 OpenAI SDK 的代码，基本不用改就能切模型。proxy 层处理认证、限流、预算、日志。成本账要算清楚：$0LiteLLM本体自建Docker/PG/Redis$3600月成本临界点OpenRouter 的官方测算是：月模型支出超过 $3,600 时，自部署 LiteLLM 的基础设施成本可以打平平台费。这是单纯从成本角度算，实际还要考虑运维人力和数据合规。LiteLLM 的另一个强项是数据合规——你的请求日志全在本地，不经过任何第三方。如果你做的是医疗、金融、政府相关业务，数据不能出防火墙，LiteLLM 是几乎唯一的开源选择。  
  
  
  
  
05OpenRouter vs Portkey：按需求选，不按名气选  
| 维度    | OpenRouter   | Portkey               |
|-------|--------------|-----------------------|
| 部署方式  | 托管，SaaS      | 托管 + 可私有化             |
| 接入模型数 | 70+          | 对标 OpenRouter         |
| 计费方式  | token 抽 5.5% | 按日志量计费                |
| 治理能力  | 基础路由 + 限流    | 虚拟密钥、预算、审计            |
| 背景    | 独立公司         | Palo Alto Networks 收购 |

决策逻辑很简单：• 小团队、快速验证 → OpenRouter，零运维，上来就能用• 中大型企业、合规驱动 → Portkey，治理能力完整，日志审计是标配• 已经在用 OpenRouter → 可以叠加 Portkey 做治理层，不是二选一  
  
  
  
  
06OpenRouter vs LiteLLM：自建还是托管  
| 维度     | OpenRouter | LiteLLM      |
|--------|------------|--------------|
| 部署方式   | 托管，SaaS    | 自部署 Docker   |
| 平台费用   | 5.5%       | 0（基础设施另算）    |
| 数据控制   | 经过第三方      | 完全自主         |
| 运维复杂度  | 零运维        | 需维护 PG/Redis |
| 月成本临界点 | —          | $3,600 模型支出  |

  
  
  
  
  
07决策框架：按场景给出答案  
三个问题帮你快速定位：• 月均模型支出多少？$0 – $3,600：OpenRouter 托管方案最省心$3,600+：LiteLLM 自建开始划算，加上运维人力再评估• 数据能不能出防火墙？不能 → LiteLLM，没有第二个选择。能 → 继续往下看。• 团队规模多大？5 人以内：OpenRouter，运维负担接近零。50 人以上且多项目 → Portkey 治理层值得上。  
  
  
  
  
08快速上手：OpenRouter 最小示例  
OpenRouter 的接入成本极低，官方提供了兼容 OpenAI 的 API 格式，SDK 不用换。

```

from openai import OpenAI  
client = OpenAI(
     base_url="https://openrouter.ai/api/v1",     
     api_key="sk-or-v1-xxxx" 
)  
response = client.chat.completions.create(
     model="anthropic/claude-3-5-sonnet-20241022",     
     messages=[{
         "role":"user",
         "content":"用一句话解释 LLM 网关是什么"
     }] 
) 
print(response.choices[0].message.content)
```

一行改 base_url，模型名称换成 OpenRouter 的模型 ID（格式是 提供商/模型名），就能在几十家模型之间切换。没有额外依赖。  
  
  
  
  
09行业背景：LLM 网关格局在变  
Portkey 被 Palo Alto 收购，说明安全厂商开始把 AI 网关当成企业安全架构的一部分。LiteLLM 的开源社区活跃度在持续上升，背后是自部署需求在增长。国内的话，阿里开源了向量数据库 Zvec，DeepSeek 研究员也开源了 AutoResearch——这些动作说明国产 AI 基础设施层的投入在加大。后续国内团队选型时，开源方案和国产云厂商的网关服务会是一个新的考量维度。从 Cloudflare 为 AI 智能体推出临时账户、到 Adobe 在 Creative Cloud 里加入 AI 智能体，大厂在 AI 基础设施层的动作越来越具体。LLM 网关不再是可选项，而是 AI 应用架构的基础层。  
  
  
  
  
10总结：没有最优解，只有最适合的起点  
回到最初的问题：你的团队该选哪个？初期 / 验证OpenRouter企业 / 合规Portkey大用量 / 数据自主LiteLLM这三个选项不是互斥的。很多团队的最优路径是：先用 OpenRouter 跑通产品验证，中期加 Portkey 做治理层，后期随着用量增长自建 LiteLLM。技术选型不是一次性决策，而是跟着业务节奏走。最重要的一点：不要为了"技术正确"选一个超出团队当前运维能力的方案。小团队用 OpenRouter 把时间花在产品上，比花时间维护 Docker 和 PostgreSQL 划算得多。  
  
  
  
  
参考来源 • **OpenRouter vs Portkey：你的团队该选哪个 LLM 网关？** https://openrouter.ai/blog/insights/openrouter-vs-portkey• **OpenRouter vs LiteLLM：如何选择 LLM 网关** https://openrouter.ai/blog/insights/openrouter-vs-litellm• **AI HOT — 最近 30 条精选动态** https://aihot.virxact.com

