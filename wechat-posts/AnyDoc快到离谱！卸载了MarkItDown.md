# AnyDoc快到离谱！卸载了MarkItDown

**作者**: 字节笔记本
**发布时间**: 2026-08-06 17:26
**原文链接**: https://mp.weixin.qq.com/s/2MmtfB0JLQwFt8fRx8I5sg

---

Firecrawl开源了AnyDoc，一个用Rust写的文档转Markdown引擎。

对标的正是微软早前发布、如今已经被大量项目采用的MarkItDown。

虽然两边解决的是同一个问题，怎么把Word、PPT、Excel、PDF这些格式统一转成干净的Markdown，喂给大模型用，做法却完全不是一回事。

AnyDoc是用纯Rust 写的文档转 Markdown 引擎，把 Word、PPT、Excel、OpenDocument、RTF、EPUB、CSV、PDF 等格式统一转成干净的Markdown。

速度快到离谱，我测试了一下转化Epub格式的文件，一本 2.1M的图书仅用时 236ms。

![](https://r2.jeanjan.kdns.fr/pictures/img-144ae01d01.png)

其他的办公文档基本也是在个位数毫秒级转成。

比MarkItDown到处东拼西凑的下各种包 简直就是质的飞跃。

AnyDoc非常适合 LLM 读取的 Markdown，不同格式输入都能得到一致的输出，它也是目前Firecrawl Parse 的底层引擎。

同时还提供了 CLI、Node.js 绑定、Python 绑定，设置还有浏览器里跑的 WASM 版本。

它还打包成了一个 Agent Skill，能配合 Claude Code、Codex、Cursor、OpenCode 等智能体使用，让智能体读到任何文档格式时都能调用。CLI 用法大概是:
```

npx @firecrawl/anydoc report.docx        # 输出到 stdout  
npx @firecrawl/anydoc slides.pptx -o slides.md
```

直接塞进Claude Code、Codex、Cursor这些智能体工具链里面。

为了更方便生成预览文件管理以及做一些批量化的处理，我根据这个开源的库写了一个桌面端。

![](https://r2.jeanjan.kdns.fr/pictures/img-144ae01d02.png) Mac和Windows客户端地址： https://link.bytenote.net/note  


