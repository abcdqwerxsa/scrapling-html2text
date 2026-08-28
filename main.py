import argparse
import html2text
import re
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from scrapling import Fetcher

WECHAT_HOST = "mp.weixin.qq.com"


def _convert_code_blocks_to_fenced(text: str) -> str:
    """将缩进代码块转换为 ``` 格式"""
    lines = text.split('\n')
    result = []
    in_code_block = False
    code_buffer = []

    # 列表项的模式（微信特殊格式：4空格 + 数字 + 点 + 多空格）
    # 匹配: "    1.   ", "    2.  ", "- ", "* "
    list_pattern = re.compile(r'^\s*[0-9]+\.\s+|^[-*+]\s')

    for i, line in enumerate(lines):
        # 检测缩进代码块（4个空格开头）
        is_indented = line.startswith('    ')
        # 判断是否是列表项
        is_list_item = bool(list_pattern.match(line))

        if is_indented and not is_list_item:
            if not in_code_block:
                in_code_block = True
                code_buffer = []
            # 移除前导4空格
            code_buffer.append(line[4:] if len(line) > 4 else '')
        else:
            if in_code_block:
                # 结束代码块
                if code_buffer:
                    # 过滤掉只有空行的代码块
                    non_empty = [c for c in code_buffer if c.strip()]
                    if non_empty:
                        result.append('```')
                        result.extend(code_buffer)
                        result.append('```')
                        result.append('')
                    else:
                        result.extend([''] * len(code_buffer))
                in_code_block = False
                code_buffer = []
            result.append(line)

    # 处理末尾的代码块
    if in_code_block and code_buffer:
        non_empty = [c for c in code_buffer if c.strip()]
        if non_empty:
            result.append('```')
            result.extend(code_buffer)
            result.append('```')
        else:
            result.extend([''] * len(code_buffer))

    return '\n'.join(result)


def _localize_images(content_html: str, images_dir: Path) -> str:
    """下载微信图片到本地（绕过 mmbiz.qpic.cn 防盗链），并将 src 重写为相对路径"""
    images_dir.mkdir(parents=True, exist_ok=True)
    counter = 0

    def repl(m: re.Match) -> str:
        nonlocal counter
        counter += 1
        url = m.group(1)
        fmt = re.search(r'wx_fmt=(\w+)', url)
        dest = images_dir / f"img-{counter:02d}.{fmt.group(1) if fmt else 'png'}"
        if not dest.exists():
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0',
                'Referer': 'https://mp.weixin.qq.com/',
            })
            dest.write_bytes(urllib.request.urlopen(req, timeout=30).read())
        return f'src="images/{dest.name}"'

    return re.sub(r'src="(https://mmbiz\.qpic\.cn/[^"]+)"', repl, content_html)


def _html_to_markdown(content_html: str, images_dir: Path | None = None) -> str:
    """统一的 HTML → Markdown 转换管道，微信和普通网页共用。

    依次处理：图片懒加载 → 图片本地化 → 代码块换行 → html2text 转换 → 代码围栏 → 装饰点清理。
    """
    # 微信图片懒加载：data-src 才是真实地址
    content_html = re.sub(
        r'<img([^>]*?)data-src=["\']([^"\']+)["\']([^>]*?)>',
        r'<img\1src="\2"\3>',
        content_html,
    )
    # 微信防盗链：图片下载到本地，否则外部 Markdown 查看器加载不出
    if images_dir is not None:
        content_html = _localize_images(content_html, images_dir)
    # 微信代码块：每行一个 <code> 标签且无换行符，补上换行
    content_html = re.sub(r'</code>\s*<code', '</code>\n<code', content_html)

    h = html2text.HTML2Text()
    h.ignore_links = False      # 保留链接
    h.ignore_images = False     # 保留图片
    h.ignore_emphasis = False   # 保留粗体/斜体
    h.body_width = 0            # 不自动换行，防止段落被截断
    h.unicode_snob = True       # 使用 Unicode 字符，避免乱码
    h.pad_tables = True         # 表格对齐
    markdown = h.handle(content_html)

    markdown = _convert_code_blocks_to_fenced(markdown)
    # 去掉微信装饰性分隔点（被 html2text 转成空列表项），压缩多余空行
    markdown = re.sub(r'^(\s*[*·•]\s*)+$', '', markdown, flags=re.M)
    return re.sub(r'\n{3,}', '\n\n', markdown)


def crawl_wechat_article(url: str, images_dir: Path | None = None) -> str:
    """爬取微信公众号文章并转换为 Markdown，返回 Markdown 文本"""
    page = Fetcher().get(url)

    def text_of(selector: str) -> str:
        elems = page.css(selector)
        return elems[0].get_all_text().strip() if elems else ""

    title = text_of("#activity-name") or "无标题"
    author = text_of("#js_name") or "未知作者"

    # 发布时间由 JS 渲染，静态抓取拿不到；从页面内嵌的 var ct（Unix 时间戳）恢复
    publish_time = text_of("#publish_time")
    if not publish_time:
        m = re.search(r'var ct = ["\'](\d+)["\']', page.body.decode("utf-8", "ignore"))
        if m:
            publish_time = datetime.fromtimestamp(
                int(m.group(1)), tz=timezone(timedelta(hours=8))
            ).strftime("%Y-%m-%d %H:%M")

    content_elems = page.css("#js_content")
    if not content_elems:
        raise ValueError("未能获取到文章内容：页面可能需要验证，或不是微信公众号文章")

    markdown_content = _html_to_markdown(content_elems[0].html_content, images_dir)

    return f"""# {title}

**作者**: {author}
**发布时间**: {publish_time}
**原文链接**: {url}

---

{markdown_content}
"""


def crawl_webpage(url: str, images_dir: Path | None = None) -> str:
    """爬取任意网页并转换为 Markdown，返回 Markdown 文本"""
    page = Fetcher().get(url)

    title = ""
    for sel in ("h1", "title"):
        elems = page.css(sel)
        if elems and (t := elems[0].get_all_text().strip()):
            title = t
            break

    # 按优先级尝试多种正文选择器
    content_html = ""
    for selector in ("article", "main", ".post-content", ".article-content",
                     ".entry-content", "#article-content", ".content",
                     "[class*='content']", "[class*='article']"):
        elems = page.css(selector)
        if elems:
            content_html = elems[0].html_content
            break
    if not content_html:
        body = page.css("body")
        content_html = body[0].html_content if body else ""
    if not content_html:
        raise ValueError("未能获取到网页内容")

    markdown_content = _html_to_markdown(content_html, images_dir)

    return f"""# {title or '无标题'}

**原文链接**: {url}

---

{markdown_content}
"""


def _save(markdown: str, output_dir: Path) -> Path:
    """按文章标题命名保存，返回文件路径"""
    m = re.match(r'# (.+)', markdown)
    name = re.sub(r'[\\/:*?"<>|\s]+', '-', m.group(1)).strip('-')[:80] if m else 'article'
    path = output_dir / f"{name}.md"
    path.write_text(markdown, encoding='utf-8')
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="爬取网页并转换为 Markdown")
    parser.add_argument("url", help="目标网页 URL")
    parser.add_argument("-o", "--output-dir", default="wechat-posts",
                        help="输出目录（默认 wechat-posts）")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if WECHAT_HOST in args.url:
        markdown = crawl_wechat_article(args.url, images_dir=out_dir / "images")
    else:
        markdown = crawl_webpage(args.url, images_dir=out_dir / "images")

    path = _save(markdown, out_dir)
    print(f"文章已保存到: {path}")


if __name__ == "__main__":
    main()
