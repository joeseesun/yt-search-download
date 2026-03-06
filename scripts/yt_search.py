#!/usr/bin/env python3
"""
YouTube Search & Download Tool
- Search YouTube videos/channels using YouTube Data API v3
- Download via yt-dlp
"""

import os
import sys
import json
import argparse
import urllib.request
import urllib.parse
import urllib.error
import datetime
import re
import subprocess
import shutil
from typing import Optional


API_KEY = os.environ.get("YT_BROWSE_API_KEY") or os.environ.get("YOUTUBE_API_KEY")
BASE_URL = "https://www.googleapis.com/youtube/v3"


def api_get(endpoint: str, params: dict) -> dict:
    """Call YouTube Data API v3 and return parsed JSON response."""
    params["key"] = API_KEY
    url = f"{BASE_URL}/{endpoint}?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        try:
            err_msg = json.loads(body).get("error", {}).get("message", body[:200])
        except Exception:
            err_msg = body[:200]
        print(f"[API Error] {e.code}: {err_msg}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"[Network Error] {e.reason}", file=sys.stderr)
        sys.exit(1)


def parse_duration(iso: str) -> tuple:
    """Convert ISO 8601 duration (e.g. PT3H55M16S) to (readable string, total seconds)."""
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m:
        return "?", 0
    h = int(m.group(1) or 0)
    mi = int(m.group(2) or 0)
    s = int(m.group(3) or 0)
    total_secs = h * 3600 + mi * 60 + s
    parts = []
    if h:
        parts.append(f"{h}h")
    if mi:
        parts.append(f"{mi}m")
    if s:
        parts.append(f"{s}s")
    return "".join(parts) or "0s", total_secs


def parse_duration_input(s: str) -> int:
    """Parse user duration input to seconds. Supports: 30m, 1h, 1h30m, 90 (= 90 min)."""
    s = s.strip().lower()
    m = re.match(r"^(?:(\d+)h)?(?:(\d+)m)?$", s)
    if m and (m.group(1) or m.group(2)):
        return int(m.group(1) or 0) * 3600 + int(m.group(2) or 0) * 60
    try:
        return int(s) * 60  # bare number = minutes
    except ValueError:
        return 0


def fmt_views(n: int) -> str:
    """Format view count for display (e.g. 1.2M, 35.5K)."""
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def validate_date(date_str: str) -> bool:
    """Validate date string is in YYYY-MM-DD format."""
    try:
        datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def resolve_channel(query: str) -> Optional[str]:
    """Resolve channel handle/URL/ID to channel ID."""
    if re.match(r"^UC[a-zA-Z0-9_-]{22}$", query):
        return query
    handle = query.strip("/").split("/")[-1].lstrip("@")
    try:
        data = api_get("channels", {"forHandle": handle, "part": "id", "maxResults": 1})
        items = data.get("items", [])
        if items:
            return items[0]["id"]
    except SystemExit:
        pass
    # Fallback: search for the channel
    try:
        data = api_get("search", {"q": query, "type": "channel", "part": "id", "maxResults": 1})
        items = data.get("items", [])
        if items:
            return items[0]["id"]["channelId"]
    except SystemExit:
        pass
    return None


def search_videos(
    query: str = "",
    channel_id: str = None,
    max_results: int = 20,
    order: str = "relevance",
    published_after: str = None,
    published_before: str = None,
) -> list:
    """Search videos and return list of video dicts with details."""
    params = {
        "part": "id",
        "type": "video",
        "maxResults": min(max_results, 50),
        "order": order,
    }
    if query:
        params["q"] = query
    if channel_id:
        params["channelId"] = channel_id
    if published_after:
        params["publishedAfter"] = published_after
    if published_before:
        params["publishedBefore"] = published_before

    data = api_get("search", params)
    video_ids = [item["id"]["videoId"] for item in data.get("items", [])]
    if not video_ids:
        return []

    details = api_get("videos", {
        "part": "snippet,statistics,contentDetails",
        "id": ",".join(video_ids),
    })

    results = []
    for item in details.get("items", []):
        snip = item["snippet"]
        stats = item.get("statistics", {})
        cd = item.get("contentDetails", {})
        pub = snip.get("publishedAt", "")[:10]
        dur_str, dur_secs = parse_duration(cd.get("duration", ""))
        results.append({
            "id": item["id"],
            "title": snip.get("title", ""),
            "channel": snip.get("channelTitle", ""),
            "published": pub,
            "views": int(stats.get("viewCount", 0)),
            "duration": dur_str,
            "duration_seconds": dur_secs,
            "url": f"https://www.youtube.com/watch?v={item['id']}",
            "description": snip.get("description", "")[:200],
        })
    return results


def search_channel_videos(
    channel: str,
    query: str = "",
    max_results: int = 20,
    order: str = "date",
) -> list:
    """Search within a specific channel."""
    channel_id = resolve_channel(channel)
    if not channel_id:
        print(f"[错误] 找不到频道: {channel}", file=sys.stderr)
        return []
    return search_videos(
        query=query,
        channel_id=channel_id,
        max_results=max_results,
        order=order,
    )


def print_results(results: list, show_desc: bool = False):
    """Print search results as a Markdown table with translation placeholder."""
    if not results:
        print("未找到结果")
        return

    print()
    print("| # | 标题（原文 → 中文译文） | 日期 | 时长 | 播放量 |")
    print("|---|------------------------|------|------|--------|")
    for i, v in enumerate(results, 1):
        title = v["title"].replace("|", "\\|")
        short = title if len(title) <= 55 else title[:52] + "..."
        link = f"[{short}]({v['url']})"
        print(f"| {i} | {link}<br>【译】___ | {v['published']} | {v['duration']} | {fmt_views(v['views'])} |")
        if show_desc and v["description"]:
            desc = v["description"][:120].replace("|", "\\|").replace("\n", " ")
            print(f"| | _{desc}_ | | | |")
    print()


def apply_duration_filter_sort(results: list, min_secs: int = 0, max_secs: int = 0, sort_by: str = "") -> list:
    """Filter by duration and/or sort client-side."""
    if min_secs:
        results = [r for r in results if r["duration_seconds"] >= min_secs]
    if max_secs:
        results = [r for r in results if r["duration_seconds"] <= max_secs]
    if sort_by == "duration-asc":
        results = sorted(results, key=lambda r: r["duration_seconds"])
    elif sort_by == "duration-desc":
        results = sorted(results, key=lambda r: r["duration_seconds"], reverse=True)
    elif sort_by == "views":
        results = sorted(results, key=lambda r: r["views"], reverse=True)
    return results


def download_video(url: str, output_dir: str = None, quality: str = "best", audio_only: bool = False) -> bool:
    """Download a video via yt-dlp."""
    if not shutil.which("yt-dlp"):
        print("[错误] 未找到 yt-dlp。安装方式: brew install yt-dlp", file=sys.stderr)
        return False

    out = output_dir or os.path.expanduser("~/Downloads")
    os.makedirs(out, exist_ok=True)

    cmd_parts = ["yt-dlp"]

    # Try to use browser cookies for age-restricted or region-locked videos
    for browser in ["chrome", "firefox", "safari"]:
        if shutil.which(browser) or os.path.exists(f"/Applications/{browser.capitalize()}.app"):
            cmd_parts += ["--cookies-from-browser", browser]
            break

    if audio_only:
        cmd_parts += ["-x", "--audio-format", "mp3"]
    else:
        fmt_map = {
            "best": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "1080p": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]",
            "720p": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]",
            "480p": "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]",
        }
        cmd_parts += ["-f", fmt_map.get(quality, fmt_map["best"])]

    output_fmt = "mp3" if audio_only else "mp4"
    cmd_parts += [
        "--merge-output-format", output_fmt,
        "-o", f"{out}/%(title)s.%(ext)s",
        "--no-playlist",
        url,
    ]

    print(f"\n▶ 开始下载: {url}")
    print(f"  保存到: {out}\n")
    result = subprocess.run(cmd_parts, capture_output=False)
    if result.returncode != 0:
        print(f"\n[错误] 下载失败 (退出码 {result.returncode})", file=sys.stderr)
        return False
    print("\n✓ 下载完成")
    return True


def main():
    if not API_KEY:
        print("[错误] 未设置 YouTube API Key。")
        print("请设置环境变量: export YT_BROWSE_API_KEY=your_key")
        print("获取方式: https://console.cloud.google.com/ → 启用 YouTube Data API v3 → 创建 API Key")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="YouTube 搜索 & 下载工具")
    sub = parser.add_subparsers(dest="cmd")

    # search
    ps = sub.add_parser("search", help="搜索 YouTube 视频")
    ps.add_argument("query", help="搜索关键词")
    ps.add_argument("-c", "--channel", help="限定频道 (handle/@name/URL/ID)")
    ps.add_argument("-n", "--max", type=int, default=20, help="最多返回条数 (默认20)")
    ps.add_argument("-o", "--order", choices=["relevance", "date", "viewCount", "rating"], default="relevance",
                    help="API 排序: relevance|date|viewCount|rating")
    ps.add_argument("--sort-by", choices=["views", "duration-asc", "duration-desc"],
                    help="本地二次排序: views|duration-asc|duration-desc")
    ps.add_argument("--min-duration", metavar="DUR", help="最短时长 (如 30m, 1h, 1h30m, 或纯数字=分钟)")
    ps.add_argument("--max-duration", metavar="DUR", help="最长时长 (如 30m, 1h, 1h30m, 或纯数字=分钟)")
    ps.add_argument("--after", help="发布时间起 (YYYY-MM-DD)")
    ps.add_argument("--before", help="发布时间止 (YYYY-MM-DD)")
    ps.add_argument("-d", "--desc", action="store_true", help="显示简介")
    ps.add_argument("--json", action="store_true", help="输出 JSON 格式")

    # channel
    pc = sub.add_parser("channel", help="浏览频道最新视频")
    pc.add_argument("channel", help="频道 (handle/@name/URL/ID)")
    pc.add_argument("-q", "--query", default="", help="在频道内搜索")
    pc.add_argument("-n", "--max", type=int, default=20, help="最多返回条数 (默认20)")
    pc.add_argument("-o", "--order", choices=["date", "relevance", "viewCount"], default="date",
                    help="API 排序: date|relevance|viewCount")
    pc.add_argument("--sort-by", choices=["views", "duration-asc", "duration-desc"],
                    help="本地二次排序: views|duration-asc|duration-desc")
    pc.add_argument("--min-duration", metavar="DUR", help="最短时长 (如 30m, 1h, 1h30m, 或纯数字=分钟)")
    pc.add_argument("--max-duration", metavar="DUR", help="最长时长 (如 30m, 1h, 1h30m, 或纯数字=分钟)")
    pc.add_argument("-d", "--desc", action="store_true", help="显示简介")
    pc.add_argument("--json", action="store_true", help="输出 JSON 格式")

    # download
    pd = sub.add_parser("download", help="下载视频")
    pd.add_argument("url", help="YouTube 视频 URL")
    pd.add_argument("--dir", default=os.path.expanduser("~/Downloads"), help="下载目录")
    pd.add_argument("-q", "--quality", choices=["best", "1080p", "720p", "480p"], default="best")
    pd.add_argument("--audio-only", action="store_true", help="仅下载音频 (MP3)")

    # info
    pi = sub.add_parser("info", help="获取视频信息")
    pi.add_argument("url", help="YouTube 视频 URL 或 ID")

    args = parser.parse_args()

    if args.cmd == "search":
        after, before = None, None
        if args.after:
            if not validate_date(args.after):
                print(f"[错误] 日期格式无效: {args.after} (应为 YYYY-MM-DD)", file=sys.stderr)
                sys.exit(1)
            after = f"{args.after}T00:00:00Z"
        if args.before:
            if not validate_date(args.before):
                print(f"[错误] 日期格式无效: {args.before} (应为 YYYY-MM-DD)", file=sys.stderr)
                sys.exit(1)
            before = f"{args.before}T23:59:59Z"
        channel_id = resolve_channel(args.channel) if args.channel else None
        results = search_videos(
            query=args.query,
            channel_id=channel_id,
            max_results=args.max,
            order=args.order,
            published_after=after,
            published_before=before,
        )
        min_secs = parse_duration_input(args.min_duration) if args.min_duration else 0
        max_secs = parse_duration_input(args.max_duration) if args.max_duration else 0
        results = apply_duration_filter_sort(results, min_secs, max_secs, args.sort_by or "")
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            print_results(results, show_desc=args.desc)

    elif args.cmd == "channel":
        results = search_channel_videos(
            channel=args.channel,
            query=args.query,
            max_results=args.max,
            order=args.order,
        )
        min_secs = parse_duration_input(args.min_duration) if args.min_duration else 0
        max_secs = parse_duration_input(args.max_duration) if args.max_duration else 0
        results = apply_duration_filter_sort(results, min_secs, max_secs, args.sort_by or "")
        if hasattr(args, 'json') and args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            print_results(results, show_desc=getattr(args, 'desc', False))

    elif args.cmd == "download":
        ok = download_video(args.url, output_dir=args.dir, quality=args.quality, audio_only=args.audio_only)
        sys.exit(0 if ok else 1)

    elif args.cmd == "info":
        vid_id = args.url
        m = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", args.url)
        if m:
            vid_id = m.group(1)
        details = api_get("videos", {"part": "snippet,statistics,contentDetails", "id": vid_id})
        items = details.get("items", [])
        if not items:
            print("未找到视频", file=sys.stderr)
            sys.exit(1)
        item = items[0]
        snip = item["snippet"]
        stats = item.get("statistics", {})
        cd = item.get("contentDetails", {})
        print(f"\n标题: {snip.get('title')}")
        print(f"频道: {snip.get('channelTitle')}")
        print(f"发布: {snip.get('publishedAt', '')[:10]}")
        print(f"时长: {parse_duration(cd.get('duration', ''))}")
        print(f"播放: {fmt_views(int(stats.get('viewCount', 0)))}")
        print(f"点赞: {fmt_views(int(stats.get('likeCount', 0)))}")
        print(f"URL:  https://www.youtube.com/watch?v={vid_id}")
        print(f"\n简介:\n{snip.get('description', '')[:500]}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
