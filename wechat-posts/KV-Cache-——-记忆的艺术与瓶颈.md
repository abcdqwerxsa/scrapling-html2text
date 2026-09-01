# KV Cache —— 记忆的艺术与瓶颈

**作者**: 过拟合AI
**发布时间**: 2026-06-04 23:43
**原文链接**: https://mp.weixin.qq.com/s/kXCYeGiLrDyC_LhyZ_HXVg?scene=1&click_id=12

---

> 为什么同一个模型，短回答很快，长文续写却越来越慢？为什么 128K 上下文看起来只是"多塞点文本"，部署成本却会爆炸？答案不是模型"变笨"了，而是每生成一个 token，服务端都在搬运越来越长的历史状态：KV Cache。

![封面](https://r2.jeanjan.kdns.fr/pictures/img-f109b9bb01.png)

## 一、问题不是"算不动"，而是"记不下"

你用 LLM 时会看到两个完全不同的延迟指标：

• TTFT（Time To First Token）：从请求发出到第一个 token 出来的时间。

• TPOT（Time Per Output Token）：后续每生成一个 token 平均要多久。

长 prompt 会拖慢 TTFT，因为模型要先把整段输入过一遍。长输出会拖慢 TPOT，因为每一步 decode 都要读取更长的历史 KV Cache。前者更像"通读材料"，后者更像"一边写一边翻越来越厚的笔记"。

KV Cache 的核心作用很简单：把历史 token 的 Key 和 Value 存起来，避免每生成一个新 token 都重新计算整段前缀。 它显著提高速度，但代价是显存会随序列长度线性增长。

MQA、GQA、MLA、PagedAttention 这些看似不同的技术，最后都在围绕同一个问题打转：少存一点、少搬一点、别浪费已经分配的显存。

## 二、推理分两段：Prefill 和 Decode

LLM 推理不是一个均匀过程，而是两个瓶颈明显不同的阶段。

### 2.1 Prefill：一次性读完整段 prompt

假设用户输入 2000 个 token。Prefill 阶段会把这 2000 个 token 一次性送进模型。对每一层来说，输入张量大致是：
```

x: [batch, seq_len, hidden_dim]
```

模型会投影出 Q、K、V：
```

Q = x @ W_q  
K = x @ W_k  
V = x @ W_v
```

然后计算 attention：
```

Attention(Q, K, V) = softmax(QK^T / sqrt(d)) V
```

只看 attention 子层，Prefill 有一个随 `seq_len²` 增长的矩阵乘；再加上每层的投影和 FFN，整体计算量很大。但它有一个优势：所有 prompt token 可以并行处理。GPU 喜欢大矩阵乘，FlashAttention、Tensor Core、张量并行都能发挥作用。

因此在常见服务条件下，Prefill 往往更偏 compute-bound。它主要吃算力，决定首 token 延迟。

### 2.2 Decode：一次只生成一个 token

Prefill 结束后，模型开始逐 token 生成。第 `t` 步 decode 时，新输入只有上一步生成的 token。模型只需要为这个新 token 计算一份新的 Q、K、V：
```

q_new: [batch, 1, n_q_heads, head_dim]  
k_new: [batch, 1, n_kv_heads, head_dim]  
v_new: [batch, 1, n_kv_heads, head_dim]
```

新的 K/V 会追加到 KV Cache 末尾；新的 Q 则要和历史所有 K/V 做 attention。也就是说，每一步新增计算不大，但要读取的历史缓存越来越长：
```

KV Cache at step t:  
K_cache, V_cache: [batch, t, n_kv_heads, head_dim]
```

这就是 decode 的麻烦之处：单步矩阵很小，GPU 算力吃不满；同时每一步都要从显存读取大量历史 K/V。于是它往往更偏 memory-bound。

| 阶段      | 输入形状     | 主要工作                   | 常见瓶颈             | 典型优化                                             |
|---------|----------|------------------------|------------------|--------------------------------------------------|
| Prefill | `[B, N]` | 一次性处理整段 prompt         | 算力、首 token 延迟    | FlashAttention、chunked prefill、张量并行              |
| Decode  | `[B, 1]` | 每步生成一个新 token，并查询历史 KV | 显存带宽、KV Cache 容量 | GQA/MLA、KV 量化、PagedAttention、continuous batching |

## 三、KV Cache 到底存了什么？

Attention 里的 Q、K、V 可以简单理解为：Q 是当前 token 的查询，K 是历史 token 的匹配索引，V 是匹配后取回的内容。Decode 时，历史 token 的 K/V 不会因为新 token 到来而改变；如果不缓存，每一步都要重新计算整段历史 K/V。

KV Cache 保存的是每一层的历史 K/V，而不是全模型共享一份缓存。80 层模型就有 80 份逐层缓存。它和权重不同：权重是固定成本，请求进来前就已加载；KV Cache 是请求相关成本，会随着 batch、上下文长度和输出长度增长。

## 四、内存公式：每个 token 到底多少钱？

标准估算公式是：
```

KV Cache bytes  
= 2 × batch × seq_len × n_layers × n_kv_heads × head_dim × bytes_per_element
```

其中：

• `2`：同时存 K 和 V。

• `batch`：并发序列数。

• `seq_len`：prompt token + 已生成 token。

• `n_layers`：Transformer 层数。

• `n_kv_heads`：KV head 数，不一定等于 query head 数。

• `head_dim`：每个 head 的维度。

• `bytes_per_element`：FP16/BF16 通常是 2，INT8 是 1，INT4 理论上是 0.5。

### 4.1 先算一个 MHA 70B 基线

为了看清量级，先假设一个 70B 级别 MHA 模型：
```

n_layers = 80  
n_kv_heads = 64  
head_dim = 128  
dtype = fp16 = 2 bytes
```

单条序列的 KV Cache：

| 上下文长度 | KV Cache  |
|-------|-----------|
| 4K    | 10.0 GiB  |
| 32K   | 80.0 GiB  |
| 128K  | 320.0 GiB |

这只是 batch=1。如果 batch=8，4K 上下文就会变成约 80 GiB KV Cache；再加上 70B FP16 权重约 140 GB、运行时缓冲区和框架开销，显存压力会非常快地失控。

### 4.2 真实模型通常已经用了 GQA

上面的 70B MHA 是基线，不是 Llama 2-70B / Llama 3-70B 的真实缓存大小。Llama 2-70B 使用 GQA，64 个 query heads 共享 8 个 KV heads。KV Cache 相比 64 KV heads 的 MHA 基线缩到 `1/8`：

| 模型口径               | KV heads | 4K       | 128K      |
|--------------------|----------|----------|-----------|
| 70B MHA 基线         | 64       | 10.0 GiB | 320.0 GiB |
| 70B GQA，8 KV heads | 8        | 1.25 GiB | 40.0 GiB  |

这就是为什么看模型 config 时，`num_key_value_heads` 比 `num_attention_heads` 更关键。参数量告诉你权重多大；KV head 数告诉你长上下文和并发会多贵。

## 五、为什么 KV Cache 会卡 batch size？

服务端最怕的不是单个请求，而是一堆请求同时来。权重只加载一次，但 KV Cache 是每个请求一份。

假设你部署一个 70B GQA 模型，4K 上下文，FP16 KV Cache：
```

单请求 KV Cache ≈ 1.25 GiB  
batch = 16  →  约 20 GiB  
batch = 64  →  约 80 GiB  
batch = 128 →  约 160 GiB
```

这还没算输出继续增长。一个请求如果从 4K prompt 继续生成 2K token，它的 `seq_len` 会从 4096 增到 6144，KV Cache 也同步增长 50%。

这带来三个工程后果：

1\. 并发不是免费的。 batch 越大，吞吐可能提高，但 KV Cache 会线性吃显存。

2\. 长短请求混跑会浪费。 如果为每个请求预留最大上下文长度，短请求会占着用不到的空间。

3\. 输出长度也要预算。 只限制 prompt 长度不够，`max_new_tokens` 同样会改变缓存上限。

这就是 vLLM 这类 serving 系统要重做 KV Cache 管理的原因：显存分配策略直接决定能塞多少并发请求。

## 六、四代 Attention：从多存到少存

KV Cache 优化的第一条路线，是减少每个 token 要存的 K/V 数量。

### 6.1 MHA：每个 head 独立存 K/V

原始 Transformer 使用 Multi-Head Attention（MHA）。如果有 32 个 attention heads，就有 32 组 K/V。好处是表达力强，每个 head 可以学习不同的匹配模式；坏处是 KV Cache 最大。
```

32 Q heads  
32 K heads  
32 V heads
```

对长上下文 serving 来说，MHA 是最贵的口径。

### 6.2 MQA：所有 Q head 共享一组 K/V

Multi-Query Attention（MQA）把 K/V head 数压到 1：
```

32 Q heads  
1  K head  
1  V head
```

Shazeer 的 MQA 论文目标很明确：incremental decoding 时，少读 K/V，就能减少显存带宽压力。它对推理非常友好，但共享 K/V 会损失一部分多头多样性，因此质量和稳定性需要评估。

### 6.3 GQA：在 MHA 和 MQA 之间折中

Grouped-Query Attention（GQA）把多个 Q heads 分成几组，每组共享一组 K/V：
```

32 Q heads  
8  K/V heads
```

它的缓存大小在 MHA 和 MQA 之间。如果从 32 个 KV heads 变成 8 个 KV heads，KV Cache 缩到 `1/4`。GQA 论文也讨论了从已有 MHA checkpoint uptraining 到 MQA/GQA 的方法，用较少额外训练成本得到更适合推理的结构。

这就是它被广泛采用的原因：缓存明显变小，质量通常比纯 MQA 更稳。

### 6.4 MLA：不直接缓存完整 K/V

DeepSeek-V2/V3/R1 使用 Multi-head Latent Attention（MLA）。它和 MQA/GQA 的思路不同：不是简单减少 KV head 数，而是把 K/V 相关状态压到低维 latent 表示里。

简化理解：
```

传统 GQA:  
cache K/V heads directly  
  
MLA:  
cache compressed latent + RoPE 相关分量  
decode 时再通过投影恢复 attention 所需信息
```

DeepSeek-V2 报告称，相比 DeepSeek 67B，MLA 相关设计将 KV Cache 减少 93.3%。这个数字不能机械套到所有模型上，但它说明一件事：KV Cache 已经重要到值得为它重新设计 attention 结构。

## 七、动手估算：别只看参数量

下面这段代码可以用来估算 KV Cache。重点不是复刻某个框架的精确显存，而是建立数量级直觉。
```

def kv_cache_gib(layers, kv_heads, head_dim, seq_len, batch=1, dtype_bytes=2):  
    bytes_total = 2 * batch * seq_len * layers * kv_heads * head_dim * dtype_bytes  
    return bytes_total / (1024 ** 3)  
  
print(kv_cache_gib(layers=80, kv_heads=8, head_dim=128, seq_len=4096))
```

DeepSeek-V3 MLA 不是标准 K/V heads 公式，表中按每层每 token 约 `512 + 64` 个缓存元素估算：

| 模型口径                     | 4K        | 32K       | 128K       |
|--------------------------|-----------|-----------|------------|
| 70B MHA baseline         | 10.00 GiB | 80.00 GiB | 320.00 GiB |
| 70B GQA-8                | 1.25 GiB  | 10.00 GiB | 40.00 GiB  |
| Llama-3 8B GQA-8         | 0.50 GiB  | 4.00 GiB  | 16.00 GiB  |
| DeepSeek-V3 MLA estimate | 0.27 GiB  | 2.14 GiB  | 8.58 GiB   |

实际部署还要加上 page 元数据、对齐填充、量化元数据、框架临时 buffer 等开销。这段代码适合做容量规划，不替代压测。

## 八、服务端怎么继续压 KV Cache 成本？

Attention 结构只是第一层。真正上线时，还要解决"很多请求同时进来"的问题。

### 8.1 PagedAttention：把 KV Cache 当虚拟内存管理

传统做法容易为每个请求预留一整段连续显存。问题是请求长度不一样：有的只用 300 token，有的要 30K token。PagedAttention 的思路类似操作系统分页：把 KV Cache 切成固定大小的 block，请求需要多少就分配多少，生成继续增长时再追加。

它解决的是显存管理问题：

• 短请求不会占用长请求的预留空间。

• 请求结束后 block 可以回收。

• 多个请求可以更灵活地进入动态 batch。

vLLM 论文报告，在其测试设置下 PagedAttention + vLLM 能显著提高吞吐。这里的关键不是某个固定倍数，而是：KV Cache 的分配方式会直接影响可服务并发。

### 8.2 Continuous batching：让 decode 队列不断流动

普通 batching 要等一批请求都结束才能换下一批。LLM 请求长度差异很大，短请求会被长请求拖住。Continuous batching 的做法是：每个 decode step 后，已结束请求退出，新请求补进来。代价是调度更复杂：每个请求的 KV Cache 长度、block 分配、位置编码和 attention mask 都要动态维护。

### 8.3 Prefix caching：相同前缀不要反复算

很多产品有共享前缀：系统提示词、固定工具说明、同一份长文档、多轮对话历史。Prefix caching 会把相同前缀的 KV Cache 复用起来，让后续请求不必重新 prefill。它对 RAG、Agent 工具调用和企业知识库有用，但要求 token 序列完全一致；多一个空格或模板版本变了，cache key 都可能失效。

### 8.4 KV 量化与淘汰：能省，但要测

KV Cache 可以像权重量化一样压到 INT8 或更低。理论上，FP16 到 INT8 可以省一半缓存；到 INT4 可以再省一半。但 KV 不是静态权重，它直接参与每一步 attention，误差会影响后续生成。

另一类方法是淘汰部分历史 KV，例如只保留窗口、保留 attention sink、或根据 attention 权重选择重要 token。工程判断很简单：能不能丢，取决于你的任务是否真的需要远距离信息。 摘要、代码库问答、法律合同审查这类任务，不能只看短样本 benchmark。

### 8.5 Prefill/Decode 分离：把两类瓶颈拆开

Prefill 偏大矩阵计算，Decode 偏带宽和缓存管理。DistServe 等系统把两者拆到不同 GPU 池里，让 prefill worker 处理首 token，让 decode worker 做持续生成。这个方向不是银弹：拆分后要传输 KV Cache 或中间状态，网络带宽和调度策略会成为新瓶颈。小规模自部署通常先用成熟 serving 框架更实际。

## 九、选型时应该看哪些字段？

不要只看模型宣传页的"支持 128K"。先看 config：
```

{  
  "num_hidden_layers":80,  
"num_attention_heads":64,  
"num_key_value_heads":8,  
"hidden_size":8192,  
"torch_dtype":"bfloat16"  
}
```

几个判断规则：

• `num_key_value_heads == num_attention_heads`：MHA，KV Cache 最大。

• `num_key_value_heads == 1`：MQA，KV Cache 最小，但要关注质量。

• `1 < num_key_value_heads < num_attention_heads`：GQA，当前大模型常见折中。

• 文档明确提到 MLA、latent KV、decoupled RoPE：按模型报告给出的缓存公式估算，不要套标准 GQA 公式。

还要看运行时：

• 是否支持 paged KV cache。

• 是否支持 prefix caching。

• 是否支持 KV cache quantization。

• 长上下文是否支持 chunked prefill。

• 最大 batch 是否受 `max_num_batched_tokens`、`max_model_len` 等参数限制。

很多"模型能不能跑"的问题，最后不是权重放不放得下，而是 权重 + KV Cache + runtime buffer + 并发策略 能不能一起成立。

## 十、长上下文的几个误区

支持 128K 不等于有效使用 128K。窗口长度只是上限，长文检索、跨段推理和真实业务问答都要单独测。KV Cache 小也不必然更快：MLA、KV 量化、PagedAttention 都可能引入额外 kernel 或调度成本。

生产上还要同时估算 prompt 和输出。一个 32K prompt 如果继续写 20K token，KV Cache 会继续线性增长。CPU offload 也不是免费解法：活跃 KV 参与每步 decode，放到 CPU 会带来明显带宽和延迟问题。

## 十一、小结：KV Cache 是推理系统的成本账本

理解 KV Cache 后，很多 LLM 部署现象会变得清楚：

1\. Prefill 和 Decode 是两类问题。 前者偏大矩阵计算，后者偏持续读取缓存。

2\. KV Cache 线性吃显存。 它随 batch、上下文长度、输出长度、层数和 KV head 数增长。

3\. GQA/MLA 是架构层压缩。 它们减少每 token 需要存的历史状态。

4\. PagedAttention/continuous batching 是系统层压缩。 它们减少显存碎片，提高并发调度效率。

5\. 长上下文能力必须实测。 标称窗口、缓存大小和真实任务质量是三件不同的事。

下一次你看到"支持 128K 上下文"的模型，不要只问参数量。更关键的问题是：它有多少 KV heads，KV Cache 每 token 多大，服务框架怎么管理缓存，真实业务里能跑多少并发。

## 参考

[1]: Vaswani, A. et al. (2017). "Attention Is All You Need."  _NeurIPS 2017_.

[2]: Shazeer, N. (2019). "Fast Transformer Decoding: One Write-Head is All You Need." arXiv:1911.02150.

[3]: Ainslie, J. et al. (2023). "GQA: Training Generalized Multi-Query Transformer Models from Multi-Head Checkpoints."  _EMNLP 2023_.

[4]: DeepSeek-AI (2024). "DeepSeek-V2: A Strong, Economical, and Efficient Mixture-of-Experts Language Model." arXiv:2405.04434.

[5]: Xiao, G. et al. (2023). "Efficient Streaming Language Models with Attention Sinks." arXiv:2309.17453.

[6]: Kwon, W. et al. (2023). "Efficient Memory Management for Large Language Model Serving with PagedAttention."  _SOSP 2023_.

[7]: Zhong, Y. et al. (2024). "DistServe: Disaggregating Prefill and Decoding for Goodput-optimized Large Language Model Serving." arXiv:2401.09670.

下一篇预告：第 9 篇《解码策略 —— 模型如何选择下一个词》，讲清 temperature、top-p、top-k 这些每天都在用但很少有人讲透的参数。

  


