# ASR 识别模块

`asr.py` 不链接任何深度学习库。推理通过 `subprocess` 调用预编译的 C 二进制 `sense-voice` 完成，Python 层负责解析 STDOUT 输出。

## 调用架构

```mermaid
flowchart TD
    A[asr.py] -->|subprocess.run| B[sense-voice 二进制]
    B -->|加载| C["GGUF 模型<br>CPU 推理"]
    C -->|写入| D["STDOUT<br>带时间戳文本"]
    D -->|解析| E[_parse_output]
    E --> F[纯文本]
```

## 模型

| 模型 | 格式 | 大小 | 位置 |
|------|------|------|------|
| SenseVoice-Small Q4_K | GGUF | 174MB | `models/sense-voice-small-q4_k.gguf` |

模型内嵌于项目，不需在线下载。

## 二进制

| 平台 | 路径 |
|------|------|
| macOS arm64 | `bin/darwin-arm64/sense-voice` |
| Linux x64 | `bin/linux-x64/sense-voice` |
| Windows x64 | `bin/win-x64/sense-voice.exe` |

编译来源：[lovemefan/SenseVoice.cpp](https://github.com/lovemefan/SenseVoice.cpp) 静态编译。

## 调用参数

| 参数 | 含义 |
|------|------|
| `-m` | 模型文件路径 |
| `-t 4` | 解码线程数 |
| `-l auto` | 自动检测语言 |
| `-itn` | 逆文本正则化（数字、标点规范化） |
| `-nt` | 不打印时间戳 |
| `-np` | 不打印进度信息 |

## 输出解析

已传 `-nt` 请求二进制不输出时间戳，`_parse_output()` 提供防御性兜底：正则剥离行首 `[时间戳]` 前缀并过滤空行后合并。

## 错误处理

| 错误场景 | 异常 |
|----------|------|
| 二进制缺失 | `ModelError` |
| 模型缺失 | `ModelError` |
| 推理失败（returncode ≠ 0） | `ModelError` |
| 不支持的操作系统 | `ModelError` |

详见 [错误类型](errors.md)。
