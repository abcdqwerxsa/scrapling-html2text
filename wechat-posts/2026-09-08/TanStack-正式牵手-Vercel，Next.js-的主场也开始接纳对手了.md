# TanStack 正式牵手 Vercel，Next.js 的主场也开始接纳对手了

**作者**: Nodejs技术栈
**发布时间**: 2026-09-02 08:07
**原文链接**: https://mp.weixin.qq.com/s/ZUQxkPxvZ7uXqdliwAlATg

---

![TanStack 与 Vercel 正式合作](https://r2.jeanjan.kdns.fr/pictures/img-54bf159801.png)

TanStack 正式牵手 Vercel，Next.js 的主场也开始接纳对手了

TanStack 刚刚宣布与 Vercel 展开合作。双方准备把 Vercel 做成 TanStack Start 的一等运行平台，部署、运行和后续支持都会继续补强。

![TanStack 宣布与 Vercel 展开合作](https://r2.jeanjan.kdns.fr/pictures/img-54bf159802.png)

这条消息乍看很顺理成章。Vercel 做部署，TanStack Start 做全栈 React，双方各取所需。

回看时间线，Vercel 早在 2025 年 11 月就加入了 TanStack Start 自动识别，今年 6 月又专门写过一篇完整的框架介绍。到了 9 月 1 日，Vercel 再发布新的部署指南，第二天 TanStack 才对外宣布正式合作。

## TanStack Start 到底在抢谁的用户

如果你已经在用 TanStack Query 或 TanStack Router，Start 很容易勾起兴趣。它直接把 Router 扩成了一套全栈框架，补上完整文档 SSR、流式渲染、Server Functions、中间件以及前后端构建。

它和 Next.js 的区别也很鲜明。Next.js App Router 把 React Server Components 和服务端渲染放在中心位置，TanStack Start 更依赖路由树组织应用。URL 参数、搜索状态、loader 数据和服务端函数都沿着路由保持类型推导。

这套做法很适合后台、仪表盘、搜索页和交互复杂的业务系统。页面状态大量写进 URL 时，TanStack Router 那套类型安全会省掉不少手工校验。

TanStack Start 目前仍处在 RC 阶段。官方说功能已经完整，API 也趋于稳定，Bug 和生态成熟度还需要继续磨。它已经具备挑战主流框架的完整形态，离“闭眼上生产”仍有一段现实距离。

## 部署到 Vercel 现在有多麻烦

现有项目先装 Nitro。
```

pnpm i nitro  

```

随后在 `vite.config.ts` 里注册 `nitro()`。
```

import { tanstackStart } from '@tanstack/react-start/plugin/vite'  
import { defineConfig } from 'vite'  
import viteReact from '@vitejs/plugin-react'  
import { nitro } from 'nitro/vite'  
  
export default defineConfig({  
  plugins: [tanstackStart(), nitro(), viteReact()],  
})  

```

做到这里，Vercel 会自动识别 TanStack Start 和 Nitro，一般不用再手填构建命令和输出目录。项目可以从 Git 仓库导入，也可以直接运行 `vercel`。连接 Git 后，分支提交会生成预览部署，主分支提交进入生产部署。

TanStack Start 的服务端代码会由 Nitro 编译成 Vercel Functions，默认运行在 Fluid compute 上。流量上来时自动扩，空闲时也不用养着一台常驻服务器。

这套部署流程已经很短了。它和大家熟悉的 Next.js 部署体验还没有完全拉平，最容易出问题的地方主要有两个。

一个是 monorepo 或迁移项目里的框架识别。Vercel 没有自动选中 TanStack Start 时，需要在项目设置里手动指定，或者在 `vercel.json` 写入框架名称。
```

{  
  "framework": "tanstack-start"  
}  

```

另一个是环境变量。带 `VITE_` 前缀的变量会进入浏览器代码，数据库凭据和私有 API Key 不能这样写。服务端函数读取的秘密变量应该保留普通名称，通过 `process.env` 使用。

这些都属于能在文档里讲清楚的工程问题。双方合作以后，开发者更期待的是新版本适配速度、框架识别稳定性和线上问题由谁接住。

## Vercel 为什么愿意给 Next.js 的对手铺路

Vercel 当然希望 Next.js 继续领先。可一家云平台只接住自家框架，生意会被框架边界卡住。

Vercel 官网目前列出的框架已经包括 Nuxt、SvelteKit、FastAPI 和 Nitro，TanStack Start 也在其中。开发者继续使用熟悉的 Git 预览、Functions、日志和回滚能力，Vercel 则获得更多工作负载。

Vercel 在今年 6 月介绍 TanStack Start 时写得很直接。应用无需改造成 Next.js，保留原来的路由优先架构，也能部署到同一套平台设施上。

这对 Vercel 很划算。一个团队可能用 Next.js 做内容站，用 TanStack Start 做登录后的复杂应用。只要两个项目最后都留在 Vercel，框架由谁维护就没那么要紧。

TanStack 也需要这样一条省心的生产路径。框架文档写得再漂亮，部署时总要改适配器、猜输出目录、排查 SSR 路由，团队就会退回更熟悉的方案。Vercel 能把这部分摩擦压下去，TanStack Start 才更容易进入真实项目。

## 正式合作会不会把 TanStack 绑在 Vercel 上

目前看不到这种迹象。

TanStack Start 的构建依然基于 Vite 或 Rsbuild，Nitro 负责把服务端输出适配到不同运行环境。官方托管文档同时列着 Cloudflare Workers、Netlify、Railway、Node.js 和 Docker。换平台时，路由和 Server Functions 不需要跟着重写，主要变化落在部署插件和平台服务上。

Vercel 现在是 TanStack 的 Gold Partner。这个身份意味着双方会投入资源改善支持，并不改变 TanStack Start 强调的可移植性。

开发者也该保留一点耐心。TanStack Start 仍是 RC，教程数量、第三方集成、线上案例和疑难问题答案都比 Next.js 少。内容型网站依赖成熟的 RSC、图片优化和 ISR 流程时，Next.js 仍然省事。业务状态复杂、路由类型要求高的应用，TanStack Start 才更容易发挥长处。

