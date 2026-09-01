# 让 agent 帮你制作电影感产品视频的 skill：106 张镜头配方卡、162 个样式、161 条动态样片、已验收成片模板

**作者**: 几乎满级
**发布时间**: 2026-07-24 11:52
**原文链接**: https://mp.weixin.qq.com/s/MjsDlQ4VlZXaRzapSggjKA

---

> ❝
> 
> **video-shotcraft** 是一个面向 AI 编程 Agent（Claude Code / Codex）的视频制作技能包，提供 106 张镜头配方卡、161 个动态样片和一个完整的 Ink Press 产品宣传片模板，让 Agent 能够基于 Remotion 框架自动完成分镜、动画和声音设计，制作包含真实页面截图、2.5D 运镜、节奏卡点和 SFX 的视频，一支电影级宣传片。

### **看点**

  * 提供 **106 张镜头配方卡** ，每张卡包含用途、能量感、建议时长、参数、实现要点和已知坑点；
  * 附带 **161 个动态样片预览** ，覆盖 162 种视觉风格，可在在线 Gallery 中搜索和筛选；
  * 内置一个完整的 **Ink Press 模板** ：36.2 秒、1920×1080、30fps、10 个镜头，纸墨琥珀风格，含 2.5D 真实页面运镜、字卡、转场和逐帧音效；
  * 提供 **可复用的 Remotion 组件库** ：2.5D 页面摄像机、字幕、闪光切换、数字滚动、音效和素材采集脚本；
  * 所有镜头卡和模板的 TSX 实现均为 **可运行的参考代码** ，包含实际缓动和时序参数；
  * 配套提供完整的 **生产方法论** ：涵盖从素材截取 → 视觉方向 → 故事板 → 音效设计 → 节奏卡点 → 最终验收；
  * 覆盖 Web 和桌面产品宣传片场景，单个镜头卡也可用于功能演示、品牌短片、发布视频等。

**素材与合规须知**

  * **底层框架授权** ：驱动库内 demo 与模板的 Remotion 框架有自己的许可协议（个人与小团队免费，公司可能需要付费许可）。
  * **动效灵感与免责** ：镜头配方源自对 ClickUp、Perplexity、Slack、Notion、Figma、Framer、Bear、Raycast、Pitch、Miro、Superhuman、Loom 等优秀官方产品宣传片动效语言的研究学习，动效技法为从零重新实现。仓库中不包含上述影片的任何素材、画面或品牌资产。
  * **音频来源** ：库内 SFX 与音乐素材来源于 Mixkit，具有免费商用授权。
  * **数据隐私脱敏** ：模板内的产品截图为演示素材。对外发布成片前，请替换为目标产品自己的截图，并确认其中的数据、客户信息和个人信息是否需要脱敏。

### **安装与使用**

**安装（三种方式）：**

  1. **Agent 代办** （推荐）：直接把仓库链接交给 Claude Code 或 Codex，Agent 会自动 clone 并链接到 skills 目录
  2. **CLI 安装** ：`npx skills add Vincentwei1021/video-shotcraft`
  3. **手动安装** ：clone 仓库后，软链接到 `~/.claude/skills/` 或 `~/.codex/skills/`

**使用方式：**

  * 基础用法：`Use video-shotcraft to create a promo for my desktop product.`
  * 指定镜头：`Use the deck-deal-flyin and row-embed shot cards to present this feature.`
  * 套用模板：`Use video-shotcraft to make a promo for my product with the Ink Press template.`
  * 灵感参考：`Design a product close-up inspired by spotlight-hero-card.`

项目由 **Vincentwei1021（Wei Yihao）与 Claude** 开发，采用 **Apache-2.0 协议** ，当前 **935 Stars** 。该库自身的构建、迭代与验收全程由 AI coding agent 完成。

> ❝
> 
> 项目地址：github.com/Vincentwei1021/video-shotcraft

