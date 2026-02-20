# Subliminal Audio Synthesizer / 潜意识音频合成器

[![Version](https://img.shields.io/badge/version-3.1.0-blue.svg)](https://github.com/zwmopen/subliminal-audio-synthesizer)
[![Python](https://img.shields.io/badge/python-3.7%2B-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

A professional subliminal audio synthesis tool based on neuroscience and psychology principles.

基于神经科学和心理学原理的专业潜意识音频合成工具。

## ✨ Features / 功能特点

- **🎵 Dual Track Input**: Upload affirmation audio and background music / 双轨道输入：上传肯定句音频和背景音乐
- **📡 High-Frequency Modulation**: Modulate voice to 17.5kHz-19.5kHz / 高频调制：将人声调制到17.5kHz-19.5kHz
- **🧠 Theta Wave Binaural Beats**: Generate 4Hz difference frequency / Theta波双耳搏动：生成4Hz差频
- **🎚️ Volume Control Sliders**: Precise volume adjustment / 音量控制滑动条：精确音量调整
- **🔄 Track Alignment & Loop**: Automatic track alignment / 音轨对齐和循环：自动对齐音轨
- **💾 Lossless WAV Export**: Preserve high-frequency information / 无损WAV导出：保留高频信息
- **🎨 Neumorphism UI**: Modern and elegant interface / 新拟态界面：现代优雅的界面
- **🔒 Security Hardened**: File validation and path protection / 安全加固：文件验证和路径保护
- **📝 Logging System**: Complete operation logging / 日志系统：完整的操作日志
- **🧹 Auto Cleanup**: Automatic temporary file cleanup / 自动清理：临时文件自动清理

## 🔧 Core Logic / 核心逻辑

```
Hidden Track (Processed Affirmations) + 
Visible Track (Background Music) + 
Frequency Induction (Optional Binaural Beats) = 
Final Product
```

```
隐藏轨（处理后的肯定句）+ 
显性轨（背景音乐）+ 
频率诱导（可选的双耳搏动）= 
最终成品
```

## 🚀 Quick Start / 快速开始

### 1. Install Dependencies / 安装依赖

```bash
pip install pydub numpy scipy flask
```

### 2. Run Application / 运行应用

```bash
python subliminal_master.py
```

Or double-click `启动Subliminal_Master.bat` (Windows)

或双击 `启动Subliminal_Master.bat`（Windows）

### 3. Open Browser / 打开浏览器

Visit: http://localhost:5000

访问：http://localhost:5000

### 4. Upload & Process / 上传和处理

1. Upload affirmation audio (Track A) / 上传肯定句音频（Track A）
2. Upload background music (Track B) / 上传背景音乐（Track B）
3. Adjust parameters / 调整参数
4. Click "Start Synthesis" / 点击"开始合成"
5. Download processed audio / 下载处理后的音频

## ⚙️ Parameters / 参数说明

### Carrier Frequency (Hz) / 载波频率
- Default: 17500
- Range: 15000-20000
- Modulates voice to inaudible frequency range

### Subliminal Volume (dB) / 潜意识轨音量
- Default: -23 (Golden value)
- Controls processed voice volume

### Background Volume (dB) / 背景音乐音量
- Default: 0
- Controls background music volume

### Binaural Beats / 双耳搏动
- Left Ear: 430Hz
- Right Ear: 434Hz
- Difference: 4Hz Theta Wave

## 📁 Project Structure / 项目结构

```
subliminal-audio-synthesizer/
├── subliminal_master.py      # Main application / 主程序
├── config.py                 # Configuration module / 配置模块
├── audio_processor.py        # Audio processing core / 音频处理核心
├── logger.py                 # Logging module / 日志模块
├── file_cleaner.py           # Auto cleanup module / 自动清理模块
├── templates/
│   └── index.html            # Web UI template / Web界面模板
├── test_subliminal_master.py # Test script / 测试脚本
├── generate_test_audio.py    # Test audio generator / 测试音频生成器
├── 启动Subliminal_Master.bat # Windows launcher / Windows启动脚本
├── .gitignore
├── README.md
└── 使用说明.md               # Detailed documentation / 详细文档
```

## ⚠️ Important Notes / 重要提示

- **Must use WAV format**: MP3 will cut off frequencies above 16kHz / 必须使用WAV格式：MP3会切掉16kHz以上的高频信号
- **Use high-quality headphones**: For best binaural beats effect / 使用高质量耳机：获得最佳双耳搏动效果
- **Listen 1-2 times daily**: 15-30 minutes each session / 每天聆听1-2次：每次15-30分钟
- **Continue for 66 days**: For optimal results / 持续66天：获得最佳效果

## 🛠️ Technical Stack / 技术栈

- Python 3.7+
- Flask (Web Framework)
- pydub (Audio Processing)
- numpy (Numerical Computing)
- scipy (Signal Processing)

## 📊 Version History / 版本历史

### v3.1.0 (Current)
- 🔒 Security hardening: File validation, path traversal protection
- 🏗️ Modular architecture: Separated modules for better maintainability
- 📝 Logging system: Complete operation logging
- 🧹 Auto cleanup: Automatic temporary file cleanup
- 🎨 Improved UI: Better error handling and feedback

### v3.0.0
- ✨ Dual track input system
- ✨ High-frequency modulation
- ✨ Theta wave binaural beats
- ✨ Neumorphism UI

## 📄 License / 许可证

MIT License

## 👤 Author / 作者

Dadan Technology Co., Ltd. / 达丹科技

## 🙏 Acknowledgments / 致谢

Based on neuroscience and psychology research for subliminal audio processing.

基于潜意识音频处理的神经科学和心理学研究。

---

⭐ If you find this project useful, please give it a star! / 如果觉得有用，请给个星标！
