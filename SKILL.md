---
name: yt-search-download
description: |
  YouTube 视频搜索与下载工具。结合 YouTube Data API v3 进行高级搜索，yt-dlp 下载。支持全站搜索、频道浏览、按时间/播放量/相关度排序、下载视频、提取音频。当用户想搜索 YouTube、浏览频道视频、下载 YouTube 视频、提取音频时使用此 skill。触发词："搜索YouTube"、"YouTube搜索"、"找YouTube视频"、"下载YouTube"、"浏览频道"、"搜索[频道名]最新视频"、"下载这个视频"、"提取音频"。
---

# YouTube 搜索 & 下载

基于 YouTube Data API v3 进行高级搜索，配合 yt-dlp 下载。

## 前置条件

1. **YouTube API Key**：
   ```bash
   echo $YT_BROWSE_API_KEY
   ```
   如果为空：[Google Cloud Console](https://console.cloud.google.com/) → 启用 YouTube Data API v3 → 创建 API Key → 写入 `~/.zshrc`：
   ```bash
   export YT_BROWSE_API_KEY=your_key
   ```

2. **yt-dlp**（下载用）：
   ```bash
   brew install yt-dlp   # macOS
   pip install yt-dlp     # 或 pip 安装
   ```

## 命令说明

脚本路径：`~/.claude/skills/yt-search-download/scripts/yt_search.py`

### 全站关键词搜索

```bash
python3 scripts/yt_search.py search "关键词" -n 20
```

| 参数 | 说明 |
|------|------|
| `-n 20` | 最多返回条数（默认 20） |
| `-o date` | 按时间排序（默认 relevance） |
| `-o viewCount` | 按播放量排序 |
| `--after 2024-01-01` | 发布时间起 |
| `--before 2024-12-31` | 发布时间止 |
| `-c @handle` | 限定频道 |
| `-d` | 显示简介 |
| `--json` | JSON 格式输出 |

### 浏览频道视频

```bash
# 频道最新视频（按时间倒序）
python3 scripts/yt_search.py channel @channelHandle -n 10

# 频道内关键词搜索
python3 scripts/yt_search.py channel @channelHandle -q "关键词"

# 频道内按播放量排序
python3 scripts/yt_search.py channel @channelHandle -o viewCount
```

频道格式支持：`@handle`、`https://youtube.com/@handle`、频道 ID（`UCxxxx`）

### 下载视频

```bash
# 最佳画质下载到 ~/Downloads
python3 scripts/yt_search.py download "VIDEO_URL"

# 指定画质
python3 scripts/yt_search.py download "VIDEO_URL" -q 1080p

# 指定目录
python3 scripts/yt_search.py download "VIDEO_URL" --dir ~/Desktop

# 仅下载音频（MP3）
python3 scripts/yt_search.py download "VIDEO_URL" --audio-only
```

### 视频详情查询

```bash
python3 scripts/yt_search.py info "VIDEO_URL"
```

## 输出格式

```
#    标题                                                    频道                 日期         时长       播放量
------------------------------------------------------------------------------------------------------------------------
1    The spelled-out intro to neural networks and back...   Andrej Karpathy      2022-10-05   3h55m16s   3.7M
2    Let's build GPT: from scratch, in code, spelled out   Andrej Karpathy      2023-01-17   1h56m27s   2.1M
```

## 典型工作流

**找某频道最新视频并下载：**
1. `channel @handle -n 10` → 浏览结果
2. 问用户要下载哪个
3. `download "URL"` → 保存到 ~/Downloads

**搜索 + 按播放量筛选：**
1. `search "关键词" -o viewCount -n 20`

**提取播客音频：**
1. `search "播客名" -o date -n 5`
2. `download "URL" --audio-only`

## 高级用法（直接用 yt-dlp）

```bash
# 列出可用格式
yt-dlp --cookies-from-browser chrome -F "VIDEO_URL"

# 下载字幕
yt-dlp --cookies-from-browser chrome --write-auto-sub --write-sub --sub-lang zh-Hans,en --skip-download "VIDEO_URL"

# 下载整个播放列表
yt-dlp --cookies-from-browser chrome -o "~/Downloads/%(playlist_title)s/%(title)s.%(ext)s" "PLAYLIST_URL"
```
