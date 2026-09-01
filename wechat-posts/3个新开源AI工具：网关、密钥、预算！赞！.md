# 3个新开源AI工具：网关、密钥、预算！赞！

**作者**: 码农闲谈AI
**发布时间**: 2026-07-28 07:00
**原文链接**: https://mp.weixin.qq.com/s/akB3f2Dla9ZioBTbFDb1YA

---

推荐阅读：

[三个工具！给AI编程助手装安全护栏！很不错！](https://mp.weixin.qq.com/s?__biz=MzI0NTI0MTg1NQ==&mid=2247489167&idx=1&sn=a7fcaa9dccf17120922c72924b3c8e33&scene=21#wechat_redirect)  

  

最近 AI Agent 越来越火，但真要在项目里用起来，麻烦事一堆：模型 API 各家格式不一样、密钥不敢随便给 agent、调用费一不小心就爆表。今天翻 GitHub 看到三个刚冒头的基础设施工具，正好对应这三个痛点。

![](https://r2.jeanjan.kdns.fr/pictures/img-cc16bc1b01.png)

## OmniRoute：一个端点接 500+ 模型

现在写代码离不开 Claude、GPT、DeepSeek、Kimi 换着用。问题是每家 API 格式不同，Cursor 配一个、Claude Code 配一个，密钥还散落各地。

**OmniRoute** 就是个本地 AI 网关。装完后你的工具统一指向 `http://localhost:20128/v1`，它背后帮你对接了 290 多家提供商、500 多个模型。Claude Code、Codex、Cursor、Cline 这些都能直接连。

它最有用的是**自动降级** 。比如你先走 Claude Pro 订阅配额，用完了自动切到 API Key，再切到便宜模型，最后走免费模型。不用你手动改配置，代码写着写着不会突然断掉。

另外它内置了 RTK + Caveman 的 token 压缩，官方说能省 15% 到 95% 的 token。还支持 MCP 和 A2A 协议，想做 agent 工作流也能用上。路由策略也很全，priority、round-robin、least-used、cost-optimized 等十几种，你可以按自己的需求排优先级。

![](https://r2.jeanjan.kdns.fr/pictures/img-cc16bc1b02.png)

安装不复杂，有 npm 包也有 Docker 镜像，本地跑起来后打开 `http://localhost:20128` 就能看到仪表盘。MIT 协议、完全免费，密钥存在自己机器上。对不想被某一家模型绑死的开发者来说，这个比直接买各家会员划算多了。

## OneCLI：给 AI Agent 发张"门禁卡"

前阵子有个事传得挺广：Meta 的 AI 安全负责人把邮箱权限给了 OpenClaw，结果 agent 把她邮件批量删了，说"停"都不停。这种事故说到底是密钥和权限没隔离。

**OneCLI** 解决的就是这个问题。它是一个开源凭证网关，放在 agent 和外部 API 中间。你把真实密钥存进 OneCLI 的加密仓库，给 agent 一个占位符密钥。agent 发请求时，OneCLI 在网络层自动把假密钥换成真的，agent 从头到尾看不到真密钥。

![](https://r2.jeanjan.kdns.fr/pictures/img-cc16bc1b03.png)

更关键的是它能做策略控制：哪些接口能调、哪些路径禁止访问、每个 agent 每分钟能调多少次，甚至哪些操作需要先人工审批，都在网关层强制执行。规则不是写在 prompt 里靠 agent"自觉"，而是代理层面直接拦住。

部署也简单，一条 `docker run` 就起来，带 Web 管理面板。支持 Cursor、n8n、Dify、OpenHands 这些主流工具。团队里如果有多个 agent 在跑，这个比把密钥写进环境变量安全太多。离职换密钥时也不用满世界更新，改一处就行。

## llm-budget-cap：防止 AI 账单失控

用 LLM API 最怕的不是慢，是半夜一个死循环把额度烧光。自己写个计数器吧，并发一上来还有竞态条件，两个请求同时判断"没超"，结果都通过了。

**llm-budget-cap** 把 `INCR` 和 `PEXPIRE` 封进同一个 Redis Lua 脚本里原子执行，从根本上避免这个问题。用法就几行：

```typescript

const cap = new BudgetCap({

redis,

key: 'gemini:daily',

limit: 500,

});

const decision = await cap.checkAndIncrement();

if (!decision.allowed) {

return res.status(429).json({ error: 'Daily AI budget exhausted.' });

}

```

![](https://r2.jeanjan.kdns.fr/pictures/img-cc16bc1b04.png)

可以按用户、按租户、按 IP 分别设上限，窗口也能自定义。Redis 挂了默认放行，也可以配置成故障关闭。零第三方依赖，MIT 协议。整个库就一个类、一个方法，代码很短，出了问题也好排查。

作者说已经在生产环境用了三次这个模式，现在把它抽成独立包。做 AI 应用的团队，上线前加一个这样的预算兜底，心里踏实很多。毕竟模型调用可以降级，账单爆了可没法撤销。

这三个工具分别解决模型接入、密钥安全和费用控制，正好是现在把 AI Agent 放进生产环境绕不开的三个环节。开源、免费、能本地跑，值得先 star 起来，等真正遇到对应问题时再翻出来用。

  

[1.9K Star！当ai成为了你的任务管家！太香了！](https://mp.weixin.qq.com/s?__biz=MzI0NTI0MTg1NQ==&mid=2247488898&idx=1&sn=5031584e3765294a7494e67b61f4eb10&scene=21#wechat_redirect)  

[好用！3个非常给力的工具！五星好评！](https://mp.weixin.qq.com/s?__biz=MzI0NTI0MTg1NQ==&mid=2247488897&idx=1&sn=5a5be666ee10ab6ab1912bd4e08d5e7d&scene=21#wechat_redirect)  

[9.8K Star！一个非常有趣的开源项目！好玩好用！](https://mp.weixin.qq.com/s?__biz=MzI0NTI0MTg1NQ==&mid=2247488895&idx=1&sn=c2b037236bb716bac3be6d9dd56476a1&scene=21#wechat_redirect)  

[推荐：3个非常好用的工具！太香了！](https://mp.weixin.qq.com/s?__biz=MzI0NTI0MTg1NQ==&mid=2247488872&idx=1&sn=40e84ee6f3a4a94a399472d3e16f04a8&scene=21#wechat_redirect)  

[8.5K Star！拖拽组件即可搭建应用！接单神器！](https://mp.weixin.qq.com/s?__biz=MzI0NTI0MTg1NQ==&mid=2247488586&idx=1&sn=56126749b0df2d42054d589ac59f8bdc&scene=21#wechat_redirect)

  


