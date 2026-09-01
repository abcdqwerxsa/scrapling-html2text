# K8s NetworkPolicy实战：微服务间通信你说了算

**作者**: 玥哲
**发布时间**: 2026-07-08 09:01
**原文链接**: https://mp.weixin.qq.com/s/fhRecs3baJqz1fRWZurqbQ

---

> NetworkPolicy 基础、ingress/egress 规则、默认拒绝策略、前后端分离隔离实战 

上一篇聊了 ServiceAccount——Pod 的身份标识。但有了身份只是解决了"你是谁"的问题，还有一个更基础的安全维度：**Pod 之间的网络流量，谁能访问谁？**

K8s 默认网络是**全通的** ——任何 Pod 可以访问任何 Pod。这就像一栋办公楼所有门都敞着，邻居随时来串门。NetworkPolicy 就是那把锁。

## 一、为什么需要 NetworkPolicy

默认情况下，K8s 集群里：

**场景 1** ：`frontend` 可以直接访问 `database`（绕过了 backend）

**场景 2** ：一个被攻破的 Pod 可以扫描整个集群

**场景 3** ：测试 Pod 可以直连生产数据库

RBAC 管的是 API 调用权限，网络层面的流量它管不了。而且 NetworkPolicy 默认是**允许所有** ——你不创建策略，网络就是全通的。

| 维度   | RBAC       | NetworkPolicy |
|------|------------|---------------|
| 管什么  | K8s API 权限 | Pod 间网络流量     |
| 默认行为 | 拒绝所有       | **允许所有** ⚠️   |

![](https://r2.jeanjan.kdns.fr/pictures/img-8cc81faf01.png)

## 二、NetworkPolicy 是什么

**NetworkPolicy 是一组白名单规则，定义了哪些 Pod 可以和哪些 Pod 通信。**

核心字段：
```

apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: my-policy
spec:
  podSelector:          # 选择受控 Pod
    matchLabels:
      app: backend
  policyTypes:          # 策略类型
  - Ingress             # 入站
  - Egress              # 出站
  ingress:              # 入站规则（谁能访问我）
  - # ...
  egress:               # 出站规则（我能访问谁）
  - # ...
```

![](https://r2.jeanjan.kdns.fr/pictures/img-8cc81faf02.png)

> ⚠️ **关键前提** ：NetworkPolicy 需要支持它的 CNI 插件才能生效。Flannel **不支持** ，Calico/Cilium 支持。创建策略前先确认你的 CNI。 
```

kubectl get pods -n kube-system | grep -E 'calico|cilium|flannel'
```

## 三、ingress 规则（入站控制）

控制**谁能访问被选中的 Pod** 。

### 只允许 frontend 访问 backend
```

apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-only-frontend
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: backend          # 约束 backend Pod
  policyTypes: [Ingress]
  ingress:
  - from:
    - podSelector:          # 只允许 frontend Pod
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8080            # 只开放 8080 端口
```

### 禁止所有入站
```

apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-ingress
spec:
  podSelector: {}            # 空 = 所有 Pod
  policyTypes: [Ingress]
  ingress: []                # 空 = 不允许任何入站
```

> ⚠️ `podSelector: {}` 是**选择所有 Pod** ，不是不选。 

## 四、egress 规则（出站控制）

控制**被选中的 Pod 可以访问谁** 。

### 限制 backend 只能访问数据库
```

apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-only-db
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes: [Egress]
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgresql
    ports:
    - protocol: TCP
      port: 5432
```

### ⚠️ 最重要的坑：必须放行 DNS

加了 egress 策略后，DNS 查询也会被拦截，导致域名解析失败。**每条 egress 策略都必须搭配 DNS 放行规则：**
```

apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns
spec:
  podSelector: {}
  policyTypes: [Egress]
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: kube-system
    - podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - {protocol: UDP, port: 53}
    - {protocol: TCP, port: 53}
```

## 五、默认拒绝策略（生产必做）

**生产环境最佳实践：先拒绝所有，再逐步放行。**

### 第一步：默认拒绝
```

apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: production
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]
  ingress: []
  egress: []
```

### 第二步：放行 DNS

见上面的 allow-dns 策略。

### 第三步：逐步添加应用规则

NetworkPolicy 是**累加的** ——多个策略选中同一个 Pod 时，效果取并集，只要任何一个策略允许就放行。

![](https://r2.jeanjan.kdns.fr/pictures/img-8cc81faf03.png)

## 六、实战案例：前后端分离隔离

三个 namespace 的隔离方案：

**frontend namespace** ──→ **backend namespace** ──→ **database namespace**

:80 :8080 :5432

✅ frontend → backend:8080

✅ backend → database:5432

✅ 所有 Pod → DNS:53

❌ frontend → database（禁止）

❌ database → 任何（禁止所有出站）

![](https://r2.jeanjan.kdns.fr/pictures/img-8cc81faf04.png)

### 核心规则
```

# backend 允许 frontend namespace 入站 8080
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend
  namespace: backend
spec:
  podSelector:
    matchLabels:
      app: api-server
  policyTypes: [Ingress]
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: frontend
    ports:
    - {protocol: TCP, port: 8080}
---
# database 允许 backend namespace 入站 5432
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-backend
  namespace: database
spec:
  podSelector:
    matchLabels:
      app: postgresql
  policyTypes: [Ingress]
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: backend
    ports:
    - {protocol: TCP, port: 5432}
```

> ⚠️ **双向配置** ：如果源和目标都有默认拒绝策略，需要同时在源 Pod 配置 egress 放行、在目标 Pod 配置 ingress 放行，流量才能通过。 

## 七、常见踩坑

**坑 1：CNI 不支持** — Flannel 不支持 NetworkPolicy，策略创建了但不生效。排查：`kubectl get pods -n kube-system | grep -E 'calico|cilium'`

**坑 2：忘了 DNS** — 加了 egress 策略后所有请求超时，因为 DNS 被拦截了。解决：永远配套 DNS 放行规则。

**坑 3：白名单不是黑名单** — NetworkPolicy 只有 allow 没有 deny。不能写"拒绝 A 访问 B"，只能写"只允许 C 访问 B"。

**坑 4：空选择器 = 全选** — `podSelector: {}` 选择所有 Pod，不是不选。别写错了。

**坑 5：删策略 = 恢复全通** — NetworkPolicy 删除后流量立即恢复，没有缓冲期。用 GitOps 管理防止误删。

## 总结

1. **默认网络全通** 是最大安全风险，必须主动用 NetworkPolicy 隔离

2. **白名单机制** ：选中 Pod 后只允许规则内流量，其余拒绝

3. **需要 CNI 支持** ：Flannel 不支持，Calico/Cilium 支持

4. **ingress 管入站，egress 管出站** ，两个方向独立配置

5. **egress 必须放行 DNS** ，否则域名解析失败

6. **生产环境默认拒绝** ：先 deny all，再逐步放行

7. **多策略叠加是并集** ：只要一个策略允许就放行

> 📌 **下一篇** ：网络安全搞定了，但容器本身的安全呢？SecurityContext 和 Pod Security Standards（PSA）让你的 Pod 不再裸奔，下回见！ 

> 📢 「从零开始学 Kubernetes」系列持续更新中，关注不迷路！ 

