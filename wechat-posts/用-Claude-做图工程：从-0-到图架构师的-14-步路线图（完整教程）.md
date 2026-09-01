# 用 Claude 做图工程：从 0 到图架构师的 14 步路线图（完整教程）

**作者**: AI领先趋势
**发布时间**: 2026-07-25 07:52
**原文链接**: https://mp.weixin.qq.com/s/PYxTbwvrChNO2U_e6NghTw

---


# 用 Claude 做图工程：从 0 到图架构师的 14 步路线图（完整教程）

![](https://r2.jeanjan.kdns.fr/pictures/img-a2eb0d6301.jpeg)

大多数想搭多步 agent 的人，最后都把它写成了一条直线。第一步、第二步、第三步——每一步都客客气气地等上一步干完才开始。

**十个人里有九个会发现，其中一半的步骤根本不用等。**

它们不**路由** ，不**分支** ，也不**并行** 。只是排队——一个脑袋、一份上下文、一次一件事，直到窗口塞满，agent 把自己要干嘛都忘了。

**这份 14 步路线图** ，就是把这条一字长蛇阵变成一张**图** ：在舰队上扇出，自己验证自己的发现，最后收敛到一个单独 agent 根本端不下来的结果。

![](https://r2.jeanjan.kdns.fr/pictures/img-a2eb0d6302.jpeg)

这儿有一个没人挑明的转变。prompt 是一句话。loop 是一个循环。harness 是 agent 脚下的地板。

但**活儿本身的形状** ——什么先跑、什么后跑、什么能同时跑、什么必须等所有别的都跑完——这个形状，是一张图。节点负责思考。边负责把结果带走。

Claude Code 已经把搭这种图的工具直接发了出来：**动态工作流（dynamic workflows）** 。

Claude 自己写一份普通的 JavaScript 编排脚本，然后派出一支相互配合的子智能体舰队去执行它——而这套配合本身花掉零 model token，因为它是代码，不是对话。

## 01\. 节点是任务，边是流转

图这东西只有两样，把它们分清楚，能消掉大半的混乱。**节点** 是一个工作单元——一个 agent，一份有边界的活儿，一个输入进、一个输出出。

**边** 是一条依赖：它声明这个节点的输出会喂给那个节点的输入。仅此而已。

![](https://r2.jeanjan.kdns.fr/pictures/img-a2eb0d6303.png)

最常见的错误，是把"然后"当成边。"总结一下这个文件，然后告诉我天气"——这两件事之间没有边，天气不消费摘要。

这是两个互不相连的节点，被一段线性脚本硬串在了一起。边只在数据真的从上面流过去的时候才存在。

对你 agent 里的每一个"然后"，都要学会问：**下一步会不会读上一步的输出？** 如果不会，就没有边，等待是白等。

> 把它画成框和箭头。一个框就是一次 agent() 调用。  
> 一条箭头，就是一个变量从某次调用的 return 里被传进另一次调用的  
> prompt。如果你画不出这条箭头——如果没有变量流过去——那这两个  
> 框就是独立的，而"独立"这件事，是你在本课剩下的部分要反复利用的  
> 东西。

## 02\. 你的线性脚本，就是一个退化图

当你把一个 agent 写成"做 A，然后 B，然后 C，然后 D"，你其实已经画了一张图——一条不分叉的链子。每个节点都恰好有一条边进、一条边出。

它能跑。但它也跑得又慢又脆，因为链子没有冗余：C 一卡住，D 永远不会发生，A 干的活被堵在上游，无处可去。

![](https://r2.jeanjan.kdns.fr/pictures/img-a2eb0d6304.png)

图工程第一项真本事，就是**重画这条链子** 。把你那个线性 agent 拿过来，对每一条箭头，都问一遍第 1 步那个问题。

大多数链子里都有两三条不运数据的箭头——它们只是你当时敲键盘的顺序而已。

把这些箭头剪掉，链子就会塌成更宽的东西：几个相互独立的节点可以同时跑，最后一起喂给那个需要它们全部的节点。

## 03\. 给每个节点一个契约

一个你没法推理的节点，就是一个你没法并行的节点。修法是一份契约：**有界输入，有界输出，恰好一份活儿。**

输入是节点读到的东西——显式传进去的，不是从一份共享窗口里去"猜"。输出是一个定死的形状，最好校验过，这样下一个节点不用靠猜就能消费。

![](https://r2.jeanjan.kdns.fr/pictures/img-a2eb0d6305.jpeg)

在一份工作流里，这份契约靠 **schema** 强制执行。当你把一个带 JSON schema 的 agent() 调用交给 Claude，Claude 派出去的子智能体就被强制返回校验过的结构化数据——校验发生在 tool-call 这一层，所以对不上的时候 Claude 会自己重试，而不是甩给你一段自由文本，让你去解析、去祈祷。

这就是"能被 Claude 接进图的节点"和"只有人去读它的输出才管用的节点"之间的差别。
```

// A node with a real contract: bounded in, validated out, one job.  
const ITEM = {  
  type: 'object', additionalProperties: false,  
  properties: {  
    title:   { type: 'string' },  
    url:     { type: 'string' },  
    impact:  { type: 'string', enum: ['high', 'medium', 'low'] },  
  },  
  required: ['title', 'url', 'impact'],  
};  
  
const result = await agent(source.prompt, {  
  label:  `research:${source.key}`,  
  schema: ITEM,           // forces validated structured output  
  agentType: 'general-purpose',  
});  
// result is now a shape the next node can trust — not free text.
```

## 04\. 把边当作数据契约

边不只是"B 在 A 之后"。它是关于"什么流过去"的一份承诺：A 产出这种形状，而 B 就是为消费这种形状而造的。当你用数据而不是顺序去命名一条边，有两件事会变得更容易。

![](https://r2.jeanjan.kdns.fr/pictures/img-a2eb0d6306.png)

你能一眼看出这条边是不是真的（数据真的流过去了吗？），而且你可以在两端任意换节点，只要形状不变，图就不会坏。

落到实际里，边就活在普通的 JavaScript 里。扇出和合成之间的那一步归约——flatten、去重、过滤——只是代码，作用在节点返回的那些形状上。

**根本不需要 agent。** 图思维带来的一个安静红利：人们烧 model token 去做的一大堆事，其实是一条边，而边不要钱。

> 诱惑来了：派一个 agent 去"把结果合到一起"。顶住。  
> 如果"合到一起"就是 flatten + 去重，那就是 results.flatMap(...)  
> 加一个 Set——确定性的、瞬时的、零 token。把 agent 留给判断，  
> 而不是拿来干管道活。一张每条边都是 agent 的图，是在为自己的接线付房租。

## 05\. 用 parallel() 扇出

就是这一招，把前面所有的铺垫兑了现。当你有 N 个独立的节点——N 个源要查、N 个文件要审、N 条路由要巡——你不要把它们串起来。

你叫 Claude 把它们扇出去，同时跑。在一份工作流里，这就是 parallel()：Claude 拿到一个 thunk（无参函数）数组，每个 thunk 派一个子智能体，全部并发执行，然后把结果数组还给你。

![](https://r2.jeanjan.kdns.fr/pictures/img-a2eb0d6307.jpeg)

两个细节让它稳。第一，parallel() 是一道**屏障** ——它会等到每一个 thunk 都跑完才返回，所以下一阶段看到的是完整的一套。第二，一个抛异常的 thunk 会 resolve 成 null，而不是把整批一起 reject 掉，所以一个抽风的 agent 没法把整次运行拖下水。

永远对结果 .filter(Boolean)。并发上限大概在你的 CPU 核心数附近，超出的会排队，所以你扔给它一百个 thunk 它们也都能跑完——只是每次跑一小把。
```

phase('Research');  
  
// Nine sources, nine agents, all at once.  
const raw = await parallel(  
  SOURCES.map((s) => () =>  
    agent(s.prompt, {  
      label: `research:${s.key}`,  
      phase: 'Research',  
      schema: ITEM_SCHEMA,     // each node returns validated JSON  
      agentType: 'general-purpose',  
    }),  
  ),  
);  
  
const collected = raw.filter(Boolean);  // drop the nulls from failed agents
```

扇出活在 Claude 写的代码里，不在模型对话里。Claude 自己的上下文永远不用一次端着九个源——每个子智能体端着自己的上下文，只有最终答案流回来。

这就是为什么 Claude 能把一份工作流扩到**几十、几百个子智能体** 还不会把会话淹掉。编排层花掉零 token，因为它不是 Claude 又想了一回合。

## 06\. 在屏障处扇入

扇出只有被什么东西接住才有用。扇入就是边汇聚的那个节点——在这里，一个 agent（或一段代码）一次看到所有的上游结果，做一件需要整套数据才能做的事：跨源去重、按影响排序、总量一回来是空的就提前退出。这是屏障唯一值得它实际耗时的地方。

![](https://r2.jeanjan.kdns.fr/pictures/img-a2eb0d6308.jpeg)

让图保持快的规矩：**只在某一阶段真的需要把所有前面的结果放在一起时，才用屏障。** 跨所有源去重？屏障——对的。
```

// The edge: plain JS, no agent, zero tokens.  
const flat = collected.flatMap((c) => c.items);  
log(`Collected ${flat.length} items`);  
  
phase('Curate');  
// The barrier node: needs the WHOLE set to dedupe + rank.  
const curated = await agent(  
  `Dedupe and rank these by impact:\n${JSON.stringify(flat)}`,  
  { phase: 'Curate', schema: CURATED_SCHEMA },  
);
```

只是把一张列表拍平？那是边，内联做掉。嗅觉测试残酷又简单：如果你写的是 parallel → 变换 → parallel，而中间那段变换没有跨项依赖，那你本该用 pipeline，根本不该碰屏障。

## 07\. 菱形：拆 → 干 → 合

把扇出和扇入拼到一起，你就得到了每张正经 agent 图里的主力拓扑：**菱形** 。

一个节点拆活儿，很多节点并行干活，一个节点合龙。这是市场扫描、依赖审计、代码评审、研究报告背后的同一个形状——换掉源和 prompt，同一副骨架就能用。

![](https://r2.jeanjan.kdns.fr/pictures/img-a2eb0d6309.png)

这个标准形态有个名字，值得记住：**扇出 → 归约 → 合成。** 扇出去采广度，归约用纯代码压缩，合成用最后一个 agent 写出答案。

一旦你看见了菱形，你不再问"怎么让我的 agent 多做几步"，而是开始问"哪里拆、哪里合"——这才是真正能扩展的问题。

## 08\. 用条件在运行时路由这条边

不是每张图都是定死的。有时候该走哪条边，取决于一个节点发现了什么。**路由节点** 看一眼结果，决定哪条下游路径触发——先给工单分类，再分支到对应的处理器；先看 diff 大小，再决定要么快速过一眼、要么拉起一整套审计。

在一份工作流里，这就是节点校验过输出之后的一句 JavaScript if 或 switch，因为控制流活在代码里。

![](https://r2.jeanjan.kdns.fr/pictures/img-a2eb0d6310.png)

就在这里，确定性从限制变成了特性。路由节点的决策可以由 Claude 驱动（一个子智能体做分类），但路由本身是 Claude 写的代码——所以同一个分类，每次都按同一种方式跑。

你在节点上拿到 Claude 的判断，在边上拿到脚本的可靠。不会出现"Claude 自己决定跳过审计"这种涌现式惊喜——因为跳过这件事得被写进图里才行，而它没被写进去。
```

// Router node: an agent classifies, code picks the edge.  
const { severity } = await agent(  
  `Classify this diff's risk:\n${diff}`,  
  { schema: { type: 'object',  
      properties: { severity: { enum: ['low', 'high'] } },  
      required: ['severity'] } },  
);  
  
let review;  
if (severity === 'high') {  
  // heavy path: full parallel audit  
  review = await parallel(FILES.map((f) => () => agent(`Audit ${f}`)));  
} else {  
  // light path: one quick pass  
  review = await agent(`Quick review of ${diff}`);  
}
```

## 09\. 在边上放一个验证器

一张图真正的杠杆，不是更多的 agent——而是你能在它们外面包出什么样的结构，从而产出"可信度"。

验证器节点坐在一条边上，在一项结果被允许流到下游之前，它唯一的工作就是想办法毙掉这条发现。它要是活下来，就放行；要是没活下来，就永远到不了答案里。

![](https://r2.jeanjan.kdns.fr/pictures/img-a2eb0d6311.png)

三种模式值得你揣在手里。

  * • **对抗式验证（adversarial verify）：** 对每条发现，派出 N 个独立的、被 prompt 成"来反驳它"的质疑 agent；只有多数活下来，才留下。
  * • **多视角验证（perspective-diverse verify）：** 给每个验证器一个不同的视角——正确性、安全性、能不能复现——因为多样性会抓住 N 个一模一样的检查永远抓不到的失败模式。
  * • **评审团（judge panel）：** 从不同角度生成 N 份尝试，用并行的评委打分，从胜者合成，同时把落后者身上最好的部分嫁接过来。

正是一套这样的模式，让一支真实的团队把 Bun 运行时移植成功，把对抗式代码评审直接焊进了循环里。

## 10\. 隔离节点，让一次失败毒不到整张图

在一条链子里，失败会级联——C 一死，D 永远不跑，整坨停摆。在一张图里，失败应该**被关在它自己的节点里。**

这一点已经部分成立：一个在 parallel() 里抛异常的 thunk 会 resolve 成 null，所以八个好的 agent 照样返回，一个坏的自己掉队。你的 .filter(Boolean) 就是这道隔离。把每个扇入都设计成能容忍缺失的输入，而不是默认会拿到全套。

![](https://r2.jeanjan.kdns.fr/pictures/img-a2eb0d6312.png)

更隐蔽的失败，是节点之间相互踩脚。当多个 agent 并行写文件时，它们会撞车。修法是隔离：**worktree（工作树）** ——每个 agent 在自己的 git worktree 里运行，在沙箱里干自己的活，干净地合并。只有当节点真的会并行写的时候才动用它；它是那唯一需要它的一种拓扑的安全带，不是每次运行都要交的默认税。

## 11\. 加一个环——但要让它收敛

有时候你不下到活儿里，就不知道它有多大：未知规模的发现、一场 bug 扫雷，找一个 bug 又牵出三个。这需要**环** ——一条受控的、回到更早节点的边。

危险显而易见：一个不收敛的环就是一个无限循环，会一直派 agent 直到你的预算耗光。

![](https://r2.jeanjan.kdns.fr/pictures/img-a2eb0d6313.png)

能收敛的模式叫 **循环到枯竭（loop-until-dry）：** 不停地派 finder，直到连续 K 轮一个新东西都没翻出来，就停。决定它成败的一个细节——也是几乎每个人第一次都会踩的坑——是你拿什么去重。

要拿"见过的全部"去重，不只是"已确认的结果"。否则被否掉的发现会每一轮重新冒出来，循环永远不会枯竭，你就造了一台机器，永远在花钱去重新发现同一批死胡同。
```

const seen = new Set(); const confirmed = []; let dry = 0;  
  
while (dry < 2) {                       // stop after 2 empty rounds  
  const found = (await parallel(  
    FINDERS.map((f) => () => agent(f.prompt, { schema: BUGS }))  
  )).filter(Boolean).flatMap((r) => r.bugs);  
  
  const fresh = found.filter((b) => !seen.has(key(b)));  
  if (!fresh.length) { dry++; continue; } // nothing new → toward dry  
  dry = 0;  
  fresh.forEach((b) => seen.add(key(b))); // dedupe vs SEEN, not confirmed  
  
  // diverse-lens verify each fresh finding before it counts  
  const judged = await parallel(fresh.map((b) => () =>  
    parallel(['correctness', 'security', 'repro'].map((lens) => () =>  
      agent(`Judge "${b.desc}" via ${lens} — real?`, { schema: VERDICT })))  
    .then((v) => ({ b, real: v.filter(Boolean).filter((x) => x.real).length >= 2 }))));  
  
  confirmed.push(...judged.filter((v) => v.real).map((v) => v.b));  
}
```

## 12\. 跨节点给模型分级

不是每个节点都需要你最好的模型。图把这件事摆得明明白白，这是单个 agent 永远做不到的：有些节点有界又重复（抽取这个字段、给这张工单分类），有些节点才真正端着判断（合成报告、给一项发现做裁定）。

把无聊的节点丢给更便宜的模型去跑，把贵的 token 花在判断真正所在的地方。

![](https://r2.jeanjan.kdns.fr/pictures/img-a2eb0d6314.jpeg)

在一份工作流里，Claude 派出的每个子智能体默认继承你会话的模型，除非脚本显式覆盖——所以默认情况下，一次大跑全程按你会话的档位计费。单次 agent() 调用上的 model 选项，就是告诉 Claude 只把那一个节点路由到别处。

**大跑之前先看 /model** ，然后让 Claude 把扇出里那些重复的节点路由到更便宜的模型，把合龙节点留在高档位。这就是那根杠杆，能让一张吃 token 的图从"贵"变成"划算"，全程不用动它的形状。

## 13\. 拓扑就是你的成本和延迟

图的形状不是装饰——它是决定实际耗时的最大一根杠杆。把所有人绊住的那个选择是：parallel() 还是 pipeline()。parallel() 的屏障会让所有东西都等最慢的那个节点跑完，下一阶段才开始。

pipeline() 让每一项各自流过所有阶段，没有屏障——项 A 可能在阶段 3，而项 B 还在阶段 1。快的项早早结束，不会在慢项后面干等。

![](https://r2.jeanjan.kdns.fr/pictures/img-a2eb0d6315.png)

**默认用 pipeline()。** 只在某个阶段真的需要一次拿到所有前面的结果时——跨集合去重、基于总量提前退出、一份要跟"其他发现"对比的 prompt——才去够屏障。"代码更干净"和"这些阶段感觉分开"都不是理由；屏障带来的延迟是真金白银、可测、被白白浪费的时间。分开，不等于同步。

## 14\. 让 Claude 自己画图——自路由

最后这一招是：对你没法提前规划的活儿，别再亲手画图。

借助**动态工作流** ，你描述目标，Claude 自己来写编排脚本——拆任务、选扇出方式、派出一支相互配合的子智能体舰队、合成结果。你拿到的是一张为这一次运行量身定做的图，而不是一张你硬塞进去的定死图。

![](https://r2.jeanjan.kdns.fr/pictures/img-a2eb0d6316.jpeg)

有三条入口。在你的 prompt 里说**"workflow"** 这个词，Claude 就给这个任务写一份。跑一份已保存或打包好的——/deep-research 就是正跑在生产里的一张真实的图：范围 → 并行搜索 → 抓取 → 对抗式验证 → 合成，正是本课讲的那副骨架。

或者打开 ultracode，Claude 会为会话里每一个有分量的任务都规划一份工作流。某次跑得好，按 s 把它的脚本存进 .claude/workflows/——有版本控制、可以按名字重跑，一张任何 clone 了这个仓库的人都能拉起来的图。
```

› Run a workflow to audit every route under src/routes/ for missing  
auth. Spawn one agent per route file, then verify each finding before  
reporting. ● Claude wrote an orchestration script · launching in  
background… /workflows — auth-audit · running ✓ Scope 1/1 2.1k tok ·  
4s ✓ Fan-out 18/18 one agent per route file ◯ Verify 11/18 3-vote  
skeptics per finding… ○ Synthesize 0/1 waiting on verify session stays  
responsive — keep working while the fleet runs
```

## 本周用 Claude 搭的六张图

![](https://r2.jeanjan.kdns.fr/pictures/img-a2eb0d6317.png)

  * • **每条路由上的安全扫雷。** Claude 给**每个路由文件派一个子智能体** ，各自找缺失的权限校验，再由一轮验证在每条发现进入报告前确认一遍。这种广度，单个上下文根本端不下。
  * • **带引用的 /deep-research 报告。** 一张已经在 Claude Code 里出货的图。Claude 把你的问题拆成不同角度，并行搜索，跨源去重，然后在动笔之前用三人投票的质疑 agent 对**每条主张做对抗式验证** 。
  * • **按文件移植一个模块。** 把 Bun 的那道天花板，按你自己的仓库再放大一遍。Claude 跨文件并行翻译，对每个文件跑测试套件做关卡，把失败的那部分打回去——**对抗式评审** 会抓住单次过手会放过去的破玩意。
  * • **对一份 diff 做对抗式评审。** Claude 按 diff 大小路由：小改动走一次快速过手，大改动触发一整套**并行审计** ，评审员各带不同视角——正确性、安全、性能——最后由评审团合成。
  * • **定时运行的生态扫描。** 存一次，永远重跑。Claude 并行查多个源——发布、博客、讨论——在屏障处按影响排序，写出摘要。**版本控制在 .claude/workflows/ 里** ，按名字就能拉起。
  * • **未知规模的发现。** 你不知道那里到底有几个 bug。Claude 并行跑 finder，把每一条新发现**拿"见过的全部"去重** ，验证存活下来的，一直循环到连续两轮没新东西——然后停。

## 结论：

提问者问问题。架构师画图。

线性 agent 从来不是天花板——它只是第一个形状，是每个人都会先去够的那个，因为它跟我们敲键盘的方式对得上。**一行、一个脑袋、一次一件事。**

一旦你看见了节点和边，你就不再叫 agent"再多干点"，而是开始叫图"干得更宽"：活儿独立的地方扇出去，可信度要紧的地方给边把关，判断力不在的地方给模型降档。

大多数人还会继续把步骤排成一行。**学会画图的人，会指挥一支舰队** ——而其他人头顶那道天花板，他们根本注意不到。

