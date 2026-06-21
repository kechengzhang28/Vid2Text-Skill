---
name: "vid2text"
description: "将 B站视频链接转换为带标点纯文本。基于 funasr_onnx 语音识别，pip install 后即可使用。"
---

## 能力

Vid2Text 输入一个 B站视频链接或 BV 号，输出带标点的纯文本转写结果。整个流程自动化：音频下载 → ffmpeg 转码 → ONNX 语音识别 → 标点恢复，一行命令完成。

## 触发场景

- 需要将 B站视频内容转为可阅读的纯文本
- 对视频内容进行摘要、分析、检索（下游 Agent 任务）
- 批量处理 B站视频转写

## 安装

```bash
cd vid2text
pip install -e .
```

## 先决条件

- Python >= 3.10
- ffmpeg 需在系统 PATH 中
- 网络可访问 B站 API 和 ModelScope
- 首次运行自动从 ModelScope 下载模型（约 1.2GB），后续无需重复下载

## 命令格式

```
vid2text <url|bvid> [--no-cache]
vid2text cache list
vid2text cache clear
```

| 命令 | 说明 |
|------|------|
| `<url|bvid>` | 完整 B站链接或纯 BV 号 |
| `--no-cache` | 跳过缓存，重新下载和推理 |
| `cache list` | 列出所有缓存条目 |
| `cache clear` | 清空所有缓存 |

## 输出契约

- **STDOUT**：纯文本转写结果（带标点），Agent 可直接读取
- **STDERR**：进度信息和错误诊断
- 输出不含时间戳、元信息、分段结构

## 退出码

| 退出码 | 含义 | 处置 |
|--------|------|------|
| 0 | 成功 | 读取 STDOUT |
| 1 | 用户错误（无效链接、无法提取 BV 号） | 修正输入后重试 |
| 2 | 系统错误（网络失败、模型异常、转码失败） | 检查环境或报用户 |

## 典型用法

```bash
# 完整链接
vid2text https://www.bilibili.com/video/BV1MN4y177PB

# 纯 BV 号
vid2text BV1MN4y177PB

# 查看帮助
vid2text --help
```

## 约束

- 仅支持 B站平台（M0 阶段）
- 仅输出中文转写文本，不生成字幕文件（SRT/VTT）
- 不提供翻译、摘要、笔记生成（这些是下游 Agent 的任务）
- 不下载视频画面、封面、弹幕
