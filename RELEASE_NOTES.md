# Release Notes — NORP Chat v1.0.0

**Release Date:** July 29, 2026

We are thrilled to announce the **first stable release** of **NORP Chat** — a modern, desktop AI chat client built with Python (pywebview) and a rich HTML/CSS/JS frontend. It supports both OpenAI-compatible APIs and Anthropic Claude, with a focus on real-time streaming, deep reasoning transparency, and a polished user experience.

---

## 🚀 What's New

### 🧠 Multi-Model & Multi-API Support
- **OpenAI-compatible APIs**: DeepSeek, OpenAI, or any custom endpoint
- **Anthropic Claude API**: Full support via DeepSeek's Anthropic bridge
- **Dynamic model fetching**: Automatically retrieve available models from your API provider
- **Custom model name**: Manually specify any model identifier

### ⚡ Real-Time Streaming
- **Token-by-token streaming**: Instant, responsive output as the AI generates text
- **Thinking/Reasoning display**: View the AI's internal reasoning process — supports both OpenAI `reasoning_content` and Anthropic `thinking` blocks
- **Graceful interruption**: Stop generation mid-stream at any time

### 🔍 Web Search
- **Live internet search**: AI can perform real-time web searches during conversation via Anthropic `web_search_20250305` tool or OpenAI function calling
- **Context-aware**: Search results are seamlessly integrated into the AI's response

### 📁 File Upload & Parsing
- **Supported formats**: `.txt`, `.py`, `.json`, `.csv`, `.css`, `.html`, `.md` (plain text), plus `.pdf`, `.docx`, `.xlsx` (with optional dependencies)
- **Drag & drop**: Intuitive file upload interface
- **10MB configurable limit**

### 🎨 Rich Text Rendering
- **Markdown**: Full Markdown rendering via [marked.js](https://marked.js.org/)
- **LaTeX math**: Beautiful formula rendering via [KaTeX](https://katex.org/) with safe fallback
- **Syntax-highlighted code blocks**: Language labels and copy buttons
- **Rendered tables**: Zebra-striped Markdown tables
- **Smart math detection**: `$10`, `$50` and similar currency amounts are no longer mistakenly rendered as LaTeX

### 🔒 Security & Privacy
- **API key encryption**: Encrypted local storage using Windows DPAPI (`win32crypt`)
- **Keyring support**: Optional Windows Credential Manager integration
- **Local-first architecture**: All data stored in `%LOCALAPPDATA%/dschat/`
- **Encryption migration**: Seamlessly migrate between storage methods

### 🌐 Multi-Language Interface
- **简体中文 (Chinese Simplified)** — Default
- **繁體中文 (Chinese Traditional)**
- **English**
- **日本語 (Japanese)**

### 💾 Memory & Persistence
- **Conversation memory**: Automatic chat history saving with smart trimming
- **Session persistence**: Conversations survive app restarts
- **Configurable memory window**: Adjust how much context the AI remembers

---

## 🛠️ Installation

### Option 1: Pre-built Executable (Recommended)
Download `NORP Chat.exe` from the `dist/` directory — no Python installation required.

### Option 2: Run from Source
```bash
git clone <repo-url>
cd NORP-Chat
pip install -r requirements.txt
python duo2.py
```

> **First-time setup**: You will be prompted to enter your API key on first launch. Your key is encrypted and stored locally.

---

## 📦 What's Included

| File | Description |
|------|-------------|
| `duo2.py` | Main application source (Python + embedded HTML/JS) |
| `requirements.txt` | Python dependencies |
| `NORP Chat.exe` | Pre-built Windows executable (in `dist/`) |
| `ds.ico` | Application icon |
| `README.md` | Full documentation |
| `RELEASE_NOTES.md` | This file |

---

## ⚠️ Important Notes

- **API key required**: You need a valid API key from DeepSeek, OpenAI, or Anthropic. See [README.md](./README.md#faq) for guidance.
- **Windows only**: Currently built for Windows with native DPAPI encryption and `pywebview` (MS Edge WebView2).
- **Optional dependencies**: For `.pdf`, `.docx`, `.xlsx` file parsing, install extra packages listed in `requirements.txt`.

---

## 🔧 Known Issues

- File uploads larger than 10MB may cause UI lag on low-end machines
- The Anthropic streaming path uses a polling mechanism; some users may experience slightly higher latency compared to OpenAI path
- Multi-turn conversations with very long histories may impact streaming performance (mitigated by configurable memory trimming)

---

## 🙏 Acknowledgments

Built with ❤️ using:
- [pywebview](https://github.com/r0x0r/pywebview) — Desktop GUI
- [OpenAI Python SDK](https://github.com/openai/openai-python) — API client
- [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python) — API client
- [marked.js](https://marked.js.org/) — Markdown rendering
- [KaTeX](https://katex.org/) — LaTeX math rendering
- [PyInstaller](https://pyinstaller.org/) — Application packaging

---

## 📬 Feedback & Contributions

Issues, feature requests, and pull requests are welcome! Let us know how we can make NORP Chat better.
