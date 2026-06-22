# Vid2Text

将 B站视频转写为纯文本的 Skill。提供B站链接或 BV 号，即可获得带标点的完整转写文本。

## 安装

将 `.skill` 文件拖拽到 Agent 的 Skills 目录，或按照对应平台的 Skill 安装说明操作即可。

## 原理

输入B站链接后，Agent 自动完成以下步骤：

1. 从 B站 API 下载视频的音频轨（m4a）
2. 将音频转为 16kHz 单声道 WAV
3. 通过本地 SenseVoice.cpp 引擎进行语音识别
4. 输出带标点的纯文本

整个过程在本地完成，不需要联网调用任何 ASR API。

## License

MIT
