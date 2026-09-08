# K8s多集群管理：Karmada/Fleet跨集群部署实战

**作者**: 玥哲
**发布时间**: 2026-08-12 09:01
**原文链接**: https://mp.weixin.qq.com/s/lMWUJUpNAF1TsWrccZ9ELg

---

  

## 开篇场景

凌晨 2 点，公司主力机房断电，你的 K8s 集群跑在那里，300+ 微服务全部离线。备份集群在另一个机房，但应用部署、配置、DNS 切换全靠手动。等一切恢复，4 小时过去了。

或者：你的业务遍及全球，法兰克福用户要忍受 300ms 延迟。还有合规问题——GDPR 要求数据留在欧盟，金融监管要求生产环境物理隔离。

这些场景的共同痛点：**你知道需要多个集群，但不知道怎么管它们。**

![](https://r2.jeanjan.kdns.fr/pictures/img-3d57c90501.png)

##  一、为什么需要多集群

### 单集群的五大瓶颈

| 瓶颈       | 说明                            |
|----------|-------------------------------|
| **容灾**   |  整个集群挂了（etcd 脑裂、机房故障），单集群无能为力 |
| **规模限制** |  K8s 官方上限 5000 节点，大规模场景需要拆分   |
| **地理延迟** |  用户全球分布，单机房无法覆盖               |
| **合规隔离** |  GDPR、数据安全法要求数据本地化            |
| **环境隔离** |  测试压测搞挂 etcd，生产一起遭殃           |

### 多集群 vs 多 Namespace

| 维度   | 多 Namespace | 多集群        |
|------|-------------|------------|
| 隔离强度 | 逻辑隔离（软）     | 物理隔离（硬）    |
| 故障隔离 | ❌ 共享控制平面    | ✅ 独立控制平面   |
| 适合场景 | 同环境多团队      | 多环境/多区域/灾备 |

## 二、多集群管理方案全景对比

### 方案分类

多集群管理方案  
├── 手动管理（kubectl 多 context）  
├── 联邦方案：Karmada（推荐）、KubeFed（已弃）  
├── 平台方案：Rancher、OpenShift ACM  
├── GitOps：Rancher Fleet、Argo CD ApplicationSet  
└── 服务网格：Istio Multi-Primary、Linkerd

### 主流方案对比

| 方案                         | 核心理念              | 适合场景           |
|----------------------------|-------------------|----------------|
| **Karmada**                |  统一控制平面 + 智能调度    | 大规模多集群、混合云     |
| **Rancher Fleet**          |  Git 仓库为唯一真相源     | 中小规模、GitOps 实践 |
| **Argo CD ApplicationSet** |  Argo CD 多集群扩展    | 已有 Argo CD 的团队 |
| **Rancher**                |  Web UI 全功能管理     | 需要可视化管理界面      |
| **Istio Multi-Primary**    |  跨集群 Service Mesh | 需要跨集群流量管理      |

### 两种架构理念

• **Hub-Spoke 模型** （Karmada、Fleet）：一个中心管理集群，自动分发到工作集群• **Multi-Primary 模型** （Istio）：所有集群平等，通过跨集群网络直接互联

## 三、Karmada 架构与核心概念

Karmada 是华为开源的多集群管理方案，CNCF 孵化项目。核心理念：**让管理多个 K8s 集群就像管理一个集群一样简单。**

###  架构总览

┌───────────────────────────────────────────────┐  
│ Karmada 控制平面 │  
│ ┌──────────────┐ ┌────────────────────────┐ │  
│ │ karmada- │ │ karmada-controller- │ │  
│ │ apiserver │ │ manager │ │  
│ │ (兼容K8s API)│ │ (传播/覆盖/状态聚合) │ │  
│ └──────────────┘ └────────────────────────┘ │  
│ ┌──────────────┐ ┌────────────────────────┐ │  
│ │ karmada- │ │ karmada-scheduler │ │  
│ │ etcd │ │ (跨集群调度) │ │  
│ └──────────────┘ └────────────────────────┘ │  
└───────────┬───────────────────────────────────┘  
│  
┌────────┼────────┐  
▼ ▼ ▼  
集群A 集群B 集群C![](https://r2.jeanjan.kdns.fr/pictures/img-3d57c90502.png)

### 集群注册：Push vs Pull

• **Push 模式** ：Hub 持有工作集群的 kubeconfig，直接推（内网用）• **Pull 模式** ：工作集群运行 karmada-agent，主动拉（公网/混合云用）

### 三大核心 CRD

#### 📦 PropagationPolicy（传播策略）

决定资源部署到**哪些集群** 、各部署**多少副本** ：

apiVersion: policy.karmada.io/v1alpha1  
kind: PropagationPolicy  
metadata:  
name: web-app-propagation  
namespace: production  
spec:  
resourceSelectors:  
\- apiVersion: apps/v1  
kind: Deployment  
name: web-app  
placement:  
clusterAffinity:  
clusterNames:  
\- cluster-beijing  
\- cluster-shanghai  
replicaScheduling:  
replicaSchedulingType: Divided  
replicaDivisionPreference: Weighted  
weightPreference:  
staticWeightList:  
\- targetCluster:  
clusterNames: [cluster-beijing]  
weight: 5 # 北京 50%  
\- targetCluster:  
clusterNames: [cluster-shanghai]  
weight: 3 # 上海 30%  
\- targetCluster:  
clusterNames: [cluster-guangzhou]  
weight: 2 # 广州 20%

#### 🌐 ClusterPropagationPolicy

集群级别的传播策略（不限 namespace），用于管理基础设施资源。

#### 🎛️ OverridePolicy（覆盖策略）

不同集群的差异化配置——**Karmada 的杀手锏** ：

apiVersion: policy.karmada.io/v1alpha1  
kind: OverridePolicy  
metadata:  
name: web-app-overrides  
namespace: production  
spec:  
resourceSelectors:  
\- apiVersion: apps/v1  
kind: Deployment  
name: web-app  
overrideRules:  
# 北京：生产镜像  
\- targetCluster:  
clusterNames: [cluster-beijing]  
overriders:  
plaintext:  
\- path: "/spec/template/spec/containers/0/image"  
operator: replace  
value: "registry.cn-beijing.aliyuncs.com/myapp/web:v2.1.0"  
# 上海：灰度镜像  
\- targetCluster:  
clusterNames: [cluster-shanghai]  
overriders:  
plaintext:  
\- path: "/spec/template/spec/containers/0/image"  
operator: replace  
value: "registry.cn-shanghai.aliyuncs.com/myapp/web:v2.2.0-rc1"

## 四、Karmada 实战：跨集群部署

### 安装与注册

# 安装 karmadactl  
curl -s https://raw.githubusercontent.com/karmada-io/karmada/master/hack/install-cli.sh | bash  
  
# 初始化控制平面  
kubectl karmada init  
  
# 注册集群  
kubectl karmada join cluster-beijing --cluster-kubeconfig=/path/to/beijing.kubeconfig  
kubectl karmada join cluster-shanghai --cluster-kubeconfig=/path/to/shanghai.kubeconfig  
  
# 打标签  
kubectl label cluster cluster-beijing region=north env=production  
kubectl label cluster cluster-shanghai region=east env=production

### 部署应用

# 1. 创建 Deployment（在 Karmada 控制面）  
apiVersion: apps/v1  
kind: Deployment  
metadata:  
name: web-demo  
namespace: multi-demo  
spec:  
replicas: 6  
selector:  
matchLabels:  
app: web-demo  
template:  
metadata:  
labels:  
app: web-demo  
spec:  
containers:  
\- name: web  
image: nginx:1.25-alpine# 2. 传播策略：按 2:1 分配到北京和上海  
apiVersion: policy.karmada.io/v1alpha1  
kind: PropagationPolicy  
metadata:  
name: web-demo-propagation  
namespace: multi-demo  
spec:  
resourceSelectors:  
\- apiVersion: apps/v1  
kind: Deployment  
name: web-demo  
placement:  
clusterAffinity:  
clusterNames: [cluster-beijing, cluster-shanghai]  
replicaScheduling:  
replicaSchedulingType: Divided  
replicaDivisionPreference: Weighted  
weightPreference:  
staticWeightList:  
\- targetCluster:  
clusterNames: [cluster-beijing]  
weight: 2  
\- targetCluster:  
clusterNames: [cluster-shanghai]  
weight: 1

### 验证结果

# Karmada 视角：6 副本全部就绪  
kubectl get deployment -n multi-demo  
# 北京集群：4 个 Pod  
# 上海集群：2 个 Pod

### 故障转移

# 模拟北京集群故障  
kubectl label cluster cluster-beijing cluster.karmada.io/unschedulable=true  
# → 副本自动迁移到上海集群  
  
# 恢复  
kubectl label cluster cluster-beijing cluster.karmada.io/unschedulable-  
# → 副本根据策略重新分配

## 五、Rancher Fleet：轻量替代方案

Fleet 是 Rancher 开源的多集群 GitOps 工具：**Git 仓库是唯一真相源，自动同步到多个集群。**

###  核心用法

apiVersion: fleet.cattle.io/v1alpha1  
kind: GitRepo  
metadata:  
name: multi-cluster-app  
namespace: fleet-default  
spec:  
repo: https://github.com/myorg/k8s-configs  
branch: main  
paths:  
\- apps/web-app  
targets:  
\- clusterSelector:  
matchLabels:  
env: production  
targetCustomizations: # 差异化配置  
\- name: production-config  
clusterSelector:  
matchLabels:  
env: production  
yaml:  
overlays:  
\- production

### Karmada vs Fleet 对比

| 维度         | Karmada                    | Fleet             |
|------------|----------------------------|-------------------|
| **调度能力**   |  ✅ 强（副本分配、亲和性、权重）          | ❌ 弱（全量部署）         |
| **差异化配置**  |  OverridePolicy（JSON Path） | Kustomize overlay |
| **故障转移**   |  ✅ 自动迁移副本                  | ❌ 需手动处理           |
| **学习曲线**   |  中等                        | 低                 |
| **GitOps** |  需配合 Argo CD               | 原生 GitOps         |

## 六、方案选型决策树

你有几个集群？  
├── 1-3 个，同机房 → kubectl + context 切换 / Argo CD ApplicationSet  
├── 3-10 个，多环境  
│ ├── 需要 GitOps → ✅ Fleet  
│ ├── 需要智能调度 → ✅ Karmada  
│ └── 已有 Rancher → ✅ Rancher + Fleet  
├── 10-50 个，多区域 → ✅ Karmada（推荐）  
| 场景               | 推荐                     |
|------------------|------------------------|
| 小团队，3 集群多环境      | Fleet / ApplicationSet |
| 中型团队，多区域容灾       | **Karmada**            |
| 已有 Argo CD 生态    | Argo CD ApplicationSet |
| 已有 Rancher       | **Fleet** （内置）         |
| 只需跨集群 Service 通信 | Istio Multi-Primary    |

## 七、多集群 Service 发现与流量路由

集群 A 的服务怎么调用集群 B 的服务？四种方案：

| 方案                      | 原理                      | 适合场景           |
|-------------------------|-------------------------|----------------|
| **Karmada MCS**         |  原生跨集群 Service 发现       | Karmada 用户     |
| **Istio Multi-Cluster** |  跨集群 Service Mesh 流量管理  | 已有 Istio，需流量拆分 |
| **全局 DNS**              |  DNS 按地域解析到不同集群 Ingress | 简单场景           |
| **Submariner**          |  IPsec/VXLAN 打通 Pod 网络  | 需要 Pod 级直接通信   |

![](https://r2.jeanjan.kdns.fr/pictures/img-3d57c90503.png)

Istio 跨集群流量分配示例：

apiVersion: networking.istio.io/v1beta1  
kind: DestinationRule  
metadata:  
name: api-service-dr  
spec:  
host: api-service.multi-demo.svc.cluster.local  
trafficPolicy:  
loadBalancer:  
localityLbSetting:  
enabled: true  
distribute:  
\- from: "cluster-beijing/*"  
to:  
"cluster-beijing/*": 80 # 80% 本地  
"cluster-shanghai/*": 20 # 20% 上海

## 八、生产环境踩坑与最佳实践

### ⚠️ 常见坑

| 坑             | 解决方案                                                                    |
|---------------|-------------------------------------------------------------------------|
| **集群版本不一致**   |  所有集群保持同一 minor 版本（如全部 1.28.x）                                          |
| **跨域拉镜像慢**    |  每个区域部署本地镜像仓库，用 OverridePolicy 自动切换                                     |
| **Secret 同步** |  用 External Secrets Operator + Vault，或 Karmada ClusterPropagationPolicy |
| **监控盲区**      |  分层 Prometheus：本地采集 + 中心联邦                                              |
| **DNS 解析跨集群** |  配置 CoreDNS 转发规则                                                        |
| **网络连通性**     |  Submariner / Cilium Cluster Mesh / Istio East-West Gateway             |

### ✅ 10 条黄金法则

| #   | 法则                            |
|-----|-------------------------------|
| 1   | **集群版本一致** —— 所有集群同一 minor 版本 |
| 2   | **GitOps 驱动** —— 所有配置走 Git    |
| 3   | **本地镜像仓库** —— 每区域一个           |
| 4   | **统一认证** —— OIDC 统一身份         |
| 5   | **分层监控** —— 本地 + 联邦           |
| 6   | **自动化故障转移** —— 用 Karmada 自动迁移 |
| 7   | **渐进式上线** —— 测试 → 预发 → 生产     |
| 8   | **定期演练** —— 每季度故障转移演练         |
| 9   |  —— 全集群统一 base image          |
| 10  | **文档即代码** —— 集群架构文档随 Git 同步   |

## 总结

多集群管理是 K8s 生产化的必经之路。从本文的实战中，我们掌握了：

| 主题          | 要点                                   |
|-------------|--------------------------------------|
| **为什么**     |  容灾、规模、延迟、合规——单集群无法满足                |
| **Karmada** |  统一控制面 + 智能调度 + OverridePolicy 差异化   |
| **Fleet**   |  GitOps 原生，轻量上手快                     |
| **流量路由**    |  MCS / Istio / DNS / Submariner 四种方案 |
| **最佳实践**    |  版本一致、GitOps 驱动、本地镜像、分层监控            |

  


