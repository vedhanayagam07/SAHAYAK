# SAHAYAK — Tool Use & API Integration Module

This module forms the **Tool Use / API Integration** subsystem of **SAHAYAK**, an AI study & wellness assistant for students. It enables Claude (via the Anthropic `/v1/messages` tool calling API) to invoke deterministic local functions and live external web APIs instead of hallucinating answers.

---

## 🏛 Architecture Overview

```
User Prompt
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                     main_agent_loop.py                      │
│                                                             │
│  - Uttam's System Prompt & Rules Enforcement                │
│  - Anthropic Client (/v1/messages)                          │
│  - Schema Provider (tools_schema.json)                      │
│  - Tool Dispatcher & Tool Result Accumulator                │
└──────────────┬───────────────────────────────┬──────────────┘
               │                               │
               ▼                               ▼
    ┌──────────────────────┐        ┌──────────────────────┐
    │     get_weather      │        │ calculate_study_     │
    │  (weather_tool.py)   │        │      schedule        │
    │                      │        │  (schedule_tool.py)  │
    │  - OpenWeatherMap    │        │                      │
    │  - Outdoor break evaluation   │  - Pure calculation  │
    └──────────────────────┘        │  - Even distribution │
               │                    │  - Spaced repetition │
               │                    └──────────────────────┘
               ▼
    ┌──────────────────────┐
    │ search_topic_summary │
    │   (search_tool.py)   │
    │                      │
    │  - Wikipedia REST    │
    │  - No API key needed │
    │  - Source citation   │
    └──────────────────────┘
```

---

## 📁 File Structure

| File | Purpose |
|------|---------|
| `tools_schema.json` | Anthropic-standard tool definitions and parameter JSON schemas for all 3 tools. |
| `weather_tool.py` | Fetches live weather via OpenWeatherMap API and calculates outdoor study break suitability. |
| `schedule_tool.py` | Pure Python function computing days remaining and distributing topics evenly into daily study blocks. |
| `search_tool.py` | Fetches academic topic summaries and citation URLs from the public Wikipedia REST API. |
| `main_agent_loop.py` | Orchestration script that loops Claude model requests, parses `tool_use` blocks, runs tools, and passes `tool_result` back. |
| `test_tools.py` | Comprehensive unit tests covering edge cases, date arithmetic, invalid inputs, and error handling. |
| `test_logs.md` | Detailed execution logs and validation notes for the 4 core test cases. |
| `.env.example` | Template for environment variables and API keys. |
| `requirements.txt` | Python library dependencies (`anthropic`, `requests`, `python-dotenv`, `urllib3`). |

---

## 🔑 Required API Keys & Environment Configuration

Before running live API requests, create a `.env` file in `jackson-tool-integration/`:

```bash
cp .env.example .env
```

Fill in the following values in `.env`:

| Variable | Required? | Source / Where to Obtain | Description |
|---|:---:|---|---|
| `ANTHROPIC_API_KEY` | **Yes** (for live Claude calls) | [Anthropic Console](https://console.anthropic.com/settings/keys) | Required for Claude to evaluate prompts and generate `tool_use` requests. |
| `OPENWEATHER_API_KEY` | **Yes** (for live weather) | [OpenWeatherMap Keys](https://home.openweathermap.org/api_keys) | Free API key for current temperature and conditions. |
| `ANTHROPIC_MODEL` | Optional | Default: `claude-3-5-sonnet-20241022` | Claude model identifier. |

> [!NOTE]
> `search_topic_summary` uses the open Wikipedia REST API and **does not require an API key**.
> 
> If `ANTHROPIC_API_KEY` or `OPENWEATHER_API_KEY` are not yet configured, `main_agent_loop.py` automatically falls back to offline simulation/mock runner mode so you can verify execution flows immediately without crashes.

---

## 🚀 Quick Start & Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Automated Unit Tests
Verifies pure schedule math, date boundaries, Wikipedia fetching, and error handlers:
```bash
python test_tools.py
```

### 3. Run the 4 End-to-End Test Cases
Executes the test suite against all 4 scenarios described in `test_logs.md`:
```bash
python main_agent_loop.py
```

### 4. Run Interactive Chat Mode
Start an interactive pair-study session with Sahayak:
```bash
python main_agent_loop.py --interactive
```

---

## 🧪 Edge Cases Handled

1. **Date Bounds**: Past exam dates, today's date, or malformed strings return descriptive guidance rather than throwing unhandled exceptions.
2. **Daily Study Hours**: Non-positive numbers (`0` or negative hours) trigger validation messages.
3. **Uneven Topic Distribution**:
   - If `topics > days`: Topics are evenly chunked with remainder distributed across earliest days.
   - If `days > topics`: Dedicated revision and mock practice days are scheduled.
4. **Wikipedia 404 & Disambiguation**: Handled cleanly with actionable feedback.
5. **Network / SSL Fallback**: Built-in SSL fallback for corporate proxies and Windows trust store configurations.
