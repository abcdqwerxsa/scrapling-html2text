# 把 Kubernetes ConfigMap 当实时状态存储用？Watch API 了解一下

**作者**: 云原生AI视界
**发布时间**: 2026-07-27 07:01
**原文链接**: https://mp.weixin.qq.com/s/G3cKbp8WuQKYUVu5fN2ejg

---

# 把 Kubernetes ConfigMap 当实时状态存储用？Watch API 了解一下

![cover](https://r2.jeanjan.kdns.fr/pictures/img-11cd22f601.jpeg)

> 如果你的服务能在配置变更的瞬间做出反应——不需要消息代理，不需要轮询，不需要重启——会怎样？

大多数团队把 ConfigMap 当作静态配置：启动时加载，挂载到 Pod 里，然后就忘了。但 Kubernetes API 内置了 watch 流——每一次 ConfigMap 创建、更新或删除，都是服务器**推送** 的事件，而不是定时轮询获取的。

这篇文章用一个 Python 小示例，演示如何将这个流变成一个实时的发布/订阅系统。多个客户端各做各的事，在 ConfigMap 变更的瞬间收到通知——只用 Python 标准 asyncio 原语。

## 开始之前

你需要：

  * Python 3.11+，用 uv 管理依赖
  * 一个运行中的 Kubernetes 集群——orbstack、k3s 或 Docker Desktop 都行
  * 配置好的 kubectl 并指向你的集群

唯一重要的非标准库依赖是 kr8s[1]——一个 async-first 的 Kubernetes Python 客户端。它将 watch API 暴露为 async generator，自然地融入 asyncio 代码。没有线程，没有阻塞调用。

完整源码：**github[2]**

## 静态配置的问题

标准的 ConfigMap 故事是这样的：
```

Pod 启动 → 读取 ConfigMap → 使用值 → ConfigMap 变更 → 什么都没发生  

```

你的服务还拿着旧值。要获取变更要么重启 Pod，要么定时轮询 API。两者都不好。轮询浪费资源且延迟取决于轮询间隔。Pod 重启是破坏性的且慢。

Kubernetes API 已经内置了答案——你只需要用它。

## 用 Watch，不要轮询

Kubernetes API server 不仅处理请求——它可以流式推送事件。当你打开一个 watch 连接，它会保持连接，服务器在有变更时推送给你。这正是 `kubectl get pods -w` 底层的机制。

我们的示例位于这个流和应用的其余部分之间：
```

Kubernetes API  
      │  
      │  ADDED / MODIFIED / DELETED  ← 服务器推送  
      ▼  
   Watcher  （一个长连接）  
      │  
      ▼  
  Notifier  （fan-out 分发器）  
      │  
      ├──► Logger Client    — 记录每个事件  
      ├──► Counter Client   — 统计事件总数  
      └──► Filter Client    — 只响应 ADDED  

```

## 打开流

kr8s 让这个流看起来就像普通的 Python 循环。调用 `.watch()` 并带上 label selector 来限定你关心的 ConfigMap：
```

async for event, configmap in api.watch(ConfigMap.kind, label_selector="app=demo"):  
    # event → "ADDED", "MODIFIED" 或 "DELETED"  
    # configmap → 完整对象，有 .name, .data, .labels 等  
    ...  

```

label selector 很重要。没有它你会收到 namespace 中每个 ConfigMap 的事件——包括你完全不关心的系统组件创建的。限定为 `app=demo` 意味着你只看到显式选择参与的那些 ConfigMap。

## 保持连接存活

长 HTTP 连接会断开。watch 流会超时、被 API server 重置，或因网络问题关闭。解决方案是把循环包在 `while True` 中，失败时重连：
```

while True:  
    try:  
        async with ConfigMapManager() as manager:  
            async for event, configmap in manager.watch(selector="app=demo"):  
                await notifier.notify({  
                    "event": event,  
                    "name": configmap.name,  
                    "data": configmap.data,  
                })  
    except httpx.ReadError:  
        logger.warning("Watch stream dropped, reconnecting...")  
        await asyncio.sleep(0.5)  

```

当流断开时，内层的 `async for` 抛出 `httpx.ReadError`。外层循环捕获它，等待半秒，然后打开一个新连接。等待队列的客户端永远不知道——它们继续等下去。

**失败时重试整个生成器** ——这个模式值得在任何长 watch 循环中加入工具箱。

## Fan-out 问题

单个 Kubernetes 事件需要同时到达所有客户端。机制是 `asyncio.Queue`——每个客户端订阅 `Notifier` 并获得自己的私有队列。事件到达时，`notify()` 在一次遍历中将副本放入每个队列：
```

class Notifier:  
    def __init__(self):  
        self._subscribers: list[asyncio.Queue] = []  
        self._lock = asyncio.Lock()  
  
    async def subscribe(self) -> asyncio.Queue:  
        q = asyncio.Queue()  
        async with self._lock:  
            self._subscribers.append(q)  
        return q  
  
    async def unsubscribe(self, q) -> None:  
        async with self._lock:  
            try:  
                self._subscribers.remove(q)  
            except ValueError:  
                pass  
  
    async def notify(self, event: dict) -> None:  
        async with self._lock:  
            for q in self._subscribers:  
                await q.put(event)  

```

`asyncio.Lock` 是承重的。客户端可以在任何时候订阅或断开——包括 `notify()` 正在遍历列表时。锁确保订阅列表不会在迭代中途被修改。

每个事件的处理流程：
```

Kubernetes 推送 MODIFIED  
        │  
        ▼  
  notifier.notify(event) 被调用  
        │  
        ├──► Queue A ← event   [Logger:  阻塞 → 现在解锁]  
        ├──► Queue B ← event   [Counter: 阻塞 → 现在解锁]  
        └──► Queue C ← event   [Filter:  阻塞 → 检查 event type]  

```

三个客户端独立运行。慢速客户端处理事件不会延迟其他客户端。

## 三种客户端，三种反应

Logger 无条件接收每个事件。Counter 维护跨事件的状态——它不关心变了什么，只关心变了多少次。Filter 是有选择性的——只对 ADDED 做出反应。

三个行为。三种反应。都由同一个事件分发触发。在真实系统中，这些可能是缓存失效器、指标记录器和功能开关重载器——各自维护自己视角的集群状态，不知道对方存在。

三个客户端共享一个到 Kubernetes 的 watch 连接。Fan-out 很廉价。连接不是。

## 这是一个状态存储

传统的状态存储——Redis、etcd、关系数据库——让你写一个值，之后可以读回来。ConfigMap 通过 watch API 增加的，是**订阅** 变更的能力。你不只是读当前值；你每次它变动都会收到通知。

这就是一个响应式状态存储。而且每个 Kubernetes 集群都附赠了一个。

ConfigMap 的 `data` 字段是状态，watch 流是变更源，Notifier 是连接变更源和任意数量观察者的 fan-out 层。

真实世界中的客户端行为，对应这个模式的有：收到 MODIFIED 时重载内存配置、任何事件时使本地缓存失效、递增计数器、对意外的 DELETED 发出告警、收到 MODIFIED 时重算路由表。

## 与 Redis 和 Kafka 比较

ConfigMap watch 需要**零额外基础设施** 。访问控制来自已有 Kubernetes RBAC。状态跨重启持久化，任何时候都可以用一行 `kubectl get configmap -l app=demo` 检查。没有需要部署、保护或维护的新东西。

Redis Pub/Sub 适用于需要亚毫秒延迟、高事件频率或集群外消费者的场景。

Kafka 适用于需要持久事件历史、重放或跨数据中心 fan-out 的场景。

对于**集群内的配置传播** ——低频但重要——ConfigMap 已经是正确的工具。Watch API 只是让它们变成响应式的。

> **只用于轻量级、非关键、低频的用例。**

## 为什么 asyncio 是正确工具

整个 demo 是单线程的。没有线程池、没有子进程、没有外部并发原语。Asyncio 协作式多任务自然适配，因为系统中的每个角色大部分时间在**等待** ：watcher 等待来自 Kubernetes API 的下一个事件；每个客户端等待队列中的下一个项。

`kr8s` 围绕这个模型设计。它的 async generator 不产生线程——它们 `await` 底层 HTTP 连接，在事件之间将控制权交回事件循环。这就是为什么整个组合如此干净。

## 底层的模式

去掉 Kubernetes 剩下的就是：
```

长推送流  (K8s watch、WebSocket、gRPC stream、DB change feed...)  
        │  
        ▼  
  重连循环  (包装生成器，失败时重试)  
        │  
        ▼  
  fan-out notifier  (每个观察者一个 asyncio.Queue，asyncio.Lock 保证安全)  
        │  
        ├──► observer A  (做一件事)  
        ├──► observer B  (做另一件事)  
        └──► observer C  (过滤，可能忽略)  

```

这在你有一个推送流并想 fan-out 到多个并发消费者时都能用——不需要消息代理。具体的工具——kr8s、asyncio.Queue、asyncio.Lock——是 Python 的习语。但这个模式不是。

> ~150 行 Python。零额外基础设施。如果你已经在用 Kubernetes 且需要轻量级实时配置传播，这个流已经在那了——你只需要去监听。

完整源码：**github**[3]

### 引用链接

[1]kr8s: _https://kr8s.org/_

[2]github: _http://github.com/ozcanyarimdunya/k8smap_

[3]github: _http://github.com/ozcanyarimdunya/k8smap_

