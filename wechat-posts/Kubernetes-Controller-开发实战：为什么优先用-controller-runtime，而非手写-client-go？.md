# Kubernetes Controller 开发实战：为什么优先用 controller-runtime，而非手写 client-go？

**作者**: 技术控杂谈
**发布时间**: 2026-07-13 08:30
**原文链接**: https://mp.weixin.qq.com/s/f6dMBzwMiOpTMehAaDaOcA

---

很多 Kubernetes 开发者入门 Controller、Operator 开发时，都会陷入一个经典的选型困惑：

**到底该学 client-go 还是 controller-runtime？Kubebuilder 又扮演什么角色？三者到底如何选择？**

网上的各类说法杂乱不一、甚至互相矛盾，很容易误导新手：

生产环境必须用原生 client-go，框架太重、不稳定？

controller-runtime 性能差，不适合高并发业务场景？

正规 Operator 都是 Kubebuilder 写的，直接学 Kubebuilder 就够了？

手写 client-go 才是真底层，用框架都是偷懒？

近期在落地 Kubernetes 自定义控制器开发的过程中，我彻底理清了 **client-go / controller-runtime / Kubebuilder** 三者的底层关系、核心差异和适用场景，也解开了当初入门时的所有选型困惑。

原本以为只是几十行简单的业务逻辑开发，没想到最大的收获不是完成需求，而是彻底吃透了 **client-go / controller-runtime / Kubebuilder** 三者的底层关系、核心差异和适用场景。

今天这篇实战干货，一次性终结大家的选型焦虑，讲透 K8s 控制器开发的核心逻辑。

## 一、三者关系，是逐层封装

绝大多数新手的认知误区：将 client-go、controller-runtime、Kubebuilder 当成三种独立、互斥的控制器开发方案，纠结取舍。

**但事实是：三者是严格的上下层依赖关系，不存在替代关系，是层层封装的架构设计。**

给大家一个极简清晰的层级架构，一眼看懂核心逻辑：

很多新手看不懂三者的关系，这里用**分层架构逻辑** 通俗说明：

```

                 你的业务代码
                       │
        ┌──────────────┴──────────────┐
        │                             │
 controller-runtime              client-go
 （Controller 开发框架）        （官方 SDK）
        │
        └──────────────┬──────────────┘
                       │
      Informer + WorkQueue + Cache
                       │
                  Kubernetes API Server
```

**三者精准定位：**

■ **client-go** ：Kubernetes 官方原生 SDK，是所有控制器的底层基石，提供资源增删改查、Informer 监听、工作队列、缓存等基础能力。

■ **controller-runtime** ：基于 client-go 二次封装的**标准化控制器开发框架** ，屏蔽底层重复基建逻辑。

■ **Kubebuilder** ：基于 controller-runtime 的**项目脚手架工具** ，仅负责自动生成项目模板，不参与控制器运行逻辑。

通俗总结：**client-go 是地基，controller-runtime 是精装成套框架，Kubebuilder 是快速建房工具。**

##  二、手写 client-go：业务代码10行，框架基建500行

很多开发者推崇原生 client-go，认为底层完全可控、性能最优。但真实落地过就会发现一个致命问题：**纯手写 client-go，90% 的代码都是重复的基建逻辑，真正的业务代码寥寥无几。**

如果直接基于原生 client-go 开发控制器，哪怕只是简单监听 Pod、Ingress 资源变更，你必须手动实现全套底层能力，缺一不可：

■ 手动初始化 Kubernetes Client 客户端

■ 手动创建 SharedInformer 工厂实例

■ 手动注册资源增/删/改事件处理器

■ 手动初始化限速工作队列、配置限流策略

■ 手动启动 Informer，阻塞等待缓存同步完成

■ 手动编写 Worker 消费循环逻辑

■ 手动处理任务失败重试、异常兜底、遗忘机制

■ 手动实现程序优雅退出、资源释放逻辑

给大家贴一段**原生 client-go 标准模板代码** ，直观感受冗余度：

```

informerFactory := informers.NewSharedInformerFactory(clientset, 0)
podInformer := informerFactory.Core().V1().Pods()
queue := workqueue.NewRateLimitingQueue(workqueue.DefaultControllerRateLimiter())
podInformer.Informer().AddEventHandler(cache.ResourceEventHandlerFuncs{
    AddFunc: func(obj interface{}) {},
    UpdateFunc: func(oldObj, newObj interface{}) {},
    DeleteFunc: func(obj interface{}) {},
})
stopCh := make(chan struct{})
defer close(stopCh)
go informerFactory.Start(stopCh)
// 手动编写 Worker 消费死循环
for {
    obj, shutdown := queue.Get()
    if shutdown {
        break
    }
    // 手动处理业务逻辑、重试、错误、任务遗忘
    queue.Done(obj)
}
```

真实开发场景中，**核心业务可能只需要几十行代码** ，但为了跑通整个控制器流程，你要手写几百行重复框架代码。

这也是绝大多数新手的痛点：**精力全耗在底层基建，根本没时间关注业务逻辑和控制器核心思想。**

##  三、controller-runtime：帮你干掉所有重复基建代码

反观 controller-runtime，它的核心价值只有一个：**封装所有通用底层能力，让开发者只专注写业务 Reconcile 逻辑。**

同样实现资源监听、控制器调度，使用 controller-runtime 仅需几行核心代码即可完成注册：

```

// 注册控制器，监听 Pod 资源
ctrl.NewControllerManagedBy(mgr).
    For(&corev1.Pod{}).
    Complete(r)
```

开发者只需要实现唯一的核心方法 **Reconcile** ，所有资源变更都会进入这个方法做状态修正：

```

func (r *PodReconciler) Reconcile(
    ctx context.Context,
    req ctrl.Request,
) (ctrl.Result, error) {
    // 1. 获取集群实际资源状态
    // 2. 对比用户期望状态 & 集群实际状态
    // 3. 执行修正逻辑（补注解、补标签、更新配置等）
    return ctrl.Result{}, nil
}
```

简洁度肉眼可见！因为 controller-runtime 帮你**全自动实现了所有底层能****力** ：

■ 自动创建、管理 Informer 监听

■ 自动初始化缓存、完成资源同步

■ 自动创建限速工作队列、管理任务排队

■ 自动启动 Worker 工作协程

■ 自动处理任务重试、失败兜底

■ 自动管理程序生命周期、优雅退出

**一句话总结：用 controller-runtime，你写的每一行代码，都是纯粹的业务代码。**

##  四、大家最关心的问题：封装后性能会变差吗？

这是所有人的第一疑问：**封装了这么多层，性能是不是不如原生 client-go？**

答案非常明确：**绝大多数业务场景下，性能几乎无差异。**

核心原因：controller-runtime**没有重构任何底层机制** ，它只是对 client-go 原生能力做了**标准化封装与组合** 。

底层执行链路完全一致：

SharedInformer → DeltaFIFO → RateLimitingQueue → Reconcile

简单拆解：

■ 资源 Watch 监听：依然是 client-go 原生实现

■ 本地缓存 Cache：依然是 SharedInformer 机制

■ 任务队列：依然是原生限速队列

controller-runtime 只是帮你把这些零散组件**标准化组装、统一生命周期管理** ，没有任何性能损耗。

## 五、什么时候用 client-go？什么时候用 controller-runtime？

### 优先直接使用 client-go 的场景

只有需要**极致精细化控制底层事件流** 、不接受任何封装约束时，才选择原生手写：

■ 自定义特殊队列、自定义重试策略

■ 定制化缓存管理、特殊资源监听逻辑

■ 超高并发、超低延迟的核心组件

■ Kubernetes 内核级组件开发（kube-controller-manager、kube-scheduler 等）

### 优先使用 controller-runtime 的场景

95% 的企业业务开发、中间件扩展场景，都是它的主场：

■ 自定义 Controller、CRD Operator 开发

■ 集群自动运维、资源规范化管理平台

■ 各类云原生扩展组件（cert-manager、KEDA、Crossplane 等主流开源项目均基于此开发）

## 六、重新读懂 Kubebuilder：它真的不是框架

很多新手混淆核心概念，误以为 Kubebuilder 是独立的控制器开发框架。

**纠正：Kubebuilder 只是一个脚手架工具，和性能、运行逻辑毫无关系。**

它的唯一作用就是**自动生成标准化模板文件** ，帮你省去初始化工作：

■ 自动生成项目目录结构

■ 自动生成 Controller、CRD 模板代码

■ 自动生成 RBAC 权限、Webhook 配置

■ 自动生成 Dockerfile、Makefile 部署脚本

**重点：真正运行控制器、处理资源调度的，依然是 controller-runtime。**

所以学习优先级：**controller-runtime ＞ Kubebuilder** 。懂了框架核心，脚手架只是锦上添花。

## 七、建议：新手别一上来啃底层源码

很多人学习踩坑：刚入门就死磕 Informer、DeltaFIFO、队列源码，越学越懵，最终放弃。

我的实战学习建议：

**先会用，再懂底层；先写业务，再读源码。**

新手入门推荐先实现几个简单控制器，快速建立认知：

■ 自动为 Pod 补充默认 Label 标签

■ 自动为 Ingress 注入固定 Annotation

■ 监听 ConfigMap 变更，自动同步关联资源

写完你会瞬间顿悟 Kubernetes 控制器的**核心设计思想** ：

**持续监听资源变化，对比「期望状态」和「实际状态」，通过 Reconcile 逻辑不断修正差值。**

理解了这个核心模型，再回头研读 client-go 底层源码，所有设计（Informer、缓存、队列、重试）都会豁然开朗。

## 最后

回到大家最纠结的问题：**学 client-go 还是 controller-runtime？**

给大家最直白的结论：

■ **业务开发、写 Operator、做平台扩展** ：优先学 controller-runtime，高效、稳定、标准化，适配生产环境。

■ **深耕 K8s 内核、研究底层原理、做核心组件开发** ：学好框架后，再深入啃 client-go 源码。

controller-runtime 从未取代 client-go，它只是帮开发者摆脱重复造轮子的低效开发。

工具只是载体，**真正重要的是吃透 K8s 控制面核心思想：状态监听、差值比对、循环调和** 。

掌握了这套核心逻辑，无论用哪种方式开发，都能写出优雅、稳定的 Kubernetes 控制器。

