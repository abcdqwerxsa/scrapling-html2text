# LiteLLM 把网关用 Rust 重写了，150 倍延迟降低的背后，我发现了一种趋势，AI 基础设施正在集体 Rust 化

**作者**: 老码小张
**发布时间**: 2026-06-24 09:33
**原文链接**: https://mp.weixin.qq.com/s/Ank0vMgpd6UDhM5NaN9PIQ

---

朋友们，LiteLLM 上周发了一篇博客，标题很直接：把 Python 网关迁到 Rust，做最快最轻的 AI Gateway。

过去一年，我数了数，从终端 Agent 到记忆引擎到知识图谱到现在的 AI 网关，AI 基础设施的关键组件，一个接一个地在往 Rust 迁。LiteLLM 不是第一个，也不会是最后一个。这个我感受很深，我使用 Rust 写过比较多的应用，感受是 Rust 稍微难写一点，但是写完之后，使用起来的爽感是无与伦比的，[就像我写的 small Rust Hermes](https://mp.weixin.qq.com/s?__biz=MzkxNzY0OTA4Mg==&mid=2247493710&idx=1&sn=80eb54ed4188830e05455ca4b5056af5&scene=21#wechat_redirect) ，这个是群友最喜欢的，喜欢它的性能，喜欢他的轻巧够用。

![图片](https://r2.jeanjan.kdns.fr/pictures/img-a1dce7d801.png)

先说数字，因为数字是最诚实的。

LiteLLM 做了什么？它是一个 AI Gateway——你有 100 多个 LLM 提供商（OpenAI、Claude、Gemini、DeepSeek、Bedrock、Vertex……），它帮你统一成一个接口。你的代码只跟 LiteLLM 说话，LiteLLM 帮你路由、负载均衡、格式转换、限流、降级。

之前它是 Python 写的，FastAPI。现在它正在把核心路径用 Rust 重写。

![](https://r2.jeanjan.kdns.fr/pictures/img-a1dce7d802.png)

迁移前后的对比：

| 指标         | Python 版  | Rust 版      | 差距        |
|------------|-----------|-------------|-----------|
| 每请求延迟      | ~7.5ms    | ~0.05ms     | **150 倍** |
| 吞吐量（50 并发） | 453 req/s | 6,782 req/s | **15 倍**  |
| 峰值内存       | 358.9MB   | 31.7MB      | **11 倍**  |

0.05ms。这个数字意味着什么？意味着网关本身的开销基本消失了。你的请求从进来再到转发给上游 LLM，中间只花了 50 微秒。瓶颈完全在 LLM 那边，不在你这里。

31.7MB 内存。一个吃 32MB 的进程，你**根本注意不到它在跑** 。之前 Python 版吃 359MB，部署到生产环境，每个 pod 都吃这么多，跨区域、跨副本一乘，账单就不好看了。

### 那么，为什么是"又一个"？

如果你只看 LiteLLM 这一篇博客，你会觉得"哦，一家公司做了性能优化"。

但如果你把时间线拉长，你会发现一件事：**这不是个案，这是一个趋势。**

我随手列几个：

**终端 Agent 层。** Claude Code 的 harness 生态里，CodeWhale 是 Rust 写的，oh-my-pi 是 Rust 写的。我做的 small Rust Hermes 也是 Rust。终端 Agent 这个赛道，Rust 已经是默认选项了。

**记忆引擎层。** AgentMemory 的核心检索路径用 Rust 优化过。我自己做的 MemPalace 从 Python 重写为 Rust 之后，FTS5 全文检索的响应时间从百毫秒级掉到了个位数毫秒。

**AI Gateway 层。** 现在 LiteLLM 也来了。

你看，这些项目有一个共同点：**它们都是 AI 工具链里的"管道"——不做模型推理，但负责把数据搬到正确的地方。** 路由、转发、检索、格式化、持久化。这些活有一个共同特征：高频、低延迟要求、内存敏感。

而 Python 在这些场景下的 性能 问题，已经不是秘密了。

### Python 的问题不是"慢"，是"不可预测"

先说清楚，我不是 Python 黑。Python 在 AI 领域的地位不可动摇——模型训练、数据科学、快速原型，Python 仍然是最好的选择。

但在 AI 基础设施的**运行时** 层面，Python 有几个结构性的问题：

**第一，GIL。** 全局解释器锁。Python 的多线程在高并发 I/O 场景下基本是摆设。AI Gateway 是什么？就是高并发 I/O——同时几百个请求进来，每个都要转发给不同的 LLM 提供商。GIL 让 Python 在这个场景下先天吃亏。LiteLLM 的博客里专门提到了这一点。

**第二，内存不可控。** Python 的内存管理是引用计数 + 垃圾回收。在长时间运行的服务里，内存会慢慢涨，涨到你不知道哪里在吃，然后 OOM kill。LiteLLM 的博客原话："Python proxy's memory consumption multiplies across every pod, region, and retry, causing OOM kills at critical moments." 翻译一下就是：最关键的时候它崩了。

**第三，部署体积。** 一个 Python 服务要跑起来，你得装解释器、装依赖、装虚拟环境。一个 Rust binary 扔上去就能跑。31MB vs 359MB，不只是运行时的差距，是部署复杂度的差距。

这些问题在原型阶段感觉不到。但当你把 AI 工具链部署到生产环境，流量上来、并发上来、跑的时间长了——它们全会冒出来。

### Rust 不是银弹，但它解决了"管道"层的核心矛盾

这里我要说一句可能会被骂的话：**AI 基础设施的运行时层，Rust 正在成为事实标准。**

不是因为 Rust 比 Python "好"。是因为 AI 管道层的核心矛盾——高并发、低延迟、内存可控、长期稳定运行——恰好是 Rust 的设计目标。

Rust 的所有权系统在编译期就干掉了数据竞争和内存泄漏。你写完了，编译通过了，这些问题就不存在了。不是"测试覆盖了"，是"编译器保证了"。

Rust 没有 GC。内存分配和释放是确定性的。一个 Rust 服务跑了三天和跑了三个月，内存占用基本一样。这对生产环境来说太重要了。

Rust 编译出来的就是一个二进制文件。没有 runtime 依赖，没有 virtualenv，没有 pip install。扔到 Docker 里、扔到 Kubernetes 里、扔到树莓派里，都能跑。

但这些好处，LiteLLM 的博客里其实没怎么吹。它更强调的是另一件事：**迁移策略。**

###  四阶段迁移：最值得学的不是技术，是节奏

![](https://r2.jeanjan.kdns.fr/pictures/img-a1dce7d803.png)

LiteLLM 的迁移方案，我觉得比性能数字更值得看。

它不是一夜之间把 Python 全扔了。它分了四个阶段：
```

Stage 0：纯 Python（FastAPI）—— 当前状态  
  
Stage 1：Rust 核心 + Python I/O  
         Rust 负责数据转换（请求/响应/流式块/token 计数）  
         Python 仍然负责网络、数据库、认证  
         通过 PyO3 桥接  
         Rust 组件"不打开 socket、不读密钥、不写数据库"  
  
Stage 2：FastAPI 变成薄壳  
         认证、限流、回调还在 Python  
         整个转发路径变成一次 Rust 调用  
  
Stage 3：纯 Rust 服务器（axum/hyper）  
         Python 彻底退出热路径  
         用户的 Python 插件通过可选 sidecar 继续运行
```

注意这个设计的精妙之处：**每个阶段都可以独立上线。** 不是"要么全迁完要么不上"，要做的是每完成一个阶段就能部署、就能拿到那个阶段的性能收益。

而且路由是按风险排序迁移的：

  1. 1\. **先迁 OCR** （Mistral OCR）—— 最简单，没有流式、schema 小、参数少
  2. 2\. **再迁 /v1/messages** —— 加了流式复杂度：SSE 解析、chunk 发射、用量统计
  3. 3\. **最后迁 /chat/completions** —— 最大表面积：工具调用、函数调用、多模态
  4. 4\. **最后处理大提供商** —— Azure、Bedrock、Vertex，按流量来

每一条路由迁移之前要过"一致性检查"——Rust 版本的输出必须和 Python 版本完全一致才能激活。出了问题可以按提供商回退到 Python 路径。

**这不是一个技术决策，我理解这是一个工程决策。** 技术上用 Rust 重写不难，难的是怎么在生产环境里一步步替换，不翻车。

所以，我们看看这个巨大的工程迁移的时间表：

  * • 2026 年 8 月 15 日：OCR 路由迁移完成
  * • 2026 年 9 月 1 日：/messages 和 /chat/completions 迁移完成
  * • 2026 年 9 月 15 日：Router（负载均衡、降级、重试、冷却）
  * • 2026 年 12 月 1 日：全量迁移完成

半年时间，分四步走。急什么？不翻车比什么都重要。

### 这一点，我自己做 Hermes 时也有同样的感受

说实话，看这篇博客的时候我很有共鸣。

[我的Small Rust Hermes 看名字就知道，它是写的](https://mp.weixin.qq.com/s?__biz=MzkxNzY0OTA4Mg==&mid=2247493552&idx=1&sn=0f3782ce0a5727f6c52bbedbd08fd3fa&scene=21#wechat_redirect)。当初选 Rust 不是追潮流，是被 TS/JS/Python 版的 Hermes 逼的——跑几个小时内存就开始涨，并发一上来就卡，部署到服务器上还得装一堆 node_modules 依赖。重写成 Rust 之后，内存恒定在 12MB 左右，并发随便来，binary 扔上去就能跑。安装包也才 22M ，群友反馈就是很流畅，整个机器就是安静得可怕。更加重要的，有群友使用 Claude fable5 进行安全审查，发现其安全级可以打败市面上绝大多数的 agent，这说明我们的内核已经足够稳固了。

但我当时也做了一个跟 LiteLLM 类似的决定：**不是一次性全重写，而是先把核心循环用 Rust 写，外围工具慢慢迁。** 先跑通 Agent 的"思考→工具调用→结果反馈"这个循环，再逐步把记忆、技能、MCP 协议这些模块补上。当然，我也是有取舍的，我认为 Hermes 有很多功能其实我们并不需要的。

这种"分阶段迁移"的思路，我觉得是任何一个把生产系统从 Python 迁到 Rust 的团队都会走的路。一步到位太危险了。你不可能停掉业务去重写，你只能在跑着的情况下换轮子。

### 我的保留意见

**第一，150 倍这个数字需要看测试条件。** LiteLLM 的 benchmark 用的是 mock upstream——也就是上游 LLM 是模拟的，只测网关本身的转发性能。在真实场景下，你的瓶颈在 LLM 那边（动辄几秒），网关从 7.5ms 降到 0.05ms 的体感差异没有 150 倍那么夸张。它解决的不是"用户感知到的速度"，而是"网关自身不成为瓶颈"和"内存不爆炸"。

**第二，Rust 的开发成本是真实的。** LiteLLM 的博客里没提这一点，但我自己做过 Rust 重写，我知道那个痛。Rust 的学习曲线、编译时间、类型系统的严格程度，都意味着开发速度会比 Python 慢。LiteLLM 能推进这个迁移，说明他们的团队已经有了足够的 Rust 能力（他们也在招 Rust 工程师）。不是每个团队都能做这件事。

**第三，"纯 Rust"不一定是最优解。** LiteLLM 的最终形态（Stage 3）里，用户的 Python 插件仍然通过 sidecar 运行。这其实暗示了一个事实：Python 在 AI 生态里的位置短时间内是不会被 Rust 取代的，它会被**推到它擅长的层** 。运行时归 Rust，用户自定义逻辑和快速原型归 Python。这个分工比"全 Rust"更健康。

### 写在最后

过去十年，AI 领域发生过两次基础设施迁移。

第一次是从 CPU 到 GPU。训练模型跑不动了，GPU 接管了计算层。

第二次是从单机到分布式。模型太大了，一台机器装不下，分布式训练和推理成了标配。

现在正在发生第三次：**AI 工具链的运行时，正在从 Python/TS 迁移到 Rust。**

不是 Python/TS 不行了。是 AI 的规模上来了之后，Python/TS 作为运行时的物理极限到了。就像 JavaScript 在浏览器端的物理极限到了之后，WebAssembly 出现了。不是因为 JS 不好，是因为场景变了。

LiteLLM 的 0.05ms 和 31.7MB 不是一个孤立的数据点。它是一个信号：**当 AI 从实验走向生产，它脚下的地板得换材料了。**

Python/TS 搭了脚手架，Rust 浇了地基。

项目信息：

  * • LiteLLM：https://github.com/BerriAI/litellm （AI Gateway，Python + Rust 混合）
  * • LiteLLM Rust 迁移博客：https://docs.litellm.ai/blog/litellm-rust-launch


