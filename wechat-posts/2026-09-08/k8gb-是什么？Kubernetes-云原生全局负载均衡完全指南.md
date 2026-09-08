# k8gb 是什么？Kubernetes 云原生全局负载均衡完全指南

**作者**: 云原生AI视界
**发布时间**: 2026-08-12 07:00
**原文链接**: https://mp.weixin.qq.com/s/o5tU4nt02PCTJuIlVsk1KA

---

# k8gb 是什么？Kubernetes 云原生全局负载均衡完全指南

![cover](https://r2.jeanjan.kdns.fr/pictures/img-bc727eee01.jpeg)

> “
> 
> 本文带你完整认识 CNCF 最新进入孵化期的项目：从架构原理，到在 AWS 上的生产部署。

## 简介

CNCF 技术监督委员会（TOC）已于 2026 年 7 月 18 日将 K8gb（Kubernetes Global Balancer）提升为**孵化（incubating）**项目，CNCF 在几天前才正式公布这一消息。这个项目早在 2021 年 3 月就以 sandbox 项目身份加入 CNCF，这次晋升为长达五年的成熟历程画上了里程碑。

那么 K8gb 到底是做什么的？为什么大家都在讨论它？你自己集群里又该怎么用它？本文会端到端覆盖这个项目：它是什么、架构如何，以及从本地测试环境到 AWS 生产部署的全过程。

## K8gb 是什么？

全局服务器负载均衡（GSLB）传统上是网络团队解决的问题，通常依赖昂贵且绑定硬件的产品：把流量路由到跨多个地理区域的系统之间，并在某个区域宕机时自动故障转移。

K8gb 以完全 Kubernetes 原生方式解决这个问题。项目诞生于 Absa Group（南非一家银行）：该公司在多个地理区域运行 Kubernetes 集群时，一直在寻找一个能根据服务健康状态路由流量的开源 GSLB 方案，但市面上的选项要么太贵，要么没有真正与 Kubernetes 集成。

于是就有了 k8gb：一个 Kubernetes operator，通过单一的 `Gslb` 自定义资源（CRD）为任何 Ingress 或 Service 提供全局负载均衡能力。开发团队不需要再和网络团队走一套单独的协调流程，就能自行管理服务的全局可用性。

## 为什么选 K8gb？核心差异点

几个关键设计决策让 K8gb 区别于其他 GSLB 方案：

  * **基于 DNS 路由** ：运行在 DNS 之上，这是全球范围内最可靠、久经考验的协议，而且不需要额外的流量路由层。
  * **没有单点故障（SPOF）** ：不需要独立的管理集群，每个参与集群都可以独立做决策。
  * **Kubernetes 原生健康检查** ：直接基于你已有的 Liveness 和 Readiness 探针做路由决策，不需要另建一套健康检查机制。
  * **通过单一 CRD 配置** ：用 `Gslb` kind 声明，天然适配 GitOps 工作流（Kustomize、Helm、ArgoCD 等）。

## 架构：背后发生了什么

![](https://r2.jeanjan.kdns.fr/pictures/img-bc727eee02.png)

K8gb 的核心由三个组件组成：

  1. **GSLB 自定义资源** ：声明式 API，定义跨集群的流量管理。
  2. **K8gb Operator** ：核心逻辑，负责管理 GSLB 资源、检查应用健康状态、协调流量策略。
  3. **Kubernetes 原生健康检查** ：把 Pod 的 Liveness/Readiness 探针状态直接喂给路由决策。

除此之外还有几层负责生态集成：一个连接层，让 Ingress 和 Gateway API 资源与基于 DNS 的流量管理对接，不受具体 controller 限制；一个 DNS 引擎，把 CNCF 毕业项目 CoreDNS 作为内嵌组件使用；ExternalDNS 支持，负责区域委派和云厂商集成；以及一个可选的全局控制平面，构建在毕业项目 Crossplane 之上，用于多集群基础设施编排。

## 孵化状态：五年的旅程

项目从 sandbox 升到 incubating 不是偶然。根据 LFX Insights 的数据，K8gb 目前的健康评分为 72/100，评估四个主要方面：开发活跃度、贡献者、安全性和热度。从 sandbox 时期以来，项目已发展到 239 位贡献者、105 个贡献组织，73% 的贡献者每季度持续回归。GitHub 上已有 1,197 颗星和 149 个 fork，过去一年增长 71%。LFX Insights 估计该软件的价值超过 200 万美元。

在生产环境中使用它的组织里，一个突出案例是 Millennium bcp，葡萄牙最大的私营银行。这家银行采用 k8gb 提升数字银行基础设施的韧性，关键银行应用的可用性达到 99.99%，恢复时间也显著改善。

K8gb 创始人 Yury Tsarev 认为这次晋升是对项目目标的认可：为 Kubernetes 社区简化 GSLB。CNCF TOC 赞助人 Karena Angell 则强调了项目过去五年展现的技术成长和社区参与度。

## 快速开始：本地试一试

尝试 K8gb 不需要真实的多集群基础设施。项目内置了一个开箱即用的 Makefile 目标，通过 `k3d` 拉起两个本地 k3s 集群，并在它们之间配置 GSLB：
```

make deploy-full-local-setup  

```

这个命令会：

  * 创建两个本地 k3s 集群（通过 k3d）
  * 暴露 CoreDNS 服务用于 UDP DNS 流量
  * 安装 k8gb，连同测试应用和两个示例 `Gslb` 资源

整个过程完全在本地运行，不依赖外部 DNS 服务商。如果你想体验 AI 推理端点的全局容灾场景：
```

make deploy-full-local-setup FULL_LOCAL_SETUP_WITH_AI_DEMO=true  
make ai-inference-demo  

```

这些命令会向两个集群部署一个轻量级 Ollama 模型，让你通过同一个全局域名观察故障转移。想看指标的话，还可以用 `make deploy-prometheus` 拉起 Prometheus，在 `localhost:9090` 和 `localhost:9091` 查看测试集群的指标。

## 生产部署：基于 AWS Route53 的分步指南

在本地看过逻辑之后，我们进入真实场景：两个 EKS 集群分别位于 `eu-west-1` 和 `us-east-1`，Route53 作为边缘 DNS 服务商。下面大部分步骤都需要你在两个集群之间切换 `kubectl` context，并对两边执行相同命令。

**1\. 安装 Ingress Controller**

在两个集群都安装 ingress-nginx：
```

kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v0.40.2/deploy/static/provider/aws/deploy.yaml  

```

**2\. 用 Helm 部署 k8gb**

克隆仓库，用集群专属 values 安装 Helm chart。每个集群用各自的 values 文件部署，里面包含各自的 `dnsZone`、`edgeDNSZone`、`hostedZoneID` 和 IRSA（IAM Roles for Service Accounts）角色：
```

git clone https://github.com/k8gb-io/k8gb.git  
cd k8gb  

helm repo add k8gb https://www.k8gb.io  
helm repo update# 在 eu-west-1 context 下  
helm -n k8gb upgrade -i k8gb k8gb/k8gb --create-namespace \  
  -f ./docs/examples/route53/k8gb/k8gb-cluster-eu-west-1.yaml# 在 us-east-1 context 下  
helm -n k8gb upgrade -i k8gb k8gb/k8gb --create-namespace \  
  -f ./docs/examples/route53/k8gb/k8gb-cluster-us-east-1.yaml  

```

**3\. 部署测试应用并定义 Gslb 资源**
```

make deploy-test-apps  

```

把示例 `Gslb` manifest 里的主机 FQDN 改成你自己的域名，然后在两个集群应用：
```

kubectl apply -f ./docs/examples/route53/k8gb/gslb-failover.yaml  

```

简化后的 failover 策略长这样：
```

apiVersion: k8gb.io/v1beta1  
kind: Gslb  
metadata:  
  name: test-gslb-failover  
  namespace: test-gslb  
spec:  
  resourceRef:  
    apiVersion: networking.k8s.io/v1  
    kind: Ingress  
    name: test-gslb-failover  
  strategy:  
    type: failover  
    primaryGeoTag: eu-west-1  

```

**4\. 验证与故障转移测试**

检查 Gslb 资源状态，可以看到 Route53 中自动创建的 NS 和 glue 记录：
```

kubectl -n test-gslb get gslb test-gslb-failover -o yaml  

aws route53 list-resource-record-sets --hosted-zone-id $YOUR_HOSTED_ZONE_ID  

```

向应用发送请求，你会看到流量流向主区域（`eu-west-1`）。接下来是重点：把 `eu-west-1` 的 Deployment 缩到 0 来模拟故障：
```

kubectl -n test-gslb scale deploy frontend-podinfo --replicas=0  

```

很快 Gslb 资源的状态就会变化：`geoTag` 字段切到 `us-east-1`，`healthyRecords` 更新为新区域的 IP。再发同样的请求，响应就来自 `us-east-1` 了，全程没有任何人工干预。

把 `eu-west-1` 扩容回来，流量会重新回到主区域。你还可以测试 `roundRobin` 策略，它会以 active-active 方式同时从两个区域提供服务。

## 其他 DNS 服务商：Azure 与 GCP

除了 Route53，k8gb 还支持 Infoblox、NS1、CloudFlare、Azure DNS 和 GCP Cloud DNS。有两点值得注意：

在 **Azure** 上，只支持 **Azure Public DNS** ；Azure Private DNS 不能用于 k8gb，因为它不支持 NS 记录。私有 DNS 场景下，项目建议使用基于 VM 的 DNS 方案（Windows DNS 或 BIND）。配置流程涉及私有 AKS 集群、在 Microsoft Entra ID 中注册的应用（Client ID/Secret），以及 ExternalDNS 的 Azure secret。

在 **GCP** 上有一个有趣的混合架构：Cloud DNS 只管理父区域和 NS 委派记录，真正做负载均衡的区域由 k8gb 集群内的 CoreDNS 托管。ExternalDNS 自动在 Cloud DNS 中创建指向 CoreDNS LoadBalancer IP 的 NS 和 glue 记录。这种方式既加快了故障转移，也降低了 Cloud DNS 成本，因为频繁变化的记录完全由 CoreDNS 管理，完全不经过 Cloud DNS。这也是 GKE 集群使用 Workload Identity 时的推荐认证方式。

## 生产就绪吗？支持的环境

这是 k8gb 经过测试的环境矩阵：

| 组件                 | 支持选项                                                    |
|--------------------|---------------------------------------------------------|
| Kubernetes 版本      | >= 1.21                                                 |
| 环境                 | 本地或云上，任何符合规范的集群                                         |
| Ingress Controller | NGINX、Istio、AWS Load Balancer Controller                |
| 边缘 DNS             | Infoblox、Route53、NS1、CloudFlare、Azure DNS、GCP Cloud DNS |
| E2E 测试             | 使用 Terratest 和 Chainsaw 的多集群自动化                         |

这个矩阵刻意保持保守；如果你使用的 ingress 或 DNS 服务商不在列表里，建议先到 staging 环境验证再上生产。

## 路线图与结语

K8gb 团队接下来的议程包括：更复杂的多区域流量路由场景、GSLB 配置的高级可观测性和指标、不断扩展的生态集成列表，以及对 service mesh 技术的更深支持。

如果你正在处理多集群 Kubernetes 环境下的容灾和全局可用性问题，k8gb 的“单一 CRD、零额外管理集群”方案值得一试。先从上面的本地快速开始做起，再根据你的云环境选择 Route53、Azure DNS 或 GCP Cloud DNS 集成。

**资源：**

  * 项目文档：k8gb.io[1]
  * GitHub 仓库：github.com/k8gb-io/k8gb[2]

[1]k8gb.io: _https://www.k8gb.io/latest/_

[2]github.com/k8gb-io/k8gb: _https://github.com/k8gb-io/k8gb_

