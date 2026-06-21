# Vid2Text 产品需求文档

## 1. 项目概述

Vid2Text 是一个 CLI 工具，输入 B站视频链接，输出纯文本转写结果。专为 AI Agent 调用设计，追求一行命令完成全流程。

### 设计原则

- **一行命令**：`vid2text <url>`，无前置配置
- **最小依赖**：核心依赖：1 个 pip 包（click）+ 预编译 C 二进制
- **可打包**：打包为独立 exe，内嵌 ffmpeg，用户零环境依赖
- **单平台优先**：M0 仅支持 B站，架构预留平台扩展点

### 技术选型

| 环节 | 选型 | 理由 |
|------|------|------|
| 音频下载 | B站 API 直连 | 绕过 yt-dlp 的 WAF 412 拦截 |
| 音频转码 | ffmpeg | m4a → 16kHz 单声道 WAV |
| 语音识别 | SenseVoice.cpp GGUF (Q4_K 量化，Metal/CUDA 加速) |
| 模型获取 | ModelScope snapshot_download | 首次自动拉取，后续读本地 |
| CLI 框架 | click | 轻量、参数解析清晰 |

### 目标用户

AI Agent（如 Claude、TRAE）和开发者。

### 输出契约

输出为**纯文本，带标点**。无时间戳、无元信息、无分段结构。

程序始终输出到 STDOUT。同时自动写入文本缓存——同一视频下次运行时命中缓存，直接输出，跳过 ASR 推理。

### 配置

`~/.vid2text/config.json` 是技能级全局配置文件，首次运行自动生成。每次启动时读取，读取失败使用内置默认值。当前仅含缓存相关配置，未来可扩展（模型选择、线程数等）。

```json
{
  "cache": {
    "max_age_days": 30,
    "max_total_mb": 500
  }
}
```

---

## 2. 用户故事与用例

### Agent 一键调用

Agent 拿到 B站视频链接后，一行命令完成转写：

```
vid2text https://www.bilibili.com/video/BV1wDEK6MEM2
```

Agent 从 STDOUT 读取完整转写文本，自行生成摘要或 Markdown 笔记。

### 首次运行自动下载模型

模型已内嵌于 .skill 产物中（174MB GGUF），无需额外下载。

### 缓存命中

同一视频第二次转写时，检测到本地已有该 BV 号的转写结果，直接返回缓存文本。跳过下载和 ASR 推理，毫秒级返回。

`--no-cache` 彻底重跑（重新下载 + 重新推理）。

### 错误处理

| 场景 | 行为 |
|------|------|
| 无效链接 | 退出码 1，STDERR 输出原因 |
| 网络失败（下载/模型拉取） | 退出码 2，STDERR 说明失败阶段 |
| ASR 异常（模型损坏/内存不足） | 退出码 2，STDERR 输出诊断，不输出空文件 |

### 长视频

不设时长上限。

---

## 3. 命令行接口设计

```
vid2text <url|bvid> [--no-cache]
vid2text cache list
vid2text cache clear
```

### `vid2text <url|bvid>`

位置参数 `url|bvid`：完整链接或纯 BV 号。内部正则提取。

`--no-cache`：彻底重跑，重新下载和推理。

### `vid2text cache list`

列出所有缓存条目：输出 `index.json` 中记录的视频 ID、音频哈希和文本哈希。

### `vid2text cache clear`

清空 `objects/` 目录下所有文件并将 `index.json` 重置为 `{}`。模型文件不受影响（由 ModelScope 管理）。

### 退出码

| 退出码 | 含义 | Agent 处置 |
|--------|------|------------|
| 0 | 成功 | 读取 STDOUT |
| 1 | 用户错误 | 修正输入后重试 |
| 2 | 系统错误 | 检查环境或报用户 |

### STDERR / STDOUT

- **STDOUT**：仅纯文本，Agent 无需过滤
- **STDERR**：进度信息和错误诊断

### --help

```
$ vid2text --help
Usage: vid2text [OPTIONS] COMMAND [ARGS]...

  从 B站视频链接提取音频并转写为纯文本。

Commands:
  cache  缓存管理

Options:
  --no-cache         彻底重跑：重新下载、重新推理
  --help             Show this message and exit.
```

---

## 4. 技术流水线

### 总览

```
URL → 提取 BV 号 → 下载(m4a) → ffmpeg(WAV 16kHz) → VAD → ASR → 标点 → 输出纯文本
```

### 下载：B站 API 直连

不使用 yt-dlp。两步 API 调用：

1. `GET https://api.bilibili.com/x/web-interface/view?bvid={bvid}` → 获取 `cid`
2. `GET https://api.bilibili.com/x/player/playurl?bvid={bvid}&cid={cid}&qn=0&fnval=4048&fourk=1` → 获取 `data.dash.audio[0].baseUrl`
3. HTTP GET 下载 m4a 到本地缓存

请求头：`User-Agent`（模拟 Chrome）+ `Referer: https://www.bilibili.com/`。

### 转码：ffmpeg

```bash
ffmpeg -y -i input.m4a -vn -ar 16000 -ac 1 -f wav output.wav
```

打包时 ffmpeg 内嵌，通过 `sys._MEIPASS` 解析路径。

### ASR：SenseVoice.cpp GGUF

SenseVoice.cpp 是 [SenseVoice](https://github.com/FunAudioLLM/SenseVoice) 模型的 C++ 移植版，基于 [ggml](https://github.com/ggerganov/ggml) 推理框架。本项目通过 subprocess 调用预编译的 C 二进制完成推理，实现零 Python 深度学习依赖。

| 属性 | 值 |
|------|-----|
| 推理框架 | ggml（不依赖 ONNX Runtime / PyTorch） |
| 模型格式 | GGUF Q4_K 量化 |
| 模型大小 | 174MB |
| 加速 | Metal（Apple）、CUDA（Nvidia）、BLAS（CPU fallback） |

推理流程：

1. Python 通过 `subprocess.run` 调用 `bin/{arch}/sense-voice` 二进制
2. 二进制内嵌 VAD + ASR 推理
3. STDERR 输出日志，STDOUT 输出带时间戳的文本（如 `[0.54-3.78] 文本内容。`）
4. Python 解析 STDOUT，剥离时间戳，返回纯文本

```
subprocess.run(["sense-voice", "-m", "model.gguf", "-t", "4", "-l", "auto", "-itn", "audio.wav"])
```

参数说明：
- `-m`：GGUF 模型路径
- `-t`：解码线程数（默认 4）
- `-l`：语音代码，`auto` 为自动检测
- `-itn`：启用逆文本正则化（含标点恢复）

---

## 5. 缓存

采用 git 式内容寻址：所有缓存文件按内容 SHA256 哈希命名，一个 `index.json` 维护视频 ID 到缓存文件的映射。

### 缓存目录

```
~/.vid2text/cache/
├── objects/
│   ├── {sha256[:2]}/{sha256[2:]}.m4a    # 音频，按内容哈希
│   └── {sha256[:2]}/{sha256[2:]}.txt    # 文本（转写结果），按音频内容哈希
└── index.json                            # 映射表
```

### index.json

记录视频 ID → 音频哈希 → 文本哈希的映射。首次运行自动生成空表。

```json
{
  "bilibili:BV1wDEK6MEM2": {
    "audio": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6...",
    "text": { "paraformer": "d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2..." }
  }
}
```

每次转写完成后更新 `index.json` 写入新条目。重复转写同一视频时，先查 index → 找到文本哈希 → 读 `objects/` → 命中则跳过 ASR，直接输出。

### 淘汰策略

按**时间和空间**双维度自动淘汰，通过 `config.json` 控制：

| 维度 | 时机 | 行为 |
|------|------|------|
| 时间 | 读取时 | 超过 `max_age_days` → 视为未命中，从 `index.json` 删除条目 |
| 空间 | 写入后 | 若 `objects/` 总大小超过 `max_total_mb`，从 `index.json` 最旧条目开始逐个删除，直到总量 ≤ `max_total_mb`。极端情况下（仅当前文件就超限）不做进一步处理，当前文件保留 |

两类缓存（音频和文本）统一管理，不再分开计数。淘汰时同时删除 `objects/` 文件并清理 `index.json`。

淘汰参数由 `config.json` 中 `cache` 段控制（详见第 1 节配置）。

`--no-cache` 彻底重跑：重新下载、重新推理，不读缓存也不写缓存。缓存读写失败静默降级。

### 模型文件

由 ModelScope 管理，路径 `~/.cache/modelscope/hub/models/iic/`，vid2text 不干预。

---

## 6. 依赖与打包

### Python 依赖

```
click>=8.1            # CLI
```

仅 `click` 一个 Python 包。其余依赖为：
- 预编译 C 二进制（~300KB，内嵌于 `.skill`）
- GGUF 模型（~174MB，内嵌于 `.skill`）
- 系统 ffmpeg（音频转码）



### 系统依赖

| 依赖 | 处理 |
|------|------|
| ffmpeg | PyInstaller `--add-binary` 内嵌 |
| 模型文件 (174MB GGUF，内嵌) | 内嵌于 .skill 产物 |

### 打包方案：PyInstaller

```bash
pyinstaller
  --onefile
  --name vid2text
  --add-binary "ffmpeg.exe;."
  --collect-all funasr_onnx
  --collect-all modelscope
  --hidden-import funasr_onnx.paraformer_bin
  --hidden-import funasr_onnx.vad_bin
  --hidden-import funasr_onnx.punc_bin
  --hidden-import onnxruntime
  vid2text/cli.py
```

### exe 体积

| 组件 | 大小 |
|------|------|
| Python + 依赖 | ~60MB |
| ffmpeg.exe | ~80MB |
| **合计** | **~140MB** |

### 安装方式

- **开发**：`pip install -e .`
- **发行**：GitHub Releases 下载 `vid2text.exe`

---

## 7. 扩展点

### 平台下载器分派

一个映射表，不引入抽象基类：

```python
_DOWNLOADERS = {
    "bilibili": _download_bilibili,
}

def download(url: str, output_dir: Path) -> Path:
    for keyword, handler in _DOWNLOADERS.items():
        if keyword in url:
            return handler(url, output_dir)
    raise UnsupportedPlatformError(f"不支持的平台: {url}")
```

### 新增平台

两步，不修改流水线其余模块：

1. 写 `_download_youtube(url, output_dir) -> Path`
2. 注册 `"youtube.com": _download_youtube`

下载器契约：输入 URL + 输出目录 → 返回音频文件路径。失败抛异常。

### 模型切换

替换 recognizer 模块的加载和推理逻辑即可。`index.json` 中 `text` 字段按模型别名分槽（`{"paraformer": "hash..."}`），不同模型互不污染。

---

## 8. 不做的事

- **翻译** — Agent 下游任务
- **摘要/笔记生成** — Agent 下游任务
- **视频画面** — 不下载画面、封面、OCR
- **字幕文件** — 不生成 SRT/VTT，只有纯文本
- **GUI** — 纯 CLI

---

## 9. 开发计划

### M0 目标

输出纯文本，可打包为独立 exe。

### 任务拆解

| # | 模块 | 内容 |
|---|------|------|
| 1 | 下载 | B站 API 两步调用，音频存缓存 |
| 2 | 转码 | ffmpeg m4a → 16kHz WAV，已是 WAV 则跳过 |
| 3 | ASR | 集成 SenseVoice.cpp GGUF 推理（subprocess 调用 C 二进制） |
| 4 | 缓存 | git 式内容寻址（objects/ + index.json）、config.json、时/空淘汰 |
| 5 | CLI | click 参数解析、`cache list/clear` 子命令、退出码映射 |
| 6 | 打包 | PyInstaller + 内嵌 ffmpeg |

### 验收标准

1. 完整链接和纯 BV 号均可正常运行，纯文本输出到 STDOUT
2. 无效链接退出码 1，系统错误退出码 2
3. 二次转写命中缓存，不重复下载和推理
4. `vid2text.exe` 在无 Python 的 Windows 上独立运行
