# 长程任务飙升98%，斯坦福Skill原生LLM来了

**作者**: PaperAgent
**发布时间**: 2026-08-11 11:48
**原文链接**: https://mp.weixin.qq.com/s/S0m5QMmV2eyk4FkJHfK-dw

---

大家好，我是PaperAgent，不是Agent！

面对**跨Skill长时程任务** （[写论文、做攻略、agentic coding](https://mp.weixin.qq.com/s?__biz=Mzk0MTYzMzMxMA==&mid=2247509767&idx=1&sn=e55713c99e65f89bbea4bb60dafa5499&scene=21#wechat_redirect)）：即多步骤任务，其中各步骤需要不同的推理Skill，并依赖于前序输出，**普林斯顿 &CMU&斯坦福&牛津**等提出**Skill-Native** 大模型。

![](https://r2.jeanjan.kdns.fr/pictures/img-4421ea1b01.jpeg)

  * 提出 **Skill Entropy（技能熵）** ，一个度量从技能 A 切到技能 B 有多难的标量；用它搭了 **Skill²-Bench** ，发现所有前沿模型都存在 **skill-switching gap** ：任务技能熵越高，准确率单调下降。

![Code已开源](https://r2.jeanjan.kdns.fr/pictures/img-4421ea1b02.jpeg)Code已开源

  * 更妙的是，把这个熵从评测尺子改造成训练信号，提出 **Skill-Entropy RL** ：让模型每步不仅要给答案，还要预测自己用了哪个技能，奖励里加入预测技能序列 vs 标准技能序列的对齐分。[科研Agent能写代码、跑实验，但这件事，替不了你](https://mp.weixin.qq.com/s?__biz=Mzk0MTYzMzMxMA==&mid=2247509767&idx=1&sn=e55713c99e65f89bbea4bb60dafa5499&scene=21#wechat_redirect)

![SFT Warm-up与Skill-Entropy RL](https://r2.jeanjan.kdns.fr/pictures/img-4421ea1b03.jpeg)SFT Warm-up与Skill-Entropy RL

  * Qwen3-4B-Instruct 从 34.4% 干到 **68.4** %，Qwen3-1.7B 从 14.6% 到 **40.1** %。

## 1\. 单技能 benchmark 测不出的失败模式

先看一个例子：规划一次旅行，第一步要算预算（数学），第二步用预算排日程（规划），第三步按日程从网页里抠信息（信息抽取）。这是一条推理链，但每一步调用的**技能** 完全不同，且后面的步骤依赖前面的输出。论文把这类问题定义为 **cross-skill long-horizon task（跨技能长程任务）** 。

问题在于：前沿模型在单技能 benchmark 上刷分刷得很漂亮，一旦把技能串进同一条链，就” visibly brittle（肉眼可见地脆）“。但此前的评测要么孤立测单技能，要么在 agentic 环境里跑多轮——**没有一个有原理性的方法去度量”技能切换本身有多难”** 。

![Figure 1：Skill Entropy 总览](https://r2.jeanjan.kdns.fr/pictures/img-4421ea1b04.jpeg)Figure 1：Skill Entropy 总览

上面是评测侧（558 技能 / 9 领域的 Skill²-Bench + 技能熵打分），下面是训练侧（从现有数据构造带技能标注的训练集 → skill-annotated rollout → 技能熵奖励）。注意右下角那个设计：模型输出里显式带了标签，预测的技能熵（0.7）和黄金技能熵（0.9）之间的差距**直接变成奖励信号** ——这是全文最核心的一手。

## 2\. Skill Entropy：给换技能有多难一个数

技能熵 **SkE(sₐ, s_b)** 是一个有方向的成对量：在固定参考模型下，先用技能 sₐ 答了一步、再切到 s_b 答题，相比两个技能各自孤立作答，准确率掉了多少。定义很干净：

SkE(sₐ, s_b) = ½(Accuracy(sₐ) + Accuracy(s_b)) + α / Accuracy(sₐ, s_b) + α

其中 Accuracy(sₐ, s_b) 是两步跨技能对的平均步级准确率，α=0.1 是 Laplace 平滑。**SkE > 1 表示切换变难，≤ 1 表示基本无损耗**。注意它有方向性：从数学切到创意写作，和从创意写作切回数学，难度不一样。任务级技能熵则是链上所有相邻技能对熵的均值，再按经验分布切成 low / medium / high 三档。

为什么要固定一个”参考模型”来算熵？因为这样 SkE 与待评测模型无关，成为一把**公共难度尺子** ——不同模型在同一套熵标定过的任务上比，才公平。

![Figure 2](https://r2.jeanjan.kdns.fr/pictures/img-4421ea1b05.jpeg)Figure 2

Math→Creative Writing（2.73）、Science→Context Retrieval（3.42）、Planning→Info Extraction（4.41）这些”跨得远”的格子熵值明显更高；而 Context Retrieval→Instruction Following（0.82）几乎是无缝切换。右图则把”领域本身难”和”切进/切出该领域难”解耦成两个轴——这对诊断模型瓶颈到底在哪很有用。

## 3\. Skill²-Bench：9 个领域，558 个技能

![Table 1：Skill²-Bench 的 9 个领域、种子数据集与技能数量](https://r2.jeanjan.kdns.fr/pictures/img-4421ea1b06.jpeg)Table 1：Skill²-Bench 的 9 个领域、种子数据集与技能数量

benchmark 覆盖 6 个可验证领域+ 3 个开放领域，任务构造分三步：

  * (1) 从种子数据集给每道题标 3–5 个细粒度技能，embedding 聚类成技能库；
  * (2) 用参考模型在单技能 vs 跨技能问题上算出成对技能熵；
  * (3) 按目标熵档位采样技能序列，让 LLM proposer 把对应种子题重写成一条连贯场景（比如”机器人进洞穴救研究员”：解方程→文档抽取→网格寻路→动作规划），再用 verifier 过滤。每条任务自带任务级技能熵分数，难度可控、可归因。

## 4\. 评测结果：技能熵越高，模型越崩

12 个模型（8 前沿 + 4 开源）的评测揭示了两个现象：

![Table 2：Skill²-Bench 评测结果——单技能 vs 跨技能 Domain Accuracy，以及按熵档位分的 Skill²-Bench Performance](https://r2.jeanjan.kdns.fr/pictures/img-4421ea1b07.jpeg)Table 2：Skill²-Bench 评测结果——单技能 vs 跨技能 Domain Accuracy，以及按熵档位分的 Skill²-Bench Performance

**现象一：跨技能设置一致性地掉分。** 把同一个技能放进跨技能长链里，所有前沿模型准确率都掉，幅度 −4% 到 −10%（GPT-5.4-mini 掉 10.0%，Gemini-3.1-flash 掉 9.1%）。连单技能模式近乎饱和的 Logic 技能，串进链里也照掉——说明这是单技能评测**结构性测不到** 的失败模式。

**现象二：准确率随技能熵单调下降。** low→medium→high 三档，几乎所有模型阶梯式走低（如 Gemini-3.1-pro：77.1→75.2→72.2）。这反过来验证了技能熵确实抓住了跨技能任务的难度本质。

失败模式分析更是直指要害：**模型在链的深处会”沿用”上一步的技能和答案形态** ——该切换时不切换。这也为后面的训练方法埋下了伏笔。

## 5\. Skill-Entropy RL：让模型显式报技能，熵差变奖励

训练侧的设计分两步：

**SFT 预热** ：先教会模型一种结构化输出格式——每个 step 用Domain, Skill...成对输出，即模型不仅要答题，还要**自报用了哪个技能** 。

**RL 阶段（GRPO）** ：奖励 = 答案奖励 + 技能熵奖励：

r = λ_ans · r_ans + λ_ent · r_ent，其中 r_ent = 1 − |ρ̂ − ρ*|

r_ans 是逐步准确率；r_ent 比较”预测技能序列的熵在训练分布中的分位 ρ̂“和”黄金序列的分位 ρ*“。预测技能先通过 embedding 相似度映射到技能库最近邻再算熵，所以**语义相近的技能替换也拿得到分** ——不是死板的精确匹配。默认 λ_ans=0.7、λ_ent=0.3，消融显示把熵项压到 0.1 直接掉 7.6 分（60.8 vs 68.4），这个奖励项是实打实在起作用的。

![Table 3：Skill-Entropy RL 与 SFT/GRPO/Skill-Distill/SkillRL/STAT 的对比](https://r2.jeanjan.kdns.fr/pictures/img-4421ea1b08.jpeg)Table 3：Skill-Entropy RL 与 SFT/GRPO/Skill-Distill/SkillRL/STAT 的对比

结果（Table 3）：Qwen3-4B-Instruct 上 **68.4%**，比 GRPO +9.6、比最强 skill-aware 基线 STAT +7.0；Qwen3-1.7B 上 **40.1%**，比 GRPO +7.9。9 个领域里 7 个拿到最优，** Creative Writing 提升最大**（68.8→85.6）——注意开放领域完全没参与 RL 训练，说明技能熵奖励学到的”切换能力”泛化出了训练分布。外部 benchmark（MuSR、GPQA-Diamond、MMLU、IFEval 等 5 个）上两个尺寸也都是最高均分。

![Figure 3：案例研究](https://r2.jeanjan.kdns.fr/pictures/img-4421ea1b09.jpeg)Figure 3：案例研究

Figure 3 的案例很直观：第一步算三角形画作面积（几何计算），第二步要头脑风暴展览主题（创意技能）。Base 模型第二步还在用”Geometric Analysis”、输出一个短答案（错）；训练后的模型干净地切到 Theme Creation、输出长文本（对）。

## 6\. 杀手锏：即插即用到现成训练数据

如果方法只能用在自己合成的数据上，价值就有限了。4.4 节证明**不用改数据管线** ：拿 OpenR1-Math（纯数学、没有显式技能结构），用 Qwen3-8B 把每条 reasoning trace 切步骤、标技能、算任务级熵，中间步骤的结论当黄金答案，然后走同一套 SFT+RL。

![Figure 4](https://r2.jeanjan.kdns.fr/pictures/img-4421ea1b10.jpeg)Figure 4

Figure 4 里，vanilla GRPO 很快饱和，加了技能熵奖励的曲线**持续不饱和地往上走** 。下游 6 个数学 benchmark 全部最优，比 GRPO 平均 +1.9%、比 base +7.7%。这意味着技能熵是一个**可复用的训练信号** ：任何带 reasoning trace 的现有数据，标个技能就能用。
```

Toward Skill-Native LLMs: Skill Entropy for Benchmarking and Training Long-Horizon Reasoning  
https://github.com/Gen-Verse/Skill-Entropy-RL   
arXiv：2608.05139  

```

[动手设计AI Agents：（编排、记忆、插件、workflow、协作）](https://mp.weixin.qq.com/s?__biz=Mzk0MTYzMzMxMA==&mid=2247492838&idx=2&sn=1e25832e7300ef312721325d0def30b4&scene=21#wechat_redirect)[Loop工程已死，Graph工程永生](https://mp.weixin.qq.com/s?__biz=Mzk0MTYzMzMxMA==&mid=2247509270&idx=1&sn=53a5ffa2cd51583947e1cc379c8703d4&scene=21#wechat_redirect)  
[一篇Loop+Harness的自进化Agent最新综述](https://mp.weixin.qq.com/s?__biz=Mzk0MTYzMzMxMA==&mid=2247508769&idx=1&sn=1c079514aee90450f55fccb41c7ec282&scene=21#wechat_redirect)[2026，做Agentic AI，绕不开这两篇开年综述](https://mp.weixin.qq.com/s?__biz=Mzk0MTYzMzMxMA==&mid=2247508495&idx=1&sn=309c84ca5c2822416fddc1a9dd4f6048&scene=21#wechat_redirect)已经读到这了，不妨点个👍、❤️、↗️三连，加个星标⭐，不迷路哦~

