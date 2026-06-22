# Vid2Text 开发文档

## 1. 项目总览

Vid2Text 从 B站视频链接提取音频，经 ONNX 语音识别输出纯文本转写结果。

### 完整流水线

```mermaid
flowchart LR
    A[URL / BVID] --> B[下载模块]
    B --> C[m4a 音频]
    C --> D[转码模块]
    D --> E[WAV 16kHz 单声道]
    E --> F[ASR 模块]
    F --> G[VAD 切分]
    G --> H[Paraformer 推理]
    H --> I[CT-Transformer 标点]
    I --> J[STDOUT]
```

### 技术栈

| 层 | 技术 |
|----|------|
| 音频下载 | urllib + B站 Web API（`x/web-interface/view`、`x/player/playurl`） |
| 音频转码 | PyAV（`av` 库） |
| 语音识别 | SenseVoice.cpp GGUF (Q4_K) + C 二进制 subprocess 调用 |
| CLI 框架 | click |
| 打包 | build_skill.py 生成 .skill zip 产物 |

### 项目目录结构

```
vid2text/
├── __init__.py
├── cli.py              # CLI 入口（click）
├── downloader.py       # B站 API 直连下载
├── transcoder.py       # PyAV 转码
├── asr.py              # SenseVoice.cpp 推理（subprocess 调用 C 二进制）
└── errors.py           # 异常类型定义
```

---

## 2. 模块架构

### 模块依赖关系

```mermaid
flowchart TD
    cli[cli.py] --> downloader[downloader.py]
    cli --> transcoder[transcoder.py]
    cli --> asr[asr.py]
```

### 各模块职责

| 模块 | 文件 | 职责 | 输入 | 输出 |
|------|------|------|------|------|
| CLI 入口 | `cli.py` | 参数解析、流程编排、退出码 | 命令行参数 | STDOUT / 退出码 |
| 下载 | `downloader.py` | B站 API 直连下载 m4a | URL 或 BVID | 本地 m4a 文件路径 |
| 转码 | `transcoder.py` | PyAV m4a → WAV | m4a 路径 | 16kHz 单声道 WAV 路径 |
| ASR | `asr.py` | 模型加载、SenseVoiceSmall 推理（内置标点） | WAV 路径 | 纯文本字符串 |

### 数据流

```mermaid
flowchart LR
    A[parse args] --> B[download]
    B --> C[m4a]
    C --> D[transcode]
    D --> E[wav]
    E --> F[ASR: VAD + Paraformer + Punc]
    F --> G[文本]
    G --> H[STDOUT]
```

### 进程模型

单进程、同步执行。不使用线程或 async。流水线各阶段按序执行，前一步完成才进入下一步。

### 入口文件

`vid2text/cli.py` 中的 `main_entry()` 函数是唯一入口。`pyproject.toml` 注册为 `vid2text` 控制台脚本。

```toml
[project.scripts]
vid2text = "vid2text.cli:main_entry"
```

---

### 错误类型

所有错误继承基类，通过 `exit_code` 属性控制进程退出码。CLI 层捕获后取 `exit_code` 作为退出码，`str(e)` 输出到 STDERR。

| 错误类型 | 基类 | exit_code | 触发条件 |
|----------|------|-----------|----------|
| `UserError` | `Vid2TextError` | 1 | 无效链接、不含可识别的 BV 号 |
| `NetworkError` | `Vid2TextError` | 2 | B站 API 请求失败、音频下载失败 |
| `TranscodeError` | `Vid2TextError` | 2 | 转码失败 |
| `ModelError` | `Vid2TextError` | 2 | 模型文件损坏、推理异常 |

---

## 3. 下载模块

`downloader.py` 负责从 B站 API 获取音频直链并下载到本地。

### API 调用流程

```mermaid
sequenceDiagram
    participant CLI
    participant DL as downloader
    participant API as api.bilibili.com

    CLI->>DL: download(url, output_dir)
    DL->>DL: extract_bvid(url)
    DL->>API: GET /x/web-interface/view?bvid={bvid}
    API-->>DL: { data: { cid } }
    DL->>API: GET /x/player/playurl?bvid={bvid}&cid={cid}&fnval=4048&fourk=1
    API-->>DL: { data: { dash: { audio: [{ baseUrl }] } } }
    DL->>API: GET audio baseUrl
    API-->>DL: m4a 二进制流
    DL-->>CLI: 返回本地 m4a 路径
```

### 步骤一：获取视频信息

```
GET https://api.bilibili.com/x/web-interface/view?bvid={bvid}
```

**请求头**：

| 头 | 值 |
|----|-----|
| `User-Agent` | `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36` |
| `Referer` | `https://www.bilibili.com/` |

**关键返回字段**：`data.cid`、`data.bvid`、`data.title`、`data.duration`。`code != 0` 时抛出 `NetworkError`。

### 步骤二：获取音频流地址

```
GET https://api.bilibili.com/x/player/playurl?bvid={bvid}&cid={cid}&qn=0&fnval=4048&fourk=1
```

**参数说明**：

| 参数 | 值 | 含义 |
|------|-----|------|
| `qn` | `0` | 不限画质 |
| `fnval` | `4048` | 请求 DASH 流（含独立音频轨） |
| `fourk` | `1` | 允许 4K |

**关键返回字段**：`data.dash.audio[0].baseUrl`（音频直链）、`data.dash.audio[0].codecs`（编码格式，通常为 `mp4a.40.2`）。`audio` 数组为空时抛出 `NetworkError`。

### 步骤三：下载音频

对 `baseUrl` 发起 HTTP GET，请求头同步骤一。超时 120 秒。将音频写入临时目录，返回本地文件路径。

### BV 号提取

正则 `BV[0-9A-Za-z]{10}` 从输入中提取 BV 号。输入可以是完整 URL 或纯 BV 号。匹配失败时抛出 `UserError`。

### 平台分派

通过 URL 关键词匹配下载函数。M0 仅注册 `"bilibili"`。无匹配时抛出 `NetworkError`。

```python
_DOWNLOADERS: dict[str, Callable] = {
    "bilibili": _download_bilibili,
}
```

---

## 4. 转码模块

`transcoder.py` 使用 PyAV（`av`）将音频转为 16kHz 单声道 WAV，供 ASR 模块消费。

### PyAV 转码

```python
import av

container = av.open("input.m4a")
# 解复用 → 重采样 (16kHz mono) → 编码为 PCM WAV
output_stream = output_container.add_stream("pcm_s16le", rate=16000, layout="mono")
resampler = av.audio.resampler.AudioResampler(format="s16", layout="mono", rate=16000)
```

`av` 通过 `pip install av` 自动安装，零系统依赖。

### 跳过转码

输入已是 `.wav` 后缀时跳过转码，直接返回原路径。

---

## 5. ASR 识别模块

#### 架构

Vid2Text 不直接链接任何深度学习库。ASR 推理通过 `subprocess` 调用预编译的 C 二进制 `sense-voice` 完成。二进制输出文本到 STDOUT，Python 层负责解析和剥离时间戳。

```
Python (asr.py)
    │ subprocess.run(["sense-voice", "-m", "...", "audio.wav"])
    ▼
C 二进制 (sense-voice)
    │ GGUF 模型加载 + Metal/CUDA 推理
    ▼
STDOUT: "[0.54-3.78] 甚至出现交易几乎停滞的情况。"
    │ _parse_output(stdout) → 剥离时间戳
    ▼
"甚至出现交易几乎停滞的情况。"
```

#### 模型

| 模型 | 格式 | 大小 | 位置 |
|------|------|------|------|
| SenseVoice-Small Q4_K | GGUF | 174MB | `models/sense-voice-small-q4_k.gguf` |

模型已内嵌于 `.skill` 产物中，不需要在线下载。

#### 二进制

| 平台 | 路径 | 大小 |
|------|------|------|
| macOS arm64 | `bin/darwin-arm64/sense-voice` | ~300KB |
| Linux x64 | `bin/linux-x64/sense-voice` | ~300KB |
| Windows x64 | `bin/win-x64/sense-voice.exe` | ~300KB |

编译流程：`git clone → cmake -DBUILD_SHARED_LIBS=OFF → make`，从 [lovemefan/SenseVoice.cpp](https://github.com/lovemefan/SenseVoice.cpp) 源码静态编译。

#### 线程数配置

二进制通过 `-t 4` 参数控制解码线程数。不使用环境变量。

#### 错误处理

| 错误 | 异常 |
|------|------|
| 二进制文件缺失 | `ModelError`，退出码 2 |
| 模型文件缺失 | `ModelError`，退出码 2 |
| ASR 推理失败 | `ModelError`，退出码 2 |
| 不支持的平台 | `ModelError`，退出码 2 |

#### 模块接口

| 模块 | 文件 | 职责 | 输入 | 输出 |
|------|------|------|------|------|
| ASR | `asr.py` | subprocess 调用 sense-voice 二进制，解析输出 | WAV 路径 | 纯文本字符串 |

---

## 6. CLI 入口

`cli.py` 是唯一命令行入口，基于 click 框架。

### 命令结构

```mermaid
flowchart TD
    main[vid2text] --> transcribe["默认命令: url 或 bvid"]
```

### 命令格式

```
vid2text <url|bvid>
```

### `vid2text <url|bvid>`

位置参数接受完整 B站链接或纯 BV 号。

### 退出码

| 退出码 | 含义 | Agent 处置 |
|--------|------|------------|
| 0 | 成功 | 读取 STDOUT |
| 1 | 用户错误 | 修正输入后重试 |
| 2 | 系统错误 | 检查环境或报用户 |

### STDOUT / STDERR 分工

| 输出内容 | 通道 |
|----------|------|
| 转写文本 | STDOUT |
| 错误信息 | STDERR |
| 状态提示（下载完成等） | STDERR |

STDOUT 始终是纯文本内容，Agent 无需解析或过滤。

---

## 7. 打包配置

使用 `scripts/build_skill.py` 将项目打包为 `.skill` zip 产物。

### 产物内容

```
vid2text-{version}.skill
├── SKILL.md
├── pyproject.toml
├── vid2text/
│   └── *.py
├── bin/
│   ├── darwin-arm64/sense-voice
│   ├── linux-x64/sense-voice
│   └── win-x64/sense-voice.exe
└── models/
    └── sense-voice-small-q4_k.gguf
```

### .skill 体积

| 组件 | 大小 |
|------|------|
| Python 源码 | ~30KB |
| C 二进制 (3 平台) | ~3MB |
| GGUF 模型 | 174MB |
| **合计** | **~177MB** |

### 安装方式

- **开发**：`pip install -e .`
- **发行**：GitHub Releases 下载 `.skill` 文件，解压后 `pip install -e .` 即可

### 模型

模型文件（174MB GGUF）内嵌于 `.skill` 产物中，不需要在线下载。
