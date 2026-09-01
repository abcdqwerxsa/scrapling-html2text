# Cloudflare 给 AI Agent发了一台「虚拟电脑」

**作者**: 赶走坏脾气
**发布时间**: 2026-08-06 08:04
**原文链接**: https://mp.weixin.qq.com/s/usNglSKIigraHciSsv9vBA

---

Cloudflare · AI Agent · 2026.08

Computer：把文件系统塞进 Durable Object，让 Agent 拥有持久化的工作空间

Cloudflare 今天在 GitHub 上开源了一个叫 **Computer** 的项目，描述只有四个字： _Give your agent a computer_ 。给 Agent 一台电脑。

乍一看觉得在开玩笑，但看完了代码和文档之后，我发现这个项目背后的思路挺有意思——它不是真的给 AI 发了一台电脑，而是**在 Durable Object 里塞了一个虚拟文件系统** ，让 AI Agent 有了真正持久化的工作空间。

## 先理解它要解决什么问题

现在的 AI Agent 有一个根本性的局限：**没有自己的「空间」** 。

你让 Agent 帮你写一个脚本，它生成了代码，但代码在哪里？在你的终端输出里。下次对话呢？没了。你让它帮你做一个调查报告，它搜集了一堆信息，但信息存在哪？在 LLM 的上下文窗口里，对话结束就消失了。

这就好比一个员工没有工位、没有电脑、没有抽屉，所有工作成果只能口头汇报，完了就散了。

Cloudflare Computer 要做的事情，就是给 Agent 一个持久化的文件系统和执行环境。Agent 可以在这里存文件、读文件、写代码、运行代码，而且这些东西不会因为对话结束就消失。

## 技术架构：三层执行后端

Cloudflare Computer 的核心是一个虚拟文件系统，它跑在 Durable Object 里面，用 SQLite 存储状态。通过 `workspace.runtime`暴露执行接口，支持三种后端：

### Container：完整容器

把 SQLite 状态投射到一个沙箱容器里，作为真实的 FUSE 挂载点。容器里有个叫 computerd 的守护进程负责同步。这是最重的方案，但也是功能最完整的——完整的 Linux 用户空间，真实的二进制文件，真实的网络。

### Isolate Shell：轻量 Shell

在 Dynamic Worker 里运行 Vercel 的 just-bash。不需要容器，通过 Workers RPC 直接访问 Workspace。轻量快速，适合简单任务。

### Isolate JavaScript：JS 执行环境

在 Dynamic Worker 里执行 ECMAScript 模块。有结构化的输入输出、持久的相对导入、配置好的库，以及 `ws:git`和 `ws:artifacts`模块。适合纯 JS 任务。

三种后端可以共存于一个 Workspace。Agent 根据任务选择合适的后端执行，但调用的接口只有一个：`workspace.runtime.exec()`。

## 几个有意思的示例

项目仓库的 examples 目录里有一些很能说明设计意图的示例：

**think** — 一个基于 @cloudflare/think 的聊天 Agent，把 Workspace 当作自己的工作目录。你通过终端跟它对话，它直接在工作空间里读写文件。

**think-compare-runtimes** — 一个 Web UI，用同一个 Agent 任务分别跑容器后端和 Worker 后端，并排对比结果。说明后端是可以随时切换的。

**tutorial** — 一步一步教你搭一个端点，Agent 写一个 Markdown 菜谱卡片，然后在容器里跑 pandoc 生成 PDF。整个过程 Agent 有自己的工作空间。

**artifacts** — Agent 在 Workspace 里生成一个 Worker 项目，然后发布到 Cloudflare Artifacts，变成一个可以直接 clone 的仓库。

**assets** — 把一段文字 prompt 变成图片，写到 Workspace 里，然后通过 @cloudflare/computer/assets 生成分享链接。

看这些示例你会发现一个共同点：Agent 不再是一个「无家可归」的处理单元，它有自己的文件系统，可以持久化地组织工作成果。

## 我的理解

Cloudflare Computer 不是一个给终端用户用的产品，它是一个**给 Agent 开发者用的基础设施** 。它解决的是：如果你要构建一个持久的、有状态的 AI Agent，它的文件和状态放哪里？

答案目前看起来是：Cloudflare 的 Durable Object + SQLite。这有几个好处：

  * ▪**持久化** ：Durable Object 天然是持久的，不会因为请求结束就销毁
  * ▪**一致性** ：状态存在 SQLite 里，不像内存那样不可靠
  * ▪**弹性** ：三种后端可以按需选择，轻量任务用 Shell，重活用容器
  * ▪**全球分布** ：跑在 Cloudflare 的边缘网络上

当然，项目目前还是 **Preview Only** ，官方明确说了 API 不稳定，设计可能随时改。文档里也说了：适合实验和原型，不适合生产环境。

## 更大的图景

Cloudflare 布局 AI 基础设施的方向越来越清晰了。从 Workers AI 到 AI Gateway，再到现在的 Computer，他们在构建一整套 Agent 运行时的基础设施。

Computer 的思路跟腾讯的 Agent Memory 其实有异曲同工之处——都是在解决「Agent 需要有自己的状态空间」这个问题。只不过腾讯聚焦在记忆层面，Cloudflare 聚焦在执行层面。两者结合起来的想象空间挺大。

不过说实话，目前这个项目的适用面还比较窄。如果你不用 Cloudflare 的生态，它的价值有限。但如果你在 Cloudflare 上构建 Agent 应用，这个项目的思路值得认真参考。

项目地址：https://github.com/cloudflare/computer

如果觉得有用，欢迎转发分享让更多人看到好内容  


