# NORP Chat

> A modern desktop AI chat client with streaming output, deep reasoning, web search, file parsing, and rich-text rendering.

Built with **Python (pywebview)** + **HTML/CSS/JS** frontend, supporting both **OpenAI-compatible** and **Anthropic Claude** APIs.

---

## ✨ Features

### 🧠 Multi-Model & Multi-API
- **OpenAI-compatible APIs**: DeepSeek, OpenAI, or any custom API endpoint
- **Anthropic Claude API**: Built-in support via DeepSeek's Anthropic bridge
- **Custom base URL**: Connect to any OpenAI-compatible service
- **Model list fetching**: Dynamically fetch available models from your API provider
- **Custom model name**: Manually specify any model identifier

### ⚡ Streaming & Real-Time
- **Real-time streaming**: Token-by-token streaming output for instant response
- **Thinking/Reasoning display**: View the AI's internal reasoning process (supports both OpenAI reasoning_content and Anthropic thinking blocks)
- **Stop anytime**: Gracefully interrupt generation mid-stream

### 🔍 Web Search
- **Live internet search**: AI can perform web searches during conversation (via Anthropic web_search_20250305 tool or OpenAI function calling)
- **Seamless integration**: Search results are incorporated into the AI's response context

### 📁 File Upload & Parsing
- **Multiple formats**: `.txt`, `.py`, `.json`, `.csv`, `.css`, `.html`, `.md` (plain text), plus `.pdf`, `.docx`, `.xlsx` (with optional dependencies)
- **Drag & drop**: Intuitive file upload interface
- **10MB limit**: Configurable file size limit

### 🎨 Rich Text Rendering
- **Markdown**: Full Markdown rendering via [marked.js](https://marked.js.org/)
- **LaTeX math**: Beautiful math formula rendering via [KaTeX](https://katex.org/)
- **Code blocks**: Syntax-highlighted code with language labels and copy buttons
- **Tables**: Rendered Markdown tables with zebra striping
- **External links**: Open in-system browser viewer
- **Safe rendering**: KaTeX rendering wrapped in try-catch to prevent crashes

### 🔒 Security & Privacy
- **API key encryption**: Encrypted storage using Windows DPAPI (`win32crypt`)
- **Keyring support**: Optionally store keys in Windows Credential Manager
- **Encryption migration**: Seamlessly migrate between storage methods
- **Local-first**: All data stored locally in `%LOCALAPPDATA%/dschat/`

### 🌐 Multi-Language Support
- **简体中文 (Chinese Simplified)** - Default
- **English**

### 💾 Memory System (Beta)
- **Conversation memory**: AI remembers context across sessions
- **Two modes**: Full history or summary (compressed) mode
- **Configurable rounds**: Set how many conversation rounds to retain
- **Automatic trimming**: Excess memory is pruned to stay within limits

### ⚙️ Advanced Settings
- **Temperature**: Fine-tune response randomness (0.0 – 2.0)
- **Max tokens**: Control output length (up to 65536)
- **Logprobs**: Return token-level log probabilities
- **Stop sequences**: Custom stop sequences
- **JSON mode**: Force structured JSON output
- **User ID**: Identify sessions for API providers
- **Balance query**: Check your DeepSeek account balance

---

## 🚀 Getting Started

### Option 1: Pre-built Executable (Recommended)

Download the latest `NORP Chat.exe` from the [Releases](https://github.com/xingluosama121/NORP-Chat/releases) page.

> **System Requirements**: Windows 7+ (Windows 10/11 recommended)
>
> No Python or dependencies needed — it's a standalone executable.

### Option 2: Run from Source

#### Prerequisites
- Python 3.8+
- Windows (uses `win32crypt`)

#### Installation

```bash
# Clone the repository
git clone https://github.com/xingluosama/NORP-Chat.git
cd NORP-Chat

# Install core dependencies
pip install pywebview>=4.0 openai>=1.0 pywin32 anthropic>=0.30 keyring requests

# Optional: Install file parsing dependencies
pip install python-docx openpyxl PyPDF2
```

#### Run

```bash
python duo2.py
```

### 🔑 First-Time Setup

1. Launch the application
2. Click the **"Change Key"** button in the toolbar
3. Enter your API key (e.g., from [DeepSeek](https://platform.deepseek.com/) or another provider)
4. Optionally change the **API Base URL** in Settings → Advanced → API Address
5. Start chatting!

---

## 📖 Usage Guide

### Interface Layout

```
┌─────────────────────────────────────────────┐
│  Header: Title + Action Buttons              │
├─────────────────────────────────────────────┤
│                                             │
│  Chat Area: Message history                 │
│  - User messages (blue bubbles, right)      │
│  - Assistant messages (white, left)         │
│  - Reasoning box (gray, collapsible)         │
│  - Rich content (Markdown, LaTeX, code)      │
│                                             │
├─────────────────────────────────────────────┤
│  Input Area: Text input, Upload, Send/Stop  │
│  Status Bar: Status text, file info         │
└─────────────────────────────────────────────┘
```

### Toolbar Buttons

| Button | Description |
|--------|-------------|
| **About** | Show version and author info |
| **Balance** | Query API account balance (DeepSeek only) |
| **Refresh** | Re-render current message contents |
| **Reset** | Clear entire chat (requires confirmation) |
| **Settings** | Open configuration panel |
| **Key** | Change/update API key |

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Enter` | Send message |
| `Ctrl + Enter` | New line in input |

### Settings Reference

| Setting | Description | Default |
|---------|-------------|---------|
| Language | UI language | 简体中文 |
| Model | AI model to use | deepseek-chat |
| Reasoning Effort | Thinking depth (Off/Low/Medium/Max) | Off |
| Memory | Enable conversation memory (Beta) | Off |
| Web Search | Enable live internet search | Off |
| Temperature | Response randomness (0.0–2.0) | 1.0 |
| Max Tokens | Maximum output length | 32767 |
| JSON Mode | Force JSON-formatted output | Off |
| API Base URL | Custom API endpoint | https://api.deepseek.com |
| Key Storage | DPAPI (default) or Windows Keyring | DPAPI |

---

## 🔧 Development

### Project Structure

```
NORP-Chat/
├── duo2.py              # Main application (Python backend + HTML/JS frontend)
├── requirements.txt     # Python dependencies
├── ds.ico              # Application icon
├── NORP Chat.spec      # PyInstaller spec file
├── .gitignore
└── README.md
```

### Data Directory (`%LOCALAPPDATA%/dschat/`)

```
%LOCALAPPDATA%/dschat/
├── config.json          # User configuration
├── base.env             # Encrypted API key (DPAPI mode)
├── memory/
│   └── memory.json      # Conversation memory store
├── path/                # Reserved for future use
└── temp/                # Temporary file processing
```

### Build Executable

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --icon=ds.ico --name "NORP Chat" duo2.py
```

The executable will be output to `dist/NORP Chat.exe`.

### Architecture

```
┌─────────────────────────────────────────┐
│           pywebview (GUI)               │
│  ┌─────────────┐  ┌──────────────────┐  │
│  │  HTML/CSS   │  │  Python Backend  │  │
│  │  Frontend   │◄─┤  (DeepSeekWeb-   │  │
│  │  (marked.js │  │   ViewApp)       │  │
│  │   + KaTeX)  │  │                  │  │
│  └─────────────┘  └────────┬─────────┘  │
└─────────────────────────────┼───────────┘
                              │
                    ┌─────────▼─────────┐
                    │   OpenAI SDK /    │
                    │  Anthropic SDK    │
                    │                   │
                    │  ┌─────────────┐  │
                    │  │ Web Search  │  │
                    │  │ (Function   │  │
                    │  │  Calling)   │  │
                    │  └─────────────┘  │
                    └───────────────────┘
```

### Streaming Flow

```
User sends message
       │
       ▼
Python: send_message()
  └─► Starts threaded stream
       │
Python: call_deepseek_api_stream()
  └─► Yields tokens / reasoning chunks
       │
       ▼
JS Frontend: pywebview.api.get_next_chunk()
  └─► Polls every 100ms
       │
       ▼
JS: renderContent()
  └─► marked.parse() + katex.renderToString()
       │
       ▼
Display in chat area
```

---

## ❓ FAQ

### Where do I get an API key?
- **DeepSeek**: [https://platform.deepseek.com/](https://platform.deepseek.com/) — Sign up and create an API key
- **OpenAI**: [https://platform.openai.com/](https://platform.openai.com/)
- **Any OpenAI-compatible provider**: Use their base URL and API key

### Can I use a custom API endpoint?
Yes! Go to **Settings → Advanced → API Address** and enter your custom base URL (e.g., `https://api.openai.com`). Click "Apply" to save.

### How do I clear all data?
In Settings, click **"Clear All Cache"** — this removes all config, keys, memory, and cached data, then restarts the app.

### The app crashed. What now?
Crash logs are written to `%LOCALAPPDATA%/dschat/crash_log.txt`. Check this file for error details. Please include it when reporting issues.

### Can I use this on macOS/Linux?
The app uses `pywin32` and `win32crypt`, which are Windows-specific. A cross-platform version would require replacing these components.

### How do I reset my API key?
Click the **"Change Key"** button in the toolbar at any time to enter a new API key. The new key will be validated before saving.

---



## 👤 Author

**xingluosama** — NORP Studio

---

*Built with ❤️ using Python, pywebview, and modern web technologies.*
