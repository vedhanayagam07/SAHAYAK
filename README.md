# SAHAYAK — AI Study & Wellness Assistant

> **Team Project: AI Study & Wellness Companion for Students**  
> Repository: [https://github.com/vedhanayagam07/SAHAYAK](https://github.com/vedhanayagam07/SAHAYAK)

SAHAYAK is a unified student companion combining evidence-based learning principles (spaced repetition, active recall, Pomodoro), live tools, multimodal vision analysis, and document-grounded memory.

---

## 👥 Team Contributions & Architecture

```
                               ┌────────────────────────────────┐
                               │           SAHAYAK              │
                               │   Unified Assistant Runner     │
                               │         (sahayak.py)           │
                               └───────────────┬────────────────┘
                                               │
      ┌────────────────────────────────────────┼────────────────────────────────────────┐
      ▼                                        ▼                                        ▼
┌───────────────────────────┐    ┌───────────────────────────┐    ┌───────────────────────────┐
│           UTHAM           │    │          JACKSON          │    │            JOE            │
│ Persona & Prompt Design   │    │  Tool Use & Integration   │    │    Multimodal & Memory    │
│ (utham-persona-design-...)│    │ (jackson-tool-integration)│    │   (joe-multimodal-memory) │
├───────────────────────────┤    ├───────────────────────────┤    ├───────────────────────────┤
│ • Strengthened Rule 1     │    │ • get_weather             │    │ • Part A: Timetable Vision│
│   (strict mental health   │    │   (OpenWeatherMap + break)│    │ • Part B: Revision        │
│   boundary + helpline)    │    │ • calculate_study_schedule│    │   Infographics (HTML/JSON)│
│ • Cross-LLM benchmark     │    │   (Pure partition logic)  │    │ • Part C: 5-turn syllabus │
│   (ChatGPT vs Claude vs   │    │ • search_topic_summary    │    │   memory tracking (PDF)   │
│   Gemini evaluation)      │    │   (Wikipedia REST API)    │    │                           │
└───────────────────────────┘    └───────────────────────────┘    └───────────────────────────┘
```

---

## ⚡ Primary LLM Engine: Google Gemini API

The unified assistant is powered by **Google Gemini** (`gemini-1.5-flash` / `gemini-2.0-flash`) via the `GEMINI_API_KEY` (or `GOOGLE_API_KEY`), with support for Claude / Anthropic as an alternative provider.

---

## 🚀 Quick Start

### 1. Install Requirements
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Open `.env` and configure:
```env
GEMINI_API_KEY=AIzaSy...                # From https://aistudio.google.com/app/apikey
OPENWEATHER_API_KEY=your_key_here       # From https://home.openweathermap.org/api_keys
```

### 3. Launch SAHAYAK
Run the unified launcher menu:
```bash
python sahayak.py
```
Or use the CLI flags directly:
- **Interactive Chat**: `python sahayak.py --chat`
- **Run Tool Test Suite**: `python sahayak.py --tools`
- **Generate Infographic**: `python sahayak.py --infographic "Newton's Laws of Motion"`
- **System & API Key Diagnostics**: `python sahayak.py --status`

---

## 📂 Submodule Directory Overview

- **`jackson-tool-integration/`**: Contains function-calling schemas, weather/schedule/search tool implementations, and test logs.
- **`joe-multimodal-memory/`**: Contains timetable image analysis, infographic generation, and syllabus memory tracking.
- **`utham-persona-design-model-comparison/`**: Contains persona design specifications, prompt iterations (v1 & v2), and model comparison reports.
