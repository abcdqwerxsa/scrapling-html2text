# 将数据库从 Cloudflare D1 迁移至 Postgres

**作者**: 开发者山石
**发布时间**: 2026-09-03 20:27
**原文链接**: https://mp.weixin.qq.com/s/DMqhUH_JLUoMzqIBLiPMvA

---

我线上有一个应用目前是通过广告费获取收益，数据库用的 Cloudflare D1，最近在给这个应用增加一个新功能。由于新功能比较昂贵，不能像原来一样免费随便用了，于是计划实现一套 credit 系统，也不排除后续增加付费计划的可能。

在实现这套 Credit 系统时，就发现 Cloudflare D1 存在很多局限性，比如不支持完整的 Transaction、不能加锁等，导致需要很多手段去弥补竞态条件下的一致性问题，有些甚至无法解决，于是起了迁移数据库的心思。

## 数据库选择

我从一开始就排除掉了 MySQL，选择 Postgres，因为之前用过。而且社区大家也都推荐 Postgres。

Postgres 供应商有几个选择：

1.

Supabase：这是很多 SaaS 的选择，每个月 25 美元。但是这个套餐里包含了 Function, Email, Auth 等功能，我并不需要，对我来说相当于溢价了。

2.

Neon：一个 Serverless 的 postgres，按量收费。这个对于那些流量一阵一阵的应用是挺合适的，没有流量不收费。但是我这个应用大部分时间都有流量，按量付费反而会更贵，而且成本不可控。

3.

Planetscale：也是最近了解到的平台，知道它还是因为它和 Cloudflare 有了合作，可以直接在 Cloudflare 里创建，账单走 Cloudflare。这个评估下来是目前最适合我的。

在 Planetscale 购买数据其实是新建了一个数据库实例，就像部署在 VPS 上的数据库实例一样。不同的规格价格不一样，最便宜的 PS-5 如果不用副本，每个月才 5 美元。包括 1/16 CPU，512MB memory, 10G Disk。每个月出站流量限制 100G。对于目前的应用来说绰绰有余，成本也能被覆盖掉。

  

## 多个项目共用一个数据库实例

选择 Plantscale 的另一个原因是官方推荐使用逻辑数据库，从而让多个应用能共享一个数据库实例，这可以极大降低成本。而 Supabase 不推荐这么做。

官方博客：https://planetscale.com/blog/one-postgres-cluster-many-apps，也是今年 7 月才开始支持的。

具体的实现方法与之前在 VPS 上新建逻辑数据的方法类似[通过 Cloudflare Hyperdrive + Worker VPC 连接 VPS 数据库](https://mp.weixin.qq.com/s?__biz=Mzk0NDYwMzc1NA==&mid=2247485279&idx=1&sn=542c75c78ae52a1b938743887ffc7e4f&scene=21#wechat_redirect)，稍微有一些差别的地方是有些操作需要在 Planetscale 平台上进行，具体步骤如下：

### 一、创建超级管理员。

进入 Planetscale 实例控制面板后，点击【connect】，创建 default role，这是一个超级管理员。我们需要一个超级管理员来创建数据库。

![](https://r2.jeanjan.kdns.fr/pictures/img-c604b9b201.png)![](https://r2.jeanjan.kdns.fr/pictures/img-c604b9b202.png)

创建好之后，可以拿到连接链接

  

### 二、创建数据库

用第一步拿到的链接在本地通过 pgsql 连到数据里，创建数据库，并且让其他 role 无法连到这个数据。
```

CREATE DATABASE app_db;  
REVOKE CONNECT ON DATABASE app_db FROM PUBLIC;  

```

  

### 三、创建一个 app 专属的用户

来连接数据库，同样在 Planetscale 控制台进行。配置权限如下。

![](https://r2.jeanjan.kdns.fr/pictures/img-c604b9b203.png)

上面第二个红框可选 pg_strict 插件，建议选上，可以避免 delete all 这种危险操作。要开启这个功能，需要先在 cluster 里开启 pg_strict 插件。

![](https://r2.jeanjan.kdns.fr/pictures/img-c604b9b204.png)

### 四、给新用户授予权限

在之前的命令行中授予用户权限，主要有俩个：
```

// 允许用户连接这个数据  
GRANT CONNECT ON DATABASE app_db TO pscale_api_xxxx;  
  
// 允许用户能 migration  
GRANT CREATE, USAGE ON SCHEMA public TO pscale_api_xxxx;  

```

这样就创建好了，用第三方拿到的链接，修改一下数据库名称就可以了。至于怎么创建 Hyperdrive，参考之前的文章[通过 Cloudflare Hyperdrive + Worker VPC 连接 VPS 数据库](https://mp.weixin.qq.com/s?__biz=Mzk0NDYwMzc1NA==&mid=2247485279&idx=1&sn=542c75c78ae52a1b938743887ffc7e4f&scene=21#wechat_redirect)。

## 迁移数据库之后有什么好处

目前我的线上数据库已经迁移好了，观察了几天，流量完全扛得住。除了这个之外还有两个额外的好处：

1.

Planetscale 提供 Query Insight 工具，可以看到过去 24 小时耗时最多的 Query 是什么，如果是因为没有建索引导致的，还会提醒。这很方便去排查性能问题。

![](https://r2.jeanjan.kdns.fr/pictures/img-c604b9b205.png)

2.

可以使用很多支持 Postgres 的其他工具，比如 BI 分析工具 Metabase，这个会再更一篇文章来讲，原来没有 BI 分析工具支持 Cloudflare D1 。

  


