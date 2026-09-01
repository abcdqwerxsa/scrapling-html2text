# GitHub星标飙升！这款React框架让Next.js用户集体"跳槽"了？

**作者**: Ghub 宝藏项目
**发布时间**: 2026-07-12 14:29
**原文链接**: https://mp.weixin.qq.com/s/BOSu5b9e5akR7yYyTz0isw

---


![Remix 3 Logo](https://r2.jeanjan.kdns.fr/pictures/img-f4eccceb01.jpeg)Remix 3 Logo

最近逛GitHub的时候发现一个挺有意思的现象。React生态里那个叫Remix的项目，星标数涨得飞快不说，连ChatGPT的官网都悄悄从Next.js迁移过去了。这事儿让我挺好奇的，毕竟Next.js一直是React框架界的"老大哥"啊。

其实吧，Remix这玩意儿2021年就诞生了，由React Router的原班人马搞出来的。后来被Shopify收购，这几年默默憋了个大招——Remix 3。如果说之前的版本还在摸索，那现在这个版本简直就是冲着"重新定義Web开发体验"去的。

![Remix架构对比](https://r2.jeanjan.kdns.fr/pictures/img-f4eccceb02.png)Remix架构对比

Remix的哲学特别简单：**别跟浏览器对着干，顺着它来** 。它不搞那些花里胡哨的客户端状态管理，也不整什么复杂的缓存策略。数据获取就用Web标准的Request/Response，表单提交直接用HTML的form，导航就用Link。哪怕用户把JavaScript关了，网站照样能跑。这种"渐进增强"的思路，在现在一堆动不动就几百KB前端bundle的时代，简直是一股清流。

那这东西到底怎么用呢？其实上手比想象中简单。

### 先装起来试试

最省事儿的办法是用官方脚手架。你打开终端，敲这么一行：
```

npx create-remix@latest  

```

它会问你几个问题，比如要用TypeScript还是JavaScript（建议选TS，都2026年了），部署目标选啥（Vercel、Netlify、Cloudflare Workers都能选，甚至直接用Node.js也行）。整个过程大概一分钟，项目就搭好了。

进目录以后装依赖，启动开发服务器：
```

cd 你的项目名  
npm install  
npm run dev  

```

默认跑在3000端口。这时候你打开浏览器访问`http://localhost:3000`，就能看到欢迎页面了。

### 路由咋整？

Remix的路由系统是它最香的地方。它用了**嵌套路由** 的设计，说白了就是把页面拆成一个个小模块，每个模块管自己的数据和UI。

假设你要做个博客，有文章列表页和详情页。在Remix里，文件夹结构大概长这样：
```

app/  
  routes/  
    posts/  
      _layout.tsx      # 文章区的公共布局  
      route.tsx        # 文章列表  
      $slug/  
        route.tsx      # 文章详情，$slug是动态参数  

```

看到那个`$slug`了吗？这就是动态路由，比Next.js的方括号好认多了。而且Remix的路由文件统一叫`route.tsx`，不容易搞混。

每个路由文件里，你可以导出三个关键的东西：
```

// 1. loader：在服务端获取数据  
exportasyncfunction loader({ params }) {  
const post = await getPost(params.slug);  
return json({ post });  
}  
  
// 2. action：处理表单提交  
exportasyncfunction action({ request }) {  
const formData = await request.formData();  
await createPost(formData);  
return redirect('/posts');  
}  
  
// 3. default组件：渲染页面  
exportdefaultfunction Post() {  
const { post } = useLoaderData();  // 直接用loader返回的数据  
return (  
    <article>  
      <h1>{post.title}</h1>  
      <Form method="post">  
        {/* 表单内容 */}  
      </Form>  
    </article>  
  );  
}  

```

注意那个`<Form>`组件，它不是普通的form，而是Remix封装的。提交的时候会直接触发action，不用你手写`onSubmit`、不用管什么`event.preventDefault()`，更不用搞`useState`那一堆状态。数据在服务端处理好，页面自动刷新，用户体验贼顺滑。

### 错误处理很贴心

传统的React应用，一个地方报错整个页面白屏。Remix给每个路由都配了"错误边界"（Error Boundary），就类似于：
```

export function ErrorBoundary() {  
  const error = useRouteError();  
  return (  
    <div className="error-page">  
      <h2>出错了</h2>  
      <p>{error.message}</p>  
    </div>  
  );  
}  

```

子路由报错不会影响到父级布局，用户至少还能看到导航栏，不会一脸懵逼地面对全白屏幕。

### 为啥选它？

你可能会问，那跟Next.js比到底好在哪？说实话，Next.js确实生态更成熟，社区资源也多。但Remix有几个点是真让人心动：

**客户端JS体积特别小** 。同样的应用，Next.js可能得往浏览器塞100-300KB的JavaScript，Remix通常控制在30-80KB。首屏加载快了不少，特别是在移动网络下感知很明显。

**数据加载更合理** 。Next.js的App Router虽然也能做服务端获取数据，但Remix的loader/action模式更直观。每个路由的数据需求都写在路由文件里，不像Next.js那样散落在各个组件里，找起来费劲。

**部署更灵活** 。Remix基于Web标准API设计，你的代码不光能跑在Node.js上，Bun、Deno、Cloudflare Workers这些新兴运行时都能原生支持。写一次代码，到处部署，这才是真正的"云原生"嘛。

不过也得说句公道话，Remix的社区确实没有Next.js那么庞大。有些第三方库可能得自己封装，文档虽然写得好，但中文资料还不算多。如果你团队里都是React老手，熟悉Next.js那套生态，迁移过来可能需要点学习成本。

![Remix Contacts示例](https://r2.jeanjan.kdns.fr/pictures/img-f4eccceb03.jpeg)Remix Contacts示例

但话说回来，技术选型这事儿，没有绝对的谁好谁坏。如果你的项目表单特别多、实时交互要求高，或者你就是烦透了客户端那堆复杂的状态管理，想回归Web开发的本质，那Remix绝对值得试一试。

项目地址：https://github.com/remix-run/remix

