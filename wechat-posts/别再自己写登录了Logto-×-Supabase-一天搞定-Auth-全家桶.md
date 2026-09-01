# 别再自己写登录了Logto × Supabase 一天搞定 Auth 全家桶

**作者**: 乔克前端
**发布时间**: 2026-07-24 15:21
**原文链接**: https://mp.weixin.qq.com/s/3Xit_EXzsw4wjMb0Yvh27g

---

## 你写的登录系统，可能正在泄露用户数据

上个月帮一个朋友 review 他的 SaaS 项目代码。登录功能看起来挺正常：邮箱注册、密码登录、JWT 鉴权。但我随口问了一句「密码怎么存的」，他打开了 `user.ts`，我看到了这行：
```

password: await bcrypt.hash(password, 10)
```

我说还行，bcrypt 至少没问题。然后我往下翻，又看到了这个：
```

const token = jwt.sign({ userId: user.id }, 'my-secret-key')
```

**硬编码的 JWT secret。** 而且 secret 既没有走环境变量，也没有轮换机制。更关键的是，没有 refresh token，access token 有效期设置成了 **30 天** 。

这不是个例。我见过太多独立开发者和小团队，在做 SaaS 的时候把登录系统当成「附带功能」来写。能登录就行，安全以后再说。

问题是，**「以后」往往就是出事的那天。**

自己写 Auth，你需要处理的事情远比想象的多：密码哈希算法选型、JWT 签名和轮换、CSRF 防护、XSS 防护、OAuth 2.0 流程、社交登录对接、邮箱验证、密码重重置、MFA、session 管理……每一项都有坑，每一项都可能成为安全漏洞。

所以我一直在找一个方案，能让我在新项目里**不写登录代码** 。

不是不写业务逻辑，是真的不写登录那一坨。注册、登录、忘记密码、社交登录、MFA、多租户——全部交给一个靠谱的服务，我只管调 SDK。

试了一圈之后，我的答案是 **Logto + Supabase** 。

## 先说结论：为什么是这两个的组合

简单一句话分工：

> **Logto 管「谁在用」，Supabase 管「数据在哪」。**

Supabase 大家应该不陌生了，**107k Star** 的开源 Firebase 替代品。它提供了 PostgreSQL 数据库、对象存储、Edge Functions、Realtime 订阅、Row Level Security (RLS)。几乎所有后端基础设施，它都能覆盖。

但 Supabase 有一个明显的短板：**它的 Auth 模块不够强。**

Supabase Auth 基于 GoTrue，能处理基本的邮箱/密码登录和社交登录。但它不是 OIDC Provider——也就是说，你不能用 Supabase Auth 作为统一身份认证层，去对接其他系统。多租户、企业 SSO、RBAC 这些能力，要么缺失，要么需要自己大量定制。

这正是 Logto 的强项。

Logto 是一个开源的身份认证平台（**14.2k Star** ），由国内团队开发。它完整支持 OIDC / OAuth 2.1 / SAML，原生支持多租户、RBAC、企业 SSO，而且有 30+ 框架的 SDK。

两个工具组合起来，就是一个完整的 SaaS 后端方案：

| 层级       | 负责工具                       | 具体能力                      |
|----------|----------------------------|---------------------------|
| 身份认证     | **Logto**                  |  登录注册、社交登录、MFA、SSO、多租户    |
| 数据库 + 存储 | **Supabase**               |  PostgreSQL、对象存储、Realtime |
| 行级权限     | **Supabase RLS**           |  基于 JWT claims 的数据隔离      |
| 业务逻辑     | **SupabaseEdge Functions** |  Serverless 函数            |

两个都是开源的，都可以自部署。如果不想自己运维，也都有云版本和免费额度。

## Logto 到底解决了什么问题

在展开怎么接之前，先聊聊 Logto 解决了哪些实际问题。不是功能列表，是我在项目中真正遇到过的痛点。

**痛点一：社交登录对接**

每个社交平台的 OAuth 流程都不一样。Google、GitHub、微信、Apple——光是对接这四个就要写不少胶水代码。而且每个平台的 SDK 更新频率不一样，今天能用的接口明天可能就 deprecated 了。

Logto 把这些统一封装成了 **Connector** 。你只需要在 Console 里配置 client_id 和 secret，剩下的 redirect_uri 生成、token 交换、用户信息映射，全部由 Logto 处理。

**痛点二：多租户**

做 B2B SaaS 绕不开多租户。你需要「组织」的概念：一个用户可以属于多个组织，每个组织有独立的角色和权限。

自己实现这套逻辑，光是数据库表设计就够头疼的。Logto 原生支持 **Organizations** ，每个组织有独立的成员管理、角色分配、邀请机制，甚至支持 JIT（Just-in-Time）自动加入。

**痛点三：企业 SSO**

客户说「我们公司用 Okta/Azure AD，能不能对接？」如果你的 Auth 系统不支持 SAML，这个单子可能就丢了。

Logto 原生支持 SAML SSO 和 OIDC Enterprise Connector，客户只需要提供他们的 IdP metadata，你就能在 Console 里完成配置。

这三个痛点，Supabase Auth 都解决不了。但 Logto + Supabase 组合在一起，就变成了一个完整的方案。

## 实际怎么接：从零到跑通

下面是我在一个 Next.js 项目中实际接入的步骤。整个过程大概半天能搞定。

### Step 1：创建 Logto 应用

去 Logto Cloud 注册（免费额度 50k MAU），创建一个应用。

选择「Single Page Application」类型，拿到两个关键参数：
```

Endpoint:  https://your-tenant.logto.app  
App ID:    <your-app-id>  
App Secret: <your-app-secret>
```

然后配置 Redirect URIs 和 Post Sign-out Redirect URIs，指向你的应用地址。

### Step 2：前端接入 Logto SDK
```

npm install @logto/next
```

在 Next.js 中配置：
```

import LogtoClient from'@logto/next';  
  
export const logtoClient = newLogtoClient({  
  endpoint: 'https://your-tenant.logto.app',  
  appId: '<your-app-id>',  
  appSecret: '<your-app-secret>',  
  baseUrl: 'http://localhost:3000',  
});
```

在 API Route 中处理回调：
```

import { logtoClient } from'@/logto';  
  
export const GET = logtoClient.handleSignIn();
```

前端调用登录：
```

const signIn = () => {  
  window.location.href = '/api/logto/sign-in';  
};
```

到这里，用户就能通过 Logto 的预置登录页面完成注册和登录了。社交登录、MFA 都在这个页面里，**不需要你写任何 UI** 。

### Step 3：获取 JWT 并传给 Supabase

登录成功后，Logto 会签发 access token（JWT 格式）。你需要用这个 token 去初始化 Supabase 客户端：
```

import { createClient } from'@supabase/supabase-js';  
  
const supabase = createClient(  
'https://your-project.supabase.co',  
'your-anon-key',  
  {  
    global: {  
      headers: {  
        Authorization: `Bearer ${logtoAccessToken}`,  
      },  
    },  
  }  
);
```

关键问题来了：Supabase 默认只认自己签发的 JWT。要让它认 Logto 的 token，你需要做一件事——**把 Supabase 的 JWT secret 设置为 Logto 的 OIDC signing key。**

###  Step 4：配置 Supabase 认 Logto 的 JWT

在 Supabase Dashboard → Settings → API → JWT Settings，把 JWT Secret 替换成 Logto 的 OIDC discovery 中获取的 signing key。

或者更优雅的方式：在 Supabase 的 `supabase/config.toml` 中配置：
```

[auth]  
jwt_secret = "your-logto-signing-key"
```

配置完成后，Supabase 的 RLS 就能解析 Logto 签发的 JWT 了。

### Step 5：用 RLS 做数据隔离

这是整个方案**最核心的部分** ，也是 Logto + Supabase 组合的真正杀手锏。

先说一个很多开发者忽略的事实：**如果你的 API 只靠应用层代码做权限校验，你的数据其实不安全。** 任何一个能直接连数据库的工具（Supabase Dashboard、psql、第三方客户端）都能绕过你的应用层逻辑。

RLS（Row Level Security）是 PostgreSQL 的原生能力。开启后，**每一条 SQL 查询都会经过策略过滤** ，不管这个查询是从你的应用发起的，还是从 Supabase Dashboard 直接执行的。

**▸ 开启 RLS**

第一步，在你的表上启用 RLS：
```

ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
```

RLS 默认是「拒绝一切」——开启后，如果你不写任何 policy，所有查询都会返回空结果。你需要显式地声明「谁能访问哪些行」。

**▸ RLS 的工作原理**

Supabase 会在每个请求中注入一个 `request.jwt.claims` 变量，里面是当前用户的 JWT payload。你在 policy 中通过 `current_setting('request.jwt.claims', true)::json` 读取这些 claims。

Logto 签发的 JWT 长这样（解码后）：
```

{  
"sub": "user-abc-123",  
"org_id": "org-xyz-789",  
"roles": ["admin"],  
"scope": "read:documents write:documents",  
"iss": "https://your-tenant.logto.app",  
"aud": "your-app-id",  
"exp": 1721899200  
}
```

你需要在 Logto 的 **Custom JWT Claims** 中配置这些字段。去 Logto Console → Custom JWT Claims，写一段脚本把用户的角色和组织信息注入到 access token 里：
```

// Logto Custom JWT Claims 脚本  
const { user, scopes } = context;  
  
api.accessToken.addClaim('org_id', user.organizations[0]?.id ?? null);  
api.accessToken.addClaim('roles', user.roles.map(r => r.name));
```

这样，每次用户请求 Supabase 时，JWT 里都带着 `org_id` 和 `roles`。Supabase RLS 就能根据这些 claims 做精确的权限控制。

**▸ 三种最常见的 RLS 模式**

**模式一：用户只能访问自己的数据**

最简单的场景——个人 Todo、私人笔记：
```

-- 用户只能读写自己的文档  
CREATE POLICY"Users can read own documents"  
ON documents FOR SELECT  
USING (  
  user_id = current_setting('request.jwt.claims', true)::json->>'sub'  
);
```

`sub` 是 JWT 的标准字段，对应 Logto 里的用户 ID。

**模式二：组织级数据隔离**

B2B SaaS 的核心需求——用户只能看到自己所在组织的数据：
```

-- 组织成员只能访问自己组织的数据  
CREATE POLICY"Org members can view org documents"  
ON documents FOR SELECT  
USING (  
  org_id = current_setting('request.jwt.claims', true)::json->>'org_id'  
);
```

注意一个细节：一个用户可能属于多个组织。更完善的做法是用 `jsonb_array_elements_text` 检查用户是否在目标组织中：
```

CREATE POLICY"Multi-org document access"  
ON documents FOR SELECT  
USING (  
  org_id IN (  
SELECT value  
FROMjsonb_array_elements_text(  
current_setting('request.jwt.claims', true)::json->'org_ids'  
    )  
  )  
);
```

**模式三：基于角色的行级权限**

管理员能看所有数据，普通成员只能看自己创建的：
```

-- 管理员看所有，成员只看自己的  
CREATE POLICY"Role-based document access"  
ON documents FOR SELECT  
USING (  
-- 管理员看所有  
current_setting('request.jwt.claims', true)::json->'roles' ? 'admin'  
OR  
-- 普通成员只看自己的  
  user_id = current_setting('request.jwt.claims', true)::json->>'sub'  
);
```

**▸ RLS + Logto RBAC 的映射策略**

这里有一个设计决策需要提前想清楚。

Logto 的 RBAC 模型是：**用户 → 角色 → 权限** 。比如一个用户有 `editor` 角色，这个角色有 `read:documents`、`write:documents` 两个权限。

Supabase RLS 不认字符串权限，它只认 SQL 表达式。所以你需要做一个映射：

| Logto 侧              | Supabase RLS 侧                |
|----------------------|-------------------------------|
| 角色 `admin`           | JWT claim `roles: ["admin"]`  |
| 权限 `read:documents`  | `policy FOR SELECT`           |
| 权限 `write:documents` | `policy FOR INSERT/UPDATE`    |
| 组织 `org-123`         | JWT claim `org_id: "org-123"` |

我的建议是：**在 Logto 侧管理角色和组织，在 Supabase 侧只做行级过滤。** 不要在 RLS 里重复实现 RBAC 逻辑，那会变成维护噩梦。

具体做法：

  1. Logto 负责「这个用户有没有权限访问这个组织」
  2. Supabase RLS 负责「这个用户只能看到这个组织里的数据」
  3. 应用层负责「这个操作的具体业务逻辑」

三层各司其职，不要混在一起。

**▸ 实用技巧：RLS 调试**

写 RLS policy 最头疼的是调试。查询返回空结果，你不知道是数据确实没有，还是 policy 挡住了。

Supabase 提供了一个好用的函数来模拟 JWT claims：
```

-- 在 SQL Editor 中手动设置 claims 来测试  
SET request.jwt.claims = '{"sub":"user-abc-123","org_id":"org-xyz-789","roles":["admin"]}';  
  
-- 然后执行你的查询  
SELECT * FROM documents;  
  
-- 测试完记得重置  
RESET request.jwt.claims;
```

另一个技巧是在 policy 中用 `auth.jwt()` 函数代替 `current_setting`，可读性更好：
```

USING (org_id = (auth.jwt()->>'org_id'))
```

两种写法效果一样，`auth.jwt()` 是 Supabase 提供的封装函数。

## 踩过的坑：别以为接完就完事了

说实话，这个方案不是零成本的。有几个坑你需要提前知道。

**坑一：JWT Claims 映射需要手动配置**

Logto 默认签发的 JWT claims 和 Supabase 期望的格式不一定完全一致。你可能需要在 Logto 的 JWT Customizer 中配置自定义 claims，确保 `sub`、`org_id`、`roles` 等字段对得上。

这不是一个按钮就能搞定的事，需要你在 Logto Console → Custom JWT Claims 里写脚本。

**坑二：Supabase RLS 和 Logto RBAC 的粒度不同**

Logto 的 RBAC 是「角色 → 权限」模型，权限是字符串（如 `read:posts`）。Supabase RLS 是 SQL 表达式，粒度到行和列。

你需要设计一个映射策略：Logto 里的角色和权限，怎么转化成 Supabase RLS 能理解的 JWT claims。这个设计阶段花的时间比写代码多。

**坑三：社交登录 Connector 配置**

Google、GitHub 这些还算简单。如果你要接微信登录，需要在 Logto 的 Connector 配置中填入微信开放平台的 AppID 和 AppSecret，还要处理微信特有的 OAuth 流程差异。

比 Auth0 的「一键开启」繁琐一些，但好在 Logto 的 Connector 文档写得还算清楚。

**坑四：本地开发环境**

自部署 Logto 需要 PostgreSQL。本地开发时你需要同时跑 Supabase（自带 PG）和 Logto（又一个 PG）。虽然可以用同一个 PostgreSQL 实例，但需要手动建两个 database。

推荐用 Docker Compose 把 Logto 和 Supabase 一起编排。

## 成本对比：到底省了多少钱

这是我最关心的问题。以 10,000 MAU 为例：

| 方案            | 月费用           | 说明                                 |
|---------------|---------------|------------------------------------|
| Auth0         | **~$230**     |  Essential plan，不含企业 SSO           |
| Clerk         | **~$100**     |  Pro plan，但多租户功能有限                 |
| Firebase Auth | **$0**        |  但 SAML/SSO 要 Identity Platform 升级 |
| Logto Cloud   | **$0**        |  免费额度 50k MAU                      |
| Logto 自部署     | **$0** \+ 服务器 | Vercel/Railway 免费额度够用              |

Logto Cloud 的免费额度是 50k MAU，这对大多数早期 SaaS 来说足够了。等到真正需要付费的时候，你的产品已经有收入了。

自部署的话，一台 2C4G 的服务器大约 **$20/月** ，能撑住几万 MAU 没问题。加上 Supabase 的免费额度（50k MAU、500MB 数据库、1GB 存储），整个 Auth + 后端基础设施的月成本可以控制在 **$20 以内** 。

对比 Auth0 的 $230/月，一年省下 **$2,500+** 。对于 bootstrapping 的团队来说，这不是小数目。

## 这套方案适合你吗

说了这么多优点和坑，最后来个诚实的判断。

**✅ 适合的场景：**

  * 你正在做 B2B SaaS，需要多租户和 RBAC
  * 你想控制成本，不想被 Auth0 的定价绑架
  * 你需要企业 SSO（SAML），但预算有限
  * 你的后端已经在用或者打算用 Supabase
  * 你愿意花半天时间接入，换来之后不用再碰 Auth 代码

**❌ 不适合的场景：**

  * 你已经深度绑定了 Auth0，迁移成本太高
  * 你只是做一个个人项目，NextAuth 够用
  * 你的团队没有运维能力，也不想用 Logto Cloud
  * 你需要的只是最简单的邮箱/密码登录，Supabase Auth 本身就够了

**我的建议：** 如果你在做新的 SaaS 项目，先试试 Logto Cloud 免费版。花半天时间接入，体验一下完整流程。如果觉得合适，再考虑要不要自部署。

不要在项目初期就花两周时间自己写登录系统。那个时间应该用来做你的核心产品。

## 写在最后

登录系统不是你产品的核心竞争力，但它是用户接触你产品的第一道门。

选一个靠谱的方案，把门守好，然后把精力花在真正该花的地方——你的产品逻辑、你的用户体验、你的商业模式。

Logto + Supabase 不是唯一的答案，但它是我在 2024 年找到的性价比最高的答案。如果你也在找一个开源、可控、功能完整的 Auth 方案，值得一试。

相关资源：

  * Logto 官方文档
  * Logto GitHub
  * Supabase 官方文档
  * Supabase + 第三方 JWT 配置

#Logto #Supabase #SaaS开发 #开源登录 #Auth0替代 #前端

