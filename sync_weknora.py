"""微信公众号文章 → Markdown → R2 图床 → WeKnora 知识库 一键同步

用法: uv run python sync_weknora.py <url> [<url> ...]

流程: 爬取正文(main.py, 图片自动上传 R2 引用公网 URL) → 按标题存入 wechat-posts/
      → 删除 WeKnora 中同名旧文档(幂等重跑) → 上传(开图像处理) → 轮询解析状态

环境变量(可选): WEKNORA_API_KEY / WEKNORA_API_BASE / WEKNORA_KB_NAME
               未设置时从 /home/nilpo/WeKnora/.env 读 key，其余用默认值
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from main import _save, crawl_wechat_article

OUT_DIR = Path(__file__).parent / "wechat-posts"
WEKNORA_ENV = Path("/home/nilpo/WeKnora/.env")  # 兜底读取 API key


def api_key() -> str:
    if key := os.environ.get("WEKNORA_API_KEY"):
        return key
    for line in WEKNORA_ENV.read_text().splitlines():
        if line.startswith("WEKNORA_API_KEY="):
            return line.split("=", 1)[1].strip()
    sys.exit("未找到 WEKNORA_API_KEY（环境变量或 /home/nilpo/WeKnora/.env）")


def curl_json(method: str, url: str, key: str, *, body=None, form=None) -> dict:
    cmd = ["curl", "-s", "-m", "120", "-X", method, url, "-H", f"X-API-Key: {key}"]
    if body is not None:
        cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(body)]
    cmd += form or []
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    return json.loads(out) if out.strip() else {}


def list_docs(base: str, kb_id: str, key: str) -> dict[str, str]:
    """返回 {标题: 文档id}，自动翻页"""
    docs, page = {}, 1
    while True:
        resp = curl_json("GET", f"{base}/knowledge-bases/{kb_id}/knowledge"
                            f"?page={page}&page_size=200", key)
        items = resp.get("data") or []
        for it in items:
            docs[it["title"]] = it["id"]
        if len(items) < 200:
            return docs
        page += 1


def main() -> None:
    urls = sys.argv[1:]
    if not urls:
        sys.exit(__doc__)
    key = api_key()
    base = os.environ.get("WEKNORA_API_BASE", "http://127.0.0.1:8081/api/v1")
    kb_name = os.environ.get("WEKNORA_KB_NAME", "demo-wechat")

    kb_id = next((kb["id"] for kb in curl_json("GET", f"{base}/knowledge-bases", key)["data"]
                  if kb["name"] == kb_name), None)
    if not kb_id:
        sys.exit(f"知识库 {kb_name} 不存在")

    # 1) 爬取（图片经 main.py 自动上传 R2 图床）
    paths = []
    for url in urls:
        markdown = crawl_wechat_article(url, images_dir=OUT_DIR / "images")
        paths.append(_save(markdown, OUT_DIR))
        print(f"爬取完成: {paths[-1].name}", flush=True)

    # 2) 幂等：同名旧文档先删（删除为异步任务）
    existing = list_docs(base, kb_id, key)
    deleted = 0
    for path in paths:
        if path.name in existing:
            curl_json("DELETE", f"{base}/knowledge/{existing[path.name]}", key)
            deleted += 1
    if deleted:
        print(f"删除同名旧文档 {deleted} 篇，等待异步清理...", flush=True)
        time.sleep(20)

    # 3) 上传（enable_multimodel=true 配合 KB 已开启的图像处理）
    uploaded = {}
    for path in paths:
        resp = curl_json("POST", f"{base}/knowledge-bases/{kb_id}/knowledge/file", key,
                         form=["-F", f"file=@{path};type=text/markdown",
                               "-F", "enable_multimodel=true"])
        if kid := (resp.get("data") or {}).get("id"):
            uploaded[kid] = path.name
            print(f"已上传: {path.name}", flush=True)
        else:
            print(f"上传失败: {path.name}: {json.dumps(resp, ensure_ascii=False)[:200]}", flush=True)

    # 4) 轮询解析状态
    deadline, failed = time.time() + 1200, []
    while uploaded and time.time() < deadline:
        time.sleep(20)
        statuses = {it["id"]: it["parse_status"]
                    for it in (curl_json("GET", f"{base}/knowledge-bases/{kb_id}/knowledge"
                                           "?page=1&page_size=200", key).get("data") or [])}
        pending = {k: v for k, v in ((kid, statuses.get(kid, "?")) for kid in uploaded)
                   if v not in ("completed", "failed")}
        for kid, name in list(uploaded.items()):
            if statuses.get(kid) == "failed":
                failed.append(name)
                del uploaded[kid]
        if not pending:
            break
        print(f"解析中... 剩余 {len(pending)} 篇", flush=True)

    print(f"\n完成: 成功解析 {len(uploaded)} 篇, 失败 {len(failed)} 篇"
          + (f": {failed}" if failed else ""))
    sys.exit(1 if failed or len(uploaded) < len(paths) else 0)


if __name__ == "__main__":
    main()
