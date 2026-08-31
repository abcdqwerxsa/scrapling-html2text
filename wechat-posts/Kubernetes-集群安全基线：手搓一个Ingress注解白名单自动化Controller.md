# Kubernetes 集群安全基线：手搓一个Ingress注解白名单自动化Controller

**作者**: 技术控杂谈
**发布时间**: 2026-08-05 10:07
**原文链接**: https://mp.weixin.qq.com/s/pTIz3CY48SudtnT8KrN7qw

---

在 Kubernetes 集群运维中，Ingress 白名单治理绝对是很多团队的“痛点刚需”。

几乎所有落地过 Ingress 白名单的团队，都会遇到三个无解问题：

1\. **配置分散混乱** ：白名单规则全部散落在各个 Ingress 的注解中，批量维护、统一治理基本无从谈起；

2\. **集群状态不一致** ：业务随意修改注解后，平台侧无法保证全集群 Ingress 白名单配置最终统一；

3\. **兜底方案笨重低效** ：传统靠 CronJob 定时扫集群、批量 patch 的兜底方式，延迟高、损耗大、无审计。

为了解决这些行业通用痛点，手搓一款轻量级组件：**ingress-whitelist-controller** 。

它的核心定位非常清晰：**把分散在 Ingress 注解的白名单，收敛为命名空间集中配置，通过事件驱动自动下发，再结合 Kyverno 锁住配置、防止人工篡改，实现全链路标准化治理** 。

## 一、先搞懂：这个控制器到底解决了什么？

首先明确：**它不是网关，不是 Ingress Controller，纯粹的 Kubernetes 治理组件** ，只聚焦「Ingress 白名单统一管控」这一件事。

核心工作机制：

■ 监听集群全量 Ingress 资源变更

■ 监听带指定标签的白名单配置 ConfigMap

■ 配置变更实时触发计算，精准更新对应白名单规则

■ **只修改 Ingress 注解、标签，绝不改动业务 spec**

目前管控 4 个核心字段，完全覆盖白名单治理场景：

■ `nginx.ingress.kubernetes.io/whitelist-source-range`：原生 NGINX 白名单网段

■ `platform.kyverno.io/internal-whitelist-source`：平台内部白名单来源标记

■ `platform.kyverno.io/internal-whitelist-profile`：白名单配置模板标识

■ `platform.kyverno.io/internal-whitelist-managed`：平台纳管标记

简单总结：**它的核心价值是「白名单配置收敛」，不干预流量转发，只做标准化治理。**

##  二、彻底告别老旧方案：为什么放弃 CronJob 轮询？

绝大多数团队的初始方案，都是 **CronJob + kubectl patch** 定时扫集群更新白名单。

这个方案能跑，但天生带着无法根治的缺陷：

■ **存在固定延迟** ：配置修改后，必须等下一轮定时任务才能生效，无法实时同步；

■ **损耗集群资源** ：高频全集群扫描，持续给 API Server 增加不必要压力；

■ **无审计能力** ：出问题无法追溯「谁、何时、修改了什么配置」；

■ **被动兜底** ：只能靠反复扫描补全配置，无法主动感知变更。

而我设计的控制器，直接颠覆这套逻辑：

**谁变了处理谁，哪个命名空间配置变更，只重算该命名空间下的 Ingress** 。

核心升级：**从「被动周期轮询」变成「主动事件驱动」** ，高效、实时、低损耗。

## 三、核心配置模型：命名空间隔离 + 多 Profile 管理

当前版本控制器支持 **按命名空间隔离、单命名空间多 Profile** 的精细化治理模型，完美适配多环境、多业务团队隔离场景。

每一套白名单 Profile，由 **成对的两个 ConfigMap** 组成，缺一不可：

  1. 1.**domains 配置：定义该白名单模板覆盖的域名列表（白名单命中规则）**
  2. 2.**cidrs 配置：定义最终写入 Ingress 注解的白名单网段**

通过统一标签体系实现配置关联，示例标签如下：

```

platform.kyverno.io/whitelist-config: "true"
platform.kyverno.io/whitelist-profile: office
platform.kyverno.io/whitelist-config-type: domains # cidrs 配置改为 cidrs
```

治理逻辑非常清晰：

■ 域名出现在 domains 列表中：命中对应 Profile，自动注入配套 CIDR 白名单；

■ 域名未匹配任何 Profile：默认不注入自定义白名单，避免误配置。

## 四、核心工作原理：极简事件驱动模型

控制器的核心逻辑极简，全程基于资源事件触发，无无效扫描、无重复计算。

### 触发规则

■ Ingress 新增/更新：仅重算当前这一个 Ingress，精准命中，无多余开销；

■ 受管 ConfigMap 新增/更新/删除：重算当前命名空间下所有 Ingress，局部更新不影响全局。

### 完整执行链路

```

                ┌────────────────────────────┐
                │ Kubernetes API Server      │
                └──────────────┬─────────────┘
                               │
                  Watch(Ingress / Namespace /
                     ConfigMap 等资源变化)
                               │
                               ▼
                ┌────────────────────────────┐
                │      Informer 监听事件      │
                └──────────────┬─────────────┘
                               │
                 Add / Update / Delete Event
                               │
                               ▼
                ┌────────────────────────────┐
                │      WorkQueue 工作队列     │
                └──────────────┬─────────────┘
                               │
                        Worker 消费事件
                               │
                               ▼
                ┌────────────────────────────┐
                │ 加载 Namespace 配置快照      │
                │ • ConfigMap                │
                │ • Namespace Label          │
                │ • 白名单策略                 │
                └──────────────┬─────────────┘
                               │
                               ▼
                ┌────────────────────────────┐
                │     计算白名单规则            │
                │ • 域名匹配                   │
                │ • CIDR 合并                 │
                │ • 注解生成                   │
                │ • 标签计算                   │
                └──────────────┬─────────────┘
                               │
                               ▼
                ┌────────────────────────────┐
                │   Diff 当前状态与目标状态     │
                └──────────────┬─────────────┘
                               │
                  是否存在变更？
                     ┌──────┴──────┐
                     │             │
                    否            是
                     │             │
                     ▼             ▼
                 Ignore      Patch Ingress
                                 │
                                 ▼
                ┌────────────────────────────┐
                │ 精准 Patch 注解 / 标签       │
                │ • whitelist-source-range   │
                │ • 自定义 Label              │
                │ • Status 更新（可选）        │
                └────────────────────────────┘
```

下面是核心事件入口代码，完整体现整套触发设计：

```

allFactory := informers.NewSharedInformerFactory(client, resyncPeriod)
ingressInformer := allFactory.Networking().V1().Ingresses()
configCMInformer := allFactory.Core().V1().ConfigMaps()
ingressInformer.Informer().AddEventHandler(cache.ResourceEventHandlerFuncs{
    AddFunc: func(obj interface{}) { c.enqueueIngress(obj) },
    UpdateFunc: func(_, newObj interface{}) { c.enqueueIngress(newObj) },
})
configCMInformer.Informer().AddEventHandler(cache.ResourceEventHandlerFuncs{
    AddFunc: func(obj interface{}) { c.enqueueNamespaceIngressesForConfig(obj) },
    UpdateFunc: func(_, newObj interface{}) { c.enqueueNamespaceIngressesForConfig(newObj) },
    DeleteFunc: func(obj interface{}) { c.enqueueNamespaceIngressesForConfig(obj) },
})
```

从代码能清晰看出两大设计亮点：

  1. 1.Ingress 变更：只处理当前对象，极致轻量化；
  2. 2.配置变更：按命名空间批量处理，规避全集群扫描。

同时控制器做了**严格的容错约束** ，规避线上风险：

■ 仅在 Ingress 所属命名空间匹配配置，严格隔离；

■ 单个 Ingress 所有 Host 必须收敛到同一个 Profile，多 Profile 冲突直接跳过；

■ Ingress 内多个 Host 命中/未命中规则不一致时，放弃更新，优先保稳定。

除此之外，控制器会精准过滤非受管配置，只响应白名单相关 ConfigMap 变更：

```

func (c *controller) enqueueNamespaceIngressesForConfig(obj interface{}) {
    accessor, err := metaAccessor(obj)
    if err != nil {
        utilruntime.HandleError(err)
        return
    }
    if !isManagedConfigMap(accessor.GetLabels()) {
        return
    }
    ings, err := c.ingressLister.Ingresses(accessor.GetNamespace()).List(labels.Everything())
    if err != nil {
        utilruntime.HandleError(err)
        return
    }
    for _, ing := range ings {
        c.queue.Add(ing.Namespace + "/" + ing.Name)
    }
}
```

只响应受控配置变更，最大限度减少无效计算与 API 请求。

## 五、强强联合：为什么必须搭配 Kyverno？

很多同学会疑惑：控制器已经能自动下发白名单，为什么还要额外配置 Kyverno？

核心答案：**控制器负责「主动下发正确配置」，Kyverno 负责「被动拦截错误修改」，二者分工互补，闭环治理。**

###  Kyverno 核心能力

对已经被平台纳管的 Ingress，实现严格的变更保护：

■ 拦截所有人工修改受管白名单字段的操作；

■ 放行控制器服务账号的自动更新请求；

■ 从准入层杜绝业务私自篡改配置，兜底平台治理规则。

### 核心准入规则

```

preconditions:
  all:
  - key: "{{ request.operation }}"
    operator: Equals
    value: UPDATE
  - key: "{{ lookup(request.oldObject.metadata.labels || `{}`, 'platform.kyverno.io/internal-whitelist-managed') || '' }}"
    operator: Equals
    value: "true"
  - key: '{{ request.userInfo.username || "" }}'
    operator: NotEquals
    value: system:serviceaccount:kyverno:ingress-whitelist-controller
```

白话翻译：

■ 只拦截资源更新操作；

■ 仅保护平台已纳管的 Ingress；

■ 允许控制器自动更新，禁止所有人手工篡改。

这套架构的精髓：**Controller 做配置收敛，Kyverno 做权限约束，彻底解决「自动下发、人工乱改」的治理漏洞。**

##  六、成熟工程能力：可落地、可审计、高稳定

这款控制器并非 Demo 级玩具，而是具备完整线上落地能力的工程组件，核心能力包括：

■ 支持集群内 `InClusterConfig` 运行，部署简单；

■ 全量监听 Ingress、受管 ConfigMap 资源；

■ 严格的命名空间隔离、多 Profile 配置校验；

■ 强制成对校验：杜绝只有 domains/cidrs 的残缺配置；

■ 工作队列限速重试，避免突发变更压垮集群；

■ 完整审计日志，支持上海时区标准化输出；

■ 原生联动 Kyverno，实现配置读写闭环治理。

其中**可审计日志** 是运维排障的核心利器，每次 Patch 都会精准记录关键信息：

■ 待处理的 Ingress 命名空间与名称；

■ 本次执行动作、命中的 Profile 模板；

■ 本次配置依赖的两份 ConfigMap 资源。

核心日志代码如下：

```

if decision.internal {
    klog.Infof(
        "patching ingress=%s/%s action=%s profile=%s configmaps=%s/%s,%s/%s",
        namespace,
        name,
        decision.action,
        decision.profile,
        decision.configNamespace,
        decision.domainsConfigMap,
        decision.configNamespace,
        decision.cidrsConfigMap,
    )
}
```

不泄露敏感网段配置，又能完整追溯变更依据，完美适配运维审计、故障排查场景。

## 七、方案核心优势：区别于传统脚本的四大亮点

单纯实现白名单下发，脚本、定时任务都能做到，但从**企业级治理** 角度，这款控制器的优势无可替代：

### 1\. 事件驱动，实时收敛

配置变更即刻触发更新，彻底告别定时任务的延迟问题，配置一致性秒级恢复。

### 2\. 精准作用域，低集群损耗

只变更关联命名空间、关联 Ingress，无全集群无效扫描，极大降低 API Server 压力。

### 3\. 全链路可审计

每一次配置下发都有日志留存，变更来源、依赖配置、执行动作全程可追溯，满足企业合规要求。

### 4\. 职责边界清晰

控制器负责计算下发，Kyverno负责拦截防护，解耦架构，稳定可靠，便于后续迭代扩展。

## 八、客观复盘：当前版本的边界与风险

工程落地最忌讳夸大能力，这里直白说明当前版本的局限性，帮助大家避坑：

### 1\. 采用「显式白名单」治理逻辑

仅匹配 domains 列表内的域名才会注入白名单，无默认放开逻辑。优点是安全、合规、易审计，缺点是需要人工维护域名列表，不适合超高频变动的域名场景。

### 2\. 受限于 NGINX Ingress 原生机制

白名单配置是 **Ingress 级** ，而非 Host 级。如果一个 Ingress 下多个 Host 需要不同白名单规则，控制器会直接跳过更新，避免配置冲突导致线上故障。

### 3\. 强制 Profile 成对配置

任何 Profile 必须同时拥有 domains 和 cidrs 配置，残缺配置会直接报错重试，不会带病上线。

强制校验代码：

```

for profile, acc := range accumulators {
    if !acc.hasDomains || !acc.hasCIDRs {
        return configState{}, fmt.Errorf(
            "namespace %s profile %s is missing paired domains/cidrs configmaps",
            namespace,
            profile,
        )
    }
}
```

宁可报错重试，绝不错误下发配置，最大限度保障线上稳定性。

## 九、适用与不适用场景，对号入座

###  非常适合这些团队/场景

■ 大规模使用 NGINX Ingress，需要统一白名单治理；

■ 希望替换老旧 CronJob 轮询方案，降低集群损耗；

■ 需要按命名空间隔离业务配置，实现精细化治理；

■ 不想搭建重型平台，希望轻量、低成本实现配置收口与合规审计。

### 暂不适合的场景

■ 单 Ingress 下多 Host 需配置差异化白名单；

■ 命名空间内 Profile 数量极多、域名归属频繁变动；

■ 需要复杂的优先级覆盖、全局兜底、特殊例外策略。

### 后续迭代方向

■ 新增 Profile 优先级机制，支持规则覆盖；

■ 补充默认兜底策略，适配更多场景；

■ 完善官方 Demo、配置文档与落地手册；

■ 增强准入校验，禁止业务伪造平台纳管字段。

## 十、最后

做这个控制器的初衷很简单：**K8s 白名单治理，不该靠人工盯防、不该靠定时任务兜底补锅。**

理想的治理形态，一定是**事件驱动自动收敛、策略引擎强制约束、全链路可审计追溯** 。

目前这套方案已经具备完整的工程落地能力：清晰的配置模型、严谨的收敛逻辑、闭环的防护策略、完善的日志审计、明确的风险边界。

如果你的集群还在被 Ingress 白名单分散、篡改、不一致的问题困扰，**「Controller 收敛 + Kyverno 守护」**的轻量治理方案，绝对值得落地尝试。

