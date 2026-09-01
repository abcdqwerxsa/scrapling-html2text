# Cloudflare 甩出「临时账号」炸翻 Agent 开发圈：一行命令，AI 自己把代码扔到公网，零注册零登录！

**作者**: AGI社团
**发布时间**: 2026-06-24 06:44
**原文链接**: https://mp.weixin.qq.com/s/qNDuQXPZkw_vfc8U5X7W5A

---

2026 年 6 月 19 日，Cloudflare 悄悄上线了一个看起来很小的功能。

Wrangler CLI 新增了一个 flag：`--temporary`。

但就靠这个 flag，AI agent 从"写出代码"到"部署上线"之间最顽固的那堵墙，被直接击穿了。

以前 agent 帮你生成好 Worker 代码，到了部署这一步，它必须停下来求你——打开浏览器，登录账号，通过 MFA，复制 API token，在 60 秒内完成授权。后台运行的 agent 直接卡死。

现在不用了。

**wrangler deploy --temporary**

AI agent 只需跑这一行命令，Cloudflare 自动创建临时账号，自动完成 PoW 验证，自动部署 Worker，自动返回一个公开可访问的`*.workers.dev`URL。

整个过程没有人类介入。没有账号。没有 OAuth。没有 MFA。

部署完的 URL 在 60 分钟内可反复迭代、可随时 curl 验证。人类如果想保留，点一下 claim 链接接管账号和所有资源。不认领？60 分钟后自动删干净，零残留。

![Cloudflare 官方博客](https://r2.jeanjan.kdns.fr/pictures/img-50e34af301.jpeg)

▲ Cloudflare 官方博客开篇即明：agent 一碰到部署环节，就一头撞上为人类设计的高墙

## 一堵为人类设计的墙，卡死了 Agent 的最后一公里

Cloudflare 在官方博客里写了一句大实话：

> "The moment an agent needs to deploy something — it slams face-first into a wall built for humans."

「当 agent 需要部署东西的那一刻，它一头撞上了为人类建造的墙。」

这话不好听，但每一句都打在痛点上。

现在 AI 写代码已经很能打了。Claude、GPT-5.5 这些模型能在几秒内生成一个完整的 Worker 函数，逻辑清晰，类型完备，甚至能自己写测试。

**问题从来不在生成代码。**

问题在生成完之后。

传统 SaaS 的 onboarding 流，前提是人坐在屏幕前：打开浏览器 → OAuth 跳转 → 仪表盘页面 → API Keys 页面 → 生成 token → 复制粘贴回终端 → 60 秒内完成确认。对坐在电脑前的人类来说，也就是几分钟的事。

但对一个运行在后台、没有眼睛去扫描浏览器窗口的 AI agent 来说，**这就是死路** 。

Agent 要么卡在认证步骤等一个永远不会来的点击，要么直接放弃部署验证，只给你甩一个代码 diff 或 zip 文件，告诉你"代码写好了，你自己去部署吧"。

最后一公里，困住了整个流程。

## 一条命令，从零到 Live URL

> "wrangler deploy --temporary"

> 「这就是你的 AI agent 部署到 Cloudflare 所需的全部操作。」

![Simon Willison 实测博客](https://r2.jeanjan.kdns.fr/pictures/img-50e34af302.jpeg)

▲ Simon Willison 用自己的 agent 实测了整个流程，得出结论：开箱即用，完全管用

Cloudflare Workers 团队给 Wrangler CLI 加了一层智能引导。

当 agent 首次运行`wrangler deploy`且检测到本地没有任何登录凭证时，Wrangler 不会直接报错退出。它会主动提示：

> "To continue without logging in, rerun this command with`--temporary`."

Agent 解析这条输出，自动切换成`wrangler deploy --temporary`，接下来的事情全由 Cloudflare 后端接管：

  * 客户端自动完成 proof-of-work 验证（短暂延迟，但全程无需人类操作）
  * Cloudflare 分配一个临时 preview 账号，名称随机生成——比如 "Educated Celery"
  * 签发短时效 token
  * 部署 Worker bundle 到`*.workers.dev`
  * 返回 live URL + 一条敏感度等同于 API token 的 claim 链接

**60 分钟内可无限次 redeploy。** 改代码，重跑命令，同一个临时账号下复用凭证，不需要重新创建。

人类出来看一眼，觉得可以，打开 claim 链接 → 登录 Cloudflare → 一键认领账号、Worker、D1 数据库、KV 存储等全部绑定资源。不认领就全自动删掉，不留下任何孤儿账号。

完整生命周期：**创建 → 部署 → 迭代 → claim 或消亡。**

##  到底支持哪些产品？（不是 demo 玩具）

临时账号不是阉割版 playground。Cloudflare 给它开放了相当完整的产品接入：

  * **Workers** ：`workers.dev`部署
  * **Static Assets** ：最多 1000 文件，单文件 ≤5 MiB
  * **KV 存储** ：临时凭证读写
  * **D1** ：1 个数据库，单库 ≤100MB，总计 100MB
  * **Durable Objects** ：临时凭证操作
  * **Queues** ：最多 10 个队列
  * **Hyperdrive** ：最多 2 配置、10 连接
  * **SSL/TLS 证书** ：临时凭证签发

能写 Worker，能托管静态文件，能建数据库，能用消息队列。对一个想验证自己写的代码能不能在公网上跑起来的 agent 来说，完全够用。

生产和 CI/CD 自然还是建议走永久账号 + API token 的正规路径。但临时账号让"我只想试试看"这件事的成本从"先注册再说"降到了零。

![HN 社区讨论](https://r2.jeanjan.kdns.fr/pictures/img-50e34af303.jpeg)

▲ HN 上 245 分、147+ 条评论的热烈讨论。Simon Willison 在评论区惊呼 "Hot damn"，并贴出实测日志

## Agent UX 正在变成基础设施设计

如果只看功能本身，这不过是个 CLI flag。

但多个社区声音都抓到了同一个判断：**这个 primitive 的意义远超一行命令。**

开发者 @0x_codex 在帖子里把逻辑拆得很透：

> "`wrangler deploy --temporary`turns the first-run flow into a lease: deploy now, verify on a real live URL, iterate for up to 60 minutes, then the human can claim it or let it disappear."

「--temporary 把"首次运行"变成了一份有界租约：先部署，在真实 URL 上验证，60 分钟内迭代，然后人类认领或让它消失。」

**短生命周期 + 有界资源上限 + 显式 claim 路径 + 自动清理。** 这四个属性组合在一起，勾勒出了 agent-first 基础设施应有的形态。产品设计者要回答的核心问题变了——从"这个人怎么走完注册流程"切换到"一个没有身份的 agent 如何安全地获得临时能力"。

开发者 @stretchcloud 更进一步，把矛头指向了那个被很多人忽视的真正瓶颈：

> "The last mile of agent-built software is usually not the code. It is the moment the agent says: 'I built it, but now you need to log in, create an account, authorize a CLI, paste a token, and deploy it yourself.'"

> 「Agent 构建软件的最后一公里不在代码。藏在 agent 说出'我做好了，但你需要登录、创建账号、授权 CLI、粘贴 token、自己去部署'的那一刻。」

> "The hidden bottleneck is custody."

> 「隐藏的瓶颈是所有权归属。」

![Kyraa 详细拆解帖（分段1）](https://r2.jeanjan.kdns.fr/pictures/img-50e34af304.jpeg)![Kyraa 详细拆解帖（分段2）](https://r2.jeanjan.kdns.fr/pictures/img-50e34af305.jpeg)![Kyraa 详细拆解帖（分段3）](https://r2.jeanjan.kdns.fr/pictures/img-50e34af306.jpeg)![Kyraa 详细拆解帖（分段4）](https://r2.jeanjan.kdns.fr/pictures/img-50e34af307.jpeg)

▲ 来源帖的完整拆解：工作原理、支持产品、限制边界、为什么值得关注，四大板块一目了然

同样一个功能，从不同角度去看，得出了同一个结论——**agent 平台以后不会只被比较代码生成的质量，而会被比较它如何把运行中的软件干净地交还给人类或团队。**

##  不只一个 flag，Cloudflare 织了一张更大的网

如果把时间拉回两个月前，你会发现 Temporary Accounts 并不是孤立的一步棋。

**4 月底，Cloudflare 联合 Stripe 发布了生产级 agent 部署方案。** agent 可以自动创建 Cloudflare 永久账号、绑定 Stripe 订阅、购买域名、获取 API token，全程零复制粘贴。这是为"agent 帮人建站、开店、部署 SaaS"设计的付费生产路径。

6 月 19 日的 Temporary Accounts，补上了漏斗的另一端：**零摩擦试用的预览层。**

两条路合在一起，构成了一条清晰的 funnel：

  * **Temporary（试试看）** ：无账号、60 分钟、免费、自动清理。给 agent 一个可以扔东西的公网沙盒。
  * **Stripe Projects（正式用）** ：创建账号、绑定付费、买域名、长期运行。给 agent 一个可以收钱的正式环境。

从"无账号零成本试错"到"带预算的生产部署"，整个 agent deployment 的路径被从头到尾打通了。

这不是加个 flag 这么简单。这是在为 agent 重新设计 onboarding 漏斗——让 agent 走它擅长的路径——命令行、短生命周期、自动清理。硬套人类那套 OAuth-仪表盘-token 流程，只会把 agent 堵在第一步。

![Cloudflare 官方文档](https://r2.jeanjan.kdns.fr/pictures/img-50e34af308.jpeg)

▲ 官方文档完整列出了支持产品表格和限额细节——D1 100MB、Queues 最多 10 个、Static Assets 1000 文件、Hyperdrive 2 配置

## 不是没有风险

社区讨论中，有几类担忧被反复提及：

**滥用** ：恶意内容、phishing 页面、临时 bot 农场。60 分钟窗口既能限制危害存续时间，也足够让攻击者快速上线跑路。Cloudflare 的回应是 PoW 提高批量创建成本、速率限制控制洪水请求、claim 路径保留可追溯性。压得住还是压不住，需要时间验证。

**法律归属** ：agent 代签的 ToS 对最终用户有没有约束力？claim URL 一旦泄露，账号所有权也就没了。agent 时代的法律责任链条目前还是一片模糊地带。

**60 分钟不够** ：对复杂原型和长周期构建来说太短。目前不可延长，也没有暂停/恢复机制。

**交互式确认** ：`type yes`这个 ToS 确认步骤，对纯自动化流程来说仍是小摩擦。

但即使有这些问题，社区的整体判断倾向乐观——**先把门槛降到零，再逐步加固护栏，这种顺序通常比反过来有效。**

##  独立开发者的第一手验证

Simon Willison 在 6 月 21 日亲自下场实测。

他用 GPT-5.5 + Codex Desktop 让 agent 构建了一个 HTTP redirect resolver 工具，然后用`npx wrangler deploy --temporary`部署。

结果：**"The temporary deployment worked as advertised."** 「临时部署完全按文档描述工作。」

Agent 创建的临时账号名叫 "Educated Celery"，Worker 的完整 URL 是`https://cloudflare-redirect-resolver.educated-celery.workers.dev`。Claim 页面顶部挂着醒目红条倒计时，账号名、资源列表、蓝色 "Claim Account" 按钮一目了然。

他还专门强调了一条很多人会忽视的价值点：**这个功能不是只给 agent 用的。** 免费、可丢弃的 live scratch 环境对 PR preview、代码审查、协作调试都是极好的工具。你不需要创建任何东西，跑一条命令就给队友扔一个能访问的链接。

## 历史坐标里的定位

把 Cloudflare 这件事放进一个更长的时间线里看，脉络会更清楚。

Heroku 做了 review apps，Netlify 做了 deploy previews，Vercel 把 preview URL 做进了 Git 工作流。

但它们都有一个共同前提：**你得先有个账号。**

Cloudflare 做的事，是把 preview 这个概念往下再推了一层——推到 CLI 和平台层，推到了"连账号都不需要"的极端。**这层抽象对 agent 来说，属于必需品级别。**

如果让一个没有身份的 AI agent 去注册 Netlify 账号，填邮箱、收验证码、绑 GitHub、选仓库模板……这套流程走完，agent 早就迷失在几十个重定向之间了。而`wrangler deploy --temporary`的开销，只是一次命令执行加上几秒 PoW 计算。

用更少的步骤，得到更直接的结果。这正是 agent-friendly 基础设施的基本特征。

> "Agent UX is becoming infrastructure design, not just chatbot design."

@0x_codex 的这句总结被转发了无数遍。它的意思是：做 agent 产品不能只想着怎么让对话更好看、回复更聪明，还要想清楚**你的平台在 agent 触达的那一刻，给不给它一个可以操作的原语。**

Cloudflare 给了。

## 小结

Cloudflare Temporary Accounts 没有解决 agent 部署的所有问题——生产级 billing 控制、长期身份管理、跨平台编排这些课题仍然摆在前面。

但它做了一个之前没人做的事：**让 agent 从生成代码到拿到 live URL 这件事，第一次变成了一条命令、零人工干预的闭环。**

60 分钟免费窗口。自动创建账号。自动清理。随时认领。

这个模式一旦被验证有效，可以预见会有一批平台跟进——GitHub、Vercel、Netlify、AWS、GCP——它们迟早要回答一个问题：**当调用你 API 的是一个无法通过浏览器登录的 agent（而非坐在电脑前的人类），你的产品还可用吗？**

Cloudflare 先答了。

—

