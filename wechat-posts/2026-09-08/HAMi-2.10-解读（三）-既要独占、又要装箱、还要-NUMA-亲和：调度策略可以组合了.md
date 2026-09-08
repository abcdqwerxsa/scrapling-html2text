# HAMi 2.10 解读（三）| 既要独占、又要装箱、还要 NUMA 亲和：调度策略可以组合了

**作者**: HAMi Project
**发布时间**: 2026-09-02 11:21
**原文链接**: https://mp.weixin.qq.com/s/RxnfP9070V7_FfDBvmNZ3Q

---

![](https://r2.jeanjan.kdns.fr/pictures/img-57fa539201.gif)

> 推理副本要紧凑装箱，多卡要落同一 NUMA 节点保带宽，时延敏感的负载干脆独占几张卡——一句话里三种策略，以前只能选一个。本文是 HAMi 2.10 解读系列第三篇：讲清“先过滤、后排序”的求值模型，并用四张 T4 上的真实选择路径逐一验证。

系列前两篇讲了 HAMi 与外部调度器的集成：KAI Scheduler 之于 NVIDIA GPU（解读一），Volcano 之于昇腾 NPU（解读二）。本篇回到 HAMi 自己的调度器，看 v2.10.0 里另一个容易被忽视但很实用的调度特性：**可组合调度策略** 。

HAMi 一直通过 `hami.io/gpu-scheduler-policy` 注解提供按 Pod 生效的 GPU 调度策略：`binpack` 尽量把负载堆叠到少数卡上，`spread` 尽量打散，v2.10.0 新增的 `mutex` 则要求独占一张卡。但在 v2.10.0 之前，这个注解只能填**一个** 值。

真实集群很少只需要一种行为。一份典型的生产诉求是这样的：推理副本要紧凑装箱，留出整卡空闲；同时每个 Pod 的多卡要落在同一 NUMA 节点上以保证带宽；而时延敏感的那批负载，干脆要独占几张卡。一句话里出现了**三种** 策略。在 v2.10.0 之前，你只能选一个，放弃其余。

v2.10.0 补上了这块拼图：`hami.io/gpu-scheduler-policy` 现在接受**有序的、逗号分隔的列表** ，过滤型与排序型策略可以组合（PR #2621，@mesutoezdil，关闭 issue #2010）：
```

# 仅独占 GPU，再紧凑装箱，NUMA 作为决胜  
metadata:  
  annotations:  
    hami.io/gpu-scheduler-policy: "mutex,binpack,numa"
```

## 两类策略：过滤器与排序键

理解这个特性的关键是认识到：HAMi 的 GPU 策略从来就不是同一种东西，它们分属两种角色：

| 策略               | 角色                 | 作用                                        |
|------------------|--------------------|-------------------------------------------|
| `mutex`          | **过滤器**            |  只有当前没有任何负载的卡才是候选，所有已被占用的卡都被筛掉            |
| `topology-aware` | **过滤器** （仅 NVIDIA） | 只保留 NVLink/NVSwitch 拓扑满足多卡请求的卡，需先启用拓扑感知调度 |
| `binpack`        | **排序键**            |  偏好使用率最高的合格卡，让负载集中                        |
| `spread`         | **排序键**            |  偏好使用率最低的合格卡，让负载分散                        |
| `numa`           | **排序键**            |  偏好 NUMA 节点编号更低的卡，提升 locality             |

过滤器回答的是每张卡一个是非题：这张卡到底能不能参与；排序键回答的是排序题：在合格卡中谁排第一。两种角色天然不冲突，因此可以组合：**过滤器先运行、缩小候选集，排序键再对幸存者排序。**

##  调度器如何求值一条策略链

HAMi 调度器在过滤和打分一个节点的 GPU 时，策略链按固定流水线求值：

![](https://r2.jeanjan.kdns.fr/pictures/img-57fa539202.png)

规则依次是：

  1. 1\. **解析。** 注解按逗号切分，忽略每一项两侧的空白，重复项被丢弃，只有已知的策略名会生效。
  2. 2\. **先过滤。**` mutex` 和 `topology-aware` 在任何排序之前生效。对带 `mutex` 的 Pod 来说，一张卡是否合格只看一个问题：这张卡当前是否一个租户都没有？哪怕卡上只跑着一个很小的负载、剩余显存再多，这张卡也会被整体排除。当所有卡都有租户时，Pod 保持 Pending，原因为 `ExclusiveDeviceAllocateConflict`。
  3. 3\. **按书写顺序排序。**` binpack`、`spread`、`numa` 构成一个有序的排序键列表。第一个键起决定作用：`binpack,numa` 先按 binpack 排序，只有当 binpack 给两张卡打出相同分数时，才用 NUMA 节点编号决胜负；写成 `numa,binpack` 则优先级相反。**列表的顺序就是键的顺序。**
  4. 4\. **确定性决胜。** 如果两张卡在链上所有键下都比较结果相同，设备索引更小者胜出。因此在空闲集群上，相同的请求会产生相同、可复现的放置结果。
  5. 5\. **仅含过滤器时回退。** 一条完全不含排序键的链（例如 `"mutex,topology-aware"`）在过滤之后回退为 `spread` 排序。
  6. 6\. **单值行为不变。** 单独的 `"binpack"`、`"spread"` 或 `"mutex"` 与 v2.10.0 之前的行为完全一致，升级时存量负载无需任何改动。

## 排序键到底在比什么

对 `binpack` 和 `spread` 来说，“最满/最空”不是拍脑袋：调度器根据每张卡已分配的算力和显存计算利用率得分，权重由 slot、core、memory 三项组成（可以用 `hami.io/device-scoring-weights` 注解按 Pod 调整权重）。`binpack` 选**分数最高** 的卡，`spread` 选**分数最低** 的卡。`numa` 键比较的是 NVML 上报的每张卡所在 NUMA 节点编号。

值得一提的是 v2.10.0 同时修复了一个相关老问题（PR #2012）：此前即使指定纯 `binpack`/`spread`，NUMA 也是 _首要_ 排序键，导致负载无视实际利用率地被钉死在一个 NUMA 节点上。修复后，利用率得分成为主键，NUMA 只做决胜——这正是 `numa` 在策略链中扮演的 tiebreaker 角色。

## 实例：一个 Pod 在四张卡上的选择路径

把上面的流程放进真实场景：一个节点、四块 Tesla T4，一个带 `mutex,binpack` 注解、申请 1 个 vGPU（1000 MiB 切片）的 Pod 待调度。每张卡标出了租户数与利用率得分，箭头就是选择路径：

![](https://r2.jeanjan.kdns.fr/pictures/img-57fa539203.png)

从图中可以读出两件事：

  * • 最忙的 GPU 0 根本没有进入排序步骤：`mutex` 过滤器先把它剔除了，尽管纯 `binpack` 会以 3.30 的最高分优先选它。**过滤先于排序，组合链压根不会考虑纯****`binpack`**** 会选的那张卡。**
  * • 两张幸存卡得分相同（都是 0.00），`binpack` 无法区分，链继续落到设备索引决胜，确定性地选择 GPU 2。

这些数字来自实测：实验中带一个 1000 MiB 租户的卡得分 `1.651042`，空闲卡得分 `0.000000`，均来自调度器的打分日志。

## 常用配方

| 注解                     | 含义                             |
|------------------------|--------------------------------|
| `"binpack"`            | 把该 Pod 堆到能放下的最忙的卡上，最大化整卡空闲     |
| `"spread"`（默认）         | 放到最空的卡上，最小化邻居间的争抢              |
| `"mutex"`              | 要求一张当前零用户的卡                    |
| `"binpack,numa"`       | 紧凑装箱；装箱打平时偏好 NUMA 编号更低的卡       |
| `"mutex,binpack"`      | 独占且紧凑：在空闲卡中选最忙的一张，降低碎片化        |
| `"mutex,binpack,numa"` | “时延层”配方：独占卡、空闲卡中紧凑装箱、NUMA 作为决胜 |

关于 `mutex` 语义的一个重要说明：它保证的是**放置时刻** 这张卡没有用户，之后调度的普通 Pod 仍可能加入这张卡。若要让卡在负载整个生命周期内保持独占，请申请它的全部资源（显存和算力），或用 `nvidia.com/use-gpuuuid` 显式固定。

## 三步上手

**1\. 升级到 HAMi v2.10.0 或更高版本：**
```

 helm repo add hami-charts https://project-hami.github.io/HAMi/  
helm repo update  
helm upgrade hami hami-charts/hami -n kube-system --version 2.10.0
```

集群级默认值仍是节点选择 `binpack`、卡选择 `spread`，升级不会改变任何默认值。

**2\. 给需要组合行为的 Pod 打注解：**
```

 apiVersion: v1  
kind: Pod  
metadata:  
  name: inference-latency-tier  
  annotations:  
    hami.io/gpu-scheduler-policy: "mutex,binpack,numa"  
spec:  
  containers:  
    - name: app  
      image: ubuntu:22.04  
      command: ["bash", "-c", "sleep 86400"]  
      resources:  
        limits:  
          nvidia.com/gpu: 1      # 1 个 vGPU  
          nvidia.com/gpumem: 8000 # 显存配额 8000 MiB
```

**3\. 验证决策。** 调度器会把选中的卡写到 Pod 上，无需进入容器即可验证放置结果：
```

# 选中卡的设备 UUID、厂商、显存切片与算力百分比  
kubectl get pod inference-latency-tier \  
  -o jsonpath='{.metadata.annotations.hami\.io/vgpu-devices-allocated}'; echo
```

对于保持 Pending 的 `mutex` Pod，`kubectl describe pod` 会显示 `ExclusiveDeviceAllocateConflict` 原因；调度器在过滤时也会为每张候选卡输出一行利用率打分日志（`computer score is`），可以直接观察 `binpack` 与 `spread` 的排序依据：
```

kubectl -n kube-system logs deploy/hami-scheduler -c vgpu-scheduler-extender \  
  --tail=-1 | grep 'computer score' | tail
```

## 在真实集群上试试

读过滤器与排序键是一回事，亲眼看一个 `mutex` Pod 在你释放一张卡之前一直 Pending，再看 `mutex,binpack` 拒绝纯 `binpack` 本会选中的卡，是另一回事。实验 14 在一台挂四块 Tesla T4 的 GKE 节点上跑完整的特性矩阵：默认 `spread`、`binpack` 堆叠、`mutex` 阻塞与释放、组合的 `mutex,binpack` 行为，全部通过分配注解、事件和调度器日志验证。

## 总结

  * • HAMi 的 GPU 调度策略分两类：`mutex`/`topology-aware` 是**过滤器** （决定谁能参选），`binpack`/`spread`/`numa` 是**排序键** （决定谁排第一），两类天然可组合；
  * • v2.10.0 让注解接受有序的逗号分隔列表，求值模型是“先过滤、后按书写顺序排序、设备索引决胜”，单值行为与升级前完全一致；
  * • 顺手修复的 NUMA 首要排序键老问题，让 `numa` 回归 tiebreaker 本位——利用率得分才是主键。

一句话总结：**HAMi 的调度策略从“单选题”变成了“配方”。**

本文作者宋净超（Jimmy Song），来自密瓜智能。

## 系列阅读

  * • 本系列上一篇：[《HAMi 2.10 解读（二）：一张昇腾卡切给两个 Pod——Volcano + HAMi-core vNPU 软切分实测》](https://mp.weixin.qq.com/s?__biz=Mzk1NzQ1MzEzMQ==&mid=2247486763&idx=1&sn=5d33209a385d0c67b283369f6d31b31a&scene=21#wechat_redirect)
  * [HAMi 2.10 解读（一）| 实测 KAI Scheduler + HAMi GPU 显存硬隔离：谁也别想多占 1 MiB](https://mp.weixin.qq.com/s?__biz=Mzk1NzQ1MzEzMQ==&mid=2247486732&idx=1&sn=e3abe5c22d463921b4eec609bf3d5f58&scene=21#wechat_redirect)
  * [《HAMi v2.10.0 发布：Flexible MIG、可组合调度策略与更广阔的加速器生态》](https://mp.weixin.qq.com/s?__biz=Mzk1NzQ1MzEzMQ==&mid=2247486686&idx=1&sn=83d7f577264842901950ad88ee9c2068&scene=21#wechat_redirect)
  * • 动手实验：《实验 14：在 GKE 上验证可组合调度策略》

## 参考资料

以下链接为纯文本，可复制到浏览器打开：

  * • 本文官网原文：  
https://project-hami.io/zh/blog/composable-scheduler-policies
  * • HAMi v2.10.0 发布公告：  
https://project-hami.io/zh/blog/hami-v2-10-0-release
  * • 实验 14 教程（GKE 完整复现步骤）：  
https://project-hami.io/zh/tutorials/labs/composable-scheduler-policies-gke
  * • PR #2621（comma-separated gpu-scheduler-policy）：  
https://github.com/Project-HAMi/HAMi/pull/2621
  * • Issue #2010（Composable scheduling policies）：  
https://github.com/Project-HAMi/HAMi/issues/2010
  * • 调度策略设计文档：  
https://project-hami.io/zh/docs/developers/scheduling
  * • 配置参考：  
https://project-hami.io/zh/docs/userguide/configure

![](https://r2.jeanjan.kdns.fr/pictures/img-57fa539204.jpeg)

  

如需转载，请保留全文；如需改写，请先通过微信 `HAMi_community` 联系我们。

### 关于HAMi

HAMi 是由李孟轩与张潇共同发起的异构算力虚拟化与统一调度开源项目，现为 CNCF Incubating 项目，以“让异构算力因开源而好用”为目标，致力于提升异构算力利用率，并为异构 GPU 提供统一的复用接口。目前，HAMi 已支持 NVIDIA、AMD、昇腾、寒武纪、海光、天数智芯、摩尔线程、沐曦、燧原、昆仑芯、壁仞、AWS Neuron、瀚博半导体等多种异构算力，与 Volcano、Kueue、Koordinator、vLLM、KAI Scheduler 等项目广泛集成，吸引了来自全球 20 多个国家和地区的 500 余名贡献者参与，并已在数百家企业实现生产落地。  

![](https://r2.jeanjan.kdns.fr/pictures/img-57fa539205.png)

  
社区官网：https://project-hami.ioGitHub：https://github.com/Project-HAMi/HAMi  
  


