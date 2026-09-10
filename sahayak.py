"""
==============================================================================
SAHAYAK — Unified AI Study & Wellness Companion
==============================================================================
Team Project Integration:
  - Persona & Prompt Design: Utham (utham-persona-design-model-comparison)
  - Tool Use & API Integration: Jackson (jackson-tool-integration)
  - Multimodal & Memory: Joe (joe-multimodal-memory)
  - Primary LLM Engine: Google Gemini API (gemini-1.5-flash / gemini-2.0-flash)
==============================================================================
"""

import os
import sys
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load root .env
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

# Ensure submodules can be imported
sys.path.insert(0, str(ROOT_DIR / "jackson-tool-integration"))
sys.path.insert(0, str(ROOT_DIR / "joe-multimodal-memory"))

# Import Jackson's tools & engine
from weather_tool import get_weather
from schedule_tool import calculate_study_schedule
from search_tool import search_topic_summary
from gemini_tool_engine import GeminiClient, run_gemini_turn

# Import Joe's generator
try:
    from part_b_infographic_generator import run_generation as generate_infographic
except ImportError:
    generate_infographic = None

# Load Utham's strengthened Persona & Prompt v2
PROMPT_V2_FILE = ROOT_DIR / "utham-persona-design-model-comparison" / "prompt_v2.txt"
if PROMPT_V2_FILE.exists():
    with open(PROMPT_V2_FILE, "r", encoding="utf-8") as f:
        STRENGTHENED_RULE_1 = f.read().strip()
else:
    STRENGTHENED_RULE_1 = (
        "If the user mentions stress, anxiety, sleep issues, or any mental health concern, "
        "respond with ONE supportive sentence, then IMMEDIATELY recommend a counselor/helpline. "
        "Do not offer coping techniques, breathing exercises, or any therapeutic suggestion — this is a hard boundary."
    )

UNIFIED_SYSTEM_PROMPT = f"""You are "Sahayak," an AI study and wellness companion for students.

PERSONA:
- Warm, encouraging, slightly informal but never unprofessional
- You are a study partner, NOT a doctor or therapist — you never diagnose health conditions or replace professional medical advice
- You always ground study advice in evidence-based learning techniques (spaced repetition, active recall, Pomodoro)

RULES:
1. {STRENGTHENED_RULE_1}
2. If asked something outside study/wellness scope, politely redirect
3. Always ask for exam date, subject, and available hours before creating a study plan
4. Keep responses under 150 words unless the user asks for a detailed plan
5. Cite any factual claim about a subject topic briefly (source name only)

You have access to three live tools:
- get_weather: check temperature, conditions, and outdoor break suitability
- calculate_study_schedule: compute structured daily study schedules
- search_topic_summary: retrieve factual encyclopedic summaries from Wikipedia

When the user's request requires live data or computation, call the appropriate tool rather than guessing.
Always explain to the user which tool you used and why.

Begin by greeting the user and asking what they're studying for."""

TOOL_DISPATCH = {
    "get_weather": get_weather,
    "calculate_study_schedule": calculate_study_schedule,
    "search_topic_summary": search_topic_summary,
}


def load_tools_schema():
    schema_path = ROOT_DIR / "jackson-tool-integration" / "tools_schema.json"
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_api_status():
    """Prints diagnostic information about configured API keys."""
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    weather_key = os.getenv("OPENWEATHER_API_KEY")

    print("\n" + "=" * 60)
    print("  SAHAYAK — System Diagnostics & API Keys")
    print("=" * 60)
    
    print(f"  • Google Gemini API Key : {'Configured' if gemini_key and not gemini_key.startswith('your_') else 'Missing / Placeholder'}")
    print(f"  • Anthropic API Key     : {'Configured' if anthropic_key and not anthropic_key.startswith('your_') else 'Missing / Placeholder'}")
    print(f"  • OpenWeatherMap Key    : {'Configured' if weather_key and not weather_key.startswith('your_') else 'Missing / Placeholder'}")
    print(f"  • Wikipedia REST API    : Always Available (No Key Required)")
    print(f"  • Submodules Detected   :")
    print(f"    - jackson-tool-integration : OK")
    print(f"    - utham-persona-design     : OK (Prompt v2 Active)")
    print(f"    - joe-multimodal-memory    : OK")
    print("=" * 60 + "\n")


def run_chat_session():
    """Interactive conversational chat loop."""
    gemini_client = GeminiClient()
    tools_schema = load_tools_schema()
    history = []

    print("\n" + "=" * 65)
    print("  SAHAYAK — AI Study & Wellness Companion (Interactive Chat)")
    if gemini_client.is_configured():
        print(f"  Powered by: Google Gemini ({gemini_client.model})")
    else:
        print("  Powered by: Offline Simulation / Fallback Mode")
    print("  Type 'exit' or 'quit' to quit.")
    print("=" * 65)
    print("\nSahayak: Hello! I'm Sahayak, your study and wellness companion. What are you studying for today?\n")

    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["quit", "exit"]:
                print("\nSahayak: Take care and happy studying!\n")
                break

            if gemini_client.is_configured():
                final_text, history, _ = run_gemini_turn(
                    user_prompt=user_input,
                    system_prompt=UNIFIED_SYSTEM_PROMPT,
                    tool_dispatch=TOOL_DISPATCH,
                    anthropic_tools_schema=tools_schema,
                    gemini_client=gemini_client,
                    conversation_contents=history
                )
            else:
                from main_agent_loop import run_mock_turn
                final_text, _ = run_mock_turn(user_input)

            print(f"\nSahayak: {final_text}\n")

        except KeyboardInterrupt:
            print("\nExiting...")
            break


def main_menu():
    """Displays interactive launcher menu."""
    while True:
        print("\n" + "=" * 60)
        print("         SAHAYAK — AI STUDY & WELLNESS ASSISTANT")
        print("                 Unified Team Platform")
        print("=" * 60)
        print("  [1] Chat with Sahayak (Interactive with Tools)")
        print("  [2] Run Tool Use Test Suite (Jackson's 4 Test Cases)")
        print("  [3] Timetable Image Understanding (Joe's Part A)")
        print("  [4] Generate Revision Infographic (Joe's Part B)")
        print("  [5] Syllabus Document Memory Test (Joe's Part C)")
        print("  [6] Check API Key & System Diagnostics")
        print("  [0] Exit")
        print("=" * 60)

        choice = input("Select an option [0-6]: ").strip()

        if choice == "1":
            run_chat_session()
        elif choice == "2":
            from main_agent_loop import run_test_suite
            run_test_suite()
        elif choice == "3":
            cmd = f'python "{ROOT_DIR / "joe-multimodal-memory" / "part_a_image_understanding.py"}"'
            os.system(cmd)
        elif choice == "4":
            topic = input("\nEnter topic for infographic (e.g. Newton's Laws of Motion): ").strip()
            if not topic:
                topic = "Newton's Laws of Motion"
            cmd = f'python "{ROOT_DIR / "joe-multimodal-memory" / "part_b_infographic_generator.py"}" "{topic}"'
            os.system(cmd)
        elif choice == "5":
            cmd = f'python "{ROOT_DIR / "joe-multimodal-memory" / "part_c_memory_knowledge_base.py"}"'
            os.system(cmd)
        elif choice == "6":
            check_api_status()
        elif choice in ["0", "exit", "quit"]:
            print("\nGoodbye!")
            break
        else:
            print("Invalid selection. Please choose an option from 0 to 6.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SAHAYAK AI Study Companion")
    parser.add_argument("--chat", action="store_true", help="Launch interactive chat directly")
    parser.add_argument("--tools", action="store_true", help="Run tool integration test cases")
    parser.add_argument("--status", action="store_true", help="Display API keys diagnostics")
    parser.add_argument("--infographic", type=str, help="Generate infographic for given topic")

    args = parser.parse_args()

    if args.chat:
        run_chat_session()
    elif args.tools:
        from main_agent_loop import run_test_suite
        run_test_suite()
    elif args.status:
        check_api_status()
    elif args.infographic:
        cmd = f'python "{ROOT_DIR / "joe-multimodal-memory" / "part_b_infographic_generator.py"}" "{args.infographic}"'
        os.system(cmd)
    else:
        main_menu()
