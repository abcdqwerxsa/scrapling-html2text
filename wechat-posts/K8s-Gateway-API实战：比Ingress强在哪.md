# K8s Gateway API实战：比Ingress强在哪

**作者**: 玥哲
**发布时间**: 2026-06-26 09:01
**原文链接**: https://mp.weixin.qq.com/s/wem3Cpuez2SqqZs0KcXwOw

---

> Ingress 是 K8s 暴露 HTTP 服务的事实标准，但它有三个硬伤：只支持 HTTP(S)、高级功能全靠 Annotation、多团队共享一团糟。**Gateway API 是 Kubernetes 官方钦定的 Ingress 继任者** ——角色分离、协议无关、扩展标准化。本文带你搞懂 Gateway API 是什么、比 Ingress 强在哪、怎么用。 

## 一、为什么需要 Gateway API

先回顾一下 Ingress 的三大硬伤：

**硬伤 1：功能太简陋**  
Ingress 只支持 HTTP/HTTPS 流量路由。想限流？加 Annotation。想灰度发布？加 Annotation。想 TCP 路由？不好意思，不支持。

**硬伤 2：Annotation 地狱**  
Nginx Ingress 有 50+ 个 Annotation，Kong 有自己的，Traefik 又不一样。你在 Nginx 写好的注解，换到 Kong 全部作废。

**硬伤 3：权限模型太粗糙**  
一个团队想加条路由规则，就得给整个 Ingress 资源的写权限，意味着可以改其他团队的路由、TLS 证书、域名。多团队共用集群？权限没法细分。

> 💡 **Kubernetes 官方已宣布** ：Ingress-NGINX 将于 **2026 年 3 月退役** 。这不是"可能"，是时间表已定。现在开始了解 Gateway API，正是时候。 

## 二、Gateway API 核心概念：角色分离

Gateway API 最大的设计创新是**角色分离** ——把原来 Ingress 一个资源混在一起的所有职责，拆分给不同角色：

| 角色      | 负责什么         | 对应资源             | 谁管理   |
|---------|--------------|------------------|-------|
| 基础设施提供商 | 网关基础设施       | **GatewayClass** | 平台团队  |
| 集群管理员   | 网关实例（端口、TLS） | **Gateway**      | 集群管理员 |
| 应用开发者   | 路由规则         | **HTTPRoute**    | 开发团队  |
| 策略制定者   | 限流、认证等       | Policy CRD       | 安全/架构 |

**生活化比喻** ：

• **GatewayClass** = 建筑设计图纸（用什么网关？Nginx？Envoy？）• **Gateway** = 大楼前台入口（开 80 端口？443 端口？用什么证书？）• **HTTPRoute** = 前台的路由表（访客找 A 部门走左，找 B 部门走右）

![](https://r2.jeanjan.kdns.fr/pictures/img-436b008c01.png)

> 💡 **关键区别** ：Ingress 里所有东西写在一个 YAML 里，Gateway API 拆成多个独立资源。团队 A 改自己的路由不影响团队 B，RBAC 权限天然隔离。 

## 三、Gateway API vs Ingress 全面对比

![](https://r2.jeanjan.kdns.fr/pictures/img-436b008c02.png)

> 💡 **一句话总结** ：Ingress 是"能用的方案"，Gateway API 是"好用的方案"——架构更清晰、功能更强大、多团队更友好。 

## 四、从零写一个 Gateway

Gateway API 分三步：创建 Gateway（集群管理员）→ 创建 HTTPRoute（各团队）。以下是**最小可用配置** ：

**第一步：Gateway** （集群管理员在 infrastructure namespace 创建）
```

apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: prod-gateway
  namespace: infrastructure
spec:
  gatewayClassName: nginx
  listeners:
    - name: http
      port: 80
      protocol: HTTP
      allowedRoutes:
        namespaces:
          from: Selector
          selector:
            matchLabels:
              gateway-access: "true"
    - name: https
      port: 443
      protocol: HTTPS
      tls:
        mode: Terminate
        certificateRefs:
          - name: tls-cert
      allowedRoutes:
        namespaces:
          from: All
```

**第二步：HTTPRoute** （团队 A 在 team-a namespace 创建）
```

apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: api-routes
  namespace: team-a
spec:
  parentRefs:
    - name: prod-gateway
      namespace: infrastructure
      sectionName: https
  hostnames:
    - "app.example.com"
  rules:
    - matches:
        - path:
            type: PathPrefix
            value: /api
      backendRefs:
        - name: api-service
          port: 3000
          weight: 80
        - name: api-service-v2
          port: 3000
          weight: 20
    - matches:
        - path:
            type: PathPrefix
            value: /
      backendRefs:
        - name: web-service
          port: 80
```

> 💡 **allowedRoutes** 是权限控制的关键——限制哪些 namespace 的 HTTPRoute 可以挂载到这个 Gateway，防止其他团队的路由"蹭"你的入口。**团队 B 可以在 team-b namespace 创建自己的 HTTPRoute** ，挂载到同一个 Gateway，互不干扰。 

## 五、杀手级功能

**1️⃣ 原生流量拆分（金丝雀/灰度发布）**

![](https://r2.jeanjan.kdns.fr/pictures/img-436b008c03.png)

Ingress 要实现灰度？得写一堆 Nginx Annotation（canary-weight），换成 Kong 又完全不一样。Gateway API 是**标准字段** ，跨实现通用。直接在 backendRefs 里设 weight 就行：
```

backendRefs:
  - name: api-v1
    port: 80
    weight: 90      # 90% 流量
  - name: api-v2
    port: 80
    weight: 10      # 10% 流量（灰度）
```

**2️⃣ 原生请求重定向与重写**
```

# HTTPS 重定向
filters:
  - type: RequestRedirect
    requestRedirect:
      scheme: https
      statusCode: 301

# 路径重写: /api/v1/xxx → /v1/xxx
filters:
  - type: URLRewrite
    urlRewrite:
      path:
        type: ReplacePrefixMatch
        replacePrefixMatch: /v1
```

**3️⃣ 高级路由匹配** （Header / Method / Query）
```

matches:
  - path:
      type: Exact
      value: /api/upload
    method: POST
    headers:
      - name: Content-Type
        value: "multipart/form-data"
    queryParams:
      - name: version
        value: "v2"
```

Ingress 根本做不到按 Method、Header、Query 参数匹配路由。

**4️⃣ TCP/UDP 路由** （非 HTTP 协议）

Ingress 只能处理 HTTP(S)。数据库、Redis、自定义 TCP 协议？Gateway API 原生支持 TCPRoute / UDPRoute，一个 Gateway 搞定所有协议。

## 六、Ingress → Gateway API 迁移

![](https://r2.jeanjan.kdns.fr/pictures/img-436b008c04.png)

核心变化：

• Ingress 的 TLS 配置**移到 Gateway 层** 统一管理，开发者无需关心证书• Annotation 变成了**结构化的 filters 字段** ，有 schema 校验• 路由规则和入口配置**分离** ，各团队各管各的• 官方提供 **ingress2gateway** 工具自动转换

## 七、Gateway 实现选型

| 实现                | 特点           | 推荐场景             |
|-------------------|--------------|------------------|
| **Envoy Gateway** | 官方推荐、CNCF 项目 | 新项目首选            |
| **Nginx Gateway** | Nginx 团队出品   | 已用 Nginx Ingress |
| **Istio Gateway** | 服务网格集成       | 已用 Istio         |
| **Cilium**        | eBPF 高性能     | 已用 Cilium CNI    |
| **Kong**          | API 网关功能全    | 需 API 网关能力       |

## 八、该选 Ingress 还是 Gateway API？

| 场景            | 推荐            | 原因              |
|---------------|---------------|-----------------|
| 新项目           | ✅ Gateway API | 标准在演进，早用早受益     |
| 现有 Ingress 集群 | ⏳ 计划迁移        | NGINX 2026.3 退役 |
| 简单单团队         | Ingress 够用    | 不急着改，要有迁移意识     |
| 多团队共享集群       | ✅ Gateway API | RBAC 分离是刚需      |
| 需要 TCP/UDP 路由 | ✅ Gateway API | Ingress 做不到     |
| 需要灰度发布        | ✅ Gateway API | 原生支持，跨实现通用      |

**Ingress 是过去，Gateway API 是未来。**  
**角色分离，多团队各自管理自己的路由。**  
**协议无关，HTTP/TCP/UDP/gRPC 统一处理。**  
**功能内建，告别 Annotation 地狱。**

📌 **Gateway API 已经 GA** ，Ingress-NGINX 将于 2026 年 3 月退役。无论你是新项目还是存量迁移，Gateway API 都值得认真了解。**从 Gateway + HTTPRoute 两个资源开始，足以覆盖绝大多数场景。**

📢 「从零开始学 Kubernetes」系列持续更新中，关注不迷路！

*「从零开始学 Kubernetes」系列 · Gateway API 专题*

