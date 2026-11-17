---
name: youtube-clipper
description: >-
  多平台视频与实时直播智能剪辑工具 (支持 YouTube, Twitch, Kick)。支持两种工作模式：
  1. 录播/视频章节精细剪辑：AI 拆解 2-5 分钟独立话题章节、用户点选片段、双语字幕烧录与总结文案生成；
  2. 实时直播盯盘与爆款猎手 (Live Hype Hunter)：持续挂机监听直播流与弹幕聊天室，根据弹幕喷涌速率 (Chat Velocity Spike) 与高潮词 (KEKW/LMAO/W/L/💀/WTF/CLIP) 自动截取 30 秒高光切片，结合音频爆发与台词 Hook 智能计算爆款指数 (Viral Score 0-100%) 并给出排名及发布文案。
  使用场景：当用户需要剪辑 YouTube / Twitch / Kick 视频、录制/切片直播流片段、实时监控直播抓取爆款热点、制作双语字幕版本时。
  关键词：视频剪辑、直播剪辑、直播盯盘、弹幕高潮检测、爆款切片、YouTube、Twitch、Kick、Live Stream、Hype Detector、Viral Clipper、字幕翻译、双语字幕、Whisper转录、clip video
---

# 视频与直播流智能剪辑工具 (YouTube / Twitch / Kick)

支持 YouTube (视频/直播/Shorts)、Twitch (直播/VOD/Clips)、Kick (直播/VOD/Clips)。内置 Faster-Whisper 语音转录与实时聊天室热度分析引擎。

---

## 模式选择

本工具有两大工作模式，根据用户指令自动选择：

* **模式 A: 常规视频 / 录播智能精细剪辑 (VOD / Full Video Mode)**
  * 针对已完结的视频或录播。
  * 下载视频与字幕（若无字幕自动使用 Whisper 本地转录）。
  * AI 细粒度分析 2-5 分钟章节，用户挑选心仪段落，制作中英双语硬字幕与摘要。

* **模式 B: 实时直播盯盘与爆款猎手 (Live Stream Hype Hunter Mode)**
  * 针对正在直播的房间（YouTube Live / Twitch / Kick）。
  * 持续挂机录制直播流，后台匿名接入实时弹幕（Twitch IRC / Kick Pusher / YouTube Live Chat）。
  * 实时计算弹幕涌入速率（Messages/sec）与情绪浓度（`KEKW`, `LMAO`, `W`, `L`, `💀`, `WTF`, `CLIP IT` 等）。
  * 当热度突破自适应基线（如 2.2 倍爆发）时，自动触发 30 秒高能片段保存。
  * 盯盘结束时，结合音频音量暴增（尖叫/欢呼）与 Whisper 台词 Hook，综合计算 0-100% **爆款潜力指数 (Viral Score %)**，生成排行榜与发帖标题建议！

---

## 模式 B 执行指南 (实时直播盯盘与爆款猎手)

当用户说 *"盯盘这个直播间"*, *"监控直播并根据弹幕高潮剪 30 秒切片"*, *"找出最可能爆款的片段"* 时：

1. **调用 `hype_monitor.py` 脚本**:
   ```bash
   # 监控直播 10 分钟 (600秒)，每段切片 30 秒
   python scripts/hype_monitor.py <live_url> --duration 600 --clip-len 30

   # 调整敏感度 (例如 2.0 倍弹幕暴增即触发)
   python scripts/hype_monitor.py <live_url> --duration 1200 --sensitivity 2.0
   ```

2. **自动执行流程**:
   - 后台无损拉取直播音视频流
   - 实时挂接 Twitch IRC / Kick Pusher / YouTube 聊天流
   - 动态更新自适应弹幕基线（EMA），精准过滤平缓对话，捕捉突发爆点
   - 命中高潮时自动截取 `[Peak-15s, Peak+15s]`
   - 调用 Faster-Whisper 自动转录高潮时主播的反应与台词
   - 调用 `viral_scorer.py` 评估爆款指数，生成 `VIRAL_RANKING_REPORT.md`

3. **向用户展示**:
   - 捕获到的高光总数与时长
   - 爆款排行榜（Top 3 附带推荐短视频标题与标签）
   - 用户可指定片段一键烧录双语字幕

---

## 模式 A 工作流程 (常规视频 / 录播章节剪辑)

你将按照以下 6 个阶段执行视频/录播剪辑任务：

### 阶段 1: 环境检测

**目标**: 确保所有必需工具和依赖都已安装

1. 检测 yt-dlp 是否可用
   ```bash
   yt-dlp --version
   ```

2. 检测 FFmpeg 版本和 libass 支持
   ```bash
   ffmpeg -version
   # 验证 libass 支持（字幕烧录必需）
   ffmpeg -filters 2>&1 | grep subtitles
   ```

3. 检测 Python 依赖 (含 Faster-Whisper 与 Kick 支持)
   ```bash
   python -c "import yt_dlp, pysrt, faster_whisper, curl_cffi; print('✅ All dependencies available')"
   ```

**如果环境检测失败**:
- yt-dlp 未安装: 提示 `pip install yt-dlp`
- FFmpeg 无 libass: 提示安装带 libass 的 FFmpeg
- Python 依赖缺失: 提示 `pip install yt-dlp pysrt python-dotenv faster-whisper curl_cffi`

---

### 阶段 2: 下载视频或捕获直播流

**目标**: 下载视频或录制实时直播流片段，并获取/生成字幕

1. 询问用户媒体 URL (支持 YouTube, Twitch, Kick)
   - 若为正在进行的直播流：询问用户想要录制/捕获的时长（例如录制 3 分钟，即 `--duration 180`，默认 300 秒）
   - 若为 YouTube 直播流：可询问是否启用 `--live-from-start` 从直播开头抓取

2. 调用 `download_video.py` 脚本
   ```bash
   # 常规视频或录播 (VOD)
   python scripts/download_video.py <url>

   # 正在进行的直播流 (如 Twitch / Kick / YouTube Live，录制 300 秒)
   python scripts/download_video.py <live_url> --duration 300

   # YouTube 直播流 (从头开始抓取 DVR)
   python scripts/download_video.py <youtube_live_url> --live-from-start
   ```

3. 脚本会自动：
   - 自动识别平台（YouTube / Twitch / Kick）与媒体类型（Live / VOD / Clip）
   - 下载视频或录制指定时长的直播流
   - 尝试下载官方字幕（如有）
   - **智能语音转录**: 若平台无字幕（如 Twitch/Kick/未附带字幕的直播），自动调用 Faster-Whisper 本地模型生成高质量 SRT 字幕！
   - 输出视频和字幕文件路径

4. 向用户展示：
   - 媒体标题、所属平台与状态（直播 / 录播）
   - 时长与文件大小
   - 视频及字幕下载路径

**输出**:
- 视频文件: `<id>.mp4`
- 字幕文件: `<id>.srt` 或 `<id>.vtt`

---

### 阶段 3: 分析章节（核心差异化功能）

**目标**: 使用 AI 分析字幕内容，生成精细章节（2-5 分钟级别）

1. 调用 analyze_subtitles.py 解析字幕 (支持 VTT 与 SRT 格式)
   ```bash
   python scripts/analyze_subtitles.py <subtitle_path>
   ```

2. 脚本会输出结构化字幕数据：
   - 完整字幕文本（带时间戳）
   - 总时长
   - 字幕条数

3. **你需要执行 AI 分析**（这是最关键的步骤）：
   - 阅读完整字幕内容
   - 理解内容语义和主题转换点
   - 识别自然的话题切换位置
   - 生成 2-5 分钟粒度的章节（避免半小时粗粒度切分）

4. 为每个章节生成：
   - **标题**: 精炼的主题概括（10-20 字）
   - **时间范围**: 起始和结束时间（格式: MM:SS 或 HH:MM:SS）
   - **核心摘要**: 1-2 句话说明这段讲了什么（50-100 字）
   - **关键词**: 3-5 个核心概念词

5. **章节生成原则**：
   - 粒度：每个章节 2-5 分钟（避免太短或太长）
   - 完整性：确保所有视频内容都被覆盖，无遗漏
   - 有意义：每个章节是一个相对独立的话题
   - 自然切分：在主题转换点切分，不要机械地按时间切

6. 向用户展示章节列表：
   ```
   📊 分析完成，生成 X 个章节：

   1. [00:00 - 03:15] AGI 不是时间点，是指数曲线
      核心: AI 模型能力每 4-12 月翻倍，工程师已用 Claude 写代码
      关键词: AGI、指数增长、Claude Code

   2. [03:15 - 06:30] 中国在 AI 上的差距
      核心: 芯片禁运卡住中国，DeepSeek benchmark 优化不代表实力
      关键词: 中国、芯片禁运、DeepSeek

   ... (所有章节)

   ✓ 所有内容已覆盖，无遗漏
   ```

---

### 阶段 4: 用户选择

**目标**: 让用户选择要剪辑的章节和处理选项

1. 使用 AskUserQuestion 工具让用户选择章节
   - 提供章节编号供用户选择
   - 支持多选（可以选择多个章节）

2. 询问处理选项：
   - 是否生成双语字幕？（英文 + 中文）
   - 是否烧录字幕到视频？（硬字幕）
   - 是否生成总结文案？

3. 确认用户选择并展示处理计划

---

### 阶段 5: 剪辑处理（核心执行阶段）

**目标**: 并行执行多个处理任务

对于每个用户选择的章节，执行以下步骤：

#### 5.1 剪辑视频片段
```bash
python scripts/clip_video.py <video_path> <start_time> <end_time> <output_path>
```
- 使用 FFmpeg 精确剪辑
- 保持原始视频质量
- 输出: `<章节标题>_clip.mp4`

#### 5.2 提取字幕片段
- 从完整字幕中过滤出该时间段的字幕
- 调整时间戳（减去起始时间，从 00:00:00 开始）
- 转换为 SRT 格式
- 输出: `<章节标题>_original.srt`

#### 5.3 翻译字幕（如果用户选择）
```bash
python scripts/translate_subtitles.py <subtitle_path>
```
- **批量翻译优化**: 每批 20 条字幕一起翻译（节省 95% API 调用）
- 翻译策略：
  - 保持技术术语的准确性
  - 口语化表达（适合短视频）
  - 简洁流畅（避免冗长）
- 输出: `<章节标题>_translated.srt`

#### 5.4 生成双语字幕文件（如果用户选择）
- 合并英文和中文字幕
- 格式: SRT 双语（每条字幕包含英文和中文）
- 样式: 英文在上，中文在下
- 输出: `<章节标题>_bilingual.srt`

#### 5.5 烧录字幕到视频（如果用户选择）
```bash
python scripts/burn_subtitles.py <video_path> <subtitle_path> <output_path>
```
- 使用 ffmpeg-full（libass 支持）
- **使用临时目录解决路径空格问题**（关键！）
- 字幕样式：
  - 字体大小: 24
  - 底部边距: 30
  - 颜色: 白色文字 + 黑色描边
- 输出: `<章节标题>_with_subtitles.mp4`

#### 5.6 生成总结文案（如果用户选择）
```bash
python scripts/generate_summary.py <chapter_info>
```
- 基于章节标题、摘要和关键词
- 生成适合社交媒体的文案
- 包含: 标题、核心观点、适合平台（小红书、抖音等）
- 输出: `<章节标题>_summary.md`

**进度展示**:
```
🎬 开始处理章节 1/3: AGI 不是时间点，是指数曲线

1/6 剪辑视频片段... ✅
2/6 提取字幕片段... ✅
3/6 翻译字幕为中文... [=====>    ] 50% (26/52)
4/6 生成双语字幕文件... ✅
5/6 烧录字幕到视频... ✅
6/6 生成总结文案... ✅

✨ 章节 1 处理完成
```

---

### 阶段 6: 输出结果

**目标**: 组织输出文件并展示给用户

1. 创建输出目录
   ```
   ./youtube-clips/<日期时间>/
   ```
   输出目录位于当前工作目录下

2. 组织文件结构：
   ```
   <章节标题>/
   ├── <章节标题>_clip.mp4              # 原始剪辑（无字幕）
   ├── <章节标题>_with_subtitles.mp4   # 烧录字幕版本
   ├── <章节标题>_bilingual.srt        # 双语字幕文件
   └── <章节标题>_summary.md           # 总结文案
   ```

3. 向用户展示：
   - 输出目录路径
   - 文件列表（带文件大小）
   - 快速预览命令

   ```
   ✨ 处理完成！

   📁 输出目录: ./youtube-clips/20260121_143022/

   文件列表:
     🎬 AGI_指数曲线_双语硬字幕.mp4 (14 MB)
     📄 AGI_指数曲线_双语字幕.srt (2.3 KB)
     📝 AGI_指数曲线_总结.md (3.2 KB)

   快速预览:
   open ./youtube-clips/20260121_143022/AGI_指数曲线_双语硬字幕.mp4
   ```

4. 询问是否继续剪辑其他章节
   - 如果是，返回阶段 4（用户选择）
   - 如果否，结束 Skill

---

## 关键技术点

### 1. FFmpeg 路径空格问题
**问题**: FFmpeg subtitles 滤镜无法正确解析包含空格的路径

**解决方案**: burn_subtitles.py 使用临时目录
- 创建无空格临时目录
- 复制文件到临时目录
- 执行 FFmpeg
- 移动输出文件回目标位置

### 2. 批量翻译优化
**问题**: 逐条翻译会产生大量 API 调用

**解决方案**: 每批 20 条字幕一起翻译
- 节省 95% API 调用
- 提高翻译速度
- 保持翻译一致性

### 3. 章节分析精细度
**目标**: 生成 2-5 分钟粒度的章节，避免半小时粗粒度

**方法**:
- 理解字幕语义，识别主题转换
- 寻找自然的话题切换点
- 确保每个章节有完整的论述
- 避免机械按时间切分

### 4. FFmpeg vs ffmpeg-full
**区别**:
- 标准 FFmpeg: 无 libass 支持，无法烧录字幕
- ffmpeg-full: 包含 libass，支持字幕烧录

**路径**:
- 标准: `/opt/homebrew/bin/ffmpeg`
- ffmpeg-full: `/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg` (Apple Silicon)

---

## 错误处理

### 环境问题
- 缺少工具 → 提示安装命令
- FFmpeg 无 libass → 引导安装 ffmpeg-full
- Python 依赖缺失 → 提示 pip install

### 下载问题
- 无效 URL → 提示检查 URL 格式
- 字幕缺失 → 尝试自动字幕
- 网络错误 → 提示重试

### 处理问题
- FFmpeg 执行失败 → 显示详细错误信息
- 翻译失败 → 重试机制（最多 3 次）
- 磁盘空间不足 → 提示清理空间

---

## 输出文件命名规范

- 视频片段: `<章节标题>_clip.mp4`
- 字幕文件: `<章节标题>_bilingual.srt`
- 烧录版本: `<章节标题>_with_subtitles.mp4`
- 总结文案: `<章节标题>_summary.md`

**文件名处理**:
- 移除特殊字符（`/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `|`）
- 空格替换为下划线
- 限制长度（最多 100 字符）

---

## 用户体验要点

1. **进度可见**: 每个步骤都展示进度和状态
2. **错误友好**: 清晰的错误信息和解决方案
3. **可控性**: 用户选择要剪辑的章节和处理选项
4. **高质量**: 章节分析有意义，翻译准确流畅
5. **完整性**: 提供原始和处理后的多个版本

---

## 开始执行

当用户触发这个 Skill 时：
1. 立即开始阶段 1（环境检测）
2. 按照 6 个阶段顺序执行
3. 每个阶段完成后自动进入下一阶段
4. 遇到问题时提供清晰的解决方案
5. 最后展示完整的输出结果

记住：这个 Skill 的核心价值在于 **AI 精细章节分析** 和 **无缝的技术处理**，让用户能快速从长视频中提取高质量的短视频片段。
