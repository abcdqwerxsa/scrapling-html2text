# 用 Cilium 和 vCluster 管理多个 PodCIDR 池

**作者**: 云原生AI视界
**发布时间**: 2026-07-24 06:56
**原文链接**: https://mp.weixin.qq.com/s/7Zm88p_GbyN0WSh5KTGqbg

---

# 用 Cilium 和 vCluster 管理多个 PodCIDR 池

![cover](https://r2.jeanjan.kdns.fr/pictures/img-3885d93701.jpeg)

## 更好的多租户方案 —— vCluster

对很多人来说，Kubernetes 是一个共享平台。当平台被共享时，通常意味着混乱。如果没有合理的关注点分离或多租户机制，组织只能祈祷能正常使用 Kubernetes。

Kubernetes 通过 Namespace 和 RBAC 在一定程度上解决了多租户问题。但多租户不仅仅是 Namespace。很多时候团队需要一个独立的 Kubernetes 集群——可能是为了测试新版的 Istio、编写新的 Kubernetes controller 需要在更新版本上测试、或需要一个专有集群。

基于 Namespace 的方法在单个集群内有效，但上述用例无法仅靠 Namespace 解决。为临时测试或专有团队创建完整的 Kubernetes 集群既昂贵又繁琐。

**vCluster** 将多租户提升了一步。它不是在集群内给你一个 Namespace，而是在宿主集群之上给你一个"虚拟"的 Kubernetes 集群。作为平台工程师，不需要每次有人要集群时就创建一个裸金属或云上的 Kubernetes 集群，而是在宿主集群上创建一个虚拟集群分配给团队。

虚拟集群是一个虚拟化的 Kubernetes 控制平面。它有自己的 kubeconfig，团队连接上去感觉不到与任何其他 Kubernetes 发行版的差异。团队在专用的虚拟集群内创建 Namespace，感觉就像你专门为他们准备了一个独立的集群。

vCluster 还有一个新产品——vind（vCluster-in-Docker），作为 kind 的直接替代品。

## 解决了集群级的多租户，但网络问题呢？

虽然虚拟集群内部可以使用 Namespace 来隔离团队和工作负载，但网络仍然是扁平的。

平台工程师在构建 Kubernetes 集群时，对网络投入的思考往往最少。我们知道 Pod 应该可以不经过 NAT 互相通信，我们想要一个扁平的 Pod 网络——但这也恰恰是基于网络的多租户在扁平 Pod 网络下失效的地方。

一个巨大的扁平 CIDR 有几个问题：

  1. **IP 耗尽** ——你的 VPC 或子网 CIDR 空间有限，但每个 Pod 都从同一个可路由范围获取 IP。
  2. **外部访问控制** ——一个扁平的 Pod CIDR 导致防火墙或安全组管理要么全放行要么全禁止。
  3. **运维僵化** ——没有办法定义哪个 Namespace 使用哪个 IP 范围。

这些在遇到之前不是问题，但遇到时可能已经太迟了。

## Cilium 如何适配？

**Cilium** 是一个开源的云原生网络、安全和可观测性解决方案。在 Kubernetes 中，无论使用什么 CNI，每个节点都从更大的 podCIDR 中获取一个较小的 IP 子集，节点上的 Pod 从此范围获取 IP。

Cilium 有多种处理节点 IP 子网的模式，称为 IPAM 模式：

  1. **Kubernetes 模式** ——让 kube-controller-manager 处理 IPAM
  2. **Cluster-Scope 模式** ——Cilium 接管每节点子网分配，通过自定义资源 `ciliumNode` 注册 Pod 子网。允许每个集群有多个 podCIDR。
  3. **Multi-Pool 模式** ——更进一步，可以在 Pod/Namespace 请求时动态分配子网，允许控制哪个 Namespace 的 Pod 从哪个 podCIDR 获取 IP。

## 探索 Multi-Pool

我们真正感兴趣的是解决扁平网络的问题。通过 Multi-Pool，可以让不同的 Namespace 从不同的 PodCIDR 获取 IP。

配置步骤概览：

  1. 创建一个不带默认网络插件的集群（使用 vCluster v0.31.1+）
  2. 安装 Cilium 并启用 Multi-Pool IPAM 模式
  3. 创建默认的 `CiliumPodIPPool`——这是一个集群范围的 CRD，定义了默认的 podCIDR
  4. 为不同 Namespace 创建专用的 CiliumPodIPPool（如 frontend-pool、backend-pool）
  5. 在 Namespace 上添加注解 `ipam.cilium.io/ip-pool: <pool-name>` 来指定 IP 池
  6. Namespace 中没有此注解的 Pod 从默认池获取 IP

关键特性：当某个节点上没有 Pod 请求特定 CIDR 的 IP 时，该节点不再从该 CiliumPodIPPool 请求 IP——实现动态分配，IP 按需使用。

## 生产环境中的实际价值

  * **零 IP 浪费** ——将昂贵的可路由 IP 留给 ingress，临时 Pod 放入不可路由的大网段
  * **清晰的网络可视化** ——SecOps 和 FinOps 团队在流日志中看到的是有意义的 CIDR 段
  * **遗留防火墙兼容** ——给特定 Namespace 分配专用的 /28 池，直接给防火墙团队 CIDR 即可

## 需要注意的问题

  1. **默认池是必须的** ——配置 Multi-Pool IPAM 后如果忘记创建 default CiliumPodIPPool CRD，Cilium operator 拒绝启动
  2. **Masquerading 配置** ——从标准 IPAM 切换到 Multi-Pool 后，必须显式定义出口网卡（如 `--set egressMasqueradeInterfaces=eth0`），否则 agent 会 panic 并 crash loop

> vCluster in Docker (vind) 的可定制性非常强，配合 Cilium 这类优秀的 CNI 可以实现高级的网络配置

