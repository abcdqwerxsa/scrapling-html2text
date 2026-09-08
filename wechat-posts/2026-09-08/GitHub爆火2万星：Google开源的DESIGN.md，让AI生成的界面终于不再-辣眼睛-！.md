# GitHub爆火2万星：Google开源的DESIGN.md，让AI生成的界面终于不再"辣眼睛"！

**作者**: Ghub 宝藏项目
**发布时间**: 2026-08-10 17:34
**原文链接**: https://mp.weixin.qq.com/s/p8O3gveD7ZPrSNeesgS3sw

---


你有没有发现，现在让AI写个网页，出来的东西总带着一股子"AI味"？

不是满屏的靛蓝按钮，就是那种看了让人犯困的默认模板。你跟它说"高级一点"，它就只是把紫色换成橙色，跟小朋友换蜡笔似的，本质没啥变化。

这事儿困扰的不只你一个人。Google Labs那帮人也看不下去了，今年四月直接把自家内部的AI设计规范给开源了出来——一个叫 **design.md** 的项目。短短几个月在GitHub上狂揽两万多星，成了前端圈和AI圈都在盯的宝藏。

**它到底解决了啥问题**

说白了，design.md 就是写给AI Agent看的一份"设计说明书"。

以前咱们写代码，会给AI塞个 CLAUDE.md 或者 AGENTS.md，告诉它用什么框架、怎么命名变量。但设计这块一直是个盲区——AI不知道你心里的"高级感"到底是啥，只能瞎猜。

design.md 把这缺口给补上了。它用一份 Markdown 文件，同时搞定两件事：上半截是机器能读的精确数值（颜色、字号、间距），下半截是人能读的设计意图（为啥用这个色、圆角多大才舒服）。

AI读了之后，既知道"做什么"，又明白"为什么这么做"。

**文件长啥样**

打开一份 DESIGN.md，你会看到很清晰的两层结构。

最上面是 YAML 格式的"设计令牌"：
```

---  
name: Heritage  
colors:  
  primary: "#1A1C1E"  
  secondary: "#6C7278"  
  tertiary: "#B8422E"  
  neutral: "#F7F5F2"  
typography:  
  h1:  
    fontFamily: Public Sans  
    fontSize: 3rem  
rounded:  
  sm: 4px  
  md: 8px  
spacing:  
  sm: 8px  
  md: 16px  
---  

```

下面接着是 Markdown 正文，讲设计理念：
```

## 概览  
  
建筑极简主义遇上报刊庄重感。UI 呈现高级哑光质感——像高端大报或当代画廊。  
  
## 配色  
  
- **主色(#1A1C1E)**: 深墨色，用于标题和正文核心文字。  
- **次色(#6C7278)**: 沉稳石板灰，用于边框、说明文字。  
- **强调色(#B8422E)**: "波士顿黏土"——唯一的交互驱动色。  
- **中性色(#F7F5F2)**: 暖石灰底色，比纯白更柔和。  

```

你看，每个颜色都有名字、有十六进制值、还有使用场景。AI拿到这份文件，生成的按钮就不会乱套了。

**怎么安装和使用**

这个项目最爽的地方就是零配置，开箱即用。你甚至不用把它装到项目里，npx 直接跑。

**第一步：验证你的 DESIGN.md 文件**

在项目根目录建好 DESIGN.md 之后，先跑一遍校验：
```

npx @google/design.md lint DESIGN.md  

```

它会自动检查八条规则，比如有没有 broken 的引用、主色缺没缺、对比度够不够 WCAG 标准、有没有孤立的 token 等等。输出是 JSON 格式，AI agent 可以直接消费：
```

{  
  "findings": [  
    {  
      "severity": "warning",  
      "path": "components.button-primary",  
      "message": "textColor (#ffffff) on backgroundColor (#1A1C1E) has contrast ratio 15.42:1 — passes WCAG AA."  
    }  
  ],  
  "summary": { "errors": 0, "warnings": 1, "info": 1 }  
}  

```

如果报错了，根据提示改就行，特别省心。

**第二步：对比版本差异**

设计系统迭代的时候，最怕 token 被偷偷改乱了。用 diff 命令可以对比两个版本：
```

npx @google/design.md diff DESIGN.md DESIGN-v2.md  

```

它会告诉你哪些颜色加了、哪些删了、哪些被改了，token 级别的回归一眼就能看见。

**第三步：导出到 Tailwind**

如果你项目里用了 Tailwind，一行命令就能导出主题配置：
```

# Tailwind v3 版本  
npx @google/design.md export --format tailwind DESIGN.md > tailwind.theme.json  
  
# Tailwind v4 版本  
npx @google/design.md export --format css-tailwind DESIGN.md > theme.css  

```

还支持导出 W3C 标准的 DTCG tokens.json，跟 Figma、Style Dictionary 这些工具都能打通。
```

npx @google/design.md export --format dtcg DESIGN.md > tokens.json  

```

**Windows 用户注意个小坑**

因为包名带了 `.md` 后缀，在 Windows PowerShell 里直接跑可能会没反应，甚至直接打开你的 Markdown 编辑器。这时候换个写法就行：
```

npx -p @google/design.md designmd lint DESIGN.md  

```

或者用 `designmd` 这个别名，全平台都稳。

**第四步：塞进 AI 的 system prompt**

在项目的 CLAUDE.md 里加一句，让它读取根目录的 DESIGN.md。Claude Code 生成 UI 的时候，就会自动按里面的 token 来配色、排版，不会再自由发挥了。

**配合 Stitch 用更香**

Google 自家有个叫 Stitch 的AI设计工具，设计师在里面调好风格之后，能一键导出对应的 DESIGN.md 文件。你把这个文件丢进代码仓库，后面的代码生成、页面迭代，视觉风格都不会跑偏。

现在生态也起来了。除了官方项目，还有 awesome-design-md 这样的社区仓库，已经逆向分析了七十多个知名品牌的视觉风格——Claude、Notion、Apple、Airbnb 这些都有，直接复制粘贴就能用。

另外像 getdesign.md 这种第三方聚合站，专门帮你浏览和搜索各种 DESIGN.md 文件，想找灵感的时候上去翻翻挺方便。

**写在最后**

用 AI 写代码绕不开一个问题：怎么把你脑子里那个"好设计"的标准，稳定地传给它。

代码层面，AGENTS.md 和 CLAUDE.md 已经给了答案。设计层面，DESIGN.md 现在把这块空白给补上了。门槛低到只需要一份 Markdown 文件，但效果立竿见影。

如果你也受够了 AI 生成的千篇一律的靛蓝按钮，不妨试试这个项目。花十分钟写一份 DESIGN.md，后面省下的返工时间绝对值回票价。

guthub地址：https://github.com/google-labs-code/design.md

