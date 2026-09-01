# K8s探针全解：Liveness/Readiness/Startup

**作者**: 玥哲
**发布时间**: 2026-07-22 09:03
**原文链接**: https://mp.weixin.qq.com/s/P65CCDOxgaJG6jDNeut1gw

---

> 本文是「从零开始学 Kubernetes」系列第 **27** 篇，模块六 · K8s 运维实战篇。 

> 先看一个几乎所有新手都踩过的坑：你部署了一个 Spring Boot 应用，状态显示 `Running`、`1/1`，看起来完美——开始导流量，结果大量 502。为什么？因为 JVM 还在加载 Spring 上下文。**进程在跑，但应用根本没准备好服务请求。**

## 🎬 动画演示：探针全流程

![](https://r2.jeanjan.kdns.fr/pictures/img-31d4a7fe01.gif)

上面这个动画展示了三种探针的完整生命周期，发生了什么：

**① 部署** — 三种探针随 YAML 一起部署

**② Startup** — 前 5 次健康检查全 ❌，第 6 次 ✅，Spring Boot 启动花了 50 秒

**③ 正常运行** — Liveness + Readiness 定期检查全通过，流量正常分发

**④ Redis 挂了** — Readiness ❌ 移出 Endpoints，但 Liveness ✅ 不重启（重启治不了 Redis）

**⑤ 进程假死** — Liveness 连续 3 次 ❌ → 触发重启 → Startup 保护新容器启动 → 恢复

**⑥ 总结** — 三种探针各司其职，缺一不可

## 一、三种探针：各司其职

| 特性    | Liveness Probe   | Readiness Probe   | Startup Probe    |
|-------|------------------|-------------------|------------------|
| 回答的问题 | "容器还活着吗？"        | "能接流量了吗？"         | "启动完了没？"         |
| 失败后果  | 重启容器             | 移出 Endpoints（不重启） | 重启容器             |
| 生效时机  | Startup 成功后      | 整个生命周期            | 仅启动阶段            |
| 默认状态  | success（不配=永远活着） | failure（不配=立即接流量） | disabled（不配=不检查） |
| 典型用途  | 死锁、假死检测          | 滚动更新、依赖故障保护       | 保护慢启动应用          |

#### 探针类型（检查方式）

| 方式             | 适用场景            | 优点         | 缺点                   |
|----------------|-----------------|------------|----------------------|
| **HTTP GET**   | Web/API 服务      | 最灵活，支持复杂逻辑 | 需要应用支持健康端点           |
| **TCP Socket** | 数据库、消息队列        | 简单，无需应用层支持 | 只能检查端口，不能判断应用状态      |
| **Exec**       | 脚本类应用           | 最灵活        | 每次 fork 进程，开销大       |
| **gRPC**       | gRPC 微服务（1.24+） | 原生支持，高效    | 需要实现 health protocol |

## 二、Liveness vs Readiness：关键区别

| 维度   | Liveness | Readiness         |
|------|----------|-------------------|
| 失败动作 | 重启容器     | 移出 Endpoints（不重启） |
| 恢复方式 | 通过重启"自愈" | 探针恢复成功 → 自动加回     |
| 适用场景 | 进程假死     | 依赖暂时不可用、启动中       |

> ⚠️ **核心原则：Liveness 不要检查外部依赖！** 数据库挂了 → Liveness 失败 → 重启容器。但**重启解决不了数据库故障** ——所有 Pod 反复重启，形成雪崩。 

## 三、不同应用类型的建议配置

| 应用类型                 | 启动时间    | 建议配置                                  |
|----------------------|---------|---------------------------------------|
| Go/Rust/Node.js      | < 10s   | 可以不配 Startup                          |
| Python Flask/FastAPI | 10-30s  | failureThreshold=6, periodSeconds=10  |
| Java Spring Boot     | 25-100s | failureThreshold=30, periodSeconds=10 |
| ML 模型加载              | 数分钟     | failureThreshold=60, periodSeconds=10 |

## 四、完整 YAML：Spring Boot 生产配置

apiVersion: apps/v1 kind: Deployment metadata: name: order-service namespace: production spec: replicas: 3 strategy: type: RollingUpdate rollingUpdate: maxUnavailable: 0 # 不减少可用 Pod maxSurge: 1 # 允许多 1 个 Pod selector: matchLabels: app: order-service template: metadata: labels: app: order-service spec: containers: \- name: order-service image: order-service:v2.5.0 ports: \- containerPort: 8080 # Startup：保护慢启动，给 5 分钟 startupProbe: httpGet: path: /actuator/health port: 8080 failureThreshold: 30 # 30 × 10 = 300 秒 periodSeconds: 10 timeoutSeconds: 5 # Liveness：只检查进程自身，不查依赖！ livenessProbe: httpGet: path: /actuator/health/liveness port: 8080 periodSeconds: 10 failureThreshold: 3 timeoutSeconds: 3 # Readiness：检查依赖（DB/Redis），控制流量 readinessProbe: httpGet: path: /actuator/health/readiness port: 8080 periodSeconds: 5 # 比 Liveness 更频繁 failureThreshold: 3 timeoutSeconds: 3 successThreshold: 2 # 连续 2 次成功才加回，防抖 resources: requests: cpu: 500m memory: 512Mi limits: cpu: 1000m memory: 1Gi

## 五、分离端点最佳实践

**Liveness 和 Readiness 必须用不同的端点** ——这是最重要的原则之一。

/healthz（Liveness） /ready（Readiness） ├── 只检查进程自身 ├── 检查依赖 + 自身 ├── 响应 < 50ms ├── 响应 < 500ms ├── 不做外部 I/O ├── 检查 DB、Redis、MQ └── 200 / 503 └── 200 / 503

Python 示例：

@app.route('/healthz') def healthz(): """Liveness：只查进程自身""" if memory_usage() > 0.95: # 内存快爆了 return {"status": "unhealthy"}, 503 return {"status": "ok"}, 200 @app.route('/ready') def ready(): """Readiness：查依赖""" if not db_connection_healthy(): # 数据库连不上 return {"status": "not ready"}, 503 if not redis_connection_healthy(): # Redis 连不上 return {"status": "not ready"}, 503 return {"status": "ready"}, 200

## 六、生产踩坑指南

#### 坑 1：Liveness 太激进导致全员雪崩

`failureThreshold: 1` \+ `periodSeconds: 3` \+ `timeoutSeconds: 1`。某次 GC 停顿 → 所有 Pod 同时超时 → 全部被杀 → **雪崩** 。

**修复** ：`failureThreshold` ≥ 3，`timeoutSeconds` ≥ 3，配合 **PDB** 防止同时不可用。

#### 坑 2：Liveness 和 Readiness 用同一个端点

`/health` 端点检查了数据库。数据库挂了 → Readiness 失败 + Liveness 也失败 → 重启治不了数据库 → **CrashLoopBackOff** 。

**修复** ：分离端点。Liveness 用 `/healthz`，Readiness 用 `/ready`。

#### 坑 3：忘记配 Startup Probe，JVM 反复重启

没配 Startup，`initialDelaySeconds: 30` \+ `failureThreshold: 3` → 60 秒就开始杀容器。Java 应用需要 90 秒启动 → 永远启动不完。

**修复** ：加 Startup Probe，`failureThreshold: 30`，`periodSeconds: 10`，给足 5 分钟。

> 📌 **记住这五条** ：① Liveness 不检查外部依赖 ② Liveness 和 Readiness 用不同端点 ③ Startup Probe 是 Java/ML 必备 ④ timeoutSeconds 至少设 3 ⑤ 至少配 Readiness 

> 📢「从零开始学 Kubernetes」系列持续更新中，关注不迷路！ 

