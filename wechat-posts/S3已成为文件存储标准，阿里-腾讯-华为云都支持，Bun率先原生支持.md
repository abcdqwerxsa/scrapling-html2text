# S3已成为文件存储标准，阿里/腾讯/华为云都支持，Bun率先原生支持

**作者**: 半刻维度
**发布时间**: 2026-07-01 07:00
**原文链接**: https://mp.weixin.qq.com/s/L_DrdqXoLsMW9c8vvbcmXw

---

**就这几行：**
```

 import { S3Client } from "bun"  
  
// 阿里  
const aliyun = new S3Client({  
  accessKeyId: process.env.ALI_KEY!,  
  secretAccessKey: process.env.ALI_SECRET!,  
  bucket: "my-bucket",  
  endpoint: "https://oss-cn-hangzhou.aliyuncs.com",  
})  
await aliyun.write("hello.txt", "兄弟们好啊")  
  
// 腾讯  
const tx = new S3Client({  
  accessKeyId: process.env.TX_KEY!,  
  secretAccessKey: process.env.TX_SECRET!,  
  bucket: "my-bucket-1250000000",  
  endpoint: "https://cos.ap-guangzhou.myqcloud.com",  
})  
await tx.write("hello.txt", "兄弟们好啊")  
  
// 华为  
const hw = new S3Client({  
  accessKeyId: process.env.HW_KEY!,  
  secretAccessKey: process.env.HW_SECRET!,  
  bucket: "my-bucket",  
  endpoint: "https://obs.cn-north-4.myhuaweicloud.com",  
})  
await hw.write("hello.txt", "兄弟们好啊")
```

**同一份 Bun.S3 API，阿里、腾讯、华为三家云全通。**
```

 bun run demo.ts
```

**完事儿。**

##  痛点：每家云一套 SDK

兄弟们，搞过后端上传下载的都知道。

文件存储这事儿，**国内国外云厂商各写一套 SDK** ：

  * • 阿里：OSS，用 `ali-oss`
  * • 腾讯：COS，用 `cos-nodejs-sdk-v5`
  * • 华为：OBS，用 `esdk-obs-nodejs`
  * • AWS：S3，用 `aws-sdk`

**想换一家？**  
  
代码全部推倒重写。

更糟的是这堆 SDK：

  * • 包大，冷启动 80MB 往上
  * • 文档各看各的，调半天
  * • 流式上传、分片上传、签名算法各搞一套

**老板让你上华为云，**  
  
你对着阿里 SDK 写好的代码干瞪眼。

## 解决方案：S3 是行业事实标准

S3 是 AWS 在 **2006 年** 搞出来的对象存储。

**S3 协议太成功了，**  
  
现在已经是行业**事实标准** 。

啥叫事实标准？

  * • **AWS S3** 自己当然支持
  * • **阿里云 OSS** 100% 兼容 S3
  * • **腾讯云 COS** 100% 兼容 S3
  * • **华为云 OBS** 100% 兼容 S3
  * • Cloudflare R2、MinIO、七牛、京东云、金山云 **全部兼容**

**一套 API 写完，换云只改 endpoint。**

而 Bun，**率先** 把 S3 客户端焊死在运行时里。

`Bun.S3Client` 一个类，吃遍所有 S3 兼容服务。

**这是 Bun 1.2 才有的真本事，**  
  
Node.js 至今没原生 S3，要装 `aws-sdk` 一大坨。

## 一句话：啥是 S3 协议？

S3 协议就是**一套 HTTP REST API** ：

  * • `PUT /<bucket>/<key>`：上传文件
  * • `GET /<bucket>/<key>`：下载文件
  * • `DELETE /<bucket>/<key>`：删除文件
  * • `LIST /<bucket>`：列文件

每家云厂商对外暴露这四个动词，  
  
加上 **AWS 签名 v4** 鉴权。

**只要你的代码按 S3 协议发请求，**  
  
哪家云都能接住。

## 阿里 OSS：endpoint 是关键

阿里云 OSS 的 S3 兼容端点长这样：
```

import { S3Client } from "bun"  
  
const oss = new S3Client({  
  accessKeyId: "LTAIxxxxxxxx",  
  secretAccessKey: "xxxxxxxx",  
  bucket: "my-bucket",  
  region: "oss-cn-hangzhou",  
  endpoint: "https://oss-cn-hangzhou.aliyuncs.com",  
})  
  
await oss.write("hello.txt", "兄弟们好啊")  
const txt = await oss.file("hello.txt").text()  
console.log(txt)
```

**坑点：bucket 名要全球唯一。**  
  
阿里控制台开完桶，把名字填到 `bucket` 字段。

`region` 用 `oss-cn-hangzhou` 这种格式，  
  
跟 AWS 的 `us-east-1` 不一样，别照搬。

## 腾讯 COS：bucket 名带 APPID

腾讯 COS 有点特殊。

**bucket 名必须带 APPID 后缀** ：
```

import { S3Client } from "bun"  
  
const cos = new S3Client({  
  accessKeyId: "AKIDxxxxxxxx",  
  secretAccessKey: "xxxxxxxx",  
  bucket: "my-bucket-1250000000",  // ← 注意 APPID  
  region: "ap-guangzhou",  
  endpoint: "https://cos.ap-guangzhou.myqcloud.com",  
})  
  
await cos.write("hello.txt", "兄弟们好啊")
```

`1250000000` 这种数字就是你腾讯云账号的 APPID。

**没加 APPID？**  
  
404 报错，找不到桶。

控制台创建桶的时候会带，  
  
复制粘贴即可。

## 华为云 OBS：endpoint 长得很像

华为云 OBS 跟 AWS S3 几乎一模一样。

**连` region` 字段格式都照搬**：
```

import { S3Client } from "bun"  
  
const obs = new S3Client({  
  accessKeyId: "HECxxxxxxxx",  
  secretAccessKey: "xxxxxxxx",  
  bucket: "my-bucket",  
  region: "cn-north-4",  
  endpoint: "https://obs.cn-north-4.myhuaweicloud.com",  
})  
  
await obs.write("hello.txt", "兄弟们好啊")
```

华为云的 `region` 格式跟 AWS 一致：

  * • `cn-north-4` 北京
  * • `cn-east-3` 上海
  * • `cn-south-1` 广州

**从 AWS 迁到华为云，改个 endpoint 就行。**

##  一份代码通吃三家：工厂模式

兄弟们，写过电商/OA/CRM 的都知道。

**多云适配** 是硬需求。

把三家云封装成工厂：
```

import { S3Client } from "bun"  
  
type Vendor = "aliyun" | "tencent" | "huawei"  
  
const config: Record<Vendor, any> = {  
  aliyun: {  
    bucket: process.env.ALI_BUCKET!,  
    region: "oss-cn-hangzhou",  
    endpoint: "https://oss-cn-hangzhou.aliyuncs.com",  
    accessKeyId: process.env.ALI_KEY!,  
    secretAccessKey: process.env.ALI_SECRET!,  
  },  
  tencent: {  
    bucket: process.env.TX_BUCKET!,  // 带 APPID  
    region: "ap-guangzhou",  
    endpoint: "https://cos.ap-guangzhou.myqcloud.com",  
    accessKeyId: process.env.TX_KEY!,  
    secretAccessKey: process.env.TX_SECRET!,  
  },  
  huawei: {  
    bucket: process.env.HW_BUCKET!,  
    region: "cn-north-4",  
    endpoint: "https://obs.cn-north-4.myhuaweicloud.com",  
    accessKeyId: process.env.HW_KEY!,  
    secretAccessKey: process.env.HW_SECRET!,  
  },  
}  
  
export function getS3(vendor: Vendor) {  
  return new S3Client(config[vendor])  
}  
  
// 用法  
const oss = getS3("aliyun")  
await oss.write("hello.txt", "兄弟们好啊")
```

**业务代码只调` getS3("aliyun")`，**  
  
内部云厂商怎么换，外面一行不用改。

## 读文件：text / json / stream

`S3Client.file()` 返回的 `S3File` 继承自 `Blob`。

**跟` Bun.file` 用法一模一样**：
```

import { S3Client } from "bun"  
  
const oss = new S3Client({  
  accessKeyId: process.env.ALI_KEY!,  
  secretAccessKey: process.env.ALI_SECRET!,  
  bucket: "my-bucket",  
  endpoint: "https://oss-cn-hangzhou.aliyuncs.com",  
})  
  
// 读 JSON  
const data = await oss.file("user.json").json()  
  
// 读字符串  
const text = await oss.file("readme.txt").text()  
  
// 读字节  
const bytes = await oss.file("image.png").bytes()  
  
// 大文件流式读  
const stream = oss.file("big.log").stream()  
for await (const chunk of stream) {  
  process.stdout.write(chunk)  
}
```

**流式读省内存，GB 级日志不爆掉。**

##  写文件：fetch 响应直接转存

`write()` 第二个参数接 Response，**能直接把网络资源存到云** ：
```

import { S3Client } from "bun"  
  
const oss = new S3Client({  
  accessKeyId: process.env.ALI_KEY!,  
  secretAccessKey: process.env.ALI_SECRET!,  
  bucket: "my-bucket",  
  endpoint: "https://oss-cn-hangzhou.aliyuncs.com",  
})  
  
// 下载网络图片直接存到阿里 OSS  
const res = await fetch("https://example.com/photo.jpg")  
await oss.write("uploads/photo.jpg", res)
```

**没用 Bun 之前你得这么写：**
```

 // 老套路：先下到内存，再上传  
const res = await fetch("https://example.com/photo.jpg")  
const buffer = Buffer.from(await res.arrayBuffer())  
await oss.put("uploads/photo.jpg", buffer)
```

**Bun 直接把 fetch 响应流过去，零内存拷贝。**

##  presign URL：临时直传

**最香的功能** ，前端直传云端，文件不过你服务器。
```

import { S3Client } from "bun"  
  
const oss = new S3Client({  
  accessKeyId: process.env.ALI_KEY!,  
  secretAccessKey: process.env.ALI_SECRET!,  
  bucket: "my-bucket",  
  endpoint: "https://oss-cn-hangzhou.aliyuncs.com",  
})  
  
// 10 分钟过期的上传链接  
const uploadUrl = oss.file("uploads/avatar.jpg").presign({  
  method: "PUT",  
  expiresIn: 600,  
  type: "image/jpeg",  
  acl: "public-read",  
})  
  
// 把这个 URL 发给前端  
console.log("前端用这个 URL PUT 即可：", uploadUrl)
```

**前端代码：**
```

 // 前端  
const file = document.querySelector("input").files[0]  
await fetch(uploadUrl, {  
  method: "PUT",  
  body: file,  
  headers: { "Content-Type": "image/jpeg" },  
})
```

**这套东西做用户上传头像、资料文件省到爆。**

服务器只发 URL，**文件流直接从浏览器到云，**  
  
省一大笔 CDN 流量费。

三家云都能用，签名算法走 AWS v4 通用规范。

## 列文件 & 删文件

管理后台经常要清旧文件：
```

import { S3Client } from "bun"  
  
const oss = new S3Client({  
  accessKeyId: process.env.ALI_KEY!,  
  secretAccessKey: process.env.ALI_SECRET!,  
  bucket: "my-bucket",  
  endpoint: "https://oss-cn-hangzhou.aliyuncs.com",  
})  
  
// 列前 100 个 uploads/ 下的文件  
const list = await oss.list({ prefix: "uploads/", maxKeys: 100 })  
for (const obj of list.contents ?? []) {  
  console.log(`${obj.key} → ${obj.size} 字节`)  
}  
  
// 分页  
if (list.isTruncated) {  
  const next = await oss.list({  
    prefix: "uploads/",  
    startAfter: list.contents!.at(-1)!.key,  
  })  
}  
  
// 判断文件是否存在  
const exists = await oss.exists("uploads/1.png")  
  
// 删除  
await oss.delete("uploads/old.txt")
```

**同一套 API，三家云都能用，**  
  
写一次列文件逻辑，永远不用重写。

## 性能：比 aws-sdk 快 10 倍

Bun 官方测试，相同硬件、相同网络：

| 场景     | Bun.S3   | aws-sdk v3 |
|--------|----------|------------|
| 小文件读取  | 3.2 GB/s | 0.3 GB/s   |
| 大文件流式读 | 1.8 GB/s | 0.2 GB/s   |
| 小文件上传  | 1.5 GB/s | 0.15 GB/s  |

**快 10 倍左右。**

Bun 用 Zig 写了底层 HTTP 客户端，  
  
跳过 Node 的 V8 + libuv 老路。

**冷启动也从 80MB 降到 0，**  
  
因为 `Bun.S3Client` 是内置的，**不占 node_modules。**

##  避坑指南

兄弟们，**有几个坑先说在前面** ：

### 1\. 签名 region 别瞎写

阿里 OSS 用 `oss-cn-hangzhou`，  
  
腾讯 COS 用 `ap-guangzhou`，  
  
华为 OBS 用 `cn-north-4`，  
  
AWS 用 `us-east-1`。

**各家格式不一样，照搬必报错。**

###  2\. 腾讯 COS 的 bucket 带 APPID

`my-bucket-1250000000`，  
  
`1250000000` 这串数字不能少。

### 3\. 阿里 OSS 的 ACL 字段值有别
```

// 阿里  
await oss.write("public.html", html, {  
  acl: "public-read",  
  type: "text/html",  
})
```

阿里、腾讯、华为三家 ACL 字符串基本通用，  
  
**但个别值不一样** ，看云厂商文档。

### 4\. path-style 和 virtual-host-style

AWS 默认用 `virtual-host-style`：  
  
`https://my-bucket.s3.amazonaws.com/key`

阿里、腾讯、华为默认用 `path-style`：  
  
`https://oss-cn-hangzhou.aliyuncs.com/my-bucket/key`

Bun 帮你自动处理，**一般不用管。**

###  5\. Bun 版本

**Bun ≥ 1.2.0** 才内置 S3 客户端。
```

bun --version  
# 1.3.x 就行
```

## 啥时候用 Bun.S3？

| 场景                 | 推荐                          |
|--------------------|-----------------------------|
| 新项目，团队用 Bun        | **直接用 Bun.S3**              |
| 老项目 Node + aws-sdk | 别动，稳定优先                     |
| 国内多家云适配            | **用 Bun.S3** ，换 endpoint 就行 |
| 大文件（GB 级）流式处理      | **用 Bun.S3** ，自动分片          |
| 前端直传 / 临时下载链接      | **用 Bun.S3** ，presign 同步生成  |

## 总结

S3 这个协议，**20 年前 AWS 搞出来，**  
  
现在已经是**行业事实标准** 。

**国内三家：**

  * • 阿里 OSS 100% 兼容
  * • 腾讯 COS 100% 兼容
  * • 华为云 OBS 100% 兼容

**国外一堆：**

  * • AWS S3 自己
  * • Cloudflare R2
  * • MinIO
  * • Google Cloud Storage
  * • DigitalOcean Spaces

**学会 S3 API，一把钥匙开 10 把锁。**

而 Bun 率先把 S3 焊死在运行时里，  
  
`Bun.S3Client` 一个类通吃所有。

**比 aws-sdk 快 10 倍，**  
  
**0 依赖、0 冷启动，**  
  
**3 行代码搞定上传下载。**

兄弟们，下次再有人问你 "怎么对接国内多家云存储"，  
  
**直接把这篇甩给他，省你半小时口舌。**

觉得有用？**点个在看、转发** 。

评论区聊聊，你们公司在用哪家的对象存储？  
  
有没有被多云适配折腾过？

  


