# 支撑Kimi推理的Mooncake能力升级，KV Cache可卸载到SSD了！

**作者**: 智猩猩AI
**发布时间**: 2026-07-24 08:54
**原文链接**: https://mp.weixin.qq.com/s/FfkMOahdh56bP_n7-TIDxQ

---

智猩猩AI整理编辑：没方  
月之暗面的 Kimi K3 模型凭借百万级上下文推理能力引发行业关注。  
但要让这类长上下文能力在大规模在线服务中具备可接受的成本和延迟，仅靠模型本身并不够，还需要高效的推理服务基础设施。  
Mooncake 是用于支撑 Kimi 服务的以 KV Cache 为中心的分布式推理架构，由月之暗面和清华大学 MADSys 实验室联合趋境科技、阿里云、蚂蚁集团等产学研力量共同开源和建设。核心目标是让模型处理过的上下文能够被更高效地保存、复用和迁移。  
![](https://r2.jeanjan.kdns.fr/pictures/img-cf2402d001.png)  

最近，Mooncake 正式发布 SSD Offloading 功能。

  

它将KV Cache从昂贵的内存资源扩展到SSD存储层，通过GPU HBM、Host DRAM以及NVMe SSD构建分层KV Cache存储体系，大幅提升长上下文场景下的缓存容量。

  

![](https://r2.jeanjan.kdns.fr/pictures/img-cf2402d003.jpeg)

Mooncake 整体分层架构图

  

 _**01**_

**Mooncake SSD Offloading**

**的缓存分层策略  

要理解Mooncake SSD Offloading，首先需要理解大模型推理过程中一类非常重要的数据：KV Cache。

  

在基于Transformer的自回归模型中，一次推理通常可以分为Prefill和Decode两个阶段。

  

Prefill阶段负责处理用户输入的所有Token，并产生第一个输出Token。模型会保存注意力计算中间产生的Key和Value，这些数据就是KV Cache。进入Decode阶段后，模型每次只生成一个新Token。它不需要重新计算此前所有Token，可以直接读取已经保存的KV Cache。

  

但模型层数越多、上下文越长、并发请求越多，需要保存的KV Cache就越大。

  

（1）如果把所有KV Cache长期保留在GPU显存中，访问速度最快，但GPU HBM容量有限、成本高昂，还要同时容纳模型权重和当前推理任务，很难承担大规模长期缓存。

  

（2）直接删除缓存虽然能够释放空间，但当相同前缀再次出现时，GPU就要重新执行Prefill，把已经完成的计算再做一遍。

  

（3）将KV Cache卸载到Host DRAM，可以缓解GPU显存压力，但DRAM同样不是无限的。在长时间、多会话和高并发运行后，内存池也会逐渐被填满。

  

那么，不同访问频率、不同重算成本的KV Cache，能否放进不同层级的存储设备？

  

从整个推理系统的视角看，正在参与生成、对延迟最敏感的热点缓存，可以保留在GPU HBM中；短期内可能再次访问的温缓存，可以迁移到Host DRAM；访问频率较低、但重新计算成本较高的冷缓存，则可以进一步下沉到容量更大、单位成本更低的NVMe SSD。

  

Mooncake SSD Offloading正是沿着这一思路，为分布式KV Cache池增加SSD存储层。如下图所示：

  

![](https://r2.jeanjan.kdns.fr/pictures/img-cf2402d004.png)

  

当DRAM空间不足时，原本可能被直接淘汰的KV Cache对象，可以由后台线程异步写入本地NVMe SSD；当后续请求再次命中这些上下文时，系统可以从SSD中读取并恢复缓存。

  

SSD Offload 的写入路径完全由心跳线程驱动，不会阻塞任何应用的写入路径。

  

心跳线程定期向 Master 上报状态，Master 返回需要从内存卸载到 SSD 的对象列表，心跳线程执行写入并通知 Master 完成。完整的交互时序：

  

![](https://r2.jeanjan.kdns.fr/pictures/img-cf2402d005.png)

  

读取 SSD 缓存时，数据先被加载到一个预注册的、O_DIRECT 对齐的 Staging Buffer，然后再零拷贝地送入应用内存。这避免了用户态与内核态之间的多余数据拷贝，把 SSD 读取的延迟控制在可接受范围内。完整加载过程如下：

  

![](https://r2.jeanjan.kdns.fr/pictures/img-cf2402d006.png)

  

 _**02**_

**性能数据展示   

研究团队测试对比了 KV Cache 的四种存储配置：

  * **GPU only** ：KV Cache 完全驻留在 GPU 显存中；

  * **(HiCache L1) + L2** ：KV Cache 通过 HiCache 的两层架构跨越 GPU 显存和主机内存；

  * **(HiCache L1 + L2) + Mooncake** ：KV Cache 进一步扩展至一个 80GB 的 Mooncake 分布式内存池；

  * **(HiCache L1 + L2) + Mooncake + SSD** ：在上述配置基础上，启用 SSD Offload，被驱逐的缓存条目将写入本地 NVMe 存储，而非直接丢弃。

  

![](https://r2.jeanjan.kdns.fr/pictures/img-cf2402d007.png)

  

从上面的测试结果可以看出，启用 SSD Offload 后，平均 TTFT 相比纯 GPU 方案降低了 57%，相比不带 SSD 的 Mooncake 方案降低了 34%；并且输入 token 吞吐量也可以看出明显提升。

  

![](https://r2.jeanjan.kdns.fr/pictures/img-cf2402d008.png)

  

上图实验按对话轮次拆解了 TTFT 和缓存命中率，可以看出前六轮对话，80GB 内存池容量充足，因此 + Mooncake 和 + Mooncake + SSD 两组配置的表现差不多。

  

差异出现在第七轮。

  

当累积的 KV Cache 超出内存容量后，+ Mooncake 的配置需要驱逐缓存条目，因此命中率从 83% 骤降至 36%，TTFT 也从 6 秒飙升至 16 秒。

  

启用 SSD Offload 后，被驱逐的缓存条目仍然存活在磁盘上并可被重新读取，因此命中率到第八轮仍保持在 84% 以上，TTFT 稳定在 9.4 秒，约是不带 SSD 的 Mooncake 方案延迟的一半。

  

 _**03**_

**总结  

SSD Offload 把本地 NVMe 硬盘变成了缓存体系中的“增量层”。在生产环境里，长上下文和高并发是常态，纯靠内存缓存的方案一旦撑爆就会性能就会急剧下降，而 SSD Offload 恰好填上了这个坑。

  

参考资料：

https://github.com/kvcache-ai/Mooncake；

https://kvcache-ai.github.io/Mooncake/design/ssd-offload.html；

https://kvcache-ai.github.io/Mooncake/performance/mooncake/ssd-offload-benchmark-results.html

[Mooncake SSD Offloading：突破内存限制，扩展 KV Cache 容量](https://mp.weixin.qq.com/s?__biz=MzY5MjM0MTcxMg==&mid=2247483732&idx=1&sn=068e4a7991b67acb24b0509663df399d&scene=21#wechat_redirect)

  

**END**

  

**关注+星标，获取AI前沿进展与优质开源项目**

