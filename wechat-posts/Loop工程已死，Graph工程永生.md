# Loop工程已死，Graph工程永生

**作者**: PaperAgent
**发布时间**: 2026-07-21 11:29
**原文链接**: https://mp.weixin.qq.com/s/i3zHIqkJU9cX1G1Nc5RUzA

---

大家好，我是PaperAgent，不是Agent！

最近**Loop Engineering** 已经不吃香了，**Graph Engineering** 火爆，连龙虾（OpenClaw）**之父Peter Steinberger** 都开始调侃：我们还在讨论Loops吗？还是已经开始讨论Graphs了？

![](https://r2.jeanjan.kdns.fr/pictures/img-4c57019701.jpeg)![Loop Engineering is dead. Long live Graph Engineering!](https://r2.jeanjan.kdns.fr/pictures/img-4c57019702.jpeg)Loop Engineering is dead. Long live Graph Engineering!

接下来，咱们就聊一聊什么是**Graph Engineering** ，以及如何入手!**[DeepSeek和Kimi之后，又一家中国企业出手了](https://mp.weixin.qq.com/s?__biz=Mzk0MTYzMzMxMA==&mid=2247509063&idx=1&sn=18c9c68d19d5f87274b409d6145f5950&scene=21#wechat_redirect)**

直接上图，比较清晰

  * **Loop Engineering** （循环工程）：研究如何让模型自动长时间持续运行，更好地完成任务
  * **Graph Engineering** （图工程）：研究如何用图（有向图）来组织多个Agent的写作与流传，解决真实场景中的复杂问题

![https://x.com/indie_maker_fox/status/2079042889892651047](https://r2.jeanjan.kdns.fr/pictures/img-4c57019704.jpeg)https://x.com/indie_maker_fox/status/2079042889892651047

最初， **Agent** 的运行理解为简单的 while 循环结构——Agent Loop。今年兴起的 Loop Engineering，实际上是在循环外面再套一层循环，也就是父循环包裹子循环，减少人工干预，让 Agent 自己感知环境变化，持续执行直到达成目标。

然而，在实际场景中，可能需要**多个 Agent 并行运行** ，而且它们之间可能存在依赖关系，并不像 while 循环结构那么简单。在计算机中对应的概念就是图（**Graph** ）。

这个 **Graph** 是有向图（Directed Graph），因为一个 Agent 处理完的结果可能需要传递给另一个 Agent 继续处理。

Claude的**Graph Engineering** 实操入门：

![](https://r2.jeanjan.kdns.fr/pictures/img-4c57019705.jpeg)

## 01\. 节点是任务，边是流动的东西

一张图只有两样东西，把两者分清就能消除大半困惑。**节点** 是一个工作单元--一个 agent、一个有界任务、一进一出。**边是依赖关系** ：它声明这个节点的输出喂给那个节点的输入，仅此而已。

![节点是任务，边是数据流动](https://r2.jeanjan.kdns.fr/pictures/img-4c57019706.jpeg)节点是任务，边是数据流动

常见错误是把"然后"当成边。"总结这个文件，然后告诉我天气"--两者之间没有边，天气不消费摘要。那是两个本可独立、却被线性脚本无谓串起来的节点。边只有在数据真正流过时才存在。**对每个"然后"问一句：下一步是否读了上一步的输出？如果没有，就没有边，等待是浪费。**

##  02\. 你的线性脚本是一张退化图

当你把 agent 写成"做 A、然后 B、然后 C、然后 D"，你其实已经画了一张图--单条不分叉的链，每个节点一进一出。它能跑对，但慢且脆：链没有冗余，**C 卡住则 D 不跑** ，A 的成果被困在上游无处可去。

![线性脚本是一张退化图](https://r2.jeanjan.kdns.fr/pictures/img-4c57019707.jpeg)线性脚本是一张退化图

**图工程的第一项真本事就是重画这条链。** 拿你的线性 agent，对每个箭头问第 01 步的问题。多数链有两三个不携数据的箭头--只是你打字的顺序。剪掉它们，链就塌成更宽的形状：几个能同时跑的独立节点，喂给一个需要它们全部的节点。

## 03\. 给每个节点一个契约

无法推理的节点无法并行。**解法是契约：有界输入、有界输出、恰好一个任务。** 输入显式传入（绝不假设来自共享窗口），输出是定义好的形状（最好经过校验），让下一节点无需猜测就能消费。

![](https://r2.jeanjan.kdns.fr/pictures/img-4c57019708.jpeg)

在 workflow 里，契约用 **schema** 强制。给 `agent()` 一个 JSON schema，spawn 出的 subagent 被迫返回校验过的结构化数据--校验在 tool-call 层发生，mismatch 时 Claude 自动重试，而不是甩给你一段要"解析并祈祷"的自由文本。这就是"Claude 能接进图的节点"与"只有人读得懂的输出才管用的节点"之间的差别。

## 04\. 把边当作数据契约

边不只是"B 在 A 之后"，而是关于跨越内容的承诺：A 产出这个形状，B 被设计来消费这个形状。按数据而非顺序给边命名，两件事变容易：一眼看出边是否真实（数据真在流动吗）；在保持形状前提下换掉任一端的节点。

![](https://r2.jeanjan.kdns.fr/pictures/img-4c57019709.jpeg)

实践中边就是普通 JS：扇出与综合之间的 reduce（flatten / dedupe / filter）只是操作节点返回形状的代码。**不需要 agent。** 人们烧在 token 上的大量工作其实都是边，而边免费。

## 05\. 用 parallel() 扇出

这是为一切买单的关键招。当你有 N 个独立节点--N 个待查来源、N 个待审文件、N 条待审路由--不要串起来。让 Claude 把它们扇出、同时跑。在 workflow 里就是 `parallel()`：Claude 接受一个 thunk 数组，每个 thunk spawn 一个 subagent 全部并发执行，再返回结果数组。

![](https://r2.jeanjan.kdns.fr/pictures/img-4c57019710.jpeg)

**两个细节让它稳健。** 第一，`parallel()` 是 barrier--等所有 thunk 完成才返回，下一阶段看到完整集合。第二，抛错的 thunk 解析为 `null` 而非拖垮整批，**一个抽风的 agent 沉不掉整个 run** 。永远 `.filter(Boolean)`。并发按核数封顶、超额排队，传 100 个 thunk 也都跑得完。

扇出活在 Claude 写的代码里，不在模型对话里--Claude 自己的上下文从不同时持有 9 个来源，每个 subagent 自带上下文，只把最终答案传回。**这就是让 Claude 把 workflow 扩到几十上百个 subagent 而不淹没会话的原因** ，编排层零 token，因为它不是 Claude 的又一轮思考。

## 06\. 在 barrier 处扇入

扇出只有被汇聚才有用。扇入是边汇聚的节点--一个 agent（或一段代码）一次看到全部上游结果，做需要全集才能做的事：跨来源去重、按影响排序、总量为空则提前退出。这是 barrier 唯一配得上其 wall-clock 代价的地方。

![](https://r2.jeanjan.kdns.fr/pictures/img-4c57019711.jpeg)

**保持图快的规则：仅当某阶段真的需要全部前序结果时才用 barrier。** 跨所有来源去重？barrier--正确。只是展平列表？那是边，inline 做。嗅觉测试：如果你写了 `parallel -> transform -> parallel`，中间那个 transform 没有跨项依赖，就该用 pipeline、跳过 barrier。

## 07\. 钻石：拆分 -> 工作 -> 合并

把扇出和扇入拼起来，就得到每个严肃 agent 图的主力拓扑：**钻石** 。一个节点拆活、多个节点并行干活、一个节点合并。市场扫描、依赖审计、代码审查、研究报告--换来源和 prompt，同一副骨架都适配。

![](https://r2.jeanjan.kdns.fr/pictures/img-4c57019712.jpeg)

**其规范形式有个值得记住的名字：fan out - > reduce -> synthesize。** 扇出取广度、用纯代码 reduce 压缩、用最终 agent synthesize 写答案。看到钻石后，你不再问"怎么让 agent 多做几步"，而是问"在哪拆、在哪合"--这才是真正能 scale 的问题。

## 08\. 用条件在运行时路由边

并非每张图都是固定的。有时该走哪条边取决于节点发现了什么。router 节点检查结果并决定哪条下游路径触发--给工单分类再分支到对应处理器；看 diff 大小再决定快速审查还是全面审计。在 workflow 里这就是对节点校验输出做一个 JS `if`/`switch`，因为控制流活在代码里。

![](https://r2.jeanjan.kdns.fr/pictures/img-4c57019713.jpeg)

**确定性在这里成了特性而非限制。** 路由决策可由 Claude 驱动（subagent 分类），但路由本身是 Claude 写的代码--同一分类每次走同一条路。节点处用 Claude 的判断，边处用脚本的可靠。不会出现"Claude 决定跳过审计"的涌现意外--因为跳过必须被写进图里，而它并没有。

## 09\. 在边上放一个验证器

图真正的杠杆不是更多 agent，而是你能在 agent 周围包裹的结构--用来产生**信心** 。验证器节点坐在边上，在结果放行下游之前，唯一职责是**尝试毙掉这个发现** 。活下来才放行，否则永远到不了答案。

![](https://r2.jeanjan.kdns.fr/pictures/img-4c57019714.jpeg)

三种模式值得掌握：

  * **对抗式验证** ：每个发现 spawn N 个独立怀疑者去反驳，多数存活才保留。
  * **多视角验证** ：给每个验证器不同视角--正确性、安全、能否复现--多样性抓得到 N 个相同检查抓不到的失败模式。
  * **裁判组** ：从不同角度生成 N 个尝试，用并行 judge 打分，从赢家综合并嫁接亚军最好的部分。

作者声称正是这个模式让一个团队把 Bun 运行时移植时把对抗式代码审查内建进了循环。

## 10\. 隔离节点，一次失败毒不到整张图

链里失败会级联--C 死、D 不跑、整体停摆。图里**失败应被限制在它自己的节点内。** 这已部分成立：`parallel()` 里抛错的 thunk 解析为 `null`，8 个好 agent 照常返回，1 个坏的掉队。`.filter(Boolean)` 就是隔离。设计每个扇入时容忍缺失输入，而非假设全集。

![](https://r2.jeanjan.kdns.fr/pictures/img-4c57019715.jpeg)

更微妙的失败是节点互相踩。agent 并行写文件会撞车。解法是 `isolation: "worktree"`\--每个 agent 在自己的 git worktree 里跑、在沙箱里干活、干净地合并。**只在节点确实并行写时才用** ，它是那一种拓扑的安全带，不是每次 run 的默认税。

## 11\. 加一个环--但要让它收敛

有时你不到身在其中不知道活有多大：未知规模的发现、一次 bug 扫描找到一个又牵出三个。这需要**环** \--一条受控的、指回更早节点的边。危险也明显：不收敛的环是死循环，会一直 spawn agent 直到预算耗光。

![](https://r2.jeanjan.kdns.fr/pictures/img-4c57019716.jpeg)

**收敛的模式是 loop-until-dry：** 持续 spawn finder，直到连续 K 轮没有新发现才停。那个成败攸关、几乎人人第一次都错的细节是**去重对照什么** \--对照所有见过的，而不只是对照已确认的。否则被拒的发现每轮重现，循环永不干涸，你造了一台花钱反复挖同一片死胡同的机器。

## 12\. 跨节点分层模型

不是每个节点都需要你最好的模型。图把这摆得明明白白：有些节点有界且重复（抽字段、分工单），有些承载真判断（综合报告、裁决发现）。无聊节点跑便宜模型，贵 token 花在判断真正所在之处。

![](https://r2.jeanjan.kdns.fr/pictures/img-4c57019717.jpeg)

workflow 里每个 subagent 默认继承你的 session 模型，除非脚本覆盖--所以默认一次大 run 全程按 session 档计费。单个 `agent()` 的 `model` 选项让 Claude 把那一个节点路由到别处。**大 run 前查` /model`，让 Claude 把扇出的重复节点降档、合并节点保高档**\--这是把一张吃 token 的图从贵变省、却不改形状的杠杆。

## 13\. 拓扑就是你的成本与延迟

图的形状不是装饰--**它是 wall-clock 时间最大的杠杆** 。绊倒所有人的选择：`parallel()` vs `pipeline()`。`parallel()` barrier 让一切等最慢的节点；`pipeline()` 让每个 item 独立流过所有阶段、无 barrier--item A 可能在第 3 阶段而 B 还在第 1 阶段，快的早完成而不是在慢的后面干等。

![](https://r2.jeanjan.kdns.fr/pictures/img-4c57019718.jpeg)

**默认用` pipeline()`。** 只在某阶段真的需要全部前序结果时才用 barrier--跨集合去重、总量提前退出、prompt 要对照"其他发现"。"代码更干净""阶段感更分开"都不是理由；**barrier 延迟是真实的、可测的、浪费的时间** 。分开 ≠ 同步。

## 14\. 让 Claude 自己画图--自路由

![](https://r2.jeanjan.kdns.fr/pictures/img-4c57019719.jpeg)

最后一招：对没法预先规划的任务，别再手画图。**用` dynamic workflows`，你描述目标，Claude 自己写编排脚本**\--分解任务、选扇出、spawn 协调舰队、综合结果。你得到为这次 run 量身定制的图，而非你祈祷能用的固定图。

![](https://r2.jeanjan.kdns.fr/pictures/img-4c57019720.jpeg)
```

Graph Engineering with Claude:  https://x.com/svpino/status/2078516761318584774  
https://x.com/0xCodez/status/2079165300625330317
```

[动手设计AI Agents：（编排、记忆、插件、workflow、协作）](https://mp.weixin.qq.com/s?__biz=Mzk0MTYzMzMxMA==&mid=2247492838&idx=2&sn=1e25832e7300ef312721325d0def30b4&scene=21#wechat_redirect)[刚刚，Anthropic内部Loop Engineering方法论公开](https://mp.weixin.qq.com/s?__biz=Mzk0MTYzMzMxMA==&mid=2247509063&idx=1&sn=18c9c68d19d5f87274b409d6145f5950&scene=21#wechat_redirect)  
[一篇Loop+Harness的自进化Agent最新综述](https://mp.weixin.qq.com/s?__biz=Mzk0MTYzMzMxMA==&mid=2247508769&idx=1&sn=1c079514aee90450f55fccb41c7ec282&scene=21#wechat_redirect)[2026，做Agentic AI，绕不开这两篇开年综述](https://mp.weixin.qq.com/s?__biz=Mzk0MTYzMzMxMA==&mid=2247508495&idx=1&sn=309c84ca5c2822416fddc1a9dd4f6048&scene=21#wechat_redirect)已经读到这了，不妨点个👍、❤️、↗️三连，加个星标⭐，不迷路哦~

