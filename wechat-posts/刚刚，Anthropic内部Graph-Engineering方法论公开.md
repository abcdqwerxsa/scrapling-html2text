# 刚刚，Anthropic内部Graph Engineering方法论公开

**作者**: PaperAgent
**发布时间**: 2026-07-28 11:17
**原文链接**: https://mp.weixin.qq.com/s/_5j9goR1qY5RRlCKzP-xMw

---

**大家好，我是PaperAgent，不是Agent！**

**Anthropic** 工程师刚刚发布了一个关于Agentic系统**图工程** （**Graph Engineering** ）的2小时研讨会：我们80%的工程师都在使用自改进循环Loops。现在，每个人都在构建智能体图Agentic Graphs。[Harness+Model双引擎驱动的长程Agents最新综述](https://mp.weixin.qq.com/s?__biz=Mzk0MTYzMzMxMA==&mid=2247509381&idx=1&sn=60056d3e9a0745dfe19966532434b2b9&scene=21#wechat_redirect)

![https://x.com/0xCodez/status/2081429287945506950](https://r2.jeanjan.kdns.fr/pictures/img-261be5f201.jpeg)https://x.com/0xCodez/status/2081429287945506950

也发布了一份 12 页的 PDF，主题是面向多智能体系统的**图工程** （**Graph Engineering** ）。范式转变：你的智能体记忆会随着上下文窗口的耗尽而消亡。知识图谱能让它永久留存。

![https://x.com/0xCodez/status/2080250266851463209](https://r2.jeanjan.kdns.fr/pictures/img-261be5f202.jpeg)https://x.com/0xCodez/status/2080250266851463209

**Knowledge Graph Engineering** for Multi-Agentic Systems: The **Anthropic** Playbook

![来自 Anthropic 的公开资料](https://r2.jeanjan.kdns.fr/pictures/img-261be5f203.jpeg)来自 Anthropic 的公开资料

## 一、为什么上下文窗口不够用

文章举了个很具体的例子：一个竞品情报系统，orchestrator 下面挂 5 个 worker（定价、产品、财务、营销、战略综合）。战略综合 Agent 需要把三条事实链起来——“降价 15% 的竞对，和专利申请暗示新产品线的是同一家，和季报里研发翻倍的也是同一家”。**没有任何一个 worker 见过全部三条事实。**

![https://x.com/beamnxw/status/2081044232479928709](https://r2.jeanjan.kdns.fr/pictures/img-261be5f204.jpeg) https://x.com/beamnxw/status/2081044232479928709

如果 worker 之间只靠 orchestrator 的上下文窗口通信，窗口随 worker 数量线性膨胀，迟早爆掉。但如果每个 worker 把发现写成实体和关系存进共享知识图谱，综合 Agent 直接在图上遍历就能发现关联——中间上下文完全不需要。

![核心要点总结卡](https://r2.jeanjan.kdns.fr/pictures/img-261be5f205.jpeg)核心要点总结卡

这其实就是最近圈内热议的 “Graph Engineering” 话题的底层逻辑：工程重心一直在往模型外面漂——Prompt → Context → Harness → Loop → Graph，一层包一层。

![工程栈层层嵌套：Model 被 Prompt、Context、Harness、Loop、Graph 层层包裹](https://r2.jeanjan.kdns.fr/pictures/img-261be5f206.jpeg)工程栈层层嵌套：Model 被 Prompt、Context、Harness、Loop、Graph 层层包裹

RAG 为什么不行？RAG 按语义相似度捞 chunk，能答单跳问题；但多跳问题的答案散落在**彼此毫无词汇和语义相似度** 的段落里。知识图谱里，连接两个不相关文档的那个实体是一个显式节点，两边各有一条边——图遍历不关心表面形式像不像。论文的态度很明确：两者互补，RAG 管直接检索，图谱管结构推理。

## 二、四个阶段，全是 Claude API 调用

传统知识图谱要训 NER 模型、训关系分类器、手写实体消解规则——每个阶段都要标注数据，换个领域就崩。这篇笔记的主张是：**Claude 把整条管线塌缩成一串结构化输出调用，“训练数据”就是一个 Pydantic schema。**

![Fig.1 知识图谱管线](https://r2.jeanjan.kdns.fr/pictures/img-261be5f207.jpeg) Fig.1 知识图谱管线

领域适配成本从”几周标注+训练”降到”几小时调 prompt”。抽取用 Haiku（量大、schema 约束、速度成本优先），消解/摘要/查询用 Sonnet（要权衡证据、跨文档综合、多跳推理，质量优先）。

## 三、抽取：schema 就是契约

抽取阶段的精髓是 client.messages.parse() 加 output_format=ExtractedGraph——API 要么返回通过校验的强类型对象，要么直接报错。**没有正则、没有 JSON 解析错误、没有防御性检查** 。管线处理 10 篇文档和处理 1 万篇文档的差别，几乎全在阶段间接口的鲁棒性上。

抽取 prompt 的四条规则各治一种病：

  1. **“只抽取对本文档重要的实体”** —— 控召回、压噪声（precision 导向）；
  2. **“给每个实体写一句基于本文的描述”** —— 这是给下游消解准备的消歧信号，“Armstrong——第一个登月的人”和”Armstrong——爵士小号手”同名但绝不能合并；
  3. **“谓语用短动词短语”** （commanded、launched from）——“was involved with” 这种模糊谓语没法推理；
  4. **“每条关系必须连接两个已抽取实体”** —— 防止悬空边。

## 四、实体消解：字符串相似度做不到的事

原始抽取里同一个实体有多种表面形式：“NASA” vs “National Aeronautics and Space Administration”、“Neil Armstrong” vs “Neil Alden Armstrong”。最狠的是 **“Edwin Aldrin” vs “Buzz Aldrin”——零字符重叠，但是同一个人** 。编辑距离、Jaccard 全部失效。

解法：按类型分组后让 Sonnet 聚类，**把抽取阶段写的一句描述作为消歧上下文** 。

![Fig.2 实体消解](https://r2.jeanjan.kdns.fr/pictures/img-261be5f208.jpeg)Fig.2 实体消解

结果：24 个表面形式压缩成 22 个规范实体。两个要盯的失败模式：

  * **漏配** ：某个名字没进任何 cluster，就从图里悄悄消失了——生产环境要给未匹配名字兜底成单元素 cluster；
  * **过合并** ：“Gemini 12” 被并进 “Project Gemini”——丢节点是病，丢精度也是病。

论文反复强调：**消解的消歧能力全部来自抽取时写的那句描述** 。描述不是元数据，是消解的一等输入。省了描述，消解就退化回表面形式匹配——正好掉进这个方法本来想避开的坑。

## 五、组装与摘要：22 个节点，34 条边，1 个连通分量

别名映射清洗后，所有关系端点改写成规范名，装进 NetworkX MultiDiGraph（用 Multi 是因为两个实体间可以有多种谓语；用 Di 是因为方向重要——“Armstrong commanded Apollo 11” 和反过来不是同一条边）。每条边都带谓语和来源文档（provenance）。

Apollo 图的体检指标：**22 节点、34 边、边/节点比 1.55（健康区间）、单连通分量** ——单连通本身就是消解成功的证据，出现碎片孤岛说明该合并没合并。Hub 节点是 Apollo program 和 Apollo 11（度数均为 9）。

摘要阶段只给高度数节点做（度 ≥ 3），把所有提及 + 图邻域喂给 Sonnet 合成 2–3 段画像 + 3–5 条可追溯关键事实 + 时间范围。Apollo program 节点的画像综合了全部 6 篇文档，时间范围 1960–1973——**没有任何单一文档包含全部这些信息** 。这就是”把标签的图变成知识的图”的一步。

## 六、多跳查询：每个结论都引用一条具体的边

![Fig.3 图接地查询](https://r2.jeanjan.kdns.fr/pictures/img-261be5f209.jpeg)Fig.3 图接地查询

查询机制很朴素：取种子实体的 k 跳邻域，序列化成 (source) --[predicate]--> (target) 三元组，丢给 Claude 推理。k=2 是大多数多跳问题的甜点；k≥3 子图膨胀可能撑爆上下文。

**接地 vs 非接地的对比** 很说明问题。不问图谱，Claude 靠预训练知识能给出关于 Apollo 11 宇航员的漂亮答案——出生地、大学、军事基地，头头是道。问图谱，答案被约束在抽取出的边上：“图中唯一支持的人-地关系是 Neil Armstrong → walked on → the Moon”。后者没那么炫，但**可溯源、限于语料实际说了什么、且明确标注图谱里没有什么** 。在 Claude 没有先验知识的私有语料上，只有第二种答案能用。

## 七、图谱在五种 Agent 模式里的卡位

这是全文对多智能体系统最有价值的部分。Anthropic 文档化的五种模式，每一种都有图谱的集成点：

| 模式                   | 图谱角色      | 怎么帮                                |
|----------------------|-----------|------------------------------------|
| Augmented LLM        | 检索源       | 多跳问题用图遍历替代向量检索，LLM 把图当工具查          |
| Prompt chaining      | 门控信号      | 链式步骤之间查图，检查新实体是否与已有节点冲突            |
| Routing              | 分类器输入     | 用图里的实体类型和度数路由到对应专家，省一次 LLM 调用      |
| Orchestrator–workers | **共享内存**  |  worker 直接读写图，orchestrator 的窗口保持干净 |
| Evaluator–optimizer  | **事实接地层** |  评估者对照带 provenance 的图边核查声明         |

### 7.1 共享内存：orchestrator 的窗口不再膨胀

![Fig.4 图谱作为共享内存](https://r2.jeanjan.kdns.fr/pictures/img-261be5f210.jpeg)Fig.4 图谱作为共享内存

多个 Loop 之间的协调问题，交给图来解决：

![多智能体图架构](https://r2.jeanjan.kdns.fr/pictures/img-261be5f211.jpeg)多智能体图架构

不过共享状态有自己的病：**Node 2 的一次潦草写入，会变成 Node 5 的自信输入** 。论文给的解法和 X 文章如出一辙——typed schema、明确的写入权限、checkpoint：

![共享状态污染](https://r2.jeanjan.kdns.fr/pictures/img-261be5f212.jpeg)共享状态污染

### 7.2 接地层：评估者从”读者”变”事实核查员”

没有图谱的评估者只能判断”这看起来对吗”；有图谱的评估者能查”这条三元组在不在图里”。论文的例子：生成器声称 “Armstrong commanded Gemini 12”——听着很合理（Armstrong 确实是宇航员，Gemini 12 确实是真任务）。评估者查图：没有这条边；反而找到 (Buzz Aldrin) --[flew on]--> (Gemini 12) 和 (Neil Alden Armstrong) --[commanded]--> (Apollo 11)。反馈精确到边：“Armstrong 没有指挥 Gemini 12；Aldrin 乘坐了 Gemini 12；Armstrong 指挥的是 Apollo 11”。

![评估者否决权](https://r2.jeanjan.kdns.fr/pictures/img-261be5f213.jpeg)评估者否决权

还有一个关键设计：**图中查不到的声明不静默接受也不静默拒绝，而是升级给人** 。这是 fact-checking，不是 estimation。

### 7.3 持久世界模型：Agent 会忘，图不会

过夜运行的自改进 loop 需要能扛住上下文刷新的记忆。新文档来了：抽取 → 对着**已有规范集** 消解（而不是互相对）→ 只加新边；实体只在来源文档集实质变化时才重新摘要。

![loop 即单节点图](https://r2.jeanjan.kdns.fr/pictures/img-261be5f214.jpeg)loop 即单节点图

论文的原话很到位：“The agent forgets, the graph does not.”（Agent 会忘，图不会。）

## 八、评估：Precision 1.00 的代价

**Table III：对照 Gold Set 的抽取质量**

| 文档             | Raw F1 | Precision | Recall | Resolved R |
|----------------|--------|-----------|--------|------------|
| Apollo 11      | 0.71   | 1.00      | 0.55   | 0.55       |
| Neil Armstrong | 0.55   | 1.00      | 0.38   | 0.38       |

  * **Precision 满分** ：Haiku 抽出来的东西全对，非常保守。
  * **Recall 偏低** ：漏了两类——“Purdue University” 这种顺带提及（prompt 正确地过滤了），以及跨文档 scope 错配（Saturn V 在 Apollo 11 文档里提及不够”核心”，没被抽，但在它自己的文档里抽到了）。

## 九、规模化：双模型经济学

**Table IV：各阶段的模型选择**

| 阶段  | 模型     | 理由                    |
|-----|--------|-----------------------|
| 抽取  | Haiku  | 大批量、schema 约束，速度和成本主导 |
| 消解  | Sonnet | 权衡冲突证据，推理质量主导         |
| 摘要  | Sonnet | 跨文档综合，细腻度重要           |
| 查询  | Sonnet | 序列化三元组上的多跳推理          |

成本结构：抽取随语料线性增长（1 万篇 × 2000 token，用 Haiku + prompt caching + Batch API 只要个位数美元）；消解按类型批量（blocking 先用确定性信号分组 50–100 个候选，Claude 只在块内仲裁）；摘要只给高度数节点做，次线性；查询按子图大小计费。**大头成本在抽取用 Haiku、在查询用 Sonnet——这就是双模型策略的意义。**

存储上，NetworkX 撑到几十万边没问题；再大就换 Neo4j/Neptune，或者干脆三张 Postgres 表（entities / relations / aliases）+ 递归 CTE。管线代码一行不用改，只换持久层。

## 十、什么时候别用知识图谱

**Table VI：场景 vs 正确工具（节选）**

| 场景                 | 正确工具            | 为什么                        |
|--------------------|-----------------|----------------------------|
| 单文档问答              | RAG 或直接上下文      | 答案就在一个 chunk 里             |
| 多文档、单跳             | RAG + reranking | 跨文档但不需要链式推理                |
| 多文档、多跳             | **知识图谱**        |  跨文档链接事实需要实体级连接            |
| 多智能体共享状态           | **知识图谱**        |  worker 需要上下文窗口之外的共享世界模型   |
| 评估者需要 ground truth | **知识图谱**        |  事实核查需要带 provenance 的结构化事实 |
| 过夜 loop、持久记忆       | **知识图谱**        |  记忆必须跨会话存活                 |
| 简单分类/路由            | 单 Agent         | 不需要跨文档推理                   |

![何时用图决策表](https://r2.jeanjan.kdns.fr/pictures/img-261be5f215.jpeg)何时用图决策表

经验法则：**当你的 Agent 需要跨源链接事实、共享结构化状态、或把判断建立在可追溯证据上时，图谱是对的基础设施；如果只是检索段落或分类输入，更简单的工具就够了。**

[ 动手设计AI Agents：（编排、记忆、插件、workflow、协作）](https://mp.weixin.qq.com/s?__biz=Mzk0MTYzMzMxMA==&mid=2247492838&idx=2&sn=1e25832e7300ef312721325d0def30b4&scene=21#wechat_redirect)[刚刚，Anthropic内部Loop Engineering方法论公开](https://mp.weixin.qq.com/s?__biz=Mzk0MTYzMzMxMA==&mid=2247509063&idx=1&sn=18c9c68d19d5f87274b409d6145f5950&scene=21#wechat_redirect)  
[一篇Loop+Harness的自进化Agent最新综述](https://mp.weixin.qq.com/s?__biz=Mzk0MTYzMzMxMA==&mid=2247508769&idx=1&sn=1c079514aee90450f55fccb41c7ec282&scene=21#wechat_redirect)[2026，做Agentic AI，绕不开这两篇开年综述](https://mp.weixin.qq.com/s?__biz=Mzk0MTYzMzMxMA==&mid=2247508495&idx=1&sn=309c84ca5c2822416fddc1a9dd4f6048&scene=21#wechat_redirect)已经读到这了，不妨点个👍、❤️、↗️三连，加个星标⭐，不迷路哦~

