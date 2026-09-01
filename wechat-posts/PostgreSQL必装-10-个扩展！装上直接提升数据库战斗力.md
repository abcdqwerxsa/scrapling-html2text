# PostgreSQL必装 10 个扩展！装上直接提升数据库战斗力

**作者**: 隅间码栈
**发布时间**: 2026-07-25 15:08
**原文链接**: https://mp.weixin.qq.com/s/wpf-K2ZweIUtEGMcG6O-Gw

---

同样是使用PostgreSQL，不同团队发挥出来的能力差距很大。 很多项目只用到基础增删改查，完全不知道依靠扩展，可以低成本实现慢SQL排查、模糊检索、字段加密、向量搜索、定时任务等功能，不用额外引入中间件。

![](https://r2.jeanjan.kdns.fr/pictures/img-ffbf891a01.jpeg)

我整理了10个通用性最高、踩坑少、线上广泛验证的扩展，覆盖运维监控、文本检索、安全加密、AI向量、定时任务等场景。

> 说明：部分扩展需要修改配置文件重启数据库，部署生产前务必在测试环境验证兼容性。

![](https://r2.jeanjan.kdns.fr/pictures/img-ffbf891a02.jpeg)

## 1\. pg_stat_statements（生产第一优先级必装）

**作用** ：跟踪所有SQL执行统计，定位慢查询、分析SQL耗时、调用次数、缓存命中率，数据库性能排查首选工具。**注意** ：需要写入`shared_preload_libraries`，修改后重启实例生效。
```

CREATE EXTENSION IF NOT EXISTS pg_stat_statements;  
-- 查询耗时最高的SQL  
SELECT query, calls, total_time, mean_time  
FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;  

```

## 2\. pg_trgm

**作用** ：实现字符串相似度匹配、模糊高效查询，支持`LIKE %关键词%`走索引。 适用：商品名称、用户名、地址模糊搜索，不用上ES就能实现简易容错检索。
```

CREATE EXTENSION IF NOT EXISTS pg_trgm;  
SELECT similarity('张三','张三三');  

```

## 3\. pgcrypto

**作用** ：数据库内置加密函数，支持md5、aes加密、哈希加盐，敏感字段（手机号、身份证）加密存储首选。 避免业务层加密逻辑分散，统一在数据库层处理数据脱敏。
```

CREATE EXTENSION IF NOT EXISTS pgcrypto;  

```

## 4\. pgvector

**作用** ：AI时代热门扩展，原生支持向量类型、相似度检索，搭建RAG知识库、语义搜索。 优势：业务数据与向量存在同库，无需维护向量数据库，中小规模AI应用首选。
```

CREATE EXTENSION IF NOT EXISTS vector;  

```

## 5\. pg_cron

**作用** ：在数据库内部执行定时SQL，替代服务器crontab。 场景：定期清理过期数据、定时统计汇总、数据归档。
```

CREATE EXTENSION IF NOT EXISTS pg_cron;  
-- 每小时清理过期会话  
SELECT cron.schedule('clean_data','0 * * * *',$$DELETE FROM session WHERE expire<now()$$);  

```

## 6\. hypopg

**作用** ：虚拟索引扩展，可以模拟创建索引，不用占用磁盘资源，快速验证新增索引能否优化慢SQL。 索引优化神器，避免盲目建大量无用索引。
```

CREATE EXTENSION IF NOT EXISTS hypopg;  

```

## 7\. citext

**作用** ：大小写不敏感文本类型。 存储账号、邮箱时，不用反复写`lower()`做匹配，简化查询条件。
```

CREATE EXTENSION IF NOT EXISTS citext;  

```

## 8\. hll

**作用** ：HyperLogLog基数估算，高效近似去重统计，适合海量数据UV统计，占用空间远小于精确计数。 大数据报表、用户活跃统计场景。
```

CREATE EXTENSION IF NOT EXISTS hll;  

```

## 9\. pg_prewarm

**作用** ：数据库重启后，主动把热点表数据加载到内存缓存，避免重启初期大量冷查询拖垮性能。 适合核心业务库、频繁重启的测试/生产环境。
```

CREATE EXTENSION IF NOT EXISTS pg_prewarm;  

```

## 10\. postgis

**作用** ：地理空间数据扩展。 门店坐标、轨迹、距离计算、区域范围查询，需要地理位置业务直接启用。

> 没有GIS业务可以不安装。

## 简单部署建议

  1. **通用业务基线** ：pg_stat_statements、pg_trgm、pgcrypto 优先部署，几乎所有项目都能用；
  2. AI语义检索项目：追加 pgvector；
  3. 需要定时归档清理数据：增加 pg_cron；
  4. 报表海量去重统计：引入 hll；
  5. 索引调优频繁：装上 hypopg。

## 最后提醒

扩展并不是越多越好，按需启用。第三方扩展尽量选用社区成熟稳定版本，上线前评估内存开销、版本兼容性；主从架构下，大部分扩展需要主备同步安装。

  


