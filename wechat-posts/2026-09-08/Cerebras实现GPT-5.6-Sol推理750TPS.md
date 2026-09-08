# Cerebras实现GPT-5.6 Sol推理750TPS

**作者**: AI圈的9527
**发布时间**: 2026-09-03 09:04
**原文链接**: https://mp.weixin.qq.com/s/9xQdNns168CTUKYsDsjXwQ

---

**要点速览** -**核心：没改模型只换硬件** ：GPT-5.6 Sol on Cerebras不是更小模型/蒸馏/低精度量化：同一架构、权重、精度、上下文配置和推理设置，完整保留browser-use/coding/ computer-use能力。唯一差异是硬件：跑在Cerebras WSE-3（世界最大AI芯片）上，替代GPU。  
  
-**为何快：绕过GPU内存墙** ：GPU权重在片外HBM、每步推理都要越过边界传进compute：内存墙。WSE-3用整片晶圆当芯片：44GB SRAM直接分布在90万核旁，聚合带宽21PB/s。Sol跨多个CS-3按层分片，activation在wafer间移动、权重留在原地。  
  
-**结果：agent工作流提速** ：GDP-Val质量匹配样本上5.6× 更快、Humanity's Last Exam上6.9× 更快；1小时任务不到9分钟完成。开放模型端点亦达数千tok/s（GPT OSS 120B 3000、Gemma4 31B 1850、GLM4.7 1000）。

OpenAI跑在Cerebras上的GPT-5.6 Sol的新Ultrafast模式，最高750输出token/秒。这个速度改变了我们使用AI的方式：现在能和agent保持在同一节奏、实时协作。

与标准OpenAI端点上GPT-5.6 Sol**完全相同的模型架构、权重、精度、上下文配置和推理设置** 。

## 为什么前沿模型推理通常很慢

![](https://r2.jeanjan.kdns.fr/pictures/img-970b7a5001.png)图1：GPU内存墙：权重跨HBM/芯片边界搬运。

在传统GPU上，计算核心和存放模型权重的高带宽内存（HBM）在分离的芯片上。推理里每次计算，权重都必须反复越过那道边界到达计算核心。随着模型变大，推理更多受「系统能多快搬运这些权重」约束，而非算术本身。

这就是GPU内存墙（GPU memory wall）。

加GPU能提升吞吐，但不会自动让单个响应变快。把模型拆到多块芯片意味着每一层都以同步步骤收尾，每加一块芯片都让那步更贵、同时缩小它本想加速的计算。存在交叉点：互连开销压过收益，更多硬件反而让模型更慢。说白了：计算机花太多时间搬数据了。

Cerebras的构建正是为了解决这个内存搬运瓶颈：造一个足够大的处理器，让模型的活跃权重直接待在使用它们的计算核心旁。

## 如何加速：从整片硅晶圆开始

![](https://r2.jeanjan.kdns.fr/pictures/img-970b7a5002.png)图2：WSE-3：整片晶圆即芯片，44GB SRAM紧靠90万核。

传统芯片从硅晶圆上切割下来。Cerebras则直接把整片晶圆当作芯片。

![](https://r2.jeanjan.kdns.fr/pictures/img-970b7a5003.png)图3：Sol跨多个CS-3按层分区，activation在wafer间流动。

在传统GPU上，模型权重住在片外HBM、每个token都必须越过边界进入compute。WSE-3则把44GB SRAM分布在整片晶圆上、直接放在其900,000个核心旁。这套内存合起来提供21 PB/s的聚合带宽，让每个核心都能快速访问它需要的权重。

GPT-5.6 Sol对单块加速器太大，所以Cerebras在层边界把它分区到多个CS-3系统上。每片晶圆在本地SRAM保留它分到的层。对每个token，activation从一片晶圆移到下一片，直到最终阶段输出结果。

这用更简单的路径替代了传统GPU集群所需的细粒度分片和同步：权重贴近compute、只有activation在阶段间移动。然后管线重复：最高每秒750次。

## 每秒750 token对你意味着什么

![](https://r2.jeanjan.kdns.fr/pictures/img-970b7a5004.png)图4：每token延迟是每步都要付、且按步数放大的成本。

大多数人以为和agent协作就是给个输入、得到输出。但底层agent要好多步：读任务、推理结果、写代码、测试它的工作、决定下一步，在一个循环里工作直到准备好交出回合。

复杂任务可能涉及多个模型请求和工具调用，延迟会随工作流累积。

**这意味着每token延迟不是一次性代价，而是你在每一步都要付、并且乘以完成任务所需步数的成本：而那些步数累积得很快。**

那个乘数是可测的，而且比你想的大。在一份质量匹配的GDP-Val任务样本（含法律、金融、工程交付物）上，GPT-5.6 Sol Ultrafast比同一模型在标准端点**快5.6× 完成同样的任务** 。

在Humanity's Last Exam的匹配问题（推理主导工作流）上，Sol Ultrafast**快6.9× 完成成功工作** 。照这个速度，一个1小时的任务不到9分钟就完成。

## 对开发者

没有哪里比编码更能体现Cerebras的速度。开发者让agent连续工作几小时甚至几天很常见。无论跑循环还是长驻agent，Sol on Cerebras都是无与伦比的体验：前沿级智能以极速服务，让你比以往更快构建、测试、迭代想法。

## 对知识工作者

![](https://r2.jeanjan.kdns.fr/pictures/img-970b7a5005.png)图5：750 tok/s让知识工作者迭代更快。

知识工作有更多Human in the loop。但它仍是一个循环：工作流很大部分是阅读和决策、评估输出、创建交付物，而人一直在等待。每秒最多750 token让迭代显著更快，同样时间里产出更多，无论是起草邮件、处理税务还是剪视频。

## 电脑使用与自动化

agent最受欢迎的新用例之一，是在你许可下、在你专注更重要任务时，让模型在后台使用你的机器或浏览器。这赋予你创建强大自动化、把你能描述的任务直接委派给agent的能力，而不接管你的机器。

更快的推理对computer-use工作负载的好处：减少「观察界面 → 决定做什么 → 采取下一步行动」之间的延迟。

## 开放模型：公共端点数千tok/s

另外，Cerebras在其公共端点上以每秒数千token服务领先的开放模型：

![](https://r2.jeanjan.kdns.fr/pictures/img-970b7a5006.png)图6：Cerebras公共端点开放模型速度。

**OpenAI GPT OSS 120B在3,000 tok/s**

**Gemma 4 31B在1,850 tok/s**

**Z.ai GLM 4.7在1,000 tok/s**

Cerebras还支持Kimi K2.6、GLM 5.1、MiniMax M2.5、Qwen3 Coder 480B、Llama 4 Maverick、Mistral Large 3、DeepSeek V3.2，以及更多模型家族。

**结语** 同一模型架构/权重/精度/推理设置，唯一差异是硬件换成WSE-3（整片晶圆当芯片：44GB SRAM紧靠90万核、21PB/s带宽），绕过GPU片外HBM的内存墙。  
  
GPU权重要不断跨HBM边界搬进compute（内存墙），加卡只会让同步步更贵；Cerebras让权重贴近compute、Sol按层分片到多CS-3、只有activation在wafer间流动。收益可测：GDP-Val 5.6×、Humanity's Last Exam 6.9× 更快、1小时任务<9 分钟。对关心推理速度/agent 延迟的人，这是「换硬件而非换模型」的教科书级案例。

【传送门】[TokenSpeed-Kernel：把推理内核做成一等公民](https://mp.weixin.qq.com/s?__biz=MzYzNzE2MDA2Mg==&mid=2247487547&idx=1&sn=19ffd4ffd445bbe02fa169e16bf8ee52&scene=21#wechat_redirect)  
[Kimi K3技术报告-后训练Infra: 三阶段RL,MoonEP3,五千万沙箱,KDA感知缓存](https://mp.weixin.qq.com/s?__biz=MzYzNzE2MDA2Mg==&mid=2247489421&idx=1&sn=07e99b72cde7c0e327f322c28791f437&scene=21#wechat_redirect)  
[腾讯混元hy3大模型技术之TurnOPD：回合感知的在线策略蒸馏，长程Agent提速2.29倍](https://mp.weixin.qq.com/s?__biz=MzYzNzE2MDA2Mg==&mid=2247487755&idx=1&sn=e25426ecc7d5a846c93c85f094c967f7&scene=21#wechat_redirect)  
[Agent卷向AI Infra: SGLang团队用硬核Agent优化框架和CUDA Kernal性能](https://mp.weixin.qq.com/s?__biz=MzYzNzE2MDA2Mg==&mid=2247486798&idx=1&sn=0558ff29d3c016785506b7be4768944d&scene=21#wechat_redirect)  
[小米MiMo罗福莉后训练新范式MOPD: 多教师同策略蒸馏，多领域无损集成](https://mp.weixin.qq.com/s?__biz=MzYzNzE2MDA2Mg==&mid=2247486540&idx=1&sn=ceb16c23d75f11438187308f2f5522d9&scene=21#wechat_redirect)  
[Kimi K3技术解析之LatentMoE: 隐藏维度压缩至潜空间，通信与带宽开销同比例骤降](https://mp.weixin.qq.com/s?__biz=MzYzNzE2MDA2Mg==&mid=2247488779&idx=1&sn=d45689287fdd0d7d6743f88d98ff67a6&scene=21#wechat_redirect)  
[KVCache缝合术: 突破前缀匹配天花板,首Token快14倍 多文档快2~4倍](https://mp.weixin.qq.com/s?__biz=MzYzNzE2MDA2Mg==&mid=2247487915&idx=1&sn=370550f0e241a2aa43c97274f15e91d1&scene=21#wechat_redirect)  
[Kimi K3技术解析之AttnRes: 打破Transformer沿用十年的残差各层等权的假设](https://mp.weixin.qq.com/s?__biz=MzYzNzE2MDA2Mg==&mid=2247488811&idx=1&sn=7e6c7c794696fc1d4f6bfbb393e8ccb3&scene=21#wechat_redirect)  
[小米MiMo罗福莉:8卡GPU让1T参数模型跑出1000 TPS , FP4+DFlash+TileRT全解读](https://mp.weixin.qq.com/s?__biz=MzYzNzE2MDA2Mg==&mid=2247487235&idx=1&sn=9a0097b65720544b4c4ecfab6062d5af&scene=21#wechat_redirect)  
[RL的下一个大突破：不是优化可验证问题而是把'不可验证'领域变得'可验证'](https://mp.weixin.qq.com/s?__biz=MzYzNzE2MDA2Mg==&mid=2247487185&idx=1&sn=7205c7cb651f80174475060314228a03&scene=21#wechat_redirect)  
[把KVCache变成可训练记忆：Context Tuning让LLM免权重微调](https://mp.weixin.qq.com/s?__biz=MzYzNzE2MDA2Mg==&mid=2247487559&idx=1&sn=4e64c85d03dc2916893042526030fa6b&scene=21#wechat_redirect)  
[阿里Sparse Attention on CXL替代RDMA做KV Cache解耦 推理2.1×吞吐, 9.7×TTFT](https://mp.weixin.qq.com/s?__biz=MzYzNzE2MDA2Mg==&mid=2247486743&idx=1&sn=b9c987e6c6d855aa566c87c9dbf73df3&scene=21#wechat_redirect)  
[【Agent for AI Infra三】摩尔线程MusaCoder国产算子生成超过Opus4.7：数据合成-SFT-RL全栈拆解](https://mp.weixin.qq.com/s?__biz=MzYzNzE2MDA2Mg==&mid=2247488104&idx=1&sn=b7b929ccaa46755264489df99dadd09b&scene=21#wechat_redirect)  
[Kimi K3技术详解之KDA: 线性注意力如何精准编辑被压缩的记忆](https://mp.weixin.qq.com/s?__biz=MzYzNzE2MDA2Mg==&mid=2247488976&idx=1&sn=d2e3d69facf90119a08c32a6d603da34&scene=21#wechat_redirect)  
[MLP就是Hebbian记忆: 无需训练，往Transformer块注入事实知识的构造方法](https://mp.weixin.qq.com/s?__biz=MzYzNzE2MDA2Mg==&mid=2247489179&idx=2&sn=556dffb777c4c9e01ad7cb42f00ddb03&scene=21#wechat_redirect)  
[智谱GLM 5.2 RL: 单Rollout异步优化SAO稳定训练1000步全面超越GRPO](https://mp.weixin.qq.com/s?__biz=MzYzNzE2MDA2Mg==&mid=2247487770&idx=1&sn=1a9787dd7d0535f977601b4cab489da9&scene=21#wechat_redirect)  

参考：https://x.com/MilksandMatcha/status/2092664576404070562

