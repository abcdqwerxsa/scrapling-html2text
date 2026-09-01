# 比 HuggingFace 快 1000 倍！6.5 小时扫完整个互联网，这个 Rust 项目太狠了

**作者**: 何三笔记
**发布时间**: 2026-07-24 00:00
**原文链接**: https://mp.weixin.qq.com/s/7KgRLlOVaUzXMj5rmsa6yg

---

大家好，我是何三，独立开发者

事情是这样的。

前两天刷 Hacker News，看到一个项目直接把我看傻了——**GigaToken** ，一个人用 Rust 手搓的 tokenizer，比 HuggingFace 官方快了 **1000 倍** 。

没看错，不是 10%，不是 2 倍，是实打实的 1000 倍。

![速度对比](https://r2.jeanjan.kdns.fr/pictures/img-b4eb202001.png)速度对比

有图有真相：AMD EPYC 双路服务器上，GPT-2 的 tokenizer，HuggingFace 跑 24.8 MB/s，GigaToken 跑 **24.53 GB/s** ——差了 989 倍。M4 Max 上更夸张，8.79 GB/s vs 6.9 MB/s，**1268 倍** 。

这什么概念？

就是以前你得花 20 分钟等一批数据 tokenize 完，现在点个杯咖啡的功夫，它已经跑了十分之一了。不对，应该说——你咖啡还没泡好，它已经跑完了。

而且这哥们儿在 README 里算了一笔账：Common Crawl（130 万亿 tokens，通常被认为是整个互联网的大小），用这个项目来 tokenize，**6.5 小时就能干完** 。

整个互联网。6.5 小时。

要知道深度学习预处理环节里，tokenization 一直是那个被忽视的瓶颈——没人觉得它慢，但它每天让成千上万的 GPU 在那干等着。GigaToken 直接把这个瓶颈给干碎了。

## 这东西到底怎么做到的？

说人话版本。

Tokenizer 干的事，就是把一句话切碎成模型能理解的 token。比如"我喜欢吃苹果" → `["我", "喜欢", "吃", "苹果"]`。听起来简单对吧？

但问题是，它不是一个字一个字切，它得查表、配 merges、对规则——实际跑起来非常复杂。

传统 tokenizer 慢在哪儿呢？**两件事** 。

第一，它得跑正则引擎来分词。正则这东西，写起来爽，跑起来……emmm 怎么说呢，就像你开法拉利但挂着 1 档在跑。

第二，它每碰到一个词，都得从头查一遍怎么切。哪怕昨天刚刚切过"tokenization"这个词，今天再碰到，它还得再切一次——**完全没有记忆** 。

GigaToken 怎么解决的？

![架构原理](https://r2.jeanjan.kdns.fr/pictures/img-b4eb202002.png)架构原理

**用 SIMD。** 听不懂没关系，你就理解成：别人是一条一条处理数据，它是把数据排成方阵，一次处理一整片。CPU 内部有那种宽车道，普通代码只用单车道，SIMD 把所有车道同时占满。

**再加了一个超大的缓存。** 碰到过的词，切法直接记下来。下次再碰到，查缓存就完事了。这听起来简单，但实现起来巨难——因为缓存规模会爆炸，你得用非常巧妙的方式管理它。

说白了，以前你每次去超市都要从头找酱油在哪排，现在你去了十次之后脑子里自然知道——"进门右转第三排"。GigaToken 做的就是把这个"脑子"装进了 tokenizer。

作者的原话更直白：**"我对每一种 CPU、每一种 tokenizer 组合都做了极致优化。"**

不是优化个大概，是逐个击破。

不过说到这个，突然想起个事。

前阵子 AI 圈疯狂传 "Rust 正在吃掉基础设施层"，从 Tokio 到 HuggingFace 的 tokenizers 底层就是 Rust 写的。但 HuggingFace 那个 Rust 实现……说实话，可能是被 Python 绑定拖累了，跑起来也没多快。

GigaToken 的作者 Marcel 在 FAQ 里说了一句话让我印象特别深：**"这个项目的绝大部分代码是我手写的，没有用 AI。"**

结尾还补了一句——"AI 只用来帮忙写用户接口和移植 SIMD 策略"。

在 2026 年，一个人手写比 AI 辅助的代码还快 1000 倍，这个讽刺感拉满了。

## 上手试一下

安装简单到离谱：
```

   pip install gigatoken
```

没了。就这一行。

如果你想零成本替换现有的 HuggingFace tokenizer：
```

   import gigatoken as gt  
  
# 把你的 HF tokenizer 包一层  
tokenizer = gt.Tokenizer(hf_tokenizer).as_hf()  
  
# 用法跟原来一模一样  
tokens = tokenizer.encode_batch(["今天天气不错", "适合写代码"])
```

你要追求极致性能，用 GigaToken 自己的 API：
```

   import gigatoken as gt  
  
tokenizer = gt.Tokenizer("Qwen/Qwen3-8B")  
file_source = gt.TextFileSource(["data.txt"], separator=b"<|endoftext|>")  
tokens = tokenizer.encode_files(file_source)
```

甚至不用装都能测——`uvx` 一行命令验证你的 tokenizer 是不是被支持：
```

   uvx --with tokenizers gigatoken bench 'openai-community/gpt2' data.txt --validate
```

它会自动下载模型配置、跑基准、验证输出是否和 HF 一致。

实测跑完它会打印这样的结果：
```

   cpu: Apple M4 Max, 16 cores  
gigatoken: 1.432 s | 11920.51 MB at 8327.05 MB/s  
hf: 16.250 s | 100.00 MB at 6.15 MB/s  
gigatoken is 1353.13x faster than hf  
validation OK: 20401 documents match
```

说实话，第一眼看到这个输出我是不信的。1353 倍？我反复看了三遍。

然后我去 GitHub 上看 Star——1.8k。就 1.8k。一个把 HuggingFace 按在地上摩擦的项目，才 1.8k Star。

这个数字让我有点恍惚。可能是前几天才发布的，也可能是大家还没反应过来——但我觉得它会很快冲上去。

哦对了，它支持哪些模型？基本上你能想到的主流全支持了：

**GPT-2、Llama 3/3.1/3.2/3.3/4、Qwen 2/2.5/3/3.5、DeepSeek V3/R1/V4、GLM 4/5、Phi-4、Gemma 3/4、Mistral、CodeLlama、Kimi K2** ……还有一大堆衍生的模型版本。

你训练或者推理用的模型，90% 以上它都支持。唯一不太行的是 SentencePiece 类的 tokenizer（主要是 Google 系的老模型），作者说优先级不高，因为现在主流模型都在往 BPE 迁移。

同类项目的话，除了 HuggingFace tokenizers 和 OpenAI 的 tiktoken，其实没什么能打的。但这两个恰恰是现在行业里用得最多的。

我觉得有意思的是——tiktoken 本身就是 OpenAI 为了极致性能手搓的 Rust 实现，结果被 GigaToken 干翻了 140 倍。**大厂手搓的不如个人开发者手搓的，这剧情我爱看。**

项目地址放在这了，感兴趣的自己去把玩：

🔗 **https://github.com/marcelroed/gigatoken**

回到开头那句话。

Tokenization 是 AI 流水线上最不起眼的环节——没人因为它兴奋，没人因为它吵架。但它决定了你的 GPU 到底有多少时间在真正"思考"，多少时间在干等数据。

GigaToken 让我看到一件事：**有时候最大的瓶颈不是技术做不到，而是没人觉得它需要被优化。**

一个人，一个 Rust 项目，1000 倍。

这颗炸弹，我建议你早点知道。

 _本文使用 MGO 编辑并发布_

> 关注"何三笔记"，回复"mgo" 免费下载使用

