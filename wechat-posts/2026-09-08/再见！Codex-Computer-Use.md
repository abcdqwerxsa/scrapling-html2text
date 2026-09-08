# 再见！Codex Computer Use

**作者**: 字节笔记本
**发布时间**: 2026-08-08 09:26
**原文链接**: https://mp.weixin.qq.com/s/dvuGqe7k9cKBdQvh0KZpuA

---

对于像我这样的CLI党来说，下载和使用Codex APP的唯一理由就是它的computer use插件。computer use 实在是太好用了，几乎就这一个插件就可以顶掉Perplexity费尽心机开发的Comet独立AI浏览器应用。我将它大量使用在类似于APP上架、复杂的后台表单填写测试以及Excel表格的处理当中。现在我也养成了一个习惯，一件事情动手之前，首先想想是不是可以用computer use来自动化完成。因为反正几乎所有需要人盯着屏幕一格一格手动点的事情，现在真的都可以交给computer use一句话来手替完成。  
以前是有手就会，现在是手都不用了。不过 Codex APP有着它天然的缺陷。第一点就是computer use消耗极其的费，在执行过程中会涉及到大量的多模态识别以及数据结构的解析，稍微复杂一点任务就会狂掉额度。第二点是computer use是闭源且封闭的，你没法在其他的Agent当中使用，这种强绑定其实还蛮恶心的，要用computer use 你不得不先打开Codex桌面版。中间也尝试过其他的开源的computer use，比方说try cua，但是测试下来都没有Codex的效果好。第三点，Codex太卡太臃肿了。直到现在磨损硬盘的问题依然没有得到彻底的解决，OpenAI还往里面硬塞了很多的没有用的东西，再加上又是基于Electron开发的，还没正式写代码内存就直接爆掉了。最近，Kimi code上了一个硬货，推出了它的computer use插件，使用了一下非常好用，强烈推荐。不过安装方式有点奇特，并没有单独的下载通道。使用需要升级到Kimi code的最新版本，然后通过它的Plugins插件的方式来选择official来安装。![](https://r2.jeanjan.kdns.fr/pictures/img-2e16180d01.png)点击安装完成之后，就会有一个独立的computer use应用。在这个页面里，我们可以给他授权辅助功能以及屏幕，以及开启在Claude Code或者Codex当中的使用。![](https://r2.jeanjan.kdns.fr/pictures/img-2e16180d02.png)

接入其他 Agent 将下方指令发送至你的本地 Agent 配置 MCP server。

配置完成 后 重启你的 Agent 即可使用 Kimi Computer Use，可以使用如下指令一键安装：
```

将下面的 MCP Server 加入你的 Agent：  
  
Name: kimi-cu  
Type: stdio  
Command: /Applications/KimiCU.app/Contents/MacOS/kimi-cu  
Args: mcp -s user  
  
JSON:  
{  
  "mcpServers": {  
    "kimi-cu": {  
      "type": "stdio",  
      "command": "/Applications/KimiCU.app/Contents/MacOS/kimi-cu",  
      "args": ["mcp", "-s", "user"]  
    }  
  }  
}
```

我目前是结合Grok+Kimi CU来使用，两者搭配简直就是绝配，Grok自带多模态能力，而且输出速度极其得快。

和原生的codex computer user使用一毛一样，纯后台执行，不抢占鼠标，可视化的轨迹和点击交互。

Kimi CU的交互解析能力也基本和codex computer use齐平，两者的结合已经完全超越了Codex computer use的使用体验。

![](https://r2.jeanjan.kdns.fr/pictures/img-2e16180d03.png)以下就是用computer use来自动化发布x图文视频的测试截图，让Grok生成了图文之后，再使用Kimi CU来发布内容到推特。![](https://r2.jeanjan.kdns.fr/pictures/img-2e16180d04.png)CU作为一个独立的应用，既可以在Claude Code这种CLI中使用，也可以在类似ZCode桌面端使用，完全不限制它的使用场景。Kimi官方其实完全可以把这个插件作为一个独立的APP来发布，就不用绕到Kimi code当中去安装了。

