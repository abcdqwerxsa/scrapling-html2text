# /grill-me 迎来重大更新：Mattpocock Skills v1.1 详解与最佳配置

**作者**: 烨笙总Yes
**发布时间**: 2026-07-11 11:25
**原文链接**: https://mp.weixin.qq.com/s/x4Rgx2mL_DIzPtfbLrEM8A

---

**Mattpocock Skills** 在 GitHub 上有超过 16 万 star，是目前最火的 Claude Code Skills 合集。其中 `/grill-me` 尤其出名，它像一个不依不饶的面试官，追着你问，直到需求边界的每个分支都厘清，很多项目（比如我之前推荐的 `Trellis`）都基于它改造自己的需求对齐流程。

但对齐过程中有三个问题被社区反复提及：一堆问题一起问、自问自答、grill 结束后直接跳实现。

v1.1 把这三个问题修了，同时把整套 skills 的命名和流程重新理了一遍。

![](https://r2.jeanjan.kdns.fr/pictures/img-acf21bbb01.png)

## `/grilling`的三个关键修复

v1.1 对 `/grilling` 技能（`/grill-me` 和 `/grill-with-docs` 实际上都依赖它）做了三个修复。新旧两个版本的对比如下图：

![](https://r2.jeanjan.kdns.fr/pictures/img-acf21bbb02.png)

### 修复一：更清晰的提问指导

原来的指令只说「asking multiple questions at once is bewildering」。模型偶尔会忽略这条指令，一次性抛出一堆问题。

v1.1 则加了更明确的解释：**问题堆在一起，用户记不住，对齐效率反而下降** 。这比简单地从反向说「不要」效果更好。

### 修复二：确认门控

以前 grill 结束后，agent 有时会直接跳到实现阶段。你还没确认，它已经开始写代码了。

v1.1 加了一道门：`Do not enact the plan until I confirm we've reached a shared understanding.`

**grill 结束后，agent 会暂停，等你确认对齐到位，再往下走。**

###  修复三：防止自问自答

有些情况下，agent 会自己探索代码库，自己回答问题。你没参与，它已经把方案想好了。

v1.1 加了一个区分：

| 类型        | 定义         | 例子        |
|-----------|------------|-----------|
| Facts     | 探索代码库发现的东西 | 代码模式、现有实现 |
| Decisions | 需要用户决定的东西  | 架构选择、功能范围 |

**只有 Decisions 才需要追问。Facts 自己找就行。**

##  修复之后实战效果如何

我针对自己的项目 PromptMaster 测了一下。

题目就是"**我想为 PromptMaster 新增一个「提示词版本历史」功能，允许用户回滚到提示词的历史版本，请 grill 我这个方案** "，主要是来测问题1有没有被解决，因为它最直观。

强模型方面，我先后试了 GPT-5.6 Terra、Gemini 3.5 flash、GLM 5.2。说实话，我没感受到什么差异。这三个模型本来就不太会一次甩几十个问题出来，grill 结束后也基本会等你说"OK"再动手。**三个修复对它们来说更像是"把已经在做的事写进指令"，行为没变。**

弱模型就不一样了。我拿 step 3.7 flash 做对照，这个模型平时~~笨得流口水~~ ，我根本不敢用它做需求对齐。用修之前的老版本，它一上来就甩二三十个问题，你还没看清楚第一个，屏幕已经刷过去了：

![](https://r2.jeanjan.kdns.fr/pictures/img-acf21bbb03.png)

用修之后的新版本，它还真能一次只问一个，问完等你说完再问下一个。grill 结束后它也会停住，不会自己跑去写代码：

![](https://r2.jeanjan.kdns.fr/pictures/img-acf21bbb04.png)

但看到最后一行……好吧它还是没理解"推荐"是啥意思，真是流口水……

**所以这三个修复的真实定位是：给弱模型加护栏。强模型不需要，弱模型离了不行。**

##  改名让 skills 定位清晰，全流程开发更好用了

v1.1 另一件大事是改了两处命名。这看起来是小调整，但改完之后，每个技能在整个体系里的位置才真正清晰，五步闭环才成立。

### 改名一：/to-prd → /to-spec

原来的 `/to-prd` 名字有问题。PRD 是产品需求文档，描述的是产品本身。但这个技能实际创建的是 specification，可能包含技术细节、非技术内容，范围更广。

Matt 承认这个名字一直取错了。v1.1 改成 `/to-spec`，**spec 成为整个 skills 体系的统一术语** 。

### 改名二：/to-plan + /to-issues → /to-tickets

原来的 `/to-plan` 和 `/to-issues` 合并成一个技能：`/to-tickets`。

原因：`issues` 这个词偏向 GitHub 和 Linear 的术语，但概念是更通用的 tickets：**spec 下面的一层层任务切片，每个切片声明自己的阻塞依赖** 。

一个技能搞定：把计划、spec 或对话分解成 tracer-bullet tickets。

### 改名之后，五步闭环才成立

两处改名解决了定位模糊的问题，但更重要的结果是一整条流程终于能走通了。

很多人问 Matt：skills 到底该按什么顺序用？v1.1 第一次给出了完整答案。

老版本也有流程，只是碎片化、后半段模糊：

```

/grill-me → /to-prd → /to-plan 或 /to-issues → /tdd 或直接实现 → 代码审查（非标准化）
```

前半段还算清晰，但拆完 issues 之后事情就模糊了。`/tdd` 只管测试循环，没有技能告诉你「拿到一个 issue 怎么系统地实现完」。代码审查有做，但没有专门的技能标准化。`/to-plan` 和 `/to-issues` 功能重叠，用户得自己选。大型项目易超出单次会话的上下文，只能靠 `/grill-with-docs` 硬扛。**旧版核心问题是「规划有流程、落地靠自觉」。**

v1.1 补上了后半段，五步闭环：

![](https://r2.jeanjan.kdns.fr/pictures/img-acf21bbb05.jpeg)

  1. **grilling ：用 `/grill-me`、`/grill-with-docs` 或 `/wayfinder` 把需求聊透**
  2. **spec ：用 `/to-spec` 生成规格文档**
  3. **tickets ：用 `/to-tickets` 分解成任务切片**
  4. **implement ：用 `/implement` 逐个实现**
  5. **code review ：`/implement` 结束后自动调用 `/code-review` 审查**

**这条流程解决了「我先该用哪个技能」的问题，更关键的是，它把后半段从「靠自觉」变成了「有技能兜底」。**

##  grilling 环节怎么选

五步流程的第一步是 grilling，但 v1.1 给了三个入口：`/grill-me`、`/grill-with-docs`、`/wayfinder`。选哪个？

**已有代码库** ：用 `/grill-with-docs`。大多数编码场景的首选。它读取项目里的 CONTEXT.md、ADR 等文档，追问过程中自动更新 glossary 和决策记录，领域对齐比 `/grill-me` 更扎实。Matt 本人也转向优先推荐带 docs 的变体。

**项目很早期、没有代码库** ：用 `/grill-me`。最轻量的纯对话追问，适合非编码场景（纯产品讨论）或快速验证小想法。

**项目太大、太模糊，单次 session 跑不完** ：用 `/wayfinder`。它把大项目拆成 GitHub issues，每个 issue 是一个决策单元，用阻塞依赖组织顺序。你逐个关闭 issue，wayfinder 逐步构建完整地图。四种子任务类型：

| 类型        | 用途                         | 特点                               |
|-----------|----------------------------|----------------------------------|
| Research  | 调研技术方案、竞品实现、代码库现有模式        | AFK 任务，agent 自主完成，不需要实时交互        |
| Grilling  | 澄清架构选择、功能范围、体验细节           | 一次一个问题，直到达成 shared understanding |
| Prototype | 快速搭建 Logic 或 UI 原型，提高讨论保真度 | 让你"看到"方案再决策，前端尤其有用               |
| Task      | 配置环境、添加依赖、写工具函数等机械性工作      | 不需要追问，直接推进                       |

所有子任务完成后，信息汇总在 GitHub issues 里，可以直接转成 spec。

## /research、/prototype、TDD

这三个技能是辅助位，简单过一下。

`/research`：启动后台 agent 调研，你继续工作，它把发现写成 markdown 文件。

`/prototype`：两种模式，Logic prototype 测试行为逻辑，UI prototype 测试外观交互。v1.1 把它改成 model-invoked，让 Wayfinder 可以自动调用。

TDD：原来 Red-Green-Refactor 循环里的 Refactor 被 v1.1 移出去了，放到 code review 阶段处理。原因是在实现阶段同时做重构，负担太重。新的 TDD 技能变成纯参考材料，只保留核心顺序：Red → Green → Refactor（在 review 阶段）。

## mattpocock skills 应该在啥情况下使用？哪个平台最好？

我已经写了两篇文章极力推荐 `Trellis`，它真的很好用，对各种规模的任务都有很好的支持，小任务快速实现，大改动步步为营。

但它有个问题，**`Trellis` 以上下文注入为核心思路，又极度依赖 `hooks` 实现上下文注入**，一旦平台不支持 `hooks` 功能，哪怕只是不支持子代理的 `hooks` 功能，它的性能就会变得极不稳定。这点知乎的评论区就有人提过：

![](https://r2.jeanjan.kdns.fr/pictures/img-acf21bbb06.png)

当然这不能怪它，`hooks` 的确很可靠。根据官网指南，其最佳使用平台如下：

  * Claude Code
  * Cursor
  * OpenCode
  * Codebuddy
  * Droid
  * Pi Agent
  * Oh My Pi

如果你在用其它平台，那我很建议你用 **Mattpocock Skills** 。

在这里我尤其推荐新手使用 **Antigravity IDE** （别下成 2.0 版本了），因为它内置的功能已十分完整，几乎是自己实现了一套 mattpocock 软件开发流。它自带 `/grill-me`，而且交互体验比原版更好——选择的时候有UI了：

![](https://r2.jeanjan.kdns.fr/pictures/img-acf21bbb07.png)

它还有 `/schedule` 和 `/goal`，帮你规划任务和设定目标。实施计划和实施清单是每条对话必做的，不需要你手动生成。TDD 也是内置的，会自动驱动测试先行（尤其是你在`AGNETS.md`中要求的情况下）。会话交接更省心，agent 会自己维护 walkthrough，你下载到项目内就可以实现 `/handoff` 一模一样的功能。

所以 mattpocock skills 里，激进一点的话（比如我的用法），**可以只留两个：` /improve-codebase-architecture` 和 `/diagnose`**。

`/improve-codebase-architecture` 会系统性扫描代码库，找浅模块、找可测试性薄弱的地方、找垂直切片的机会，生成可视化 HTML 报告。antigravity 的架构审查维度覆盖了一部分，但没有这么系统化。

`/diagnose` 是一个结构化调试循环：复现→最小化→假设→仪器化→修复→回归测试。antigravity 的 Autonomous Debugging 可以自动诊断 Bug，但没有这个强制走完六步的 phase gate。**如果你调试时容易跳步、容易漏回归测试，这个 skill 能帮你按住自己。**

其他技能根据你自己的情况判断。比如 `/caveman` 如果你需要省 token、`/triage` 如果你有大量 issues 需要分拣、`/research` 如果你经常需要后台调研。但核心配置就这两个：`/improve-codebase-architecture` 和 `/diagnose`。**少而精，够用就行。**

在第一篇推荐 `Trellis` 的文章评论区，有人这样问过：

![](https://r2.jeanjan.kdns.fr/pictures/img-acf21bbb08.png)

现在有了 antigravity，这个问题有了更简单的答案。antigravity 已经把这些流程内置了——追问、规划、分解、实现、审查，一条对话自动走完。你只需要额外加 `/improve-codebase-architecture` 和 `/diagnose`，补上系统化架构审查和结构化调试循环。

