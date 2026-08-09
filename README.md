# AI Workshop Tool Guide

Installation guide for AI workshop tools, for Windows 11 and macOS.

## Live Site

- Landing page (choose 安裝環境 / 手作步驟): https://chenghsienwen.github.io/ai_workshop_tool_guide/
- 安裝環境 — OS picker: https://chenghsienwen.github.io/ai_workshop_tool_guide/install/index.html
  - Windows 11: https://chenghsienwen.github.io/ai_workshop_tool_guide/install/windows.html
  - macOS: https://chenghsienwen.github.io/ai_workshop_tool_guide/install/macos.html
- 手作步驟 — session picker: https://chenghsienwen.github.io/ai_workshop_tool_guide/workshop/index.html
  - Session 1: https://chenghsienwen.github.io/ai_workshop_tool_guide/workshop/session-1.html
  - Session 2: https://chenghsienwen.github.io/ai_workshop_tool_guide/workshop/session-2.html
  - Session 3: https://chenghsienwen.github.io/ai_workshop_tool_guide/workshop/session-3.html

## Site structure

```
index.html              top-level entry (安裝環境 / 手作步驟)
install/index.html      OS picker (installation guide entry)
install/windows.html    Windows 11 install guide
install/macos.html      macOS install guide
workshop/index.html     hands-on session picker
workshop/session-N.html per-session hands-on steps
```

## Local Run

Every page is a self-contained HTML file with no build step — edit and open directly,
nothing is generated or copied.

```bash
python3 -m http.server 8080
```

Then open:
- http://127.0.0.1:8080/ — top-level entry
- http://127.0.0.1:8080/install/index.html — OS picker
- http://127.0.0.1:8080/install/windows.html
- http://127.0.0.1:8080/install/macos.html
- http://127.0.0.1:8080/workshop/index.html — session picker
