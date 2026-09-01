# GitHub开源神器：全自动版本发布工具semantic-release，让你告别手动发版的深夜崩溃！

**作者**: Ghub 宝藏项目
**发布时间**: 2026-07-11 10:27
**原文链接**: https://mp.weixin.qq.com/s/UU2le4gMJxNu7qR6Hmndyg

---


写代码最烦人的是啥？不是需求改八遍，也不是bug调不通，而是发版那一刻。你得改package.json里的版本号，得写changelog，得打tag，得推送到npm，得去GitHub创建release...一套流程下来，半宿过去了，手一抖还可能输错版本号，那种崩溃感懂的都懂。

![semantic-release工作流程图](https://r2.jeanjan.kdns.fr/pictures/img-6a4e0e2301.jpeg)semantic-release工作流程图

今天要安利的这个宝贝，叫**semantic-release** ，简直就是为懒人量身定做的。它能把你从这种重复劳动里彻底解救出来。只要你的commit message写得规范点，它就能自动判断该发啥版本，自动生成release notes，自动打tag，甚至自动推送到npm。你只管写代码，发版这事交给它就行。

这东西的核心逻辑其实挺简单的。它通过分析你的提交信息来决定版本号怎么跳。比如你写了个`fix: 修复按钮点击失效`，它就自动发个patch版本，比如从1.0.0变成1.0.1。要是写了`feat: 新增用户登录功能`，那就是minor版本，直接1.1.0。要是你在提交里标注了`BREAKING CHANGE`，它立马明白这是破坏性更新，直接干到2.0.0。完全不需要你动脑子想版本号。

![GitHub Actions自动化流程](https://r2.jeanjan.kdns.fr/pictures/img-6a4e0e2302.png)GitHub Actions自动化流程

具体咋用呢？别急，一步一步来。

先安装。这个很简单，在你的项目根目录跑下面这行就行：
```

npm install --save-dev semantic-release  

```

如果你还想让它自动生成changelog文件，顺便把改动提交回仓库，那最好再装几个插件：
```

npm install --save-dev @semantic-release/changelog @semantic-release/git  

```

装好了就得配置。建个`.releaserc.json`文件放在项目根目录，内容大概长这样：
```

{  
  "branches": ["main"],  
"plugins": [  
    "@semantic-release/commit-analyzer",  
    "@semantic-release/release-notes-generator",  
    "@semantic-release/changelog",  
    "@semantic-release/npm",  
    "@semantic-release/github",  
    [  
      "@semantic-release/git",  
      {  
        "assets": ["CHANGELOG.md", "package.json"],  
        "message": "chore(release): ${nextRelease.version} [skip ci]"  
      }  
    ]  
  ]  
}  

```

这里面的`branches`记得改成你的主分支名，有些人用main有些人用master，别搞错了。plugins那一堆就是它的插件系统，commit-analyzer负责分析提交信息，release-notes-generator生成发布说明，changelog是生成变更日志，npm负责推送到npm仓库，github负责在GitHub上创建release。最后那个git插件是把生成的changelog和package.json的版本变动提交回仓库。

配置完了还得搞定GitHub Actions，这才是自动化的关键。在`.github/workflows/`目录下建个`release.yml`文件：
```

name: Release  
on:  
push:  
    branches:[main]  
  
permissions:  
contents:write  
issues:write  
pull-requests:write  
id-token:write  
  
jobs:  
release:  
    runs-on:ubuntu-latest  
    steps:  
      -name:Checkout  
        uses:actions/checkout@v4  
        with:  
          fetch-depth:0  
            
      -name:SetupNode.js  
        uses:actions/setup-node@v4  
        with:  
          node-version:"20"  
            
      -name:Installdependencies  
        run:npmci  
          
      -name:Build  
        run:npmrunbuild  
          
      -name:Release  
        env:  
          GITHUB_TOKEN:${{secrets.GITHUB_TOKEN}}  
          NPM_TOKEN:${{secrets.NPM_TOKEN}}  
        run:npxsemantic-release  

```

这里要注意两个token。`GITHUB_TOKEN`是GitHub自动给的，不用你操心。但`NPM_TOKEN`你得自己去npm网站生成一个，然后放到仓库的Settings -> Secrets and variables -> Actions里面，名字叫NPM_TOKEN。不然它没法帮你推包到npm。

![版本分支管理示意图](https://r2.jeanjan.kdns.fr/pictures/img-6a4e0e2303.jpeg)版本分支管理示意图

还有件重要的事，你的commit message得按规矩写。别再用"update"、"fix bug"这种模糊不清的话了。得用**约定式提交** （Conventional Commits）的格式：

  * `fix: 修复了某某问题` \- 会发patch版本
  * `feat: 添加了某某功能` \- 会发minor版本
  * `feat: 某某新功能\n\nBREAKING CHANGE: 接口已重构` \- 这种会发major版本

要是怕记不住或者团队成员不按规矩来，可以装个commitlint配合husky，在提交的时候自动检查，不合规的直接拦住。

都配好了以后，你啥也不用管，正常写代码，正常push。只要代码合并到main分支，GitHub Actions就会自动跑起来。如果检测到有新的fix或者feat提交，它就会自动计算版本号，自动生成release notes，自动打tag，自动推送到npm，一气呵成。你只管去泡杯咖啡，回来就发现新版本已经发好了。

刚开始用的时候可能会觉得麻烦，又要配这个又要配那个。但用过几次你就回不去了。想想以前发版的时候那种战战兢兢的感觉，再看看现在这种完全自动化的爽感，简直一个天上一个地下。特别是项目大了以后，这个功能能省多少事啊。

对了，如果你只是想试试，怕配置错了乱发版，可以在配置里加个`"dryRun": true`，这样它会跑一遍流程但不会真的发版，等你确认没问题了再关掉。

总之呢，semantic-release这工具就是那种看上去有点门槛，但一旦上手就离不开的类型。解放双手，从发版自动化开始！

GitHub地址：https://github.com/semantic-release/semantic-release

