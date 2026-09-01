# Kubernetes Controller：从原理到实战，自动给 Pod 打标签

**作者**: 技术控杂谈
**发布时间**: 2026-07-14 08:30
**原文链接**: https://mp.weixin.qq.com/s/hz7MzvmP-vAIQJhVEgK72w

---

大家好，今天这篇文章我们不讲大而全的 Operator，也不从 Kubebuilder 脚手架起步，而是基于一套**非常小、但能跑起来的真实代码** ，带大家从 0 理解 Kubernetes Controller 的工作原理，并亲手实现一个功能：

**自动给新建的 Pod 打上` company=eagle` 标签。**

这个例子很适合用来建立对 Controller 的第一性认知：

1.Controller 到底是什么2.它为什么比脚本或 CronJob 更适合做持续治理3.`Reconcile 在做什么``4.一套最小可运行 Controller 代码应该怎么写`5.怎么在本地快速验证效果

如果你想入门 Kubernetes Operator / Controller 开发，这会是一个很好的起点。

## 一、为什么需要 Controller

在 Kubernetes 里，很多自动化能力本质上都来自 Controller。

比如：

1.Deployment Controller 负责把 Pod 副本数维持在期望值2.Job Controller 负责跟踪任务执行状态3.EndpointSlice Controller 负责根据 Service 和 Pod 状态维护流量转发关系

它们有一个共同点：

**不是“执行一次任务就结束”，而是持续地把集群状态拉回期望状态。**

这也是 Controller 和脚本、CronJob 的核心区别。

假设你的需求是：

> 所有 Pod 都必须带一个统一标签 `company=eagle`

很多人的第一反应可能是：

  1. 写一个脚本，定时扫描 Pod
  2. 用 CronJob 每分钟跑一次，给漏掉标签的 Pod 补上  

这当然能做：

  1. 修复不够实时，期间会有“裸奔窗口”
  2. 高频扫描会给 APIServer 带来额外压力
  3. 逻辑上是“周期轮询”，不是“事件驱动”
  4. 很难自然表达“期望状态”
  5. 而 Controller 的思路是：只要 Pod 发生变化，就触发调谐；如果当前状态不满足期望，就立即修正。  

这正是 Kubernetes 原生自动化最推荐的模式。

## 二、先理解 Controller 的核心原理

如果只记一句话，请记住这句：

**Controller = Watch 资源变化 + Reconcile 期望状态**

可以把它拆成 3 个部分来看。

### 1\. Watch：监听资源事件

Controller 会监听某类资源，比如这里监听的是 `Pod`。

当 Pod 被创建、更新、删除时，Kubernetes 事件会被送到 Controller 的工作队列。

### 2\. Queue：把事件转成待处理任务

Controller 并不是一来一个事件就立刻同步处理，而是把它们变成一个个待调谐请求，通常只保留资源身份信息：

```

type Request struct {
    NamespacedName types.NamespacedName
}
```

也就是说，进入 `Reconcile` 的通常不是完整对象，而是“这个对象是谁”。

### 3\. Reconcile：把现实状态拉回期望状态

`Reconcile` 的职责不是“响应事件本身”，而是：

> 根据资源当前真实状态，判断它是否满足期望；如果不满足，就执行修正动作。

所以 Controller 的思维方式不是：

“刚刚发生了创建事件，我要做点什么。”

而是：

“现在这个对象长什么样？它是否符合期望？不符合就修正。”

这就是声明式系统的关键。

## 三、本文示例要实现什么

本文的 Controller 非常聚焦，只做一件事：

**监听 Pod，如果发现 Pod 没有` company=eagle` 标签，就自动补上。**

最终效果如下：

```

metadata:
  labels:
    company: eagle
```

虽然功能简单，但它覆盖了 Controller 开发里最关键的几个动作：

  1. 创建 manager
  2. 注册 Reconciler
  3. 监听 Pod
  4. 在 Reconcile中获取对象
  5. 判断当前状态
  6. 使用 Patch 更新对象

你把这个例子吃透了，后面扩展到注解注入、默认配置补全、策略校验，甚至自定义资源控制器，都会顺很多。

## 四、项目结构很简单

当前代码结构如下：

```

CustomPodLabelController/
├── go.mod
├── main.go
└── pkg/
    └── controller.go
```

职责也很清晰：

  1. 1.`main.go：启动 manager，注册控制器`
  2. 2.`pkg/controller.go：真正的调谐逻辑`

## 五、入口代码怎么工作

我们先看 `main.go`，它做的是“把 Controller 跑起来”这件事。

### 1\. 初始化日志

```

log.SetLogger(zap.New())
logger := ctrl.Log.WithName("main")
```

这里使用的是 `controller-runtime` 推荐的日志体系，底层接了 `zap`。

它的意义很简单：

1.统一控制器日志风格2.让 manager 和 controller 使用同一套日志系统3.便于后续接入结构化日志

### 2\. 获取 Kubernetes 连接配置

```

cfg := ctrl.GetConfigOrDie()
```

这一行非常关键。

它会自动尝试获取连接 Kubernetes APIServer 的配置，常见有两种场景：

  1. **集群内运行：读取 Pod 挂载的 ServiceAccount 凭证**
  2. **本地调试：读取本机 kubeconfig**

所以同一份代码，既可以本地跑，也可以部署到集群里跑。

### 3\. 创建 Manager

```

mgr, err := ctrl.NewManager(cfg, ctrl.Options{
    Scheme: clientgoscheme.Scheme,
})
```

`Manager` 可以理解为控制器运行时的大管家。它会帮我们管理这些东西：

  1. Kubernetes 客户端
  2. 本地缓存
  3. Watch 机制
  4. Controller 生命周期
  5. 优雅退出

这里把 Kubernetes 内置资源注册进 `Scheme`，这样 Pod 这类原生对象才能被正确识别、序列化和缓存。

### 4\. 注册我们的 Pod Controller

```

if err := (&pkg.PodReconciler{
    Client: mgr.GetClient(),
}).SetupWithManager(mgr); err != nil {
    logger.Error(err, "unable to create controller")
    os.Exit(1)
}
```

这一步做了两件事：

  1. 创建 PodReconciler
  2. 把它注册到 manager 上

从这一刻起，manager 就知道：

> 有一个控制器要负责处理 Pod 相关事件。

### 5\. 启动 Manager

```

if err := mgr.Start(ctrl.SetupSignalHandler()); err != nil {
    logger.Error(err, "manager exited")
    os.Exit(1)
}
```

当 `mgr.Start(...)` 运行后，整个控制器才算真正开始工作：

  1. 建立 Watch
  2. 启动事件队列
  3. 拉起调谐 worker
  4. 等待资源事件到来

## 六、核心逻辑都在 Reconcile

真正体现 Controller 思想的，是 `pkg/controller.go` 里的 `Reconcile`。

### 1\. Reconcile 的目标

这段代码的目标很明确：

> 如果 Pod 没有 `company=eagle` 标签，就补上；如果已经有了，就什么都不做。

这就是一个标准的“声明式调谐”过程。

### 2\. 先根据请求拿到当前 Pod

```

pod := &corev1.Pod{}
err := r.Get(ctx, req.NamespacedName, pod)
if err != nil {
    if apierrors.IsNotFound(err) {
        return ctrl.Result{}, nil
    }
    return ctrl.Result{}, err
}
```

这里有两个关键点。

第一，`req` 里通常只有 `namespace/name`，所以进入 `Reconcile` 后，要自己去 APIServer 或缓存里取当前对象。

第二，为什么 `NotFound` 要直接返回 `nil`？

因为这通常说明：

  1. 对象已经被删除
  2. 事件到达时，对象已经不存在

这种情况不是异常，而是控制器世界里的正常现象，不需要重试。

### 3\. 处理空标签 map

```

if pod.Labels == nil {
    pod.Labels = map[string]string{}
}
```

这是一个很容易忽略、但非常重要的细节。

在 Go 里，往 `nil map` 写数据会直接 panic，所以在写标签前必须先初始化。

### 4\. 做幂等判断

```

if pod.Labels["company"] == "eagle" {
    return ctrl.Result{}, nil
}
```

这一步是 Controller 代码质量的关键。

为什么一定要强调幂等？

因为 Controller 天生会被反复触发：

  1. 创建事件会触发
  2. 更新事件会触发
  3. 重试会触发
  4. 缓存同步、状态漂移时也可能再次进入

如果你的调谐逻辑不是幂等的，就很容易产生重复写入、死循环更新，甚至资源抖动。

而这里的判断非常干净：

**已经满足期望状态，直接退出。**

###  5\. 为什么用 Patch，而不是 Update

```

old := pod.DeepCopy()
pod.Labels["company"] = "eagle"
err = r.Patch(ctx, pod, client.MergeFrom(old))
```

这段是本文里非常值得学习的地方。

很多刚开始写 Controller 的同学会直接 `Update` 整个对象，但更推荐的做法是：

**只提交最小必要变更。**

这里通过：

  1. 先 DeepCopy()一份旧对象
  2. 修改当前对象
  3. 使用 client.MergeFrom(old)计算差异最终只把标签变化提交到 Kubernetes。

这样做的好处是：

  1. 变更范围更小
  2. 降低资源版本冲突概率
  3. 避免误覆盖其他字段
  4. 更符合 Controller 的精细化更新方式

对于“给对象补一个标签/注解”这种场景，`Patch` 通常是优先选择。

### 6\. 注册 Watch 的方式

```

return ctrl.NewControllerManagedBy(mgr).
    For(&corev1.Pod{}).
    Complete(r)
```

这段配置表达的意思是：

> 创建一个由 manager 管理的 controller，并声明它关心 `Pod` 资源，最终由 `r` 这个 Reconciler 来处理。

也就是说，只要 Pod 发生变化，就有机会进入 `Reconcile`。

## 七、把整个调用链串起来

到这里，我们可以把当前代码的运行过程串成一条完整链路：

  1. `main.go 启动 manager`  

  2. manager 注册 PodReconciler
  3. controller-runtime 监听 Pod 资源事件
  4. Pod 创建或更新后，请求进入工作队列
  5. `Reconcile根据 namespace/name取回当前 Pod`
  6. 检查 company=eagle是否存在
  7. 如果不存在，就打补丁写回 Kubernetes
  8. Pod 达到期望状态，调谐结束

这就是一个最小 Controller 的完整闭环。

## 八、为什么说这比脚本方案更“原生”

如果用脚本或 CronJob 去做，你会得到一个“补丁程序”。

如果用 Controller 去做，你得到的是一个“持续治理系统”。

两者最大的区别在于：

### 1\. 事件驱动，而不是定时扫描

Pod 一变化就能处理，不需要等下一次轮询。

### 2\. 声明式，而不是命令式

我们表达的不是“执行一次打标签命令”，而是：

> Pod 最终应该具备这个标签。

### 3\. 天然具备自愈能力

如果标签被手工删掉，只要再次触发调谐，就会被补回来。

### 4\. 更适合规模化集群

在资源量上来之后，事件驱动的 Controller 往往比高频全量扫描更稳，更省资源，也更符合 Kubernetes 的设计哲学。

## 九、基于当前代码，怎么在本地实战

这套代码非常适合本地直连测试集群。

### 1\. 准备一个可用的 Kubernetes 集群

你可以使用任意一种：

  1. 本地 minikube
  2. 本地 kind
  3. 测试环境集群
  4. 云上开发集群

只要你的本机 `kubeconfig` 可用即可。

### 2\. 直接启动控制器

在项目根目录执行：

```

go run .
```

如果启动成功，它会连接当前 `kubeconfig` 指向的集群，并开始监听 Pod。

![](https://r2.jeanjan.kdns.fr/pictures/img-fcd25ca201.png)

### 3\. 创建一个测试 Pod

比如直接创建一个最简单的 Nginx Pod：

```

kubectl run label-demo --image=nginx 
```

![](https://r2.jeanjan.kdns.fr/pictures/img-fcd25ca202.png)

### 4\. 检查标签是否被自动补上

执行：

```

kubectl get pod label-demo -o yaml
```

![](https://r2.jeanjan.kdns.fr/pictures/img-fcd25ca203.png)

如果控制器工作正常，你会在输出里看到：

```

metadata:
  labels:
    company: eagle
```

### 5\. 再做一次反向验证

你还可以手工把标签删掉，再观察控制器是否会重新补回去。

例如：

```

kubectl label pod label-demo company-
```

然后再次查看 Pod：

```

kubectl get pod label-demo -o yaml
```

如果重新出现 `company=eagle`，说明这个 Controller 的调谐闭环已经生效。

![](https://r2.jeanjan.kdns.fr/pictures/img-fcd25ca204.png)

## 十、初学 Controller 最容易踩的几个坑

最后，顺手总结几个常见问题。

### 1\. 把 Reconcile 写成“事件响应函数”

这是最常见的误区。

`Reconcile` 不应该只关心“发生了什么事件”，而应该关心：

> 当前资源状态是什么，和期望状态差多少。

### 2\. 忘记做幂等

如果没有“已满足就退出”的判断，控制器很容易反复写对象。

### 3\. 直接 Update 整个对象

对于小范围字段变更，更推荐 Patch，能显著降低误覆盖风险。

### 4\. 没处理 NotFound

资源被删掉是正常情况，不应该把它当系统异常。

### 5\. 本地调试时忽略 kubeconfig 指向

`go run .` 会连你当前上下文对应的集群，调试前一定要确认自己连的是测试环境，而不是生产环境。

## 十一、总结

这篇文章我们基于一套极小的 Go 代码，实现了一个最小可运行的 Kubernetes Controller，并把它背后的核心思想走了一遍。

你应该已经掌握了下面这些关键点：

  1. Controller 的本质是 Watch + Reconcile
  2. Controller 适合做持续治理，不适合用脚本思维去理解
  3. `Reconcile 的核心是比较“当前状态”和“期望状态”`
  4. 幂等性是 Controller 正确性的基础
  5. 对小范围字段修改，Patch往往比 Update更合适

虽然今天的例子只是给 Pod 自动打一个标签，但它已经具备了 Controller 的完整骨架。

后面你完全可以在这个基础上继续扩展，比如：

  1. 自动补充注解
  2. 自动注入 sidecar 配置
  3. 给特定业务 Pod 追加默认资源限制
  4. 基于自定义 CRD 实现更完整的 Operator  

很多看起来“很高级”的 Kubernetes 自动化系统，底层其实就是这一套思路的延展。

## 附：本文对应的关键代码文件

为了方便你对照阅读，本文对应的源码入口就是这两个文件：

  1. 1.`main.go`
  2. 2.`pkg/controller.go`

如果你正在带团队做 Kubernetes 工程化，我很建议先让大家把这种**最小 Controller** 吃透，再往 Kubebuilder、Operator Framework、自定义资源这些方向扩展，学习曲线会平滑很多。

## 附录：完整代码

为了方便大家直接复制验证，下面贴出本文示例的完整代码。

### 1\. `main.go`

```

package main
import (
"os"
"CustomPodLabelController/pkg"
	clientgoscheme "k8s.io/client-go/kubernetes/scheme"
	ctrl "sigs.k8s.io/controller-runtime"
"sigs.k8s.io/controller-runtime/pkg/log"
"sigs.k8s.io/controller-runtime/pkg/log/zap"
)
func main() {
// 初始化 controller-runtime Logger
	log.SetLogger(zap.New())
	logger := ctrl.Log.WithName("main")
// 用于自动获取连接 Kubernetes APIServer 的配置（集群内或 kubeconfig）
	cfg := ctrl.GetConfigOrDie()
// 注册 Kubernetes 内置资源到 scheme，确保 Pod 可以被缓存和序列化。
	mgr, err := ctrl.NewManager(cfg, ctrl.Options{
		Scheme: clientgoscheme.Scheme,
	})
if err != nil {
		logger.Error(err, "unable to create manager")
		os.Exit(1)
	}
// 注册 Pod Controller。
if err := (&pkg.PodReconciler{
		Client: mgr.GetClient(),
	}).SetupWithManager(mgr); err != nil {
		logger.Error(err, "unable to create controller")
		os.Exit(1)
	}
	logger.Info("starting manager")
// 启动 manager，开始监听和处理事件。
if err := mgr.Start(ctrl.SetupSignalHandler()); err != nil {
		logger.Error(err, "manager exited")
		os.Exit(1)
	}
}
```

### 2\. `pkg/controller.go`

```

package pkg
import (
"context"
"log"
	corev1 "k8s.io/api/core/v1"
	apierrors "k8s.io/apimachinery/pkg/api/errors"
"sigs.k8s.io/controller-runtime/pkg/client"
	ctrl "sigs.k8s.io/controller-runtime"
)
type PodReconciler struct {
// Client 由 controller-runtime 注入，用于与 Kubernetes APIServer 交互。
// 这里复用通用客户端能力，完成 Pod 的查询与标签更新。
	client.Client
}
// Reconcile 是控制器的核心调谐入口。
// 当监听到 Pod 的创建、更新、删除等事件时，controller-runtime 会把对应请求投递到这里。
// 当前控制器的目标很明确：确保每个被处理到的 Pod 都带有 company=eagle 标签。
func (r *PodReconciler) Reconcile(
	ctx context.Context,
	req ctrl.Request,
) (ctrl.Result, error) {
// 根据事件里携带的命名空间和名称，构造一个待查询的 Pod 对象。
	pod := &corev1.Pod{}
	err := r.Get(ctx, req.NamespacedName, pod)
if err != nil {
// 如果资源已经不存在，说明对象可能在事件到达前就被删除了。
// 这种情况不需要重试，直接结束本次调谐即可。
if apierrors.IsNotFound(err) {
return ctrl.Result{}, nil
		}
// 其余错误通常是 APIServer 短暂异常、网络问题或权限问题，交给框架重试。
return ctrl.Result{}, err
	}
// 避免对 nil map 直接写入导致 panic，先初始化标签集合。
if pod.Labels == nil {
		pod.Labels = map[string]string{}
	}
// 如果目标标签已经存在，说明当前对象已满足期望状态，无需重复更新。
if pod.Labels["company"] == "eagle" {
return ctrl.Result{}, nil
	}
// 先拷贝一份旧对象，后续使用 MergeFrom 生成最小变更补丁。
// 这样只会提交标签差异，避免把整个对象完整覆盖回去。
	old := pod.DeepCopy()
// 写入控制器期望维护的标签值。
	pod.Labels["company"] = "eagle"
	err = r.Patch(ctx, pod, client.MergeFrom(old))
if err != nil {
// 更新失败时返回错误，让 controller-runtime 按默认策略重试。
return ctrl.Result{}, err
	}
// 记录一次成功调谐，方便在本地调试或控制器日志中追踪处理结果。
	log.Printf(
"patched pod %s/%s\n",
		pod.Namespace,
		pod.Name,
	)
return ctrl.Result{}, nil
}
// SetupWithManager 把当前 Reconciler 注册到 controller-manager 中。
// 这里声明该控制器只关心 Pod 资源，manager 会据此建立 Watch 和事件分发链路。
func (r *PodReconciler) SetupWithManager(
	mgr ctrl.Manager,
) error {
return ctrl.NewControllerManagedBy(mgr).
		For(&corev1.Pod{}).
		Complete(r)
}
```


