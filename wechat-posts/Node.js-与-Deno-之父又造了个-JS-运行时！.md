# Node.js 与 Deno 之父又造了个 JS 运行时！

**作者**: Nodejs技术栈
**发布时间**: 2026-08-07 08:00
**原文链接**: https://mp.weixin.qq.com/s/VXn4ywBOi39Krgue25rskA

---

Ryan Dahl 曾告诉自己，再也不写新的 JavaScript 运行时了。

![Ryan Dahl 曾表示不再编写新的 JavaScript 运行时](https://r2.jeanjan.kdns.fr/pictures/img-648408df01.png)

然后，他又写了一个。

这次的新项目叫 **celld** 。它不是 Node.js 3.0，也不是另一个 Deno，而是一个开源、自托管的分布式运行时，目标是把 Cloudflare Workers 和 Durable Objects 搬到开发者自己的机器上。

![Ryan Dahl 发布 celld](https://r2.jeanjan.kdns.fr/pictures/img-648408df02.png)

Ryan Dahl 为这个项目断断续续做了一年多。他说，直到认真研究确定性仿真测试后，许多难题才逐渐解开。

![Ryan Dahl 讲述 celld 的开发过程](https://r2.jeanjan.kdns.fr/pictures/img-648408df03.png)

我看到 celld 的技术组合时，感觉很像 Ryan Dahl 一贯的风格：**V8、SQLite、对象存储和 Rust 异步运行时，拼成一个安装后就能跑的单文件程序。**

这次他盯上的，是后端开发中最难伺候的一类问题：有状态服务。

## 一个“对象”，就是一台带 SQLite 的小服务器

聊天室、协作文档、游戏房间、用户会话、AI Agent，这些场景都有一个共同点：请求不只是算完就走，它们还要记住状态，并处理并发修改。

传统方案通常是无状态服务加共享数据库。服务实例可以横向扩容，但并发控制、热点数据、连接管理和故障恢复，最后都压到数据库与周边基础设施上。

celld 采用了 Durable Objects 的思路。一个 **cell** 可以对应一个用户、一份文档、一个聊天室或一个 AI Agent。每个 cell 都有自己的名字、JavaScript 执行环境和私有 SQLite 数据库。

同一个 cell 同一时刻只有一个写入者，请求在一条线程上执行。这样一来，很多分布式锁和数据库争用问题，在编程模型这一层就被绕开了。

![celld 官网展示的产品定位与安装方式](https://r2.jeanjan.kdns.fr/pictures/img-648408df04.png)

官方仓库里的计数器示例只有几十行。Worker 根据名字找到 `room-42`，再把请求交给对应的 Durable Object：
```

export class Counter {  
  constructor(state, env) { this.state = state; }  
  
  async fetch(request) {  
    let n = (await this.state.storage.get("n")) ?? 0;  
    n++;  
    await this.state.storage.put("n", n);  
    return new Response(JSON.stringify({ n, url: request.url }));  
  }  
}  
  
export default {  
  async fetch(request, env) {  
    const id = env.COUNTER.idFromName("room-42");  
    return env.COUNTER.get(id).fetch(request);  
  }  
};  

```

如果你写过 Cloudflare Workers 和 Durable Objects，这套 API 几乎不用重新学习。celld 接受 Wrangler 项目，支持 module Workers、Durable Object 绑定、静态资源、WebSocket、alarm 和大部分 JS RPC。

这也是它最聪明的地方。celld 没有发明一套新框架，而是直接接住已经存在的开发模型，让一部分应用可以在 Cloudflare 与自建环境之间迁移。

## 真正有意思的，是它把 S3 当成协调中心

celld 的主机内嵌 V8，负责运行 JavaScript；每个 cell 用 SQLite 保存状态；LTX 记录 SQLite 的增量变化；Tokio 负责异步 I/O。整个集群共同依赖一个兼容 S3 的对象存储桶。

这个存储桶不只存数据，还保存部署产物、cell 状态、所有权记录、主机租约和主机间认证信息。

当请求落到某个 cell，主机会通过对象存储的原子比较交换操作争取所有权。一个 cell 在同一时期只归一台主机。主机宕机或 cell 被唤醒时，新主机从存储桶恢复 SQLite 数据并继续处理请求。

这里没有独立控制平面，也没有额外的共识服务。新机器指向同一个存储桶，就能加入集群。

代价也很明确：**一次持久写入至少要等待一次对象存储往返。** celld 会等数据进入存储桶后才向客户端确认，所以官方把恢复点目标写成 RPO=0，也就是已经确认的写入不能因为主机宕机而丢失。

这套选择更偏向数据安全与运维简化，而不是追求每次写入的极限低延迟。对象存储的尾延迟、限流和网络状态，都会进入你的写入链路。

## 休眠后接近零成本，规模越大越有吸引力

Durable Objects 的魅力之一，是你可以创建数量庞大的细粒度对象，而不必让它们一直占着内存。

celld 也会把空闲 cell 移出内存。没有主机持有的 cell，只剩对象存储中的数据；带有可休眠 WebSocket 的 cell 还能保留连接，等下一次事件到来再恢复。

官方给出的估算是，一台 8 GB 内存的机器可以容纳约 1000 个常驻 cell，单个常驻 cell 每月约 0.05 美元。休眠 cell 主要承担对象存储成本。

![celld 官方给出的规模成本对比](https://r2.jeanjan.kdns.fr/pictures/img-648408df05.png)

这些数字不能脱离测试条件理解。机器价格、对象存储请求费、跨区流量、工作集大小和写入频率，都会改变最终账单。celld 的优势不是让所有应用自动便宜，而是允许大量低活跃对象休眠，把常驻资源留给正在工作的那部分对象。

最新测试文档还给出了一组更接近真实集群的数据：10 台 4 vCPU、8 GB 内存的机器承载了 10000 个常驻 cell 和 20000 条并发 WebSocket 连接。停止其中两台后，在预留容量充足的前提下，所有 cell 的数据在尾部约 11 秒内重新可用。

官方也测得，常驻 cell 的本地请求 p50 约 1.1 ms、p99 约 7 ms。这类热请求不访问对象存储，冷启动和持久写入才需要走存储桶。

![celld 首发时公布的关键指标](https://r2.jeanjan.kdns.fr/pictures/img-648408df06.png)

## 先别急着把生产系统搬过去

celld 的架构很漂亮，但它目前还是 alpha。

它运行的是 Workers 与 Durable Objects 的部分能力，不是完整复刻 Cloudflare 平台。KV、R2、Workers AI、Vectorize、定时触发、自定义域名和 TLS 终止都不在当前能力范围内，Node.js API 也只实现了一部分。

运维侧同样有明显边界：

  * 一个集群目前只运行一个应用，没有多租户调度器和全局放置层。
  * 主机间协议带认证，但不负责 TLS 加密，需要部署在可信私网或加密网络中。
  * 存储桶凭证相当于集群管理员权限，泄露后影响的不只是数据。
  * Windows 暂不支持，Intel Mac 没有预编译版本。
  * 自动更新、托管入口和成熟的压力调度策略还没有补齐。

不过，Ryan Dahl 对可靠性测试下了不少功夫。项目会把相同程序分别跑在 workerd 与 celld 上比较输出，还用确定性模拟制造租约竞争、时钟漂移、主机崩溃和对象存储延迟。线上测试集群也会直接杀死主机进程、删除本地数据库，再检查已确认写入能否完整恢复。

这不能替代长期生产验证，但至少说明团队知道分布式系统最危险的地方不是 Demo 能不能跑，而是故障发生在最糟糕的那一瞬间，系统还能不能守住承诺。

## Ryan Dahl 又在重新划边界

Node.js 把服务器端 JavaScript 变成主流，Deno 试图重做 JavaScript 工具链。celld 这次想改变的，是应用代码与云平台之间的边界。

它最值得开发者关注的地方，不是“又一个 JS 运行时”，而是把一种成熟的有状态编程模型，变成可以装在自己机器上的开源程序。代码仍然写 Workers 和 Durable Objects，数据放在自己控制的存储桶里，计算跑在自己的服务器上。

如果 celld 能把兼容面、调度、安全和运维工具逐步补齐，它可能会成为自托管实时应用、协作服务和 AI Agent 基础设施里很有竞争力的一块拼图。

现在把核心生产系统交给它还太早，但这个方向，确实值得前端和 Node.js 开发者提前看懂。

