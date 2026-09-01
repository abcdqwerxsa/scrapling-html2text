# 零成本授权鉴权：激活码 + 设备指纹绑定，用 Cloudflare Workers 轻松搞定

**作者**: 星辰AI智界
**发布时间**: 2026-07-03 23:05
**原文链接**: https://mp.weixin.qq.com/s/--16O3OtKhQwdNztkRwpXQ

---

> 本文以「考试预约助手」浏览器插件为例，讲述如何零服务器、零数据库，仅凭 Cloudflare Workers + KV 实现一套完整的**激活码 + 设备指纹** 鉴权体系。涵盖 ECDSA 签名验签、离线宽限期、心跳续签、时钟防回拨等工程细节。

## 一、为什么选择 Cloudflare Workers + KV

浏览器插件做付费/授权分发时，开发者面临的核心难题是：

| 痛点      | 传统方案代价                  |
|---------|-------------------------|
| 需要一台服务器 | 域名 + SSL + 运维，月成本 ≥ ¥50 |
| 需要数据库   | 激活码、设备记录的存储与备份          |
| 全球低延迟   | 需要 CDN 加速 API 响应        |
| 需要防破解   | 自建签名服务，安全性难保障           |

**Cloudflare Workers + KV** 的组合拳，把上面的痛点一次性击穿：

  * **Workers** ：Serverless 函数，全球 300+ 边缘节点部署，冷启动 < 5ms
  * **KV** ：全球分布式键值存储，最终一致（~60s 全球同步），免费层每天 10 万次读
  * **零成本启动** ：免费层可支撑约 1 万活跃用户
  * **Web Crypto API 原生支持** ：Workers 和浏览器端都内置`crypto.subtle`，ECDSA-P256 签名/验签零依赖

## 二、系统架构总览
```

┌──────────────────────────────────────────────────────────────┐  
│                     浏览器插件（客户端）                        │  
│                                                              │  
│  ┌──────────┐   ┌──────────────┐   ┌──────────────────────┐ │  
│  │config.js │   │ license.js   │   │  background.js       │ │  
│  │ 公钥配置  │   │ 指纹采集     │   │  心跳调度(30min)      │ │  
│  │ Server URL│   │ 激活/验签    │   │  Auth 拦截           │ │  
│  └──────────┘   └──────┬───────┘   └──────────┬───────────┘ │  
│                        │                      │             │  
│                ┌───────▼──────────────────────▼─────┐       │  
│                │     chrome.storage.local            │       │  
│                │  (licenseState / latestAuth)        │       │  
│                └────────────────────────────────────┘       │  
│                              │ HTTPS                         │  
└──────────────────────────────┼───────────────────────────────┘  
                               │  
              ┌────────────────▼────────────────┐  
              │     Cloudflare Worker            │  
              │     (license-worker)             │  
              │                                  │  
              │  POST /activate  → 签发+签名     │  
              │  POST /verify    → 校验+续签     │  
              │  POST /heartbeat → 心跳+续签     │  
              │  POST /unbind    → 解绑设备      │  
              │  POST /admin/*   → 管理后台      │  
              │                                  │  
              │  ECDSA-P256 私钥（Worker Secret）│  
              └────────┬────────────┬────────────┘  
                       │            │  
          ┌────────────▼──┐  ┌──────▼──────────┐  
          │  KV: LICENSES │  │  KV: DEVICES     │  
          │  激活码信息    │  │  设备记录         │  
          ├───────────────┤  ├─────────────────┤  
          │ KV:CODE_DEVICES│  │ KV: TOKEN_INDEX  │  
          │ 码→设备反索引  │  │ Token→设备索引   │  
          └───────────────┘  └─────────────────┘  

```

## 三、数据模型设计

四个 KV 命名空间，职责分明：

| Namespace      | Key 格式           | Value                                                                                                     | 用途                |
|----------------|------------------|-----------------------------------------------------------------------------------------------------------|-------------------|
| `LICENSES`     | `lic:<CODE>`     | `{maxDevices, expireAt, createdAt, revoked, note}`                                                        | 激活码本身的信息          |
| `DEVICES`      | `dev:<deviceId>` | `{deviceId, code, fingerprintHash, fingerprintParts[], token, tokenExpireAt, activatedAt, lastHeartbeat}` | 每台设备的详细记录         |
| `CODE_DEVICES` | `cd:<CODE>`      | `[deviceId, deviceId, ...]`                                                                               | 激活码 → 设备列表的反向索引   |
| `TOKEN_INDEX`  | `tk:<token>`     | `deviceId`                                                                                                | Token → 设备的快速查找索引 |

### 为什么需要四个 KV？

KV 不支持按 value 查询，也不支持二级索引。如果只有`DEVICES`，想知道"某个 token 对应哪个设备"就得全量扫描——这在 KV 中是不可行的。因此用`TOKEN_INDEX` 做了一层手工索引：
```

activate/verify/heartbeat 请求带 token  
  → TOKEN_INDEX["tk:<token>"] 得到 deviceId  
  → DEVICES["dev:<deviceId>"] 得到完整设备记录  
  → 2 次 KV 读操作搞定  

```

同理，`CODE_DEVICES` 解决的是"一个激活码绑了几台设备"的查询：
```

activate 时检查设备数  
  → CODE_DEVICES["cd:<CODE>"] 得到 deviceId[]  
  → 判断 length < maxDevices  

```

## 四、设备指纹：精准但不致命

设备指纹是整套方案中"谁在用"的核心依据。

### 4.1 采集什么
```

const parts = [  
  navigator.platform,           // 操作系统平台  
  navigator.userAgent,          // 浏览器 UA  
  navigator.hardwareConcurrency, // CPU 核心数  
  screen.width + "x" + screen.height + "x" + screen.colorDepth, // 屏幕  
  Intl.DateTimeFormat().resolvedOptions().timeZone, // 时区  
  navigator.language,           // 语言  
  chrome.runtime.id,            // 扩展 ID  
];  
const hash = sha256(parts.join("|") + "|y3t00l-salt-v1");  

```

7 个维度，全部是浏览器原生 API 可获取、无需用户授权的信息。

### 4.2 模糊匹配策略

浏览器升级、屏幕分辨率微调等情况会导致指纹漂移。如果严格匹配，用户体验会很差。因此引入**模糊匹配** ：
```

7 项指纹中匹配 ≥ 5 项 → 认定为同一设备  

function countFingerprintMatch(a, b) {  
  const len = Math.min(a.length, b.length);  
  let hit = 0;  
  for (let i = 0; i < len; i++) if (a[i] === b[i]) hit++;  
  return hit;  
}  
// 匹配数 >= 5 即通过  

```

这样即使用户升级了浏览器版本（UA 变化），只要平台、屏幕、时区、语言、扩展 ID 等没变，依然被识别为同一设备。

### 4.3 指纹漂移自动更新

心跳环节有一个精巧设计——当指纹轻微漂移时，自动更新服务端记录：
```

// 心跳时发现指纹变了  
if (device.fingerprintHash !== fingerprintHash) {  
  const matchCount = countFingerprintMatch(device.fingerprintParts, body.parts);  
  if (matchCount >= 4) {  // 至少 4 项匹配才允许更新  
    device.fingerprintHash = fingerprintHash;  
    device.fingerprintParts = body.parts;  
  }  
}  

```

这意味着指纹会随用户环境自然演化，而非一次绑定终身不变。

## 五、ECDSA-P256 数字签名：防中间人

### 5.1 为什么需要签名

激活/校验的响应通过公网传输。如果不签名，攻击者可以：

  * 伪造一个假的后端返回，让插件"永久激活"
  * 中间人劫持后篡改`graceUntil`（宽限期）的值

### 5.2 密钥分发
```

gen-keys.js 生成 ECDSA-P256 密钥对  
  ├─ 私钥(PKCS8 hex) → wrangler secret put → 注入 Worker  
  └─ 公钥(SPKI hex) → 写入 config.js → 硬编码在插件里  

```

私钥永远不出 Worker。客户端只持有公钥，即使反编译插件也只能拿到公钥，无法伪造签名。

### 5.3 签名内容
```

签名原文 = JSON.stringify(responseData) + "|" + serverTime + "|" + nonce  

```

  * `responseData`：响应体，包含`deviceId, token, expireAt, graceUntil` 等
  * `serverTime`：服务器时间戳，防止重放攻击（客户端校验 ±60s 时间漂移）
  * `nonce`：一次性随机数，防止同一响应被重复利用

### 5.4 客户端验签
```

async function verifySign(body, serverTime, nonce, signB64) {  
const payload = strToBytes(  
    JSON.stringify(body) + "|" + serverTime + "|" + nonce  
  );  
const sig = base64ToBytes(signB64);  
const key = await getPublicKey(); // 从 config.js 导入公钥  
return crypto.subtle.verify(  
    { name: "ECDSA", hash: "SHA-256" },  
    key, sig, payload  
  );  
}  

```

Web Crypto API 是浏览器原生支持的，性能极高且安全——私钥永远不需要在客户端出现。

## 六、完整鉴权生命周期

### 6.1 激活流程
```

用户输入激活码  
  │  
  ▼  
插件采集设备指纹 (7维 parts + sha256 hash)  
  │  
  ▼  
POST /activate { code, fingerprintHash, parts }  
  │  
  ▼  
Worker 查 LICENSES["lic:<code>"]  
  ├─ 不存在 → 404  
  ├─ 已撤销 → 403  
  ├─ 已过期 → 403  
  │  
  ▼ 查 CODE_DEVICES["cd:<code>"] → 设备列表  
  │  
  ├─ 指纹匹配已有设备 → 复用 deviceId，刷新 token  
  ├─ 指纹模糊匹配(≥5项) → 复用 deviceId  
  └─ 全新设备  
       ├─ 设备数 ≥ maxDevices → 409 (DEVICE_LIMIT_REACHED)  
       └─ 创建新设备记录，写入 4 个 KV  
  │  
  ▼ 签发签名响应  
{ deviceId, token, expireAt, graceUntil, serverTime, nonce, sign }  
  │  
  ▼  
客户端验签 + 校验时间漂移 → 写入 chrome.storage.local  

```

### 6.2 启动校验流程
```

插件启动 / 侧边栏打开  
  │  
  ▼  
读取本地 licenseState  
  ├─ 无记录 → 显示激活表单  
  │  
  ▼ 有记录  
检测时钟回拨 (now < _lastMonotonicTs - 5min)  
  ├─ 回拨 → 强制联网校验  
  │  
  ▼ 无回拨  
检查宽限期 (now <= graceUntil)  
  ├─ 在宽限期内 → 直接放行，不联网 ← 离线可用！  
  └─ 超过宽限期 → 联网 POST /verify  
       ├─ 网络失败 → 宽限期兜底检查  
       ├─ 后端拒绝 → 标记 revoked，锁定  
       └─ 验签通过 → 更新 graceUntil，放行  

```

**关键设计——离线宽限期** ：后端每次响应都会签发新的`graceUntil = now + 7天`。这意味着即使用户断网，只要 7 天内曾成功校验过，插件就能正常工作。这解决了"网络波动导致用户无法使用"的痛点。

### 6.3 心跳续签
```

chrome.alarms 每 30 分钟触发  
  │  
  ▼  
POST /heartbeat { token, fingerprintHash }  
  │  
  ▼  
Worker 校验 → 更新 lastHeartbeat → 签发新 graceUntil  
  │  
  ▼  
客户端更新本地状态  
  ├─ 成功 → 后台静默，用户无感知  
  ├─ 被拒(revoked) → 通知 sidepanel 锁定  
  └─ 网络失败 → 宽限期兜底，不影响使用  

```

### 6.4 解绑设备
```

用户点击"解绑当前设备"  
  │  
  ▼  
POST /unbind { token }  
  │  
  ▼  
Worker 通过 TOKEN_INDEX 找到设备  
  ├─ 删除 DEVICES["dev:<deviceId>"]  
  ├─ 删除 TOKEN_INDEX["tk:<token>"]  
  └─ 从 CODE_DEVICES["cd:<code>"] 中移除  
  │  
  ▼  
客户端清除本地 licenseState  

```

即使后端不可达（离线解绑），客户端也会清本地状态。用户可以拿激活码在新设备上重新激活。

## 七、防破解工程细节

### 7.1 时钟回拨检测

用户如果把系统时间往前调，理论上可以永远停留在宽限期内。方案中用单调时钟思路对抗：
```

// 每次写入 state 时，记录"见过的最大时间戳"  
_monotonicTs: Math.max(prev, now)  
  
// 下次读取时，如果当前时间 < _lastMonotonicTs - 5min → 判定回拨  
if (now < state._lastMonotonicTs - 5 * 60 * 1000) {  
  // 强制联网校验！  
}  

```

这不是完美的防篡改（用户可以同时修改 chrome.storage），但大幅提高了破解门槛。

### 7.2 时间漂移校验
```

function checkTimeSkew(serverTimeMs) {  
  return Math.abs(Date.now() - serverTimeMs) < 60 * 1000;  
}  

```

签名响应中携带服务器时间。如果客户端时间与服务器相差超过 60 秒，拒绝接受响应。这防止了"伪造旧响应重放"的攻击。

### 7.3 激活码格式
```

V1-XXXX-XXXX-XXXX-XXXX※  
  
字符集：ABCDEFGHJKMNPQRSTUVWXYZ23456789（去掉 0/O/1/I/L 等易混淆字符）  
末尾校验位：前 16 字符 ASCII 累加取模映射  

```

人工输入时不易出错，且基础格式校验在客户端就能做。

## 八、管理后台

Worker 同时提供 Admin API，配套一个纯前端`admin.html` 管理面板：

| 接口                           | 功能                       |
|------------------------------|--------------------------|
| `POST /admin/code/create`    | 批量生成激活码（指定数量/设备数/有效期/备注） |
| `GET /admin/code/list`       | 列出所有激活码及使用情况             |
| `POST /admin/code/unbindAll` | 解绑某激活码下所有设备              |
| `POST /admin/code/revoke`    | 撤销激活码（立即失效）              |

Admin 接口通过`ADMIN_TOKEN` 鉴权（Cloudflare Secret 注入），与用户接口完全隔离。

![](https://r2.jeanjan.kdns.fr/pictures/img-2c44d15001.png)

## 九、部署成本清单

### Cloudflare 免费层容量

| 资源         | 免费额度    | 本方案每用户日均消耗            |
|------------|---------|-----------------------|
| Workers 请求 | 10 万/天  | ~5-10 次（激活 + 30 分钟心跳） |
| KV 读取      | 10 万/天  | ~15-30 次              |
| KV 写入      | 1,000/天 | ~1-2 次（主要在新激活时）       |

**结论** ：免费层可支撑约**1 万活跃用户** 。超出后升级 Workers Paid（$5/月，1000 万请求/月），性价比极高。

### 无需维护的基础设施

  * 无服务器实例 → 不需要 SSH、不需要监控磁盘
  * 无数据库 → 不需要备份、不需要 Migrate
  * Cloudflare 自动 TLS → 不需要证书续期
  * 全球边缘部署 → 不需要 CDN 配置

## 十、方案总结

| 维度    | 实现方式                               |
|-------|------------------------------------|
| 用户身份  | 激活码（V1-XXXX-XXXX-XXXX-XXXX 格式）     |
| 设备绑定  | 7 维指纹 hash + 模糊匹配（≥5 项命中即同设备）      |
| 传输安全  | ECDSA-P256 数字签名（私钥在 Worker，公钥在客户端） |
| 防重放   | serverTime ± 60s 时间漂移校验 + nonce    |
| 离线可用  | 7 天宽限期（每次心跳/校验自动续签）                |
| 防时钟篡改 | 单调时钟检测（回拨 > 5min 强制联网）             |
| 设备数限制 | 每码默认 2 台，可配置到 50 台                 |
| 撤销能力  | Admin 一键撤销 → 下次心跳立即生效              |
| 运维成本  | 零服务器、零数据库、$0/月（免费层）                |
| 扩展性   | Workers Paid $5/月 即可支撑百万级请求        |

这套方案的精妙之处在于：**用很少的基建（一个 Worker + 四个 KV），实现了商业级软件授权的核心能力** 。它不追求密码学上的绝对安全——浏览器环境天然无法防住所有逆向——而是把破解成本提高到远大于激活码价格的程度，同时给正常用户极致的离线体验。

若你在搭建过程中遇到问题，欢迎在评论区留言交流。  

`  
`

