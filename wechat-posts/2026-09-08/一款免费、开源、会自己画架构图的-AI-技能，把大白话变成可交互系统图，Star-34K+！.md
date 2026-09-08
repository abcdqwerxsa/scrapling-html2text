# 一款免费、开源、会自己画架构图的 AI 技能，把大白话变成可交互系统图，Star 34K+！

**作者**: 有趣的开源集市
**发布时间**: 2026-08-31 08:08
**原文链接**: https://mp.weixin.qq.com/s/G32OVxaXCuy5N4koHgSt-g

---

开会讲方案，最累的不是写代码，而是画那张「看起来很专业」的架构图。

`浏览器 -> API -> Redis -> PostgreSQL` 这种描述，老板听不懂，同事看不下去，PPT 里贴半天箭头最后还是一团乱。Archify 就是为这种场景生的：你只用大白话描述系统，它直接在聊天里生成一张可交互、可导出、能讲给别人听的架构图。

![Archify light 主题架构图](https://r2.jeanjan.kdns.fr/pictures/img-e58a139001.png)

## 项目简介

Archify 是一个面向 Cursor、Claude Code、Codex CLI、OpenCode 等 AI 编程助手的 **Agent Skill** （渲染与校验系统）。它的工作方式很特别：AI 先把你的系统描述转成一份带类型的 JSON 中间表示，Archify 再把它确定性地编译成 HTML/SVG 架构图、时序图、数据流图等可视化产物。

最新稳定版本是 v2.16.0，基于 Node.js，MIT 协议。GitHub 上 Star 数已经冲到 34,370，今日新增 3,730，属于近期 trending 里增长最快的项目之一。

![架构图示例](https://r2.jeanjan.kdns.fr/pictures/img-e58a139002.png)

它解决的痛点很具体：

  * 不想学 Mermaid / PlantUML 的语法；
  * 想从一句话、一段代码描述直接出图；
  * 需要一张能导出 PNG/SVG、能交互查看上下游依赖的图；
  * 做 Code Review 或方案评审时，想直观看到「改了哪些地方」。

## 核心特性

Archify 不止是把文本变成图，它更像一个「有校验、可交互的图生成器」。

**1\. 五种图类型，覆盖系统表达常见场景**

  * Architecture：组件、服务、存储、边界；
  * Workflow：CI/CD、审批、工具调用、运维手册；
  * Sequence：API 调用、缓存回源、鉴权、异步链路；
  * Data Flow：数据管道、血缘、敏感数据边界；
  * Lifecycle：状态机、重试、等待、终态。

**2\. 可交互，不只是静态图**

生成后的 HTML 里可以搜索节点、追踪 Upstream/Downstream 依赖、探测指定路由、对比两个语义角色，还能以「故事」模式按章节播放关键路径。

**3\. 带校验的生成流程**

Schema、布局、HTML/SVG、路由、标签与路由间隙都会经过验证，失败时会给出带修复建议的 JSON 报告，而不是一段 Node 堆栈。

**4\. 一套图，多格式交付**

同一份源码可以输出自包含的 HTML、PNG、SVG、WebM，还能生成 1200×630 的社交分享卡片。

**5\. 架构变更 Delta 视图**

对比两个已校验的快照，生成 Before / Delta / After 视图，标出新增、删除、修改、移动的节点和边，做设计评审或 PR 说明非常直观。

## 怎么用

Archify 支持两种方式使用：作为 AI 助手的 Skill 全局安装，或在有仓库时直接让 Agent 分析代码结构出图。

### 方式一：全局安装成 Agent Skill
```

npx skills add tt-a1i/archify -g  

```

如果你用 Cursor，可以加上 agent 参数：
```

npx -y skills add tt-a1i/archify --skill archify --agent cursor --global --copy --yes  

```

安装后，在 Claude Code 的 Skills 页面里就能看到一条 `architecture-diagram` 条目。

![Claude Skills 页面](https://r2.jeanjan.kdns.fr/pictures/img-e58a139003.png)

### 方式二：在聊天里直接描述

不需要仓库，直接说：
```

Use Archify to draw: Browser -> API -> Redis cache -> PostgreSQL fallback.  

```

也可以带上更具体的要求：
```

Analyze this repository, then use Archify to create a high-level runtime architecture diagram.  
Show 8-12 core components, one primary path, external dependencies, and trust boundaries.  
Put supporting detail in cards instead of adding more edges.  

```

### 方式三：本地 CLI 生成与导出
```

cd archify  
node bin/archify.mjs validate workflow examples/agent-tool-call.workflow.json --quality showcase --json  
node bin/archify.mjs deliver workflow examples/agent-tool-call.workflow.json /tmp/workflow.html --quality showcase --open --json  

```

生成后的 HTML 用浏览器打开，顶部可以切换 Dark/Light/Classic 主题，点 Export 能导出 PNG、JPEG、SVG、WebM，也可以一键复制分享卡片到剪贴板。

![导出菜单](https://r2.jeanjan.kdns.fr/pictures/img-e58a139004.png)

## 效果长啥样

下面是两张真实从 Archify 生成的图。第一张是一个 CI/CD / Agent 工具调用的工作流：

![工作流示例](https://r2.jeanjan.kdns.fr/pictures/img-e58a139005.png)

第二张是数据流图，能清晰展示数据从入口到存储、消费、边界的完整路径：

![数据流示例](https://r2.jeanjan.kdns.fr/pictures/img-e58a139006.png)

这些不是示意图，而是可以从 `archify` 的 `examples/` 目录直接渲染出来的产物。节点、颜色、主题、路由都经过校验，不会因为 AI 随手一画就对不齐。

## 为什么值得用

对个人开发者来说，Archify 最大的价值是「省时间」。以前为了画一张架构图要打开 Draw.io、Excalidraw 或 PPT，拖半天组件；现在一句话就能出一张能交付的图。

对技术团队来说，它提供了一种「可审查的视觉资产」。因为它会在渲染前做 Schema 和布局校验，生成的图不是「AI 瞎画的」，而是可复现、可对比、可嵌入到文档或 README 里的产物。

![语义对比视图](https://r2.jeanjan.kdns.fr/pictures/img-e58a139007.png)![架构变更 Delta](https://r2.jeanjan.kdns.fr/pictures/img-e58a139008.jpeg)

上图分别是 Archify 的语义角色对比视图和架构变更 Delta 视图，做方案评审或写 Release Note 时直接贴上去，别人一眼就能看懂你改了什么、为什么改。

一句话：如果你厌倦了用 PPT 画箭头，也不想背 Mermaid 语法，Archify 是那种装完就能用、用完就想留下的工具。

## 轻松收尾

Archify 目前还在快速迭代，最新版本 v2.16.0 是 2026-08-30 发布的。它不是一个通用绘图编辑器，而是把「技术意图」变成「沟通资产」的专用管道。对于有画图需求、但不想把生命浪费在排版上的人来说，值得一试。

https://github.com/tt-a1i/archify

