# Cloudflare Hyperdrive：让远程数据库变快，像本地一样

**作者**: 木兆纸
**发布时间**: 2026-07-05 23:15
**原文链接**: https://mp.weixin.qq.com/s/mn_HgHKi39byvcogRSNIGQ

---

![](https://r2.jeanjan.kdns.fr/pictures/img-a1df90c201.jpeg)

## 为什么数据库这么慢？

你用 Workers 写了一个 API，部署到全球 300 多个数据中心，用户访问快如闪电。但只要一查数据库，整个请求就慢下来了。

问题不在你的代码，而在物理距离。

![](https://r2.jeanjan.kdns.fr/pictures/img-a1df90c202.jpeg)

你的数据库通常只部署在一个区域（比如 AWS us-east-1）。当一个东京用户触发请求时，Worker 可能在大阪执行，然后要跨太平洋去弗吉尼亚查数据库。一次查询的延迟结构是这样的：
```

╭─────────╮    网络延迟    ╭─────────╮    网络延迟    ╭─────────╮  
│  东京    │────── 80ms ──▶│  大阪    │────── 120ms ─▶│ us-east-1│  
│  用户    │◀────── 80ms ──│  Worker  │◀────── 120ms ─│ 数据库   │  
╰─────────╯               ╰─────────╯               ╰─────────╯  
  
总延迟 ≈ 400ms（光速的物理极限）
```

更糟糕的是，Worker 是无状态环境，每次请求都可能建立新连接。一次新的数据库连接需要：

  1. 1\. **TCP 握手** ：1 次往返
  2. 2\. **TLS 协商** ：3 次往返
  3. 3\. **数据库认证** ：3 次往返

光建连接就要 7 次往返。如果你的数据库在大洋彼岸，这 7 次往返可能就要 1 秒以上。

再加上数据库连接数有限（大多数托管数据库上限 20-100 个连接），全球流量一上来，连接就被打满了。

**Hyperdrive 就是为了解决这三个问题而生的：连接建立慢、查询延迟高、连接数不够用。**

##  Hyperdrive 是什么？

Hyperdrive 是 Cloudflare 的数据库加速服务。它不是一个新数据库，而是放在你现有数据库前面的一层加速代理。它做三件事：

  1. 1\. **边缘连接建立** ：在离 Worker 最近的地方完成连接握手，省掉跨洋往返
  2. 2\. **连接池管理** ：在数据库附近维护一组长期连接，所有 Worker 复用
  3. 3\. **查询缓存** ：自动缓存只读查询的响应，热门查询直接返回，不用回源

![](https://r2.jeanjan.kdns.fr/pictures/img-a1df90c203.jpeg)
```

                     ┌─────────────────────────────────────┐  
                     │        Cloudflare 全球网络           │  
                     │                                     │  
╭─────────╮         │  ╭──────────╮    ╭──────────────╮   │         ╭───────────╮  
│  全球    │  请求   │  │ 边缘节点  │    │ Hyperdrive   │   │  复用   │  你的     │  
│  用户    │────────▶│  │ Worker   │───▶│ · 连接池     │───▶│ 连接    │  数据库   │  
│          │◀────────│  │          │◀───│ · 查询缓存   │◀───│         │  PG/MySQL │  
╰─────────╯  响应    │  ╰──────────╯    ╰──────────────╯   │         ╰───────────╯  
                     │       边缘               数据库附近   │  
                     └─────────────────────────────────────┘  
  
① 连接建立：在边缘完成（< 5ms）  
② 查询路由：缓存命中直接返回 / 未命中走连接池  
③ 连接复用：数据库端保持长期连接
```

![](https://r2.jeanjan.kdns.fr/pictures/img-a1df90c204.jpeg)

关键区别：

| 场景   | 没有 Hyperdrive   | 有 Hyperdrive         |
|------|-----------------|----------------------|
| 建连接  | 7 次跨洋往返（~1s）    | 边缘完成（< 5ms）          |
| 查询延迟 | 每次跨洋（100-300ms） | 缓存命中 < 10ms，未命中走池化连接 |
| 连接数  | 每个请求一个，容易打满     | 全局池化，复用现有连接          |
| 改代码  | —               | 不用改，换连接字符串就行         |

## 免费额度 & 定价

Hyperdrive 包含在 Workers 套餐里，不单独收费：

| 项目          | 免费计划    | 付费计划（$5/月起） |
|-------------|---------|-------------|
| 数据库查询       | 10 万次/天 | **无限**      |
| 连接池         | ✅ 包含    | ✅ 包含        |
| 查询缓存        | ✅ 包含    | ✅ 包含        |
| 数据出口费       | 无       | 无           |
| 最大数据库配置数    | 10 个/账户 | 25 个/账户     |
| 最大连接数（每个配置） | ~20     | ~100        |

几个关键点：

  * • **"数据库查询"包括什么** ：`SELECT`、`INSERT`、`UPDATE`、`DELETE`、`CREATE`、`ALTER`、`DROP`，所有经过 Hyperdrive 的数据库语句都算
  * • **缓存查询也算** ：命中缓存的查询和未命中的计费方式一样
  * • **没有隐藏费用** ：连接池和查询缓存不额外收费，不收数据出口费
  * • **免费版限制** ：每天 10 万次查询，超了会报错，UTC 0 点重置

对比一下自建方案的成本：

| 方案                      | 月成本             | 维护负担           |
|-------------------------|-----------------|----------------|
| 自建 PgBouncer + Redis 缓存 | $20-50（服务器）+ 人力 | 高              |
| Supabase 连接池            | 含在 Supabase 套餐内 | 低，但绑定 Supabase |
| Neon 无服务器               | 按 compute 时间计费  | 低              |
| **Hyperdrive + 任意数据库**  | **$5/月起**       | **几乎为零**       |

##  5 分钟快速开始

### 前置条件

  * • Cloudflare 账户
  * • Node.js 16.17.0+
  * • 一个公开可访问的 PostgreSQL 或 MySQL 数据库

### 1\. 创建 Worker 项目
```

npm create cloudflare@latest -- hyperdrive-tutorial  
# 选择：Hello World → Worker only → TypeScript  
cd hyperdrive-tutorial
```

### 2\. 创建 Hyperdrive 配置
```

npx wrangler hyperdrive create my-db \  
  --connection-string="postgres://user:password@db-host.example.com:5432/mydb"
```

成功后会返回一个配置 ID，复制备用。

### 3\. 配置 wrangler.jsonc
```

{  
  "$schema": "node_modules/wrangler/config-schema.json",  
  "name": "hyperdrive-tutorial",  
  "main": "src/index.ts",  
  "compatibility_date": "2025-02-04",  
  "compatibility_flags": [  
    "nodejs_compat"  
  ],  
  "hyperdrive": [  
    {  
      "binding": "HYPERDRIVE",  
      "id": "<你的 Hyperdrive 配置 ID>",  
      "localConnectionString": "postgres://user:password@localhost:5432/mydb"  
    }  
  ]  
}
```

`localConnectionString` 用于本地开发（`wrangler dev`），线上环境自动使用 Hyperdrive 代理。

### 4\. 安装数据库驱动
```

# PostgreSQL  
npm i pg  
npm i -D @types/pg  
  
# 或 MySQL  
npm i mysql2
```

### 5\. 写 Worker 代码

**PostgreSQL 版本：**
```

 import { Client } from "pg";  
  
export interface Env {  
  HYPERDRIVE: Hyperdrive;  
}  
  
export default {  
  async fetch(request, env, ctx): Promise<Response> {  
    const client = new Client({  
      connectionString: env.HYPERDRIVE.connectionString,  
    });  
  
    try {  
      await client.connect();  
      const result = await client.query(  
        "SELECT id, title, created_at FROM articles ORDER BY created_at DESC LIMIT 10"  
      );  
      return Response.json(result.rows);  
    } catch (e) {  
      return Response.json(  
        { error: e instanceof Error ? e.message : e },  
        { status: 500 }  
      );  
    }  
  },  
} satisfies ExportedHandler<Env>;
```

**MySQL 版本：**
```

 import { createConnection } from "mysql2/promise";  
  
export interface Env {  
  HYPERDRIVE: Hyperdrive;  
}  
  
export default {  
  async fetch(request, env, ctx): Promise<Response> {  
    const connection = await createConnection({  
      host: env.HYPERDRIVE.host,  
      user: env.HYPERDRIVE.user,  
      password: env.HYPERDRIVE.password,  
      database: env.HYPERDRIVE.database,  
      port: env.HYPERDRIVE.port,  
      disableEval: true, // Workers 不支持 eval()  
    });  
  
    try {  
      const [results] = await connection.query(  
        "SELECT id, title, created_at FROM articles ORDER BY created_at DESC LIMIT 10"  
      );  
      return Response.json(results);  
    } catch (e) {  
      return Response.json(  
        { error: e instanceof Error ? e.message : e },  
        { status: 500 }  
      );  
    }  
  },  
} satisfies ExportedHandler<Env>;
```

注意：每个请求都 `new Client()` / `createConnection()`。这看起来很低效，但 Hyperdrive 在底层维护连接池，创建客户端只是拿到连接字符串，实际连接是复用的。

### 6\. 本地开发 & 部署
```

# 本地开发（连接 localConnectionString 指定的数据库）  
npx wrangler dev  
  
# 部署到全球  
npx wrangler deploy
```

部署后，你的 API 就通过 Hyperdrive 加速访问数据库了。**代码和原来几乎一样，只是连接字符串换了。**

##  查询缓存：默认开启，自动加速

Hyperdrive 最强大的特性之一是自动查询缓存。它不需要你写缓存逻辑，而是在数据库协议层识别读写查询，自动缓存只读查询的响应。

### 缓存的工作方式
```

╭─────────╮         ╭──────────────╮         ╭─────────╮  
│ Worker  │ ──SQL──▶│ Hyperdrive   │ ──miss──▶│ 数据库  │  
│         │         │              │◀──resp───│         │  
│         │◀─cached─│  缓存层      │         ╰─────────╯  
│         │         │  max_age=60s │  
│         │         │  swr=15s     │  
╰─────────╯         ╰──────────────╯
```

默认配置：

  * • **max_age** ：60 秒（缓存最大存活时间，可配置到 1 小时）
  * • **stale_while_revalidate** ：15 秒（过期后还能用旧数据顶 15 秒）

### 什么能缓存，什么不能？

| 查询类型                           | 是否缓存  | 例子                                  |
|--------------------------------|-------|-------------------------------------|
| `SELECT`（参数化）                  | ✅ 缓存  | `SELECT * FROM users WHERE id = $1` |
| `INSERT` / `UPDATE` / `DELETE` | ❌ 不缓存 | 写操作永远不缓存                            |
| 含 `NOW()` / `CURRENT_DATE`     | ❌ 不缓存 | 非确定性函数                              |
| 含 `RANDOM()` / `LASTVAL()`     | ❌ 不缓存 | 每次结果不同                              |
| `SET` 语句                       | ❌ 不缓存 | 会话级设置                               |

**重要提示** ：Hyperdrive 用文本匹配检测不可缓存的函数。即使 `NOW()` 只出现在 SQL 注释里，也会导致整个查询不被缓存。

![](https://r2.jeanjan.kdns.fr/pictures/img-a1df90c205.jpeg)

### 缓存优化技巧
```

// ❌ 不缓存：NOW() 是 STABLE 函数  
const result = await client.query(  
  "SELECT * FROM events WHERE created_at > NOW() - INTERVAL '1 hour'"  
);  
  
// ✅ 缓存：把时间计算移到应用层，用参数传入  
const oneHourAgo = new Date(Date.now() - 3600000).toISOString();  
const result = await client.query(  
  "SELECT * FROM events WHERE created_at > $1",  
  [oneHourAgo]  
);
```

### 多连接配置：一个缓存，一个不缓存

有些查询不适合缓存（比如实时仪表盘），你可以配置两个 Hyperdrive 绑定：
```

{  
  "hyperdrive": [  
    {  
      "binding": "HYPERDRIVE",  
      "id": "<缓存配置 ID>"  
    },  
    {  
      "binding": "HYPERDRIVE_RAW",  
      "id": "<不缓存配置 ID>"  
    }  
  ]  
}

// 读取热门数据 → 走缓存  
const cached = await client.query("SELECT * FROM products WHERE popular = true");  
  
// 实时仪表盘 → 不缓存  
const raw = new Client({ connectionString: env.HYPERDRIVE_RAW.connectionString });  
const realtime = await raw.query("SELECT COUNT(*) FROM active_sessions");
```

## 支持的数据库

Hyperdrive 支持所有主流 PostgreSQL 和 MySQL 数据库：

| 数据库                  | 类型                 | 状态                       |
|----------------------|--------------------|--------------------------|
| PostgreSQL（自建 / 云托管） | PostgreSQL         | ✅                        |
| Neon                 | PostgreSQL         | ✅                        |
| Supabase             | PostgreSQL         | ✅                        |
| Amazon RDS / Aurora  | PostgreSQL / MySQL | ✅                        |
| Google Cloud SQL     | PostgreSQL / MySQL | ✅                        |
| Azure Database       | PostgreSQL / MySQL | ✅                        |
| PlanetScale          | MySQL              | ✅（可在 Cloudflare 仪表盘直接创建） |
| CockroachDB          | PostgreSQL 兼容      | ✅                        |
| Timescale            | PostgreSQL 兼容      | ✅                        |
| Materialize          | PostgreSQL 兼容      | ✅                        |

只要你的数据库有公网可访问的地址，Hyperdrive 就能连接。如果数据库在私有网络里，可以通过 Workers VPC 连接。

## 实战场景

### 场景 1：加速现有 API

你有一个跑在 Vercel/Cloudflare Workers 上的 API，数据库在 AWS RDS。加上 Hyperdrive 只需要：

  1. 1\. 创建 Hyperdrive 配置，指向 RDS
  2. 2\. 把连接字符串换成 `env.HYPERDRIVE.connectionString`
  3. 3\. 部署

不需要改 SQL，不需要换 ORM，不需要迁移数据库。全球用户的查询延迟立刻下降。

### 场景 2：配合 D1 做读写分离

D1 是 Cloudflare 自己的 SQLite 数据库，适合边缘低延迟场景。但如果你的数据在 PostgreSQL 里，不想迁移，可以用 Hyperdrive 加速读查询 + D1 做本地缓存：
```

// 先查 D1 本地缓存  
const cached = await env.DB.prepare(  
  "SELECT * FROM cache WHERE key = ? AND expires_at > datetime('now')"  
).bind(cacheKey).first();  
  
if (cached) return Response.json(JSON.parse(cached.value));  
  
// D1 没命中，走 Hyperdrive 查 PostgreSQL  
const pg = new Client({ connectionString: env.HYPERDRIVE.connectionString });  
await pg.connect();  
const result = await pg.query("SELECT * FROM products WHERE category = $1", [category]);  
  
// 写入 D1 缓存  
await env.DB.prepare(  
  "INSERT OR REPLACE INTO cache (key, value, expires_at) VALUES (?, ?, datetime('now', '+5 minutes'))"  
).bind(cacheKey, JSON.stringify(result.rows)).run();  
  
return Response.json(result.rows);
```

### 场景 3：多区域读副本 + Placement

如果你的 Worker 每个请求要执行多次数据库查询（比如先查用户、再查订单、再查商品），可以用 Placement 把 Worker 调度到数据库附近：
```

{  
  "placement": {  
    "region": "aws:us-east-1"  
  },  
  "hyperdrive": [  
    {  
      "binding": "HYPERDRIVE",  
      "id": "<配置 ID>"  
    }  
  ]  
}
```

这样 Worker 在数据库同区域执行，每次查询只要 1-3ms，而不是跨洋的 100-300ms。

## 成本计算器

以一个独立开发者的典型场景估算：
```

╭──────────────────────────────────────────────────────╮  
│  场景：SaaS 产品，日活 1000 用户                       │  
│                                                      │  
│  每用户每天平均 50 次 API 调用                         │  
│  每次 API 调用 2 次数据库查询（1 读 + 1 写）            │  
│  总查询数 = 1000 × 50 × 2 = 100,000 次/天            │  
│                                                      │  
│  免费额度：100,000 次/天                              │  
│  结论：免费版刚好覆盖，升级 Paid 后无限                 │  
╰──────────────────────────────────────────────────────╯
```

| 项目            | 免费版    | Paid 版（$5/月） |
|---------------|--------|--------------|
| Workers 请求    | 10 万/天 | 1000 万/月含内   |
| Hyperdrive 查询 | 10 万/天 | 无限           |
| 连接池 + 缓存      | 包含     | 包含           |
| 数据出口费         | 0      | 0            |
| **月成本**       | **$0** | **$5**       |

**对比：如果自建连接池 + 缓存层**

| 方案                      | 月成本      | 维护           |
|-------------------------|----------|--------------|
| EC2 + PgBouncer + Redis | $30-60   | 高（要维护 3 个组件） |
| Supabase Pro（含连接池）      | $25      | 低            |
| Neon Pro                | $19+     | 低            |
| **Hyperdrive + 任意数据库**  | **$0-5** | **几乎为零**     |

##  最佳实践 & 避坑指南

### ✅ 最佳实践

  1. 1\. **每个请求创建新客户端** ：`new Client()` 放在 `fetch` handler 里，不要放全局。Hyperdrive 底层会复用连接
  2. 2\. **用参数化查询** ：`$1`、`$2` 占位符，既防 SQL 注入，又让缓存生效
  3. 3\. **把时间函数移到应用层** ：`NOW()`、`CURRENT_DATE` 不会被缓存，改用参数传入
  4. 4\. **读写分离** ：读操作走缓存配置，写操作走不缓存配置
  5. 5\. **配合 Placement** ：多次顺序查询时，把 Worker 调度到数据库附近
  6. 6\. **本地开发用 localConnectionString** ：不走 Hyperdrive，直连本地数据库

### ❌ 常见坑

  1. 1\. **全局创建客户端** ：会导致连接在 Worker 生命周期内一直持有，影响连接池效率
  2. 2\. **长事务** ：事务期间连接不会归还池，会阻塞其他请求。尽量保持事务短小
  3. 3\. **SQL 注释里写 NOW()** ：文本匹配会检测注释里的函数名，导致整个查询不缓存
  4. 4\. **SET 语句跨查询** ：`SET` 只在当前事务/查询内生效，不要依赖跨查询的 `SET` 状态
  5. 5\. **忘记` disableEval: true`（MySQL）**：mysql2 默认用 eval() 解析结果，Workers 不支持
  6. 6\. **连接字符串里用非参数化密码** ：特殊字符需要 URL 编码

### 调试技巧
```

# 查看 Hyperdrive 配置  
npx wrangler hyperdrive list  
  
# 查看某个配置详情  
npx wrangler hyperdrive get   
  
# 更新配置（比如禁用缓存）  
npx wrangler hyperdrive update  \  
  --origin-password "your-password" \  
  --caching-disabled true  
  
# 本地开发时查看查询日志  
npx wrangler dev --log-level debug
```

## Hyperdrive vs 其他方案

| 特性     | Hyperdrive | PgBouncer | Supabase 连接池 | Neon         |
|--------|------------|-----------|--------------|--------------|
| 全球边缘加速 | ✅          | ❌         | ❌            | ❌            |
| 查询缓存   | ✅ 自动       | ❌         | ❌            | ❌            |
| 连接池    | ✅          | ✅         | ✅            | ✅（按 compute） |
| 改代码    | 换连接字符串     | 换端口       | 换端口          | 换连接字符串       |
| 运维负担   | 零          | 要自己部署     | 零            | 零            |
| 支持数据库  | PG + MySQL | PG        | PG           | PG           |
| 数据出口费  | 无          | 取决于云厂商    | 按套餐          | 按套餐          |
| 月成本    | $0-5       | $20+（服务器） | $25+         | $19+         |

**结论** ：如果你已经在用 Cloudflare Workers，Hyperdrive 几乎是零成本接入，零运维负担。它不是要替代你的数据库，而是让你已有的数据库在全球范围内更快。

## 相关资源

  * • Hyperdrive 官方文档[1]
  * • 如何连接 PostgreSQL[2]
  * • 如何连接 MySQL[3]
  * • 查询缓存详解[4]
  * • Hyperdrive 定价[5]
  * • Hyperdrive 限制[6]
  * • Workers 存储选项对比[7]
  * • Cloudflare Developers Discord[8]

#### 引用链接

`[1]` Hyperdrive 官方文档:  _https://developers.cloudflare.com/hyperdrive/_  
`[2]` 如何连接 PostgreSQL:  _https://developers.cloudflare.com/hyperdrive/examples/connect-to-postgres/_  
`[3]` 如何连接 MySQL:  _https://developers.cloudflare.com/hyperdrive/examples/connect-to-mysql/_  
`[4]` 查询缓存详解:  _https://developers.cloudflare.com/hyperdrive/concepts/query-caching/_  
`[5]` Hyperdrive 定价:  _https://developers.cloudflare.com/hyperdrive/platform/pricing/_  
`[6]` Hyperdrive 限制:  _https://developers.cloudflare.com/hyperdrive/platform/limits/_  
`[7]` Workers 存储选项对比:  _https://developers.cloudflare.com/workers/platform/storage-options/_  
`[8]` Cloudflare Developers Discord:  _https://discord.cloudflare.com_  


