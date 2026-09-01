# Cloudflare发布免费的AI云端浏览器

**作者**: 字节笔记本
**发布时间**: 2026-08-07 21:20
**原文链接**: https://mp.weixin.qq.com/s/tg0oFE35AEsP7JcQIpWnXw

---

Cloudflare 发布了 Kitesurf，一款只为 AI 代理而生的浏览器。

![](https://r2.jeanjan.kdns.fr/pictures/img-18d90aba01.png)

Kitesurf运行在 Cloudflare Workers运行环境当中，专门服务于 AI 代理这一类使用者，现在开放免费测试。

没有使用传统的Chromium内核，Kitesurf是全部从零写的浏览器引擎。

摆脱了这个沉重的枷锁，可以让 AI 代理能够以更低的内存和计算开销完成截图、抓取 HTML 这类常见任务。

整套系统拆成三个核心组件如图：

![](https://r2.jeanjan.kdns.fr/pictures/img-18d90aba02.png)

Cloudflare自研浏览器这件事其实已经好几年了，也积累了非常多的相关的经验，这次之所以要从头开始写，是因为Chromium 这类浏览器其实是为人设计的，标签页、主题、扩展、跨设备同步，这些对 AI 代理毫无意义，给每个代理配一个独立浏览器实例的成本高得离谱。

同时，Agent面对的安全模型也和人类用户不同，提示词注入这类问题成了新的优先级。

得益于Rust 写的无依赖无头引擎 obscura，性能非常不错，官方给的对比图如下：

![](https://r2.jeanjan.kdns.fr/pictures/img-18d90aba03.png)

使用方式如下：

第一个是公共 Playground：

https://kitesurf.cloudflare.app/

打开 Playground，输入目标 URL就可以查看 Kitesurf 渲染结果：

![](https://r2.jeanjan.kdns.fr/pictures/img-18d90aba04.png)

提供了内嵌 Chrome DevTools，可以实时地查看DOM信息、网络请求以及调试的输出。

试了一个打开公众号的地址，依然显示环境异常。

![](https://r2.jeanjan.kdns.fr/pictures/img-18d90aba05.png)

第二种是Quick Actions。

需要在CF的官网获取一下CF token以及用户ID，这种适合编程式的一次性任务，像是截图、抽 HTML、PDF、Markdown 等。

以截图为例
```

curl -X POST \  
  "https://api.cloudflare.com/client/v4/accounts/${CF_ACCOUNT_ID}/browser-run/screenshot?browser=kitesurf" \  
  -H "Authorization: Bearer ${CF_API_TOKEN}" \  
  -H "Content-Type: application/json" \  
  -d '{"url":"https://example.com"}' \  
  --output screenshot.png
```

成功后得到 `screenshot.png`。

也可以用来提取 HTML：
```

curl -X POST \  
  "https://api.cloudflare.com/client/v4/accounts/${CF_ACCOUNT_ID}/browser-run/content?browser=kitesurf" \  
  -H "Authorization: Bearer ${CF_API_TOKEN}" \  
  -H "Content-Type: application/json" \  
  -d '{"url":"https://example.com"}'
```

其他的使用方式，比如CDP协议或者是MCP可以参照文档：

https://developers.cloudflare.com/browser-run/quick-actions/

团队公布的一组基准数据显示，在截图和 HTML 抓取这两个常见任务上，Kitesurf 的 CPU 消耗只有 Chromium 的三分之一左右，内存消耗低到五到七分之一。

兼容性上，Kitesurf 已经能正确渲染 TodoMVC 的各种框架实现、维基百科、Hacker News，以及 Cloudflare 自己的博客和控制台。

但它还处理不了视频播放、WebGL、需要真实 TLS 指纹的反爬验证，以及长时间保持登录状态的场景，遇到这些情况官方建议退回到 Browser Run 默认的 Chromium 方案。

团队接下来的重点是扩展 CDP 协议覆盖范围、提升截图和 PDF 的还原精度、继续刷 WPT 测试通过率，并计划在准备好之后把 Kitesurf 开源，让用户可以在自己的账号里部署一份。

从产品逻辑上看，这其实是 Cloudflare 把 Browser Run 这条业务线进一步做细分的动作，用一个更轻量的引擎去覆盖那些不需要像素级还原的批量抓取和截图场景，把 Chromium 留给真正需要完整浏览器能力的任务。

对于经常写抓取脚本或者搭代理工作流的开发者，这算是多了一个成本更低的选项。

虽然目前Agent的访问网页的数量已经超过了人类，但是各个平台之间访问的壁垒还是存在，要正常浏览依然需要采取各种Hack手段，一套全平台Agent共享，类似于Oauth2授权机制可能会比Kitesurf更有意义。

