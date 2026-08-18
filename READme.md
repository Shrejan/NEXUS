# 🧠 NEXUS - AI Assistant Hub

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=flat-square&logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=flat-square)]()

*An intelligent, multi-modal AI assistant platform combining WhatsApp integration, voice assistance, and advanced LLM capabilities*

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Architecture](#-architecture) • [Contributing](#-contributing)

</div>

---

## 🌟 Features

<table>
<tr>
<td width="50%">

### 🤖 AI Integration
- **GPT-Powered Agent** - Advanced language understanding
- **WhatsApp Integration** - Seamless messaging interface
- **Smart Routing** - Intelligent request processing

</td>
<td width="50%">

### 🎤 Voice Assistant
- **Speech-to-Text** - High-accuracy STT engine
- **Wake Word Detection** - Always-on listening capability
- **Voice Activity Detection** - Smart audio processing

</td>
</tr>
<tr>
<td width="50%">

### 🛠️ Advanced Tools
- **LLM Management** - Flexible language model handling
- **Multi-Agent System** - Specialized agent types
- **C++ Acceleration** - Performance-critical components

</td>
<td width="50%">

### 🔌 Extensible Architecture
- **Modular Design** - Easy to extend and customize
- **Multiple Integrations** - WhatsApp, Voice, and more
- **Scalable Framework** - Built for growth

</td>
</tr>
</table>

---

## 📁 Project Structure

```
NEXUS/
├── 🤖 AI-agent/              # WhatsApp & LLM integration
│   ├── main.py               # Agent orchestration
│   ├── res.json              # Response configurations
│   ├── test.py               # Test suite
│   ├── uia.py                # UI automation
│   └── whatsapp_tree.json    # Dialog tree structure
│
├── 🔧 Tools/                 # Agent implementations
│   ├── GPT_agent.py          # OpenAI GPT integration
│   ├── WA_agent.py           # WhatsApp automation
│   └── cpp/                  # Performance-critical code
│       └── AUI.cpp           # Advanced UI Interface
│
├── 🎤 Voice_assist/          # Voice processing pipeline
│   ├── main.py               # Voice assistant entry point
│   ├── STT.py                # Speech-to-Text engine
│   ├── Vad.py                # Voice Activity Detection
│   ├── wake_word.py          # Wake word detection
│   └── test.py               # Voice module tests
│
├── llm.py                    # Core LLM utilities
└── README.md                 # This file

```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- pip package manager
- Virtual environment (recommended)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd NEXUS

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.\.venv\Scripts\Activate.ps1
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

#### 🤖 Run the AI Agent
```python
cd AI-agent
python main.py
```

#### 🎤 Run the Voice Assistant
```python
cd Voice_assist
python main.py
```

---

## 🏗️ Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────┐
│           NEXUS AI Assistant Platform               │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────┐  ┌──────────────┐                 │
│  │  WhatsApp    │  │  Voice Input │                 │
│  │  Interface   │  │  (Microphone)│                 │
│  └──────┬───────┘  └──────┬───────┘                 │
│         │                 │                         │
│         └────────┬────────┘                         │
│                  ▼                                  │
│         ┌──────────────────┐                        │
│         │   AI Agent Core  │                        │
│         │ (GPT Integration)│                        │
│         └────────┬─────────┘                        │
│                  │                                  │
│         ┌────────▼───────────┐                      │
│         │  Response Engine   │                      │
│         │  & Dialog Manager  │                      │
│         └────────┬───────────┘                      │
│                  │                                  │
│    ┌─────────────┼──────────┐                       │
│    ▼             ▼          ▼                       │
│ ┌──────┐   ┌──────┐   ┌──────────┐                  │
│ │Voice │   │ Text │   │WhatsApp  │                  │
│ │Output│   │ Logs │   │Response  │                  │
│ └──────┘   └──────┘   └──────────┘                  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 📦 Key Modules

### `AI-agent` 🤖
**WhatsApp-based AI conversation system**
- Manages LLM interactions
- Handles message routing and responses
- Supports complex dialog trees

### `Voice_assist` 🎤
**Real-time voice processing pipeline**
- `STT.py` - Converts speech to text
- `Vad.py` - Detects voice activity
- `wake_word.py` - Triggers assistant activation
- Optimized for low-latency responses

### `Tools` 🔧
**Specialized agent implementations**
- **GPT_agent.py** - OpenAI GPT interface
- **WA_agent.py** - WhatsApp automation
- **C++ Components** - High-performance processing

---

## ⚙️ Configuration

### Environment Variables
Create a `.env` file in the project root:

```bash
# LLM Configuration
OPENAI_API_KEY=your_api_key_here
LLM_MODEL=gpt-4

# WhatsApp Configuration
WA_CHROME_PATH=path/to/chrome

# Voice Configuration
WAKE_WORD=nexus
STT_ENGINE=google
```

---

## 🧪 Testing

```bash
# Run AI Agent tests
cd AI-agent && python test.py

# Run Voice Assistant tests
cd ../Voice_assist && python test.py

# Run all tests
pytest
```

---

## 📚 Usage Examples

### Using the AI Agent
```python
from AI_agent.main import Agent
from Tools.GPT_agent import GPTAgent

agent = Agent()
response = agent.process_message("Hello, how are you?")
print(response)
```

### Voice Assistant Integration
```python
from Voice_assist.main import VoiceAssistant
from Voice_assist.STT import SpeechToText

assistant = VoiceAssistant()
assistant.start()  # Listens for wake word
```

---

## 🔐 Security & Privacy

- Secure API key management via environment variables
- Local processing for voice data where possible
- Encrypted WhatsApp communication
- No persistent logging of sensitive data

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| WhatsApp connection fails | Verify Chrome path in `.env` |
| Voice input not detected | Check microphone permissions |
| LLM API errors | Validate OpenAI API key |
| STT accuracy issues | Adjust audio input levels |

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Setup
```bash
pip install -r requirements-dev.txt
pre-commit install
```

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 💡 Roadmap

- [ ] Mobile app integration
- [ ] Advanced NLP capabilities
- [ ] Real-time translation
- [ ] Custom model fine-tuning
- [ ] Multi-language support
- [ ] Cloud deployment ready

---

## 🙋 Support & Contact

- 📧 Email: shrejankotyan@gmail.com
- 🐛 Issues: [GitHub Issues](link-to-issues)
- 💬 Discussions: [GitHub Discussions](link-to-discussions)

---

<div align="center">

**Made with ❤️ by the NEXUS Team**

⭐ If you find this project useful, please consider giving it a star!

</div>
