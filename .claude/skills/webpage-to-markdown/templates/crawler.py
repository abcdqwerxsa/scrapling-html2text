"""
网页内容爬取转 Markdown

使用 Scrapling + html2text 组合爬取网页内容并转换为干净的 Markdown 格式。
特别适用于微信公众号等有反爬机制的网站。

依赖安装:
    uv add scrapling html2text playwright browserforge curl-cffi
    uv run playwright install chromium

使用示例:
    from crawler import crawl_webpage
    crawl_webpage("https://mp.weixin.qq.com/s/xxxxxx", "article.md")
"""

import html2text
import re
from scrapling import Fetcher


def crawl_webpage(url: str, output_file: str = None) -> str:
    """
    爬取网页内容并转换为 Markdown 格式

    Args:
        url: 目标网页 URL
        output_file: 输出文件路径（可选）

    Returns:
        Markdown 格式的文本内容
    """
    fetcher = Fetcher()
    page = fetcher.get(url)

    # 尝试获取文章元信息（适用于微信公众号等）
    title = _extract_text(page, "#activity-name") or _extract_title(page)
    author = _extract_text(page, "#js_name") or _extract_author(page)
    publish_time = _extract_text(page, "#publish_time") or ""

    # 提取正文内容
    content_html = _extract_content_html(page)

    if not content_html:
        raise ValueError("未能获取到文章内容")

    # 转换为 Markdown
    markdown_content = _html_to_markdown(content_html)

    # 后处理：将缩进代码块转换为 ``` 格式
    markdown_content = _convert_code_blocks_to_fenced(markdown_content)

    # 组装完整文档
    full_markdown = f"""# {title}

**作者**: {author}
**发布时间**: {publish_time}
**原文链接**: {url}

---

{markdown_content}
"""

    # 保存到文件
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(full_markdown)
        print(f"文章已保存到: {output_file}")

    return full_markdown


def _extract_text(page, selector: str) -> str:
    """通过 CSS 选择器提取文本"""
    elems = page.css(selector)
    return elems[0].get_all_text().strip() if elems else ""


def _extract_title(page) -> str:
    """提取页面标题（通用方法）"""
    selectors = ["h1", "title", "[property='og:title']"]
    for sel in selectors:
        text = _extract_text(page, sel)
        if text:
            return text
    return "无标题"


def _extract_author(page) -> str:
    """提取作者信息（通用方法）"""
    selectors = ["[rel='author']", ".author", "[name='author']"]
    for sel in selectors:
        text = _extract_text(page, sel)
        if text:
            return text
    return "未知作者"


def _extract_content_html(page) -> str:
    """提取正文 HTML（按优先级尝试多种选择器）"""
    # 微信公众号、博客、新闻网站常用的正文选择器
    content_selectors = [
        "#js_content",           # 微信公众号
        "article",               # HTML5 article
        "main",                  # HTML5 main
        ".post-content",         # 常见博客
        ".article-content",      # 新闻网站
        "[class*='content']",    # 包含 content 的类
        "[class*='article']",    # 包含 article 的类
        "[class*='body']",       # 包含 body 的类
    ]

    for selector in content_selectors:
        elems = page.css(selector)
        if elems:
            html = elems[0].html_content
            # 修复微信图片延迟加载问题（data-src -> src）
            html = re.sub(
                r'<img([^>]*?)data-src=["\']([^"\']+)["\']([^>]*?)>',
                r'<img\1src="\2"\3>',
                html
            )
            return html

    # 最后尝试获取 body
    body_elems = page.css("body")
    return body_elems[0].html_content if body_elems else ""


def _html_to_markdown(html_content: str) -> str:
    """将 HTML 转换为 Markdown"""
    h = html2text.HTML2Text()

    # === 核心配置（推荐） ===
    h.ignore_links = False          # 保留链接
    h.ignore_images = False         # 保留图片
    h.ignore_emphasis = False       # 保留强调格式（粗体/斜体）
    h.body_width = 0                # 不自动换行（重要！防止段落被截断）
    h.unicode_snob = True           # 使用 Unicode 字符（避免乱码）
    h.pad_tables = True             # 表格填充对齐

    # 注意：不要使用 mark_code = True，会生成 [code]...[/code] 格式
    # 代码块转换使用后处理函数 _convert_code_blocks_to_fenced()

    return h.handle(html_content)


def _convert_code_blocks_to_fenced(text: str) -> str:
    """将缩进代码块转换为 ``` 格式

    html2text 默认生成 4 空格缩进的代码块，
    此函数将其转换为更通用的 ``` 格式。
    """
    lines = text.split('\n')
    result = []
    in_code_block = False
    code_buffer = []

    # 列表项的模式（匹配微信特殊格式：4空格 + 数字 + 点 + 多空格）
    list_pattern = re.compile(r'^\s*[0-9]+\.\s+|^[-*+]\s')

    for line in lines:
        is_indented = line.startswith('    ')
        is_list_item = bool(list_pattern.match(line))

        if is_indented and not is_list_item:
            if not in_code_block:
                in_code_block = True
                code_buffer = []
            code_buffer.append(line[4:] if len(line) > 4 else '')
        else:
            if in_code_block:
                if code_buffer:
                    non_empty = [c for c in code_buffer if c.strip()]
                    if non_empty:
                        result.append('```')
                        result.extend(code_buffer)
                        result.append('```')
                        result.append('')
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

    return '\n'.join(result)


# 使用示例
if __name__ == "__main__":
    # 微信公众号文章
    crawl_webpage(
        "https://mp.weixin.qq.com/s/EwVItQH4JUsONqv_Fmi4wQ",
        output_file="article.md"
    )

    # 普通网页
    # crawl_webpage(
    #     "https://example.com/blog/post",
    #     output_file="blog.md"
    # )
