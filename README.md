# yt-search-download

YouTube 视频搜索、下载、字幕提取工具 — Claude Code Skill

基于 YouTube Data API v3 进行高级搜索，配合 yt-dlp 下载视频/音频/字幕，自动翻译英文标题为中文。

## 功能

- **搜索**：全站关键词搜索，支持按时间 / 播放量 / 相关度排序
- **频道浏览**：浏览指定频道最新视频，支持频道内关键词搜索
- **下载视频**：支持多种画质（最高 4K），指定保存目录
- **提取音频**：一键下载 MP3
- **下载字幕**：自动生成 SRT（带时间轴）+ TXT（供 AI 总结），支持中英双语
- **中文翻译**：搜索结果为英文时自动附加中文译名，无需额外操作
- **视频详情**：查询时长、播放量、简介等元数据

## 安装

```bash
npx skills add joeseesun/yt-search-download
```

## 前置条件

1. **YouTube API Key**：[Google Cloud Console](https://console.cloud.google.com/) → 启用 YouTube Data API v3 → 创建 API Key
   ```bash
   export YT_BROWSE_API_KEY=your_key   # 写入 ~/.zshrc
   ```

2. **yt-dlp**（下载 / 字幕用）：
   ```bash
   brew install yt-dlp   # macOS
   pip install yt-dlp     # 或 pip
   ```

## 使用场景

在 Claude Code 中直接用自然语言描述需求，无需记命令：

### 🔍 搜索视频

```
"搜索 Lex Fridman 最近更新的 YouTube"
"YouTube 上有什么关于 Claude 4 的最新视频"
"找 Andrej Karpathy 频道的视频，按播放量排序"
"搜索 AI agent 相关视频，最近一个月发布的"
```

搜索结果示例（英文自动附中文译名）：
```
1  Rick Beato: Greatest Guitarists of All Time
   【译】里克·贝阿托：史上最伟大的吉他手、音乐史与创作秘密
   2026-03-01  2h34m  301.9K

2  State of AI in 2026: LLMs, Coding, Scaling Laws
   【译】2026年AI现状：大模型、编程、Scaling法则与中国AI
   2026-01-31  4h25m  741.7K
```

### 📺 浏览频道

```
"看看 Lex Fridman 最近发了什么视频"
"浏览 @karpathy 的频道，找讲 GPT 的视频"
"查看 3Blue1Brown 最新上传"
```

### ⬇️ 下载视频

```
"下载这个视频 https://youtube.com/watch?v=..."
"把这个视频下载到桌面，要 1080p"
"下载 Lex Fridman 和 Sam Altman 的那期播客"
```

### 🎵 提取音频

```
"提取这个视频的音频"
"YouTube 转 MP3，只要音频"
"下载播客音频 https://youtube.com/watch?v=..."
```

### 📝 下载字幕（SRT + TXT）

字幕下载**自动生成两个文件**：
- `.srt`：带时间轴，适合视频剪辑、精准定位
- `.txt`：保留时间戳，适合交给 AI 总结归纳

```
"下载这个视频的字幕 https://youtube.com/watch?v=..."
"提取 Lex Fridman 这期节目的英文字幕"
"获取视频文本，我要交给 AI 总结"
"下载中文字幕"
```

TXT 格式示例（保留时间戳，AI 可引用具体时间点）：
```
00:00:01,000 --> 00:00:04,000
Welcome to the Lex Fridman podcast.

00:00:05,000 --> 00:00:09,000
Today we're talking about the greatest guitarists of all time.
```

### 🔄 典型工作流

**① 找频道最新视频并下载字幕：**
1. "看看 Lex Fridman 最近更新了什么"
2. 选择感兴趣的视频
3. "下载第2个视频的字幕"
4. 得到 `.srt` + `.txt`，丢给 Claude 总结

**② 搜索 + 筛选 + 下载：**
1. "搜索 AI safety 相关视频，最近半年，按播放量排序"
2. "下载播放量最高那个"

**③ 批量提取播客音频：**
1. "搜索 Lex Fridman 播客最新5期"
2. "把第1、3期的音频都下载下来"

## 命令行用法

```bash
# 全站搜索
python3 scripts/yt_search.py search "关键词" -n 20 -o date

# 浏览频道（最新视频）
python3 scripts/yt_search.py channel @lexfridman -n 10

# 频道内搜索
python3 scripts/yt_search.py channel @karpathy -q "GPT"

# 下载视频
python3 scripts/yt_search.py download "VIDEO_URL" -q 1080p

# 仅下载音频（MP3）
python3 scripts/yt_search.py download "VIDEO_URL" --audio-only

# 下载字幕（SRT + TXT）
yt-dlp --cookies-from-browser chrome \
  --write-auto-sub --write-sub \
  --sub-lang en,zh-Hans \
  --convert-subs srt \
  --skip-download \
  -o "~/Downloads/%(title)s.%(ext)s" \
  "VIDEO_URL"

# 视频详情
python3 scripts/yt_search.py info "VIDEO_URL"
```

## 搜索参数

| 参数 | 说明 |
|------|------|
| `-n 20` | 最多返回条数（默认 20） |
| `-o date` | 按时间排序 |
| `-o viewCount` | 按播放量排序 |
| `-o relevance` | 按相关度排序（默认） |
| `--after 2025-01-01` | 发布时间起 |
| `--before 2025-12-31` | 发布时间止 |
| `-c @handle` | 限定频道搜索 |
| `-d` | 显示视频简介 |

## License

MIT

## 📱 关注作者

如果这个项目对你有帮助，欢迎关注我获取更多技术分享：

- **X (Twitter)**: [@vista8](https://x.com/vista8)
- **微信公众号「向阳乔木推荐看」**:

<p align="center">
  <img src="https://github.com/joeseesun/terminal-boost/raw/main/assets/wechat-qr.jpg?raw=true" alt="向阳乔木推荐看公众号二维码" width="300">
</p>
