# Anthropic内部Skills方法论首度公开：一文讲透Claude Code技能设计思路

**作者**: 智猩猩AI
**发布时间**: 2026-06-25 19:25
**原文链接**: https://mp.weixin.qq.com/s/Q5y_yiQQZkbHzywREZ_Now

---

智猩猩AI整理

编辑：林夕  

# 同样用Claude Code，为什么大厂团队效率碾压个人开发者？

#   

差距从来不在提示词，也不在模型调参。

  

很多开发者使用Claude Code时，仍然停留在对话式编程阶段：写需求、补上下文、不断修正结果，每个项目都像重新开始。

  

但在Anthropic内部，Claude Code已经是另一种用法。

  

在最新博客《Lessons from building Claude Code: how we use Skills》中，Anthropic首次系统分享了团队的Skills方法论。

  

过去一年里，他们围绕编码、测试、部署、运维、数据分析等场景，沉淀出了数百个生产级Skills，并逐渐形成了一套完整的能力复用体系。

  

在他们看来，真正决定AI开发效率的，不是提示词写得有多长，而是：

  

是否把团队经验沉淀成了一套可复用、可扩展、可持续演进的能力系统。

  

![](https://r2.jeanjan.kdns.fr/pictures/img-37fca36901.png)

  * 博客链接：https://claude.com/blog/lessons-from-building-claude-code-how-we-use-skills

  

 _**01**_

**Skill≠Prompt  

很多人误以为，Claude Skills就是高级一点的Markdown提示词。

在Anthropic官方定义里，**Skills不是单文件文本，而是一整套 专属工程能力文件夹**。

  

Agent可以自主发现、探索并使用这些资源来更准确、高效地完成任务。

  

在Claude Code中，技能还拥有丰富的配置选项，甚至可以注册动态钩子（Hooks）。一个精心设计的技能，能极大地释放AI的潜力。

  

通俗总结：**Prompt是一次性指令，用完即废；Skill是永久资产，一次配置、反复复用、越用越精准。**

 _**02**_

**9类生产级Claude Skills  

随着团队不断积累，逐渐形成了一套覆盖研发全流程的Skill体系。

  

从代码生成到故障排查，从自动化测试到基础设施管理，大部分高频工作都可以被封装成独立Skills，并在不同项目之间复用。

  

Anthropic复盘数百个内部技能，得出一个关键结论：**好用的技能，只专注一件事** 。

  

以下是适配所有研发团队的9大标准化技能，按需搭建即可。

  

![](https://r2.jeanjan.kdns.fr/pictures/img-37fca36902.png)

  

**（1）库 &API适配技能**  

  

针对项目内部SDK、私有CLI、第三方库做专属适配，沉淀独有调用规则、边界场景、高频报错坑点，解决AI通用代码和本地项目不匹配的问题。

  

**（2）产品自动化验证技能**

**支持页面流程、CLI交互全自动化测试，自动校验功能状态、留存测试记录，替代低效人工复测，是提升AI输出质量效果最明显的技能。

  

**（3）数据与监控分析技能**  

  

统一团队数据、监控口径，内置Grafana/Datadog配置、字段映射、查询模板，快速完成指标统计、漏斗分析、异常排查，告别数据混乱。

  

**（4）团队业务自动化技能**  

  

一键自动化处理所有琐碎工作：站会总结、工单创建、周报复盘、迭代汇总，彻底解放开发者的重复文案整理工作。

  

**（5）代码脚手架模板技能**  

  

固化团队代码规范，一键生成新服务、迁移文件、项目配置，内置权限、日志、部署规范，统一代码风格，降低新人上手成本。

  

**（6）代码质量 &评审技能**  

  

可接入Git钩子、自动化流水线，自动完成代码风格校验、漏洞排查、逻辑复审，提前规避低级Bug，大幅降低人工评审压力。

  

**（7）CI/CD部署运维技能**  

  

标准化代码合并、灰度发布全流程，自动监控PR、修复不稳定CI、处理合并冲突，异常时自动回滚，有效规避线上部署事故。

  

**（8）线上故障排查技能**  

  

对接告警、日志、链路追踪工具，根据异常信号自动匹配排查思路，快速定位根因，输出标准化故障复盘报告，提升值班排障效率。

  

**（9）基础设施运维技能**  

  

规范高危运维操作，自动清理冗余资源、管理项目依赖、排查云账单异常，自带操作防护机制，杜绝人工误操作引发线上问题。

  

 _**03**_

**Anthropic总结的8条Skills设计原则  

很多人做的Skills毫无价值，核心原因在于只是重复描述Claude默认就具备的能力。

  

Anthropic官方明确指出：优质Skill不应堆砌通用常识或基础编码规则，而应该专注于三件事——**补齐模型认知盲区、规避高频错误、赋予专属工程能力** 。

  

以下是Claude Code团队内部沉淀出的Skills制作黄金标准。

  

## （1）不要写显而易见的内容

##   

Claude已经具备编码、读代码库、基础调试等能力，因此Skill如果只是重复这些内容，只会增加上下文负担而不会带来任何增益。

  

真正有价值的内容，是让模型偏离默认解法路径的信息。

  

例如在设计类Skill中刻意规避Inter字体或紫色渐变等默认审美偏好，从而引导模型形成新的设计空间与决策方式。

###   

![](https://r2.jeanjan.kdns.fr/pictures/img-37fca36903.png)

博客例子：frontend design skill，通过避免Inter font和purple gradients提升设计偏好

  

## （2）构建陷阱区（Gotchas）

##   

Skills中最重要的不是规则，而是错误经验沉淀区（Gotchas），它记录的是模型在真实执行中反复踩过的坑。

  

这些问题往往不是逻辑错误，而是工程语境中的隐性失败，例如：

  

  * 数据表是append-only结构，必须取最高版本行，而不是最新created_at
  * API gateway与billing service中字段名称不同但语义一致
  * staging环境即使webhook未成功也会返回200，需要从payment_events判断真实状态  

这些内容会直接决定Skill的稳定性与可靠性。

###   

## （3）文件夹分层，实现渐进式信息披露

##   

Skills从来不是单文件，而是一个完整的文件系统工程，通过结构化拆分实现context engineering。

###   

![](https://r2.jeanjan.kdns.fr/pictures/img-37fca36904.png)

SKILL.md + stuck-jobs.md + api.md + assets + scripts

  

**标准分层架构** ：

  

  * 主文件SKILL.md：核心规则、触发条件、使用场景（入口总览）

  * 辅助文档：reference.md、stuck-jobs.md 存放详细规则、异常处理方案

  * 资源目录：assets模板文件、scripts可执行脚本、api示例文档

  

AI按需读取对应文件，精简上下文，同时保证复杂场景有完整支撑，兼顾轻量化与专业性。

  

## （4）避免过度约束Claude（不要 railroading）

##   

Skills不应该变成执行手册，因为Claude本身具备任务适配与路径规划能力。

  

如果过度规定步骤顺序，会直接削弱模型在复杂场景中的决策能力。

  

只定义目标与约束，而不规定执行路径，例如Slack standup skill只定义输出目标，而不是逐步控制生成流程。

###   

![](https://r2.jeanjan.kdns.fr/pictures/img-37fca36905.png)

Slack standup skill需灵活处理流程

  

## （5）支持私有化配置与交互式初始化

##   

Skills在团队环境中通常需要依赖外部上下文，例如Slack channel、API endpoint或内部模板，因此推荐使用config.json进行统一管理。

  

当配置缺失时，Skills可以主动引导用户补全，复杂情况下可通过AskUserQuestion工具生成结构化问题，实现低成本初始化配置。

###   

![](https://r2.jeanjan.kdns.fr/pictures/img-37fca36906.png)

Slack channel 未配置 → 触发询问

  

## （6）description是模型触发信号，而不是文档

##   

Skills的description字段并不是给人看的说明，而是Claude用于任务路由的识别信号，因此必须包含明确的触发语义与关键词。

  

例如babysit、standup、review、debug等，使模型能够在任务执行时自动匹配对应Skills，而无需用户显式调用。

###   

![](https://r2.jeanjan.kdns.fr/pictures/img-37fca36907.png)

description用于skill selection scan

  

## （7）引入持久化记忆，实现持续演化

##   

Skills可以通过日志文件、JSON或SQLite等方式记录执行历史，并借助 ${CLAUDE_PLUGIN_DATA} 作为稳定存储路径，实现跨会话持久化。

  

例如standup-post skill会维护standups.log，用于记录每次输出内容，从而让模型能够对比历史变化并生成差异化结果。

###   

![](https://r2.jeanjan.kdns.fr/pictures/img-37fca36908.png)

standups.log 记录历史

##   

## （8）固化脚本能力，让模型专注决策

##   

所有确定性操作都不应该由模型重复生成，而应该提前封装为脚本或工具函数，例如数据抓取、格式转换、API查询等。

  

例如data-science skill提供helper functions，使Claude可以直接组合调用，而不是重新实现底层逻辑，从而将计算资源集中在分析与策略判断上。

###   

![](https://r2.jeanjan.kdns.fr/pictures/img-37fca36909.png)![](https://r2.jeanjan.kdns.fr/pictures/img-37fca36910.png)

  

data-science skill 提供 helper functions

  

## （9）使用on-demand hooks，而不是全局hooks

##   

Skills可以绑定仅在调用期间生效的hooks，用于处理特定风险或增强行为，而不是全局常驻。

  

例如：

  * /careful：拦截rm -rf、DROP TABLE、强制推送等高危操作
  * /freeze：限制编辑范围，用于调试阶段防止误改代码

  

这种方式可以在保证灵活性的同时提供安全边界控制。

  

## （10）技能联动，实现能力复用

##   

Skills之间可以形成依赖关系并进行组合调用，从而构建端到端能力链路。

  

例如CSV生成Skill可以直接调用文件上传Skill，实现从数据生成到输出分发的一体化流程，本质是将单点能力组合成系统级工作流。

###   

 _**04**_

**以迭代沉淀技能，**

**用Skills管理AI业务能力  

Anthropic在文章最后提到，他们最成功的Skills往往并不是一开始就设计完善。

  

很多技能最初只是几行简单说明，或者一次真实项目中踩过的坑。

  

随着团队持续使用，不断补充新的案例、规则和边界条件，这些技能才逐渐成长为真正可靠的生产工具。

  

这也是Skills与Prompt最大的区别：Prompt解决的是一次性问题，Skills积累的是长期能力。

  

当项目规范、业务规则、排障经验、自动化流程都被封装成Skills后，AI不再是一个通用助手，而开始真正理解团队的工作方式。

  

从这个角度看，Claude Code团队分享的并不仅仅是一套使用技巧。

  

它更像是在回答一个问题：当AI开始进入真实工作流之后，我们应该如何组织和管理这些能力。

  

而Skills，正是Anthropic当前给出的答案。

  

**END**

✦

✦

**2026中国AI智能体大会**

✦

 _智猩猩主办的**2026中国AI智能体大会** 7月2-3日杭州举行，大会设有开幕式，企业级AI智能体、AI智能体产品创新**2场论坛** ，以及Coding Agent、自进化智能体、深度研究智能体、Computer-Use Agent、多智能体协同、Agent Skills、Agent Harness**7场技术研讨会** 。_ _最终议程已公布⬇️_

![](https://r2.jeanjan.kdns.fr/pictures/img-37fca36911.jpeg)![](https://r2.jeanjan.kdns.fr/pictures/img-37fca36912.jpeg)![](https://r2.jeanjan.kdns.fr/pictures/img-37fca36913.jpeg)![](https://r2.jeanjan.kdns.fr/pictures/img-37fca36914.jpeg)![](https://r2.jeanjan.kdns.fr/pictures/img-37fca36915.jpeg)![](https://r2.jeanjan.kdns.fr/pictures/img-37fca36916.jpeg)![](https://r2.jeanjan.kdns.fr/pictures/img-37fca36917.jpeg)![](https://r2.jeanjan.kdns.fr/pictures/img-37fca36918.jpeg)![](https://r2.jeanjan.kdns.fr/pictures/img-37fca36919.jpeg)![](https://r2.jeanjan.kdns.fr/pictures/img-37fca36920.jpeg)

✦

✦

**入群申请**

✦

![](https://r2.jeanjan.kdns.fr/pictures/img-37fca36921.png)

**关注+星标，每日获取AI前沿进展与高星开源项目**

