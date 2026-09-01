# Cloudflare Workflows：让多步骤任务永不半途而废

**作者**: 木兆纸
**发布时间**: 2026-07-06 22:00
**原文链接**: https://mp.weixin.qq.com/s/2VYWMW_F2IzwC_Fll-FNRg

---

![](https://r2.jeanjan.kdns.fr/pictures/img-6a16bd8a01.jpeg)

## 一个订单，四个步骤，第三步挂了怎么办？

你在写一个电商下单流程，逻辑很简单：

  1. 1\. 检查库存
  2. 2\. 扣款
  3. 3\. 生成物流单
  4. 4\. 发确认邮件

用普通 Worker 写，一个 `fetch` handler 从头跑到尾。库存查了，钱扣了，然后第三步调物流 API 时对方超时报错——整个请求挂掉。

现在你有一堆麻烦：钱已经扣了，但物流单没生成，邮件也没发。用户付了钱却什么都没收到。你得写补偿逻辑：捕获异常、回滚扣款、记录到哪一步失败了、下次怎么重试……

更麻烦的是那些**要等很久** 的流程：

  * • 用户注册后第 3 天发一封激活提醒邮件
  * • 试用到期前 1 天发续费提醒
  * • 文档提交后等人工审批，可能等好几天

普通 Worker 最多跑 30 秒 CPU 时间，根本没法"等 3 天"。你只能拆成一堆 Cron 定时任务 + 数据库状态字段，自己维护"这个流程走到哪了"。

**Workflows 就是来解决这些问题的：多步骤、能失败重试、能睡上几天、状态自动持久化，而且不用你管任何基础设施。**

![](https://r2.jeanjan.kdns.fr/pictures/img-6a16bd8a02.jpeg)

##  Workflows 是什么？

Workflows 是 Cloudflare 的**持久化执行引擎** （durable execution engine），建立在 Workers 之上。它让你把一个复杂任务拆成若干个"步骤"（step），每个步骤：

  * • **独立重试** ：某一步失败了，只重试这一步，不用从头再来
  * • **状态自动持久化** ：每步的结果自动存下来，Worker 重启、部署、崩溃都不丢
  * • **可以睡很久** ：`step.sleep` 能暂停几秒到一年，睡觉期间不占资源、不计费
  * • **可以等外部事件** ：`step.waitForEvent` 能挂起等 webhook、等人工审批

关键在于"持久化"三个字。传统 Worker 是无状态的、短命的；Workflows 底层用 Durable Objects 给每个实例存档，每完成一步就写一次"存档点"（checkpoint）。哪怕整个流程要跑一周、中途机器重启了 10 次，它都能从上次的存档点接着跑。

![](https://r2.jeanjan.kdns.fr/pictures/img-6a16bd8a03.jpeg)

它特别适合这些场景：

  * • **可靠的 AI 应用** ：调 LLM、处理结果、存数据库，任何一步失败自动重试
  * • **数据处理管道** ：从 R2 读文件、逐条处理、写回结果
  * • **用户生命周期** ：注册后的一系列自动邮件、试用到期提醒
  * • **人工介入审批** ：挂起等人点"批准"，可能等几天

## Workflows vs Queues：到底该用哪个？

这是最常见的困惑。两个都能做"异步任务"，但定位完全不同：

| 维度    | Queues（队列）    | Workflows（工作流） |
|-------|---------------|----------------|
| 核心模型  | 消息进、消息出       | 多步骤编排，有状态      |
| 单个任务  | 一条消息 = 一个独立任务 | 一个实例 = 一个多步骤流程 |
| 步骤间状态 | 不保留，消息处理完就没了  | 每步结果自动持久化      |
| 失败重试  | 整条消息重投        | 只重试失败的那一步      |
| 等待能力  | 不能长时间等        | 能睡几天、等外部事件     |
| 适合场景  | 削峰填谷、批量处理独立任务 | 有先后依赖的多步骤业务流程  |
| 成本    | 极低（按操作数计费）    | 每步都有存档开销，比队列贵  |

一句话区分：

  * • **任务之间互相独立、只是想异步处理** → 用 **Queues** （比如批量发 1 万封营销邮件，每封都一样）
  * • **任务分好几步、有先后依赖、要么全成功要么能优雅回滚** → 用 **Workflows** （比如一个订单的下单流程）

两者也能配合：Queue 消费者收到消息后，触发一个 Workflow 实例来处理复杂流程。

## 免费额度 & 定价

好消息：**Workflows 不单独收费** ，它的计费方式和 Workers 完全一样，包含在 Workers 套餐里。

它按三个维度计费：

| 维度           | Workers 免费版            | Workers 付费版（$5/月起）            |
|--------------|------------------------|-------------------------------|
| **请求（调用次数）** |  10 万次/天（与 Workers 共享） | 1000 万次/月含内，超出 $0.30/百万       |
| **CPU 时间**   |  每次调用 10ms             | 3000 万 CPU 毫秒/月含内，超出 $0.02/百万 |
| **存储（状态）**   |  1GB                   | 1GB 含内，超出 $0.20/GB-月          |

几个关键点：

  * • **"请求"指什么** ：只算**触发一个新实例** （invocation）。实例内部有多少个 step 都不额外算请求。子请求（subrequest）也不额外收费。
  * • **只按 CPU 时间计费，不按墙上时间** ：这是 Workflows 最省钱的地方。你的流程等 API 响应、等 LLM 推理、`step.sleep` 睡 30 天——这些**等待时间不消耗 CPU，不花钱** 。大多数应用 CPU 只有个位数毫秒，但墙上时间可能好几秒。
  * • **存储计费** ：从 2025 年 9 月 15 日开始对状态存储计费。默认免费版状态保留 3 天，付费版 30 天，过期自动清理。可以在创建实例时设更短的保留期来省存储。
  * • **睡觉/等待不占并发** ：处于 `waiting` 状态（`step.sleep`、等重试、等事件）的实例**不算并发数** 。你可以同时有几百万个实例在睡觉或等 webhook。

![](https://r2.jeanjan.kdns.fr/pictures/img-6a16bd8a04.jpeg)

对比一下其他方案：AWS Step Functions 按"状态转换次数"计费，等 7 天要么用 Express（一直轮询付计算费）要么用 Standard（付状态转换费）。Workflows 让"等任意时长"变成零边际成本的操作。

## 5 分钟快速开始

### 前置条件

  * • Cloudflare 账户
  * • Node.js 16.17.0+

### 1\. 创建项目
```

npm create cloudflare@latest -- workflows-tutorial  
# 选择：Hello World → Worker only → TypeScript  
# "是否部署" 选 No，我们要先改代码  
cd workflows-tutorial
```

如果想直接拉官方完整示例，可以跑：
```

npm create cloudflare@latest workflows-starter -- --template "cloudflare/workflows-starter"
```

### 2\. 写 Workflow

新建 `src/workflow.ts`：
```

import { WorkflowEntrypoint, WorkflowStep } from "cloudflare:workers";  
import type { WorkflowEvent } from "cloudflare:workers";  
  
type Params = { name?: string };  
type IPResponse = { result: { ipv4_cidrs: string[] } };  
  
export class MyWorkflow extends WorkflowEntrypoint<Env, Params> {  
  async run(event: WorkflowEvent<Params>, step: WorkflowStep) {  
    // step.do：执行代码并持久化结果  
    const data = await step.do("fetch data", async () => {  
      const response = await fetch("https://api.cloudflare.com/client/v4/ips");  
      return await response.json<IPResponse>();  
    });  
  
    // step.sleep：暂停一段时间（睡觉不计费）  
    await step.sleep("pause", "20 seconds");  
  
    // 带重试配置的 step  
    const result = await step.do(  
      "process data",  
      { retries: { limit: 3, delay: "5 seconds", backoff: "linear" } },  
      async () => {  
        return {  
          name: event.payload.name ?? "World",  
          ipCount: data.result.ipv4_cidrs.length,  
        };  
      },  
    );  
  
    return result;  
  }  
}
```

一个 Workflow 就是一个继承 `WorkflowEntrypoint` 的类，实现 `run` 方法。`step` 对象是整个 API 的核心。

**怎么划分步骤？** 问自己一个问题："如果这段代码里有一部分失败了，我希望整段都重跑吗？" 调外部 API、查数据库、读存储——这些都该独立成一个 step。这样后面的步骤失败时，可以直接复用前面已经拿到的数据，不用重复调用。

### 3\. 配置 wrangler.jsonc
```

{  
  "$schema": "node_modules/wrangler/config-schema.json",  
  "name": "workflows-tutorial",  
  "main": "src/index.ts",  
  "compatibility_date": "2026-07-03",  
  "observability": {  
    "enabled":true  
  },  
  "workflows": [  
    {  
      "name": "workflows-tutorial",  
      "binding": "MY_WORKFLOW",  
      "class_name": "MyWorkflow"  
    }  
  ]  
}
```

`class_name` 必须和你导出的类名一致，`binding` 是代码里访问它的变量名（`env.MY_WORKFLOW`）。

配置完生成类型：
```

npx wrangler types
```

### 4\. 写触发入口

替换 `src/index.ts`，用一个 fetch handler 来创建和查询实例：
```

export default {  
  async fetch(req, env): Promise<Response> {  
    const url = new URL(req.url);  
    const instanceId = url.searchParams.get("instanceId");  
  
    // 查询已有实例状态  
    if (instanceId) {  
      const instance = await env.MY_WORKFLOW.get(instanceId);  
      return Response.json(await instance.status());  
    }  
  
    // 创建新实例  
    const instance = await env.MY_WORKFLOW.create();  
    return Response.json({ instanceId: instance.id });  
  },  
} satisfies ExportedHandler<Env>;
```

### 5\. 本地开发 & 部署
```

# 本地开发  
npx wrangler dev  
  
# 另开一个终端，触发一个实例  
curl http://localhost:8787  
# 返回 { "instanceId": "abc-123-def" }  
  
# 用返回的 ID 查状态  
curl "http://localhost:8787?instanceId=abc-123-def"  
  
# 部署到全球  
npx wrangler deploy
```

部署后还能用 CLI 直接查看实例执行详情：
```

npx wrangler workflows instances describe workflows-tutorial latest
```

它会显示每一步的状态（成功/失败/运行中）、每步产出的数据、sleep 状态（什么时候醒）、重试次数、以及错误信息。

## 四种步骤类型

![](https://r2.jeanjan.kdns.fr/pictures/img-6a16bd8a05.jpeg)

Workflows 的核心就是 `step` 对象提供的几个方法：

### 1\. `step.do` — 执行并持久化

最基础的步骤。执行一段代码，返回值会被持久化。流程中断重跑时，已完成的 `step.do` 不会重新执行，直接用存档的结果。
```

const user = await step.do("fetch user", async () => {  
  return await this.env.KV.get(event.payload.userId);  
});
```

### 2\. `step.sleep` / `step.sleepUntil` — 暂停

`step.sleep` 睡一段时长，`step.sleepUntil` 睡到某个具体时间点。**睡觉不消耗 CPU、不计费、不占并发数** ，最长能睡 365 天。
```

// 睡 3 天后发提醒  
await step.sleep("wait 3 days", "3 days");  
  
// 睡到某个具体时间  
await step.sleepUntil("wait until new year", new Date("2027-01-01"));
```

注意：`sleep` 不计入最大步骤数限制。

### 3\. `step.waitForEvent` — 等外部事件

挂起流程，等一个外部事件（webhook、人工审批、状态变化）到来才继续。这是"人工介入"（human-in-the-loop）的关键。
```

// 等 Stripe 的付款成功 webhook，最多等 1 小时  
const stripeEvent = await step.waitForEvent<StripeWebhook>(  
  "receive invoice paid webhook",  
  { type: "stripe-webhook", timeout: "1 hour" },  
);
```

在 Worker 里通过 `instance.sendEvent` 把事件发给正在等待的实例：
```

const instance = await env.MY_WORKFLOW.get(instanceId);  
await instance.sendEvent({  
  type: "stripe-webhook",  
  payload: webhookPayload,  
});
```

你甚至可以用 `Promise.race` 同时等多个事件，谁先到就走谁的分支：
```

const result = await Promise.race([  
  step.waitForEvent("payment success", { type: "payment-success", timeout: "4 hours" }),  
  step.waitForEvent("payment failure", { type: "payment-failure", timeout: "4 hours" }),  
]);
```

### 4\. 定时触发（schedules）

想让 Workflow 定期自动运行？直接在配置里加 `schedules`（cron 表达式），每次触发自动创建一个新实例，不用再写单独的 `scheduled` handler：
```

{  
  "workflows": [  
    {  
      "name": "my-workflow",  
      "binding": "MY_WORKFLOW",  
      "class_name": "MyWorkflow",  
      "schedules": ["0 * * * *"]  // 每小时执行一次  
    }  
  ]  
}
```

被定时触发的实例，能通过 `event.schedule` 拿到匹配的 cron 表达式和触发时间。

## 错误处理与重试

### 配置重试策略

每个 `step.do` 都能单独配置重试行为：
```

await step.do(  
  "call flaky API",  
  {  
    retries: {  
      limit: 5,              // 最多重试 5 次  
      delay: "10 seconds",   // 每次间隔  
      backoff: "exponential" // 退避策略：constant / linear / exponential  
    },  
    timeout: "30 seconds",   // 单次超时  
  },  
  async () => {  
    // 可能失败的操作  
  },  
);
```

三种退避策略：

  * • `constant`：固定间隔（10s, 10s, 10s...）
  * • `linear`：线性增长（10s, 20s, 30s...）
  * • `exponential`：指数增长（10s, 20s, 40s...）

### 不可重试的错误

有些错误重试也没用（比如参数非法）。抛 `NonRetryableError` 会立刻停止重试，把错误抛到顶层：
```

import { NonRetryableError } from "cloudflare:workflows";  
  
await step.do("validate input", async () => {  
  if (!event.payload.email) {  
    throw new NonRetryableError("email is required");  
  }  
});
```

### Saga 回滚：失败时自动补偿

这是 2026 年 6 月新增的强力特性。回到开头那个下单例子——扣款成功了，但后面物流单生成失败，整个流程要终止。钱怎么退？

现在你可以给每个 `step.do` 注册一个 `rollback` 补偿动作。当流程后续失败时，已成功步骤的 rollback 会**逆序执行** ，实现 Saga 模式的分布式事务回滚：
```

await step.do(  
  "create charge",  
  async () => {  
    const charge = await createCharge();  
    return { chargeId: charge.id };  
  },  
  {  
    // 当 Workflow 后续失败时，自动执行这个补偿动作  
    rollback: async ({ ctx, output, error }) => {  
      const { chargeId } = output as { chargeId: string };  
      await refundCharge(chargeId, {  
        reason: `${ctx.step.name}: ${error.message}`,  
      });  
    },  
    rollbackConfig: {  
      retries: { limit: 3, delay: "30 seconds", backoff: "linear" },  
      timeout: "5 minutes",  
    },  
  },  
);
```

`rollback` 能拿到原始步骤的输出（比如 `chargeId`）和导致失败的错误，让你精确地撤销之前的副作用。这省掉了大量手写的补偿逻辑。

![](https://r2.jeanjan.kdns.fr/pictures/img-6a16bd8a06.jpeg)

## Workflows 的"游戏规则"

Workflows 的执行模型有几条铁律，违反了会出诡异的 bug。核心原因是：**引擎会 hibernate（休眠）并丢掉所有内存状态** ，还可能重启重放。

![](https://r2.jeanjan.kdns.fr/pictures/img-6a16bd8a07.jpeg)

### 规则 1：步骤要幂等

步骤可能被重试多次，所以操作最好是幂等的——执行多次和执行一次结果一样。比如写数据库用 `INSERT ... ON CONFLICT`，而不是纯 `INSERT`。

### 规则 2：不要在步骤外存状态

休眠后内存变量会清空。所有状态都必须来自 `step.do` 的返回值。
```

// 🔴 错误：休眠后 imageList 会变空  
const imageList = [];  
await step.do("get cat 1", async () => {  
  imageList.push(await this.env.KV.get("cat-1")); // 存到了内存变量  
});  
  
// ✅ 正确：状态完全由 step 返回值构成  
const imageList = await Promise.all([  
  step.do("get cat 1", async () => this.env.KV.get("cat-1")),  
  step.do("get cat 2", async () => this.env.KV.get("cat-2")),  
]);
```

### 规则 3：副作用只放在步骤里

步骤外的代码可能在引擎重启时重复执行。比如步骤外的 `console.log` 可能打印两次。非确定性函数（`Math.random()`、`Date.now()`）必须包在 step 里。
```

// 🔴 错误：重启时结果不同，可能走不同分支  
const random = Math.random();  
  
// ✅ 正确：包在 step 里，成功后就固定了  
const random = await step.do("roll dice", async () => Math.random());
```

### 规则 4：步骤命名要确定

步骤名就是"缓存 key"。不要用日期/随机数命名，否则每次名字不同，缓存失效，步骤会被重复执行。
```

// 🔴 错误：名字每次都不同  
await step.do(`step at ${Date.now()}`, async () => { ... });  
  
// ✅ 正确：确定性命名  
await step.do("fetch user data", async () => { ... });
```

### 规则 5：一定要 `await` 你的步骤

忘记 `await` 会引入竞态条件和难查的 bug。

### 规则 6：条件逻辑基于确定性的值

`if`、循环这些可以用，但条件必须基于确定性的值（`event.payload` 或前面步骤的返回值），不能基于 `Math.random()` 这类。

## 实战场景

### 场景 1：可靠的 AI 图片处理流程

从 R2 读图 → 调 Workers AI 生成描述 → 等人工审核 → 发布。任何一步失败自动重试，等审核期间零成本挂起：
```

export class ImageProcessingWorkflow extends WorkflowEntrypoint<Env> {  
  async run(event: WorkflowEvent<{ imageKey: string }>, step: WorkflowStep) {  
    // 1. 从 R2 读图  
    const imageData = await step.do("fetch image", async () => {  
      const object = await this.env.BUCKET.get(event.payload.imageKey);  
      return await object.arrayBuffer();  
    });  
  
    // 2. 调 AI 生成描述  
    const description = await step.do("generate description", async () => {  
      const result = await this.env.AI.run("@cf/llava-hf/llava-1.5-7b-hf", {  
        image: [...new Uint8Array(imageData)],  
        prompt: "描述这张图片",  
      });  
      return result.description;  
    });  
  
    // 3. 等人工审核（可能等好几天，零成本）  
    const approval = await step.waitForEvent<{ approved: boolean }>(  
      "wait for approval",  
      { type: "review-decision", timeout: "7 days" },  
    );  
  
    // 4. 审核通过则发布  
    if (approval.approved) {  
      await step.do("publish", async () => {  
        await this.env.DB.prepare(  
          "UPDATE images SET status = 'published', description = ? WHERE key = ?"  
        ).bind(description, event.payload.imageKey).run();  
      });  
    }  
  }  
}
```

### 场景 2：用户生命周期邮件

注册后自动发一系列邮件，中间穿插 `step.sleep`：
```

async run(event: WorkflowEvent<{ email: string }>, step: WorkflowStep) {  
  await step.do("send welcome email", async () => {  
    await sendEmail(event.payload.email, "欢迎加入！");  
  });  
  
  await step.sleep("wait 3 days", "3 days");  
  
  await step.do("send tips email", async () => {  
    await sendEmail(event.payload.email, "3 个上手技巧");  
  });  
  
  await step.sleep("wait until trial ends", "11 days");  
  
  await step.do("send trial ending email", async () => {  
    await sendEmail(event.payload.email, "试用即将到期，续费享 8 折");  
  });  
}
```

一个普通 Worker 绝对做不到"睡 3 天再发下一封"，但 Workflows 天生支持，而且睡觉期间不花一分钱。

### 场景 3：带回滚的订单处理

开头的下单流程，用 Saga 回滚彻底解决：
```

async run(event: WorkflowEvent<OrderParams>, step: WorkflowStep) {  
  // 1. 扣库存（失败自动退回）  
  await step.do("reserve inventory", async () => {  
    await reserveStock(event.payload.items);  
    return { reserved: true };  
  }, {  
    rollback: async () => { await releaseStock(event.payload.items); },  
  });  
  
  // 2. 扣款（失败自动退款）  
  const charge = await step.do("charge payment", async () => {  
    return await createCharge(event.payload.amount);  
  }, {  
    rollback: async ({ output }) => { await refundCharge(output.chargeId); },  
  });  
  
  // 3. 生成物流单（如果这步失败，上面两步的 rollback 会逆序执行）  
  await step.do("create shipment", async () => {  
    return await createShipment(event.payload.address);  
  });  
  
  // 4. 发确认邮件  
  await step.do("send confirmation", async () => {  
    await sendEmail(event.payload.email, "下单成功！");  
  });  
}
```

如果第 3 步一直失败，引擎会自动执行：退款 → 退库存，让系统回到一致状态。你不用再手写那一大坨补偿代码。

## 关键限制

| 特性                 | Workers 免费版        | Workers 付费版          |
|--------------------|--------------------|----------------------|
| 每步 CPU 时间          | 10ms               | 默认 30 秒，可配到 5 分钟     |
| 每步墙上时间             | 无限（等 I/O 不算）       | 无限                   |
| 每步返回结果大小           | 1MiB               | 1MiB                 |
| 每实例可持久化状态          | 100MB              | 1GB                  |
| 单次 `step.sleep` 最长 | 365 天              | 365 天                |
| 每个 Workflow 最大步骤数  | 1,024              | 默认 10,000，可配到 25,000 |
| 每日实例创建数            | 10 万（与 Workers 共享） | 无限                   |
| 并发运行实例数            | 100                | 50,000               |
| 完成实例状态保留           | 3 天                | 30 天                 |

几个要点：

  * • **`step.sleep` 不计入步骤数限制**，尽管睡
  * • **`waiting` 状态不占并发数**：可以有几百万个实例同时在睡觉/等事件
  * • **大二进制输出** ：如果某步要返回大文件，返回 `ReadableStream<Uint8Array>`，但仍计入存储限制。超大文件建议存 R2，只在 step 里返回引用

## 进阶：管理实例

除了创建和查状态，你还能程序化地管理运行中的实例：
```

const instance = await env.MY_WORKFLOW.get(instanceId);  
  
// 查状态  
await instance.status();  
  
// 暂停 / 恢复  
await instance.pause();  
await instance.resume();  
  
// 终止  
await instance.terminate();  
  
// 从头或从某一步重启  
await instance.restart();  
await instance.restart({ from: { name: "charge payment" } });
```

批量创建实例（一次最多一批）、带自定义 ID 创建、设置更短的状态保留期，都在 `WorkflowInstanceCreateOptions` 里支持。

## Workflows vs 其他方案

| 特性     | Cloudflare Workflows | AWS Step Functions | Temporal           |
|--------|----------------------|--------------------|--------------------|
| 定义方式   | TypeScript 代码        | JSON(ASL) 或 SDK    | 多语言代码              |
| 执行模型   | 每实例一个 Durable Object | 托管服务               | 自建或 Temporal Cloud |
| 最大时长   | 数周                   | 1 年                | 无限                 |
| 单步状态上限 | 1MiB                 | 256KB（总计）          | 可配                 |
| 冷启动    | 亚毫秒                  | ~50-100ms          | 取决于部署              |
| 计费方式   | 按 CPU 时间（等待免费）       | 按状态转换次数            | 按动作数（云版）           |
| 运维负担   | 零                    | 零（托管）              | 高（自建）/ 中（云）        |

**结论** ：如果你已经在用 Cloudflare Workers，Workflows 几乎是零成本、零运维地接入持久化执行能力。它最大的优势是"只为 CPU 付费，等待免费"——对那些大量时间在等 API、等 LLM、等人工审批的流程，这个模型省钱又省心。

## 最佳实践速查

### ✅ 该做的

  1. 1\. **粗粒度划分步骤** ：把"调外部 API""查数据库"这种可能失败、且不想重跑的操作独立成 step
  2. 2\. **步骤保持幂等** ：用 `ON CONFLICT`、检查是否已执行，防止重试造成重复副作用
  3. 3\. **状态只来自 step 返回值** ：不要依赖步骤外的内存变量
  4. 4\. **确定性命名步骤** ：步骤名是缓存 key，别用时间戳/随机数
  5. 5\. **善用 sleep 和 waitForEvent** ：长时间等待是 Workflows 的杀手锏，且免费
  6. 6\. **给关键步骤配 rollback** ：涉及扣款、下单等有副作用的操作，用 Saga 回滚保证一致性
  7. 7\. **开启 observability** ：配置里加 `"observability": { "enabled": true }`，方便调试

### ❌ 常见坑

  1. 1\. **在步骤外做副作用** ：`console.log`、写数据库放在 step 外会在重启时重复执行
  2. 2\. **步骤外用非确定性函数** ：`Math.random()`、`Date.now()` 会导致重启后走不同分支
  3. 3\. **忘记` await`**：漏 await 会引入竞态条件
  4. 4\. **单步塞太多逻辑** ：一步失败会重跑整步，浪费已完成的工作
  5. 5\. **返回超大对象** ：单步返回上限 1MiB，大文件用流或存 R2
  6. 6\. **把 Workflows 当 Queues 用** ：处理大量独立任务用 Queues 更便宜

## 相关资源

  * • Workflows 官方文档[1]

#### 引用链接

`[1]` Workflows 官方文档:  _https://developers.cloudflare.com/workflows/_  


