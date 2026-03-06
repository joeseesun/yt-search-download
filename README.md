# yt-search-download

YouTube 视频搜索与下载工具 — Claude Code Skill

基于 YouTube Data API v3 进行高级搜索，配合 yt-dlp 下载视频/音频。

## 功能

- 全站关键词搜索，支持按时间/播放量/相关度排序
- 指定频道浏览最新视频
- 频道内关键词搜索
- 下载视频（支持多种画质）
- 提取音频（MP3）
- 查询视频详情

## 安装

```bash
npx skills add joeseesun/yt-search-download
```

## 前置条件

1. **YouTube API Key**：[Google Cloud Console](https://console.cloud.google.com/) → 启用 YouTube Data API v3 → 创建 API Key
   ```bash
   export YT_BROWSE_API_KEY=your_key
   ```

2. **yt-dlp**（下载用）：
   ```bash
   brew install yt-dlp   # macOS
   pip install yt-dlp     # 或 pip
   ```

## 使用示例

在 Claude Code 中直接用自然语言：

- "搜索 Andrej Karpathy 频道最新视频"
- "搜索 Claude 3.5 相关视频，按播放量排序"
- "下载这个视频 https://youtube.com/watch?v=..."
- "提取这个视频的音频"

## 命令行用法

```bash
# 全站搜索
python3 scripts/yt_search.py search "关键词" -n 20

# 浏览频道
python3 scripts/yt_search.py channel @karpathy -n 10

# 下载视频
python3 scripts/yt_search.py download "VIDEO_URL" -q 1080p

# 仅下载音频
python3 scripts/yt_search.py download "VIDEO_URL" --audio-only

# 视频详情
python3 scripts/yt_search.py info "VIDEO_URL"
```

## 输出格式

```
#    标题                                                    频道                 日期         时长       播放量
------------------------------------------------------------------------------------------------------------------------
1    The spelled-out intro to neural networks and back...   Andrej Karpathy      2022-10-05   3h55m16s   3.7M
2    Let's build GPT: from scratch, in code, spelled out   Andrej Karpathy      2023-01-17   1h56m27s   2.1M
```

## License

MIT

## 📱 关注作者

如果这个项目对你有帮助，欢迎关注我获取更多技术分享：

- **X (Twitter)**: [@vista8](https://x.com/vista8)
- **微信公众号「向阳乔木推荐看」**:

<p align="center">
  <img src="https://github.com/joeseesun/terminal-boost/raw/main/assets/wechat-qr.jpg?raw=true" alt="向阳乔木推荐看公众号二维码" width="300">
</p>
