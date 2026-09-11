"""
SAHAYAK — Interactive Web Platform
A modern, responsive web dashboard integrating:
  - Jackson: Tool Use & API Integration (Weather, Schedule, Search)
  - Utham: Persona & Prompt v2 (Mental Health Guardrails)
  - Joe: Multimodal & Memory (Timetable Vision, Infographics, Syllabus Tracking)
  - Engine: Google Gemini API (gemini-1.5-flash / gemini-2.0-flash) & Claude fallback
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import date, timedelta
from dotenv import load_dotenv

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

# Load environment
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

# Ensure submodules can be imported
sys.path.insert(0, str(ROOT_DIR / "jackson-tool-integration"))
sys.path.insert(0, str(ROOT_DIR / "joe-multimodal-memory"))

from weather_tool import get_weather
from schedule_tool import calculate_study_schedule
from search_tool import search_topic_summary
from gemini_tool_engine import GeminiClient, run_gemini_turn
from sahayak import UNIFIED_SYSTEM_PROMPT, TOOL_DISPATCH, load_tools_schema

app = FastAPI(title="SAHAYAK Web Dashboard", version="1.0.0")


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, Any]]] = []


class ScheduleRequest(BaseModel):
    exam_date: str
    hours_per_day: float
    topics: List[str]


class WeatherRequest(BaseModel):
    location: str


class SearchRequest(BaseModel):
    topic: str


class InfographicRequest(BaseModel):
    topic: str


@app.get("/api/status")
async def get_status():
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    weather_key = os.getenv("OPENWEATHER_API_KEY")

    has_gemini = bool(gemini_key and not gemini_key.startswith("your_"))
    has_anthropic = bool(anthropic_key and not anthropic_key.startswith("your_"))
    has_weather = bool(weather_key and not weather_key.startswith("your_"))

    return {
        "gemini": {"configured": has_gemini, "model": os.getenv("GEMINI_MODEL", "gemini-1.5-flash")},
        "anthropic": {"configured": has_anthropic, "model": os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")},
        "weather": {"configured": has_weather},
        "wikipedia": {"configured": True, "note": "Always live via public REST API"},
        "active_provider": "Gemini (gemini-1.5-flash)" if has_gemini else ("Claude" if has_anthropic else "Simulation Mode")
    }


@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    user_prompt = req.message.strip()
    history = req.history or []

    gemini_client = GeminiClient()
    tools_schema = load_tools_schema()

    if gemini_client.is_configured():
        try:
            final_text, new_history, tool_calls = run_gemini_turn(
                user_prompt=user_prompt,
                system_prompt=UNIFIED_SYSTEM_PROMPT,
                tool_dispatch=TOOL_DISPATCH,
                anthropic_tools_schema=tools_schema,
                gemini_client=gemini_client,
                conversation_contents=history
            )
            if "Error from Gemini" in final_text:
                from main_agent_loop import run_mock_turn
                final_text, tool_calls = run_mock_turn(user_prompt)
        except Exception:
            from main_agent_loop import run_mock_turn
            final_text, tool_calls = run_mock_turn(user_prompt)
    else:
        from main_agent_loop import run_mock_turn
        final_text, tool_calls = run_mock_turn(user_prompt)

    return {
        "reply": final_text,
        "tool_calls": tool_calls,
        "history": history
    }


@app.post("/api/tools/weather")
async def weather_endpoint(req: WeatherRequest):
    return get_weather(req.location)


@app.post("/api/tools/schedule")
async def schedule_endpoint(req: ScheduleRequest):
    return calculate_study_schedule(req.exam_date, req.hours_per_day, req.topics)


@app.post("/api/tools/search")
async def search_endpoint(req: SearchRequest):
    return search_topic_summary(req.topic)


def build_infographic_data(topic: str) -> dict:
    """Builds structured infographic revision data for any topic."""
    from datetime import datetime
    clean_topic = topic.strip()
    lower = clean_topic.lower()

    if "photo" in lower or "plant" in lower or "bio" in lower:
        return {
            "topic": "Photosynthesis",
            "subtitle": "Converting sunlight, water, and CO2 into glucose and oxygen",
            "color_theme": "green",
            "key_definition": "Photosynthesis is the fundamental biochemical process by which green plants, algae, and cyanobacteria convert light energy into chemical energy stored in glucose molecules, generating oxygen as a vital byproduct.",
            "sections": [
                {
                    "heading": "Light-Dependent Reactions",
                    "icon": "☀️",
                    "points": [
                        "Occurs in the thylakoid membranes of chloroplasts",
                        "Chlorophyll pigments capture photons and excite electrons",
                        "Photolysis: Water (H2O) splits into O2, H+ ions, and electrons",
                        "Generates ATP and NADPH to fuel the Calvin cycle"
                    ]
                },
                {
                    "heading": "Calvin Cycle (Light-Independent)",
                    "icon": "🔄",
                    "points": [
                        "Occurs in the chloroplast stroma",
                        "Carbon fixation catalyzed by the enzyme RuBisCO",
                        "Consumes ATP and NADPH to produce G3P sugar precursors",
                        "Continuously regenerates RuBP to sustain cycle operation"
                    ]
                },
                {
                    "heading": "Overall Chemical Equation",
                    "icon": "🧪",
                    "points": [
                        "6 CO2 + 6 H2O + Light Energy -> C6H12O6 + 6 O2",
                        "Carbon dioxide is reduced to glucose",
                        "Water is oxidized to molecular oxygen",
                        "Endergonic reaction storing ~2870 kJ/mol of solar energy"
                    ]
                },
                {
                    "heading": "Key Limiting Factors",
                    "icon": "📊",
                    "points": [
                        "Light Intensity: Increases rate up to light-saturation point",
                        "CO2 Concentration: Drives carbon fixation by RuBisCO",
                        "Temperature: Optimum 25-35°C; enzymes denature above 40°C",
                        "Water Availability: Stomata close during drought, stalling CO2"
                    ]
                }
            ],
            "mnemonic": "Light Energizes All Plants / Water Yields Oxygen",
            "quick_quiz": [
                {"q": "Where do the light-dependent reactions take place?", "a": "In the thylakoid membranes of chloroplasts"},
                {"q": "What is the key enzyme responsible for carbon fixation in the Calvin cycle?", "a": "RuBisCO"},
                {"q": "Does the oxygen released come from CO2 or H2O?", "a": "H2O (via photolysis of water)"}
            ],
            "source_citations": ["Campbell Biology (12th Ed.)", "Khan Academy Biology", "Britannica"],
            "exam_tip": "High-Yield Exam Trap: The molecular oxygen (O2) released into the air comes exclusively from WATER (H2O), not from carbon dioxide (CO2)!",
            "_meta": {
                "generated_at": datetime.now().isoformat()
            }
        }
    elif "newton" in lower or "motion" in lower:
        from part_b_infographic_generator import generate_infographic_content_mock
        return generate_infographic_content_mock(clean_topic)
    else:
        # Dynamic encyclopedia-grounded infographic
        wiki_res = search_topic_summary(clean_topic)
        title = wiki_res.get("title", clean_topic)
        extract = wiki_res.get("summary", f"Key conceptual overview and principles of {clean_topic}.")
        source_url = wiki_res.get("source_url", "https://en.wikipedia.org")

        return {
            "topic": title,
            "subtitle": f"High-yield revision summary for {title}",
            "color_theme": "purple",
            "key_definition": extract[:350],
            "sections": [
                {
                    "heading": "Core Definition & Principles",
                    "icon": "🎯",
                    "points": [
                        extract[:180] + ("..." if len(extract) > 180 else ""),
                        "Foundational topic in syllabus and exam assessments",
                        "Essential for structured numerical and conceptual problems",
                        "Ground your answers in primary theorems and principles"
                    ]
                },
                {
                    "heading": "Essential Concepts",
                    "icon": "⭐",
                    "points": [
                        f"Master the core operational definitions of {title}",
                        "Examine relationship to related syllabus models",
                        "Practice standard calculation and proof problems",
                        "Link concepts across previous chapters"
                    ]
                },
                {
                    "heading": "Common Exam Pitfalls",
                    "icon": "⚠️",
                    "points": [
                        "Failing to state boundary conditions and units clearly",
                        "Confusing definitions under exam pressure",
                        "Passive reading without solving actual questions",
                        "Skipping intermediate calculation steps"
                    ]
                },
                {
                    "heading": "Active Recall & Revision",
                    "icon": "📝",
                    "points": [
                        "Self-test without notes using the Feynman technique",
                        "Solve 3 practice questions under 25-minute Pomodoro timers",
                        "Spaced repetition: review key formulas tomorrow and in 3 days",
                        "Highlight high-yield summary points for final review"
                    ]
                }
            ],
            "mnemonic": f"Recall {title} with Spaced Repetition",
            "quick_quiz": [
                {"q": f"What is the main subject of {title}?", "a": extract[:140]},
                {"q": "What evidence-based method best solidifies this topic?", "a": "Active recall and spaced repetition practice"}
            ],
            "source_citations": [f"Wikipedia ({source_url})", "Standard Academic Reference"],
            "exam_tip": f"Always state definitions and formulas clearly at the start of your exam answers for {title}.",
            "_meta": {
                "generated_at": datetime.now().isoformat()
            }
        }


@app.post("/api/infographic")
async def infographic_endpoint(req: InfographicRequest):
    try:
        from part_b_infographic_generator import render_html_infographic
        data = build_infographic_data(req.topic)
        html = render_html_infographic(data)
        return {"status": "success", "html": html, "topic": req.topic}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/", response_class=HTMLResponse)
async def home_page():
    return HTML_CONTENT


HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SAHAYAK — AI Study & Wellness Assistant</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-primary: #0a0e17;
      --bg-secondary: #111827;
      --bg-card: rgba(17, 24, 39, 0.7);
      --border-color: rgba(255, 255, 255, 0.08);
      --border-glow: rgba(99, 102, 241, 0.25);
      --primary: #6366f1;
      --primary-hover: #4f46e5;
      --primary-glow: rgba(99, 102, 241, 0.35);
      --accent: #06b6d4;
      --accent-glow: rgba(6, 182, 212, 0.3);
      --success: #10b981;
      --warning: #f59e0b;
      --danger: #ef4444;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --text-subtle: #64748b;
      --radius-sm: 8px;
      --radius-md: 14px;
      --radius-lg: 20px;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      font-family: 'Plus Jakarta Sans', sans-serif;
    }

    body {
      background: radial-gradient(circle at 15% 15%, #151c2e 0%, #0a0e17 65%);
      color: var(--text-main);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      overflow-x: hidden;
    }

    /* Top Navigation Header */
    header {
      background: rgba(10, 14, 23, 0.85);
      backdrop-filter: blur(16px);
      border-bottom: 1px solid var(--border-color);
      padding: 0.9rem 2rem;
      position: sticky;
      top: 0;
      z-index: 100;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .logo-container {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .logo-icon {
      width: 40px;
      height: 40px;
      background: linear-gradient(135deg, #6366f1 0%, #06b6d4 100%);
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 20px;
      font-weight: 700;
      box-shadow: 0 0 20px var(--primary-glow);
    }

    .brand-title {
      font-family: 'Outfit', sans-serif;
      font-size: 1.4rem;
      font-weight: 700;
      letter-spacing: -0.5px;
      background: linear-gradient(to right, #ffffff, #94a3b8);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .brand-badge {
      font-size: 0.7rem;
      background: rgba(99, 102, 241, 0.15);
      color: #818cf8;
      border: 1px solid rgba(99, 102, 241, 0.3);
      padding: 2px 8px;
      border-radius: 20px;
      font-weight: 600;
      letter-spacing: 0.5px;
      text-transform: uppercase;
    }

    .nav-status {
      display: flex;
      align-items: center;
      gap: 16px;
    }

    .status-pill {
      display: flex;
      align-items: center;
      gap: 8px;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--border-color);
      padding: 6px 14px;
      border-radius: 30px;
      font-size: 0.8rem;
      color: var(--text-muted);
    }

    .dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--success);
      box-shadow: 0 0 8px var(--success);
    }

    /* Main Container */
    .container {
      max-width: 1400px;
      margin: 0 auto;
      padding: 1.5rem 2rem;
      flex: 1;
      width: 100%;
      display: grid;
      grid-template-columns: 1fr 380px;
      gap: 1.5rem;
    }

    /* Left Chat Section */
    .chat-section {
      display: flex;
      flex-direction: column;
      background: var(--bg-card);
      backdrop-filter: blur(12px);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-lg);
      height: calc(100vh - 120px);
      overflow: hidden;
      box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
    }

    .chat-header {
      padding: 1rem 1.5rem;
      border-bottom: 1px solid var(--border-color);
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: rgba(255, 255, 255, 0.01);
    }

    .chat-header h2 {
      font-size: 1rem;
      font-weight: 600;
      color: var(--text-main);
    }

    .pill-group {
      display: flex;
      gap: 8px;
    }

    .chip {
      font-size: 0.75rem;
      padding: 4px 10px;
      border-radius: 6px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border-color);
      color: var(--text-muted);
    }

    /* Chat Messages Window */
    .messages-window {
      flex: 1;
      overflow-y: auto;
      padding: 1.5rem;
      display: flex;
      flex-direction: column;
      gap: 1.25rem;
    }

    .message {
      display: flex;
      gap: 12px;
      max-width: 85%;
      animation: fadeIn 0.25s ease-out;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(6px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .message.user {
      align-self: flex-end;
      flex-direction: row-reverse;
    }

    .message.assistant {
      align-self: flex-start;
    }

    .avatar {
      width: 36px;
      height: 36px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 16px;
      flex-shrink: 0;
    }

    .message.assistant .avatar {
      background: linear-gradient(135deg, #6366f1, #06b6d4);
      color: white;
      box-shadow: 0 0 12px var(--primary-glow);
    }

    .message.user .avatar {
      background: #334155;
      color: white;
    }

    .bubble {
      padding: 0.9rem 1.2rem;
      border-radius: 16px;
      font-size: 0.92rem;
      line-height: 1.55;
    }

    .message.assistant .bubble {
      background: rgba(30, 41, 59, 0.6);
      border: 1px solid rgba(255, 255, 255, 0.08);
      color: #f1f5f9;
      border-top-left-radius: 4px;
    }

    .message.user .bubble {
      background: linear-gradient(135deg, #4f46e5, #6366f1);
      color: #ffffff;
      border-top-right-radius: 4px;
      box-shadow: 0 4px 15px rgba(79, 70, 229, 0.3);
    }

    /* Tool Activity Cards */
    .tool-badge-container {
      margin-top: 10px;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .tool-pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 5px 10px;
      background: rgba(6, 182, 212, 0.12);
      border: 1px solid rgba(6, 182, 212, 0.35);
      border-radius: 6px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.75rem;
      color: #38bdf8;
    }

    .tool-result-box {
      background: #0f172a;
      border: 1px solid rgba(255, 255, 255, 0.06);
      border-radius: var(--radius-sm);
      padding: 12px;
      font-size: 0.8rem;
    }

    /* Preset Prompt Chips */
    .preset-container {
      padding: 0.5rem 1.5rem;
      display: flex;
      gap: 8px;
      overflow-x: auto;
      background: rgba(10, 14, 23, 0.5);
      border-top: 1px solid var(--border-color);
    }

    .preset-btn {
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--border-color);
      color: var(--text-muted);
      padding: 6px 12px;
      border-radius: 20px;
      font-size: 0.78rem;
      white-space: nowrap;
      cursor: pointer;
      transition: all 0.2s;
    }

    .preset-btn:hover {
      background: rgba(99, 102, 241, 0.15);
      color: #c7d2fe;
      border-color: rgba(99, 102, 241, 0.4);
    }

    /* Input Bar */
    .chat-input-bar {
      padding: 1rem 1.5rem;
      border-top: 1px solid var(--border-color);
      display: flex;
      gap: 12px;
      background: rgba(15, 23, 42, 0.5);
    }

    .chat-input {
      flex: 1;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-md);
      padding: 0.8rem 1.2rem;
      color: var(--text-main);
      font-size: 0.95rem;
      outline: none;
      transition: border-color 0.2s, box-shadow 0.2s;
    }

    .chat-input:focus {
      border-color: var(--primary);
      box-shadow: 0 0 0 3px var(--primary-glow);
    }

    .send-btn {
      background: linear-gradient(135deg, #6366f1, #4f46e5);
      border: none;
      color: white;
      padding: 0.8rem 1.5rem;
      border-radius: var(--radius-md);
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      transition: transform 0.15s, box-shadow 0.2s;
    }

    .send-btn:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 14px var(--primary-glow);
    }

    /* Right Sidebar (Tool Inspector & Features) */
    .sidebar {
      display: flex;
      flex-direction: column;
      gap: 1.25rem;
    }

    .panel {
      background: var(--bg-card);
      backdrop-filter: blur(12px);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-md);
      padding: 1.25rem;
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.25);
    }

    .panel-title {
      font-size: 0.85rem;
      font-weight: 700;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 12px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    /* Live Tool Cards in Sidebar */
    .tool-card {
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-sm);
      padding: 10px;
      margin-bottom: 8px;
      cursor: pointer;
      transition: border-color 0.2s;
    }

    .tool-card:hover {
      border-color: rgba(99, 102, 241, 0.4);
    }

    .tool-name {
      font-weight: 600;
      font-size: 0.85rem;
      color: #e2e8f0;
      margin-bottom: 4px;
    }

    .tool-desc {
      font-size: 0.75rem;
      color: var(--text-subtle);
    }

    /* Infographic Preview Modal */
    .modal {
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.85);
      backdrop-filter: blur(8px);
      z-index: 1000;
      align-items: center;
      justify-content: center;
      padding: 2rem;
    }

    .modal-content {
      background: #ffffff;
      color: #000000;
      width: 100%;
      max-width: 900px;
      height: 85vh;
      border-radius: 12px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }

    .modal-header {
      background: #0f172a;
      color: white;
      padding: 12px 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .close-btn {
      background: transparent;
      border: none;
      color: white;
      font-size: 20px;
      cursor: pointer;
    }

    .modal-iframe {
      flex: 1;
      border: none;
      width: 100%;
    }
  </style>
</head>
<body>

  <!-- Top Header -->
  <header>
    <div class="logo-container">
      <div class="logo-icon">S</div>
      <div>
        <div style="display: flex; align-items: center; gap: 8px;">
          <span class="brand-title">SAHAYAK</span>
          <span class="brand-badge">Unified Platform</span>
        </div>
        <div style="font-size: 0.72rem; color: var(--text-subtle);">AI Study & Wellness Assistant</div>
      </div>
    </div>

    <div class="nav-status">
      <div class="status-pill">
        <div class="dot"></div>
        <span id="active-llm">Gemini 1.5 Flash Active</span>
      </div>
      <div class="status-pill">
        <span>Utham Persona v2</span>
      </div>
    </div>
  </header>

  <!-- Main Grid -->
  <div class="container">
    
    <!-- Chat Section -->
    <div class="chat-section">
      <div class="chat-header">
        <h2>Live Study Partner</h2>
        <div class="pill-group">
          <span class="chip">Spaced Repetition</span>
          <span class="chip">Pomodoro</span>
          <span class="chip">Active Recall</span>
        </div>
      </div>

      <!-- Messages Window -->
      <div class="messages-window" id="messages-window">
        <div class="message assistant">
          <div class="avatar">S</div>
          <div class="bubble">
            Hello! I'm <strong>Sahayak</strong>, your AI study and wellness companion. 
            What subject or exam are you preparing for today?
          </div>
        </div>
      </div>

      <!-- Preset Prompt Buttons -->
      <div class="preset-container">
        <button class="preset-btn" onclick="sendPreset('I have a maths exam in 5 days, 2 hours/day, can I study outside today? I\'m in Bangalore.')">
          Maths Exam + Bangalore Weather
        </button>
        <button class="preset-btn" onclick="sendPreset('Give me a quick summary of the topic \'Newton\'s laws of motion\'')">
          Newton's Laws of Motion
        </button>
        <button class="preset-btn" onclick="sendPreset('just make me a plan')">
          Ambiguous Plan (Rule 3 Test)
        </button>
        <button class="preset-btn" onclick="sendPreset('What is the weather right now in XyzzyNonExistentLand99999, and can I take a break outside?')">
          Hallucination Check
        </button>
      </div>

      <!-- Input Bar -->
      <div class="chat-input-bar">
        <input type="text" id="user-input" class="chat-input" placeholder="Ask for a study schedule, concept summary, or break recommendation..." onkeydown="if(event.key==='Enter') sendMessage()">
        <button class="send-btn" onclick="sendMessage()">
          <span>Send</span>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/></svg>
        </button>
      </div>
    </div>

    <!-- Right Sidebar -->
    <div class="sidebar">
      
      <!-- Live Tools Panel -->
      <div class="panel">
        <div class="panel-title">
          <span>Jackson's Live Tools</span>
          <span style="color: var(--success); font-size: 0.7rem;">3 Active</span>
        </div>
        
        <div class="tool-card" onclick="testWeatherPrompt()">
          <div class="tool-name">get_weather</div>
          <div class="tool-desc">Checks temperature & outdoor study break suitability.</div>
        </div>

        <div class="tool-card" onclick="testSchedulePrompt()">
          <div class="tool-name">calculate_study_schedule</div>
          <div class="tool-desc">Pure math partitioning of topics leading to exam date.</div>
        </div>

        <div class="tool-card" onclick="testSearchPrompt()">
          <div class="tool-name">search_topic_summary</div>
          <div class="tool-desc">Fetches verified Wikipedia summary & citations.</div>
        </div>
      </div>

      <!-- Multimodal Infographics (Joe's Part B) -->
      <div class="panel">
        <div class="panel-title">
          <span>Joe's Revision Infographics</span>
          <span style="color: var(--accent); font-size: 0.7rem;">Printable A4</span>
        </div>
        <p style="font-size: 0.78rem; color: var(--text-muted); margin-bottom: 10px;">
          Generate a color-coded visual revision infographic with mnemonics & self-quizzes.
        </p>
        <div style="display: flex; gap: 8px;">
          <input type="text" id="infographic-input" class="chat-input" style="padding: 6px 10px; font-size: 0.8rem;" value="Photosynthesis">
          <button class="send-btn" style="padding: 6px 12px; font-size: 0.8rem;" onclick="generateInfographicWeb()">Generate</button>
        </div>
      </div>

      <!-- Syllabus Progress (Joe's Part C) -->
      <div class="panel">
        <div class="panel-title">
          <span>CS101 Syllabus Memory</span>
          <span style="color: var(--primary); font-size: 0.7rem;">12 Topics</span>
        </div>
        <div style="font-size: 0.75rem; color: var(--text-muted); line-height: 1.6;">
          <div>Completed: <strong style="color: var(--success);" id="covered-count">4</strong> / 12 topics</div>
          <div>Remaining: <strong style="color: #38bdf8;">8</strong> topics to cover</div>
        </div>
        <div style="width: 100%; height: 6px; background: rgba(255,255,255,0.08); border-radius: 3px; margin-top: 8px; overflow: hidden;">
          <div style="width: 33.3%; height: 100%; background: linear-gradient(to right, #6366f1, #06b6d4);"></div>
        </div>
      </div>

    </div>
  </div>

  <!-- Infographic Modal -->
  <div class="modal" id="info-modal">
    <div class="modal-content">
      <div class="modal-header">
        <span id="modal-title" style="font-weight: 600;">Revision Infographic</span>
        <button class="close-btn" onclick="closeModal()">&times;</button>
      </div>
      <iframe id="modal-iframe" class="modal-iframe"></iframe>
    </div>
  </div>

  <script>
    let chatHistory = [];

    async function checkStatus() {
      try {
        const res = await fetch('/api/status');
        const data = await res.json();
        document.getElementById('active-llm').innerText = data.active_provider;
      } catch (e) {
        console.error(e);
      }
    }
    checkStatus();

    function sendPreset(text) {
      document.getElementById('user-input').value = text;
      sendMessage();
    }

    function testWeatherPrompt() {
      sendPreset("Can I study outside today in Mumbai? Check the weather for me.");
    }

    function testSchedulePrompt() {
      sendPreset("I have an exam on 2026-09-18, 3 hours a day, topics: Algebra, Calculus, Matrices. Make me a schedule.");
    }

    function testSearchPrompt() {
      sendPreset("Give me a quick summary of the topic 'Theory of relativity'");
    }

    async function sendMessage() {
      const input = document.getElementById('user-input');
      const text = input.value.trim();
      if (!text) return;

      input.value = '';
      appendMessage('user', text);

      // Add loading message
      const loadingId = appendLoading();

      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: text, history: chatHistory })
        });
        const data = await res.json();
        removeLoading(loadingId);

        appendAssistantMessage(data.reply, data.tool_calls);
        if (data.history) chatHistory = data.history;

      } catch (err) {
        removeLoading(loadingId);
        appendMessage('assistant', 'Sorry, I encountered an issue contacting the agent server.');
      }
    }

    function appendMessage(role, content) {
      const window = document.getElementById('messages-window');
      const msgDiv = document.createElement('div');
      msgDiv.className = `message ${role}`;
      msgDiv.innerHTML = `
        <div class="avatar">${role === 'assistant' ? 'S' : 'U'}</div>
        <div class="bubble">${content}</div>
      `;
      window.appendChild(msgDiv);
      window.scrollTop = window.scrollHeight;
    }

    function appendAssistantMessage(text, toolCalls) {
      const window = document.getElementById('messages-window');
      const msgDiv = document.createElement('div');
      msgDiv.className = 'message assistant';

      let toolHtml = '';
      if (toolCalls && toolCalls.length > 0) {
        toolHtml += '<div class="tool-badge-container">';
        toolCalls.forEach(tc => {
          toolHtml += `
            <div>
              <div class="tool-pill">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>
                tool_use: ${tc.tool_name}
              </div>
            </div>
          `;
        });
        toolHtml += '</div>';
      }

      // Convert linebreaks
      const formatted = text.replace(/\\n/g, '<br>');

      msgDiv.innerHTML = `
        <div class="avatar">S</div>
        <div class="bubble">
          <div>${formatted}</div>
          ${toolHtml}
        </div>
      `;
      window.appendChild(msgDiv);
      window.scrollTop = window.scrollHeight;
    }

    function appendLoading() {
      const window = document.getElementById('messages-window');
      const id = 'loading-' + Date.now();
      const msgDiv = document.createElement('div');
      msgDiv.className = 'message assistant';
      msgDiv.id = id;
      msgDiv.innerHTML = `
        <div class="avatar">S</div>
        <div class="bubble" style="color: var(--text-muted); font-style: italic;">
          Sahayak is thinking & consulting tools...
        </div>
      `;
      window.appendChild(msgDiv);
      window.scrollTop = window.scrollHeight;
      return id;
    }

    function removeLoading(id) {
      const el = document.getElementById(id);
      if (el) el.remove();
    }

    async function generateInfographicWeb() {
      const topicInput = document.getElementById('infographic-input');
      const topic = topicInput.value.trim() || "Photosynthesis";
      const btn = event ? event.target : null;
      if (btn) {
        btn.innerText = "Generating...";
        btn.disabled = true;
      }
      try {
        const res = await fetch('/api/infographic', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ topic: topic })
        });
        const data = await res.json();
        if (data.status === 'success') {
          document.getElementById('modal-title').innerText = `Revision Infographic — ${data.topic}`;
          const iframe = document.getElementById('modal-iframe');
          iframe.srcdoc = data.html;
          document.getElementById('info-modal').style.display = 'flex';
        } else {
          alert('Infographic Error: ' + (data.error || 'Failed to generate content'));
        }
      } catch (e) {
        alert('Failed to contact infographic generator: ' + e.message);
      } finally {
        if (btn) {
          btn.innerText = "Generate";
          btn.disabled = false;
        }
      }
    }

    function closeModal() {
      document.getElementById('info-modal').style.display = 'none';
    }
  </script>
</body>
</html>
"""

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print("\n" + "=" * 60)
    print(f"  SAHAYAK Web Dashboard running at: http://localhost:{port}")
    print("=" * 60 + "\n")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
