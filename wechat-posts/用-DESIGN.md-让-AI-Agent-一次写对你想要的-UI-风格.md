# 用 DESIGN.md 让 AI Agent 一次写对你想要的 UI 风格

**作者**: Git 拆解
**发布时间**: 2026-06-16 09:30
**原文链接**: https://mp.weixin.qq.com/s/Ym2FZnBO8HnP4TnPm8QQag

---

> **项目卡片**
> 
>   * **项目** ：DESIGN.md[1]
>   * **状态** ：Alpha / 15.7k Star / Apache 2.0
>   * **一句话判断** ：给 AI agent 写的设计系统说明书，格式简单但够用，CLI 工具链完整，导出 Tailwind 和 DTCG 零配置。
> 

问题：AI 不是不会写 UI，是不知道你要什么风格

用 Claude、Cursor、Copilot 帮写前端，功能经常能跑通，但颜色偏了、字体不对、间距节奏乱。你跟它描述一遍设计规范，下次对话它又忘了。

截图它记不住，Figma 链接它打不开，口头描述每次都不一样。缺一种稳定的格式让它反复读取你的设计意图。

DESIGN.md 做的事很简单：把设计系统写成一个纯文本文件，一半是 YAML token（机器解析），一半是设计说明（人能读懂）。读一次，就知道你想要什么风格。

文件长什么样

两层结构：YAML front matter 放 token（机器读），Markdown body 放设计说明（人读）。
```

---  
name: Heritage  
colors:  
  primary: "#1A1C1E"  
  secondary: "#6C7278"  
  tertiary: "#B8422E"  
typography:  
  body-md:  
    fontFamily: Public Sans  
    fontSize: 1rem  
rounded:  
  sm: 4px  
  md: 8px  
---  

```

对应 body 部分：
```

## Colors  
  
- **Primary (#1A1C1E):** Deep ink for headlines and core text.  
- **Tertiary (#B8422E):** Boston Clay — the sole driver for interaction.  

```

YAML 给精确值，prose 告诉 agent 为什么这么选、怎么用。仓库哲学文档说得很直白：**prose 比 token 更重要** 。token 是上下文参考，不是渲染指令；真正约束 agent 行为的是那些描述性文字。

5 分钟写你的第一份 DESIGN.md

### 第一步：确定文件结构

仓库规范定义了 8 个标准 section，按顺序排列：

  1. Overview（品牌调性）
  2. Colors
  3. Typography
  4. Layout
  5. Elevation & Depth
  6. Shapes
  7. Components
  8. Do's and Don'ts

不必全部写，但写了的要按这个顺序。agent 遇到不认识的 section 会保留而不报错，所以你可以自由扩展（比如加 `## Motion` 或 `## Iconography`）。

### 第二步：写 token

最简配置只需要 `name` \+ `colors`。推荐先把这几个写上：
```

---  
name: My Design System  
colors:  
  primary: "#1A1C1E"       # 主色，用于标题和核心操作  
  secondary: "#6C7278"     # 辅助色，用于边框、元数据  
  neutral: "#F7F5F2"       # 底色，比纯白柔和  
typography:  
  body-md:  
    fontFamily: Inter  
    fontSize: 16px  
    fontWeight: 400  
    lineHeight: 1.6  
rounded:  
  sm: 4px  
  md: 8px  
  lg: 12px  
spacing:  
  base: 8px  
---  

```

颜色支持所有 CSS 格式：hex、`rgb()`、`oklch()`、命名色都可以。token 引用用 `{colors.primary}` 这种花括号语法，可以在 components 里互相引用。

### 第三步：写 prose

这一步比 token 更关键。不要堆形容词（"现代、简洁、高级"），要给具体参照。
```

## Overview  
  
一个面向开发者的技术文档站。不追求视觉冲击，  
追求信息密度和长时间阅读的舒适度。  
像一份排版考究的论文预印本，不像营销落地页。  

```

一个具体参照（"排版考究的论文预印本"）比十个形容词更能约束生成行为。仓库哲学文档的原话是：**具体的参照自带负面约束** ——你不用说"不要发光、不要渐变"，因为"论文预印本"这个参照已经排除了这些。

CLI 工具：lint、diff、export

CLI 发布在 npm，不需要全局安装：
```

npx @google/design.md lint DESIGN.md  

```

### lint：校验文件

检查 9 条规则，输出 JSON。几条值得知道的：

  * `broken-ref`（error）：token 引用指向了不存在的路径
  * `contrast-ratio`（warning）：组件的背景色和文字色对比度不够 WCAG AA
  * `missing-primary`（warning）：定义了颜色但没有 primary

这个 lint 不只是格式检查——它会帮你发现设计系统本身的逻辑问题。比如你给按钮定义了白色文字配浅色背景，它会直接告诉你对比度不够。

### diff：对比两个版本
```

npx @google/design.md diff DESIGN.md DESIGN-v2.md  

```

输出 token 级别的变更报告（哪些颜色加了、删了、改了），新版本比旧版本多了 error 或 warning 时 exit code 非零。

### export：导出到其他格式
```

# 导出为 Tailwind v3 配置  
npx @google/design.md export --format json-tailwind DESIGN.md > tailwind.theme.json  
  
# 导出为 Tailwind v4 CSS 主题  
npx @google/design.md export --format css-tailwind DESIGN.md > theme.css  
  
# 导出为 W3C Design Token 格式  
npx @google/design.md export --format dtcg DESIGN.md > tokens.json  

```

实际用途：把 DESIGN.md 当单一信源，export 到 Tailwind 或 DTCG，不用手动维护多份配置。

实际接入 AI 工作流

### 方式一：放进项目上下文

最直接的方式——把 DESIGN.md 内容放到 agent 能读到的地方：

  * Claude Code：放到 `CLAUDE.md` 或 `.claude/` 目录下
  * Cursor：放到 `.cursorrules` 或项目根目录
  * Windsurf / Copilot：放到项目上下文文件

写一个最小可用版本就行，不用一上来就把 8 个 section 全写满：
```

---  
name: 我的项目  
colors:  
  primary: "#2563EB"  
  neutral: "#F8FAFC"  
typography:  
  body-md:  
    fontFamily: Inter  
    fontSize: 16px  
---  
  
## Overview  
  
一个 B2B SaaS 后台。信息密度优先，不追求视觉花哨。  
参考 Linear 和 Vercel Dashboard 的克制感。  

```

10 行就能用。后面慢慢补。

### 方式二：CI 集成

在 CI 里跑 lint + diff，设计系统变更自动检查：
```

- name: Lint design system  
  run: npx @google/design.md lint DESIGN.md  
  
- name: Check regressions  
  run: npx @google/design.md diff DESIGN-base.md DESIGN.md  

```

diff 命令会输出 token 级变更报告，如果新版本比旧版本多了 error 或 warning，exit code 非零，CI 直接挂。

参考：三个真实示例

仓库带了三个完整 DESIGN.md，风格完全不同：

**Paws & Paths**（宠物 App）：暖橙主色、Plus Jakarta Sans、大圆角。prose 里写"友好、可靠"，token 里 rounded 直接给到 `xl: 1.5rem`。

![Paws & Paths 设计系统：暖橙主色、Plus Jakarta Sans、大圆角卡片和柔和阴影，友好可靠的宠物 App 风格](https://r2.jeanjan.kdns.fr/pictures/img-5f1e853b01.png)

**Totality Festival** （日食音乐节）：深空黑底 + 琥珀色高亮、玻璃态。prose 写"Cosmic Premium"，组件里定义了 `card-glass-level-2` 用 `rgba(52, 52, 58, 0.2)` 做半透明背景。

![Totality Festival 设计系统：深空黑底配琥珀高亮，玻璃态卡片组件，日食主题的宇宙级视觉体验](https://r2.jeanjan.kdns.fr/pictures/img-5f1e853b02.png)

**Atmospheric Glass** （天气 App）：深蓝渐变 + 全玻璃态。prose 里写"ethereal yet functional"，组件定义了 `glass-card-standard` 和 `glass-card-elevated` 两个层级。

![Atmospheric Glass 设计系统：深蓝渐变背景上的全玻璃态 UI，多层透明度和模糊效果营造空灵通透感](https://r2.jeanjan.kdns.fr/pictures/img-5f1e853b03.png)

写自己的 DESIGN.md 之前翻一遍这三个，重点看 prose 和 token 怎么配合——prose 定调性，token 给精确值，两者缺一不可。

坑点清单

**token 命名没有强制规范** 。仓库建议用 `primary/secondary/tertiary/neutral`，但你用什么都行。问题是 agent 不知道你自定义的名字是什么意思——所以 prose 里必须解释。

**组件定义还很早期** 。spec 里明确说"components specification is actively evolving"。目前只支持 `backgroundColor`、`textColor`、`typography`、`rounded`、`padding`、`size`、`height`、`width` 这几个属性。想描述复杂的交互状态（hover、focus、disabled）得靠命名约定（`button-primary-hover`）而不是结构化语法。

**Windows 用户注意** ：npm 包名 `@google/design.md` 在 Windows PowerShell 里有冲突（`.md` 后缀被当成 Markdown 文件），需要用 `designmd` 别名：
```

npx -p @google/design.md designmd lint DESIGN.md  

```

**Alpha 阶段** 。格式还在演进，不保证向后兼容。生产环境用的话，锁定版本号。

它的定位

DESIGN.md 不是要替代 Figma、Tailwind 或 DTCG。它卡在一个中间位置：用最低成本（一个纯文本文件）让 AI coding agent 理解你的设计意图，然后通过 export 命令同步到你实际用的工具链。

如果你已经在用 Tailwind，流程变成：写 DESIGN.md → `export --format css-tailwind` → 拿到 `@theme` 块，不用手动维护两份配置。

Alpha 阶段，格式还在演进。但对"让 AI 写对风格"这个具体问题，它已经是目前最轻量的解法。

这里会继续拆真实可用的开发者工具：少讲概念，多看入口、成本和坑点。你只需要判断一件事——它值不值得放进自己的工作流。

### 引用链接

[1]DESIGN.md: _https://github.com/google-labs-code/design.md_

