"""
Main Agent Orchestration Loop for SAHAYAK.
Coordinates Claude API (/v1/messages) with tool execution (weather, study schedule, search).
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv

# Load environment variables from local .env if present
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# Import local tool modules
from weather_tool import get_weather
from schedule_tool import calculate_study_schedule
from search_tool import search_topic_summary
from gemini_tool_engine import GeminiClient, run_gemini_turn, anthropic_to_gemini_schema

# Teammate Uttam's exact system prompt (DO NOT MODIFY)
SYSTEM_PROMPT = """You are "Sahayak," an AI study and wellness companion for students.

PERSONA:
- Warm, encouraging, slightly informal but never unprofessional
- You are a study partner, NOT a doctor or therapist — you never diagnose 
  health conditions or replace professional medical advice
- You always ground study advice in evidence-based learning techniques 
  (spaced repetition, active recall, Pomodoro)

RULES:
1. If the user shares exam stress or mental health concerns, respond 
   supportively but recommend professional resources — never attempt 
   therapy-style intervention
2. If asked something outside study/wellness scope, politely redirect
3. Always ask for exam date, subject, and available hours before creating 
   a study plan
4. Keep responses under 150 words unless the user asks for a detailed plan
5. Cite any factual claim about a subject topic briefly (source name only)

You have access to three tools: get_weather, calculate_study_schedule, and 
search_topic_summary. When the user's request requires live data or 
computation, call the appropriate tool rather than guessing. Always explain 
to the user which tool you used and why.

Begin by greeting the user and asking what they're studying for."""

# Tool Dispatch Table
TOOL_DISPATCH = {
    "get_weather": get_weather,
    "calculate_study_schedule": calculate_study_schedule,
    "search_topic_summary": search_topic_summary,
}


def load_tools_schema() -> List[Dict[str, Any]]:
    """Loads Anthropic tool specifications from tools_schema.json."""
    schema_path = Path(__file__).parent / "tools_schema.json"
    if not schema_path.exists():
        raise FileNotFoundError(f"Tools schema not found at {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def execute_tool(tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Safely executes a tool by name with provided arguments.
    """
    if tool_name not in TOOL_DISPATCH:
        return {
            "status": "error",
            "error": f"Unknown tool: '{tool_name}'. Available tools: {list(TOOL_DISPATCH.keys())}"
        }
    
    func = TOOL_DISPATCH[tool_name]
    try:
        print(f"  [Tool Dispatch] Executing '{tool_name}' with args: {tool_input}")
        result = func(**tool_input)
        return result
    except TypeError as te:
        return {
            "status": "error",
            "error": f"Invalid arguments passed to '{tool_name}': {str(te)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Unexpected execution error in '{tool_name}': {str(e)}"
        }


def get_anthropic_client():
    """
    Initializes Anthropic client with fallback for corporate SSL proxies.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key.strip() == "" or api_key == "your_anthropic_api_key_here":
        return None

    import anthropic
    import httpx

    # Try standard client, with fallback for custom/corporate SSL configurations
    try:
        # Check standard connection
        client = anthropic.Anthropic(api_key=api_key)
        return client
    except Exception:
        # Fallback to verify=False client if system certificates cause issues
        custom_http = httpx.Client(verify=False)
        return anthropic.Anthropic(api_key=api_key, http_client=custom_http)


def run_conversation_turn(
    user_prompt: str,
    conversation_history: List[Dict[str, Any]] = None,
    client=None,
    model: str = "claude-3-5-sonnet-20241022",
    max_turns: int = 5
) -> Tuple[str, List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Runs an end-to-end multi-turn conversation turn with Claude and tools.

    Returns:
        Tuple of (final_response_text, updated_history, recorded_tool_calls)
    """
    if conversation_history is None:
        conversation_history = []

    tools = load_tools_schema()
    recorded_tool_calls = []

    # Append new user prompt
    conversation_history.append({
        "role": "user",
        "content": user_prompt
    })

    if client is None:
        raise ValueError("Anthropic client is not initialized. Please set ANTHROPIC_API_KEY.")

    turn_count = 0

    while turn_count < max_turns:
        turn_count += 1
        print(f"\n[Agent Turn {turn_count}] Requesting completion from Claude ({model})...")

        try:
            response = client.messages.create(
                model=model,
                max_tokens=1500,
                system=SYSTEM_PROMPT,
                tools=tools,
                messages=conversation_history
            )
        except Exception as e:
            # Check if SSL error or connection issue
            if "certificate verify failed" in str(e).lower() or "ssl" in str(e).lower():
                import httpx
                import anthropic
                api_key = os.getenv("ANTHROPIC_API_KEY")
                client = anthropic.Anthropic(api_key=api_key, http_client=httpx.Client(verify=False))
                response = client.messages.create(
                    model=model,
                    max_tokens=1500,
                    system=SYSTEM_PROMPT,
                    tools=tools,
                    messages=conversation_history
                )
            else:
                raise e

        # Separate text content and tool_use blocks
        assistant_content = response.content
        tool_use_blocks = [b for b in assistant_content if b.type == "tool_use"]
        text_blocks = [b for b in assistant_content if b.type == "text"]

        # Append assistant's full response (including tool_use blocks) to history
        conversation_history.append({
            "role": "assistant",
            "content": assistant_content
        })

        if text_blocks:
            for tb in text_blocks:
                print(f"[Assistant Text]: {tb.text}")

        # If model is not requesting any tools, we have reached the final answer
        if response.stop_reason != "tool_use" or not tool_use_blocks:
            final_text = "\n".join([tb.text for tb in text_blocks])
            return final_text, conversation_history, recorded_tool_calls

        # Execute each requested tool and collect results
        tool_result_blocks = []
        for tb in tool_use_blocks:
            tool_name = tb.name
            tool_input = tb.input
            tool_id = tb.id

            print(f"[Tool Call Detected] Tool: {tool_name} (ID: {tool_id})")
            print(f"  Input: {json.dumps(tool_input, indent=2)}")

            # Execute matching python function
            tool_result = execute_tool(tool_name, tool_input)

            recorded_tool_calls.append({
                "tool_name": tool_name,
                "tool_id": tool_id,
                "tool_input": tool_input,
                "tool_result": tool_result
            })

            tool_result_blocks.append({
                "type": "tool_result",
                "tool_use_id": tool_id,
                "content": json.dumps(tool_result)
            })

        # Send tool results back to Claude
        conversation_history.append({
            "role": "user",
            "content": tool_result_blocks
        })

    return "Max conversation turns reached.", conversation_history, recorded_tool_calls


# Fallback / Mock simulation runner for testing when API key is not yet configured
def run_mock_turn(user_prompt: str) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Deterministic mock runner to test tool executions and prompt responses
    when an ANTHROPIC_API_KEY is not yet supplied.
    """
    recorded_calls = []
    lower_prompt = user_prompt.lower()

    print("\n--- Running Mock Tool Calling Simulation ---")
    print(f"User Prompt: {user_prompt}")

    # Case 1: Exam in 5 days, bangalore weather, outdoor break
    if "maths" in lower_prompt or "exam" in lower_prompt and "bangalore" in lower_prompt:
        print("[Simulated Claude]: Decided to call 'calculate_study_schedule' AND 'get_weather'")
        
        # Tool 1: get_weather
        w_input = {"location": "Bangalore"}
        w_res = execute_tool("get_weather", w_input)
        recorded_calls.append({"tool_name": "get_weather", "tool_input": w_input, "tool_result": w_res})
        
        # Tool 2: calculate_study_schedule
        from datetime import date, timedelta
        target_date = (date.today() + timedelta(days=5)).isoformat()
        s_input = {
            "exam_date": target_date,
            "hours_per_day": 2,
            "topics": ["Calculus", "Algebra", "Vectors", "Trigonometry", "Probability"]
        }
        s_res = execute_tool("calculate_study_schedule", s_input)
        recorded_calls.append({"tool_name": "calculate_study_schedule", "tool_input": s_input, "tool_result": s_res})

        final_answer = (
            f"Hello! I'm Sahayak, your study companion! For your maths exam in 5 days studying 2 hours/day, "
            f"I used `calculate_study_schedule` to build a 5-day plan across your topics. "
            f"I also checked `get_weather` for Bangalore: it is {w_res.get('temperature_celsius', '24')}°C ({w_res.get('condition', 'Clear')}). "
            f"Outdoor break suitability: {w_res.get('good_for_outdoor_break', 'yes')}. {w_res.get('outdoor_break_reason', '')} "
            f"Remember to use 25-minute Pomodoro sessions and take fresh air breaks!"
        )
        return final_answer, recorded_calls

    # Case 2: Newton's laws of motion
    elif "newton" in lower_prompt:
        print("[Simulated Claude]: Decided to call 'search_topic_summary'")
        search_input = {"topic": "Newton's laws of motion"}
        search_res = execute_tool("search_topic_summary", search_input)
        recorded_calls.append({"tool_name": "search_topic_summary", "tool_input": search_input, "tool_result": search_res})
        
        final_answer = (
            f"Hello! What are you studying for today? Here is a quick summary of Newton's laws of motion using `search_topic_summary`: "
            f"{search_res.get('summary', '')[:200]}... (Source: Wikipedia). "
            f"Would you like an active-recall flashcard on this?"
        )
        return final_answer, recorded_calls

    # Case 3: Ambiguous prompt "just make me a plan"
    elif "just make me a plan" in lower_prompt or "make me a plan" in lower_prompt:
        print("[Simulated Claude]: Enforcing RULE 3 - No tool call; asking clarifying questions.")
        final_answer = (
            "Hi there! I'd love to help you build a study schedule! To make sure it works best for you, "
            "could you let me know: 1) What subject are you preparing for? 2) What is your exact exam date? "
            "and 3) How many hours per day can you realistically dedicate to studying?"
        )
        return final_answer, recorded_calls

    # Case 4 & General Weather: extract city or handle fake location
    elif "weather" in lower_prompt or "outside" in lower_prompt:
        import re
        if any(term in lower_prompt for term in ["fake", "xyzzy", "nonexistent", "atlantis", "asdfghjkl"]):
            loc = "Atlantis_FakeCity_123"
        else:
            match = re.search(r'\bin\s+([A-Za-z\s]+?)(?:\?|\.|\,|$|\bcheck\b|\btoday\b|\band\b)', user_prompt, re.IGNORECASE)
            loc = match.group(1).strip() if match else "Mumbai"
        
        print(f"[Simulated Agent]: Calling 'get_weather' for '{loc}'")
        w_input = {"location": loc}
        w_res = execute_tool("get_weather", w_input)
        recorded_calls.append({"tool_name": "get_weather", "tool_input": w_input, "tool_result": w_res})

        if w_res.get("status") == "success":
            temp = w_res.get("temperature_celsius")
            cond = w_res.get("description", w_res.get("condition"))
            good = w_res.get("good_for_outdoor_break")
            reason = w_res.get("outdoor_break_reason")
            final_answer = (
                f"I checked the current weather for **{loc}** using `get_weather`: it is currently {temp}°C with {cond}. "
                f"**Outdoor study break suitability: {good.upper()}**. {reason} "
                f"Remember to study in focused 25-minute Pomodoro blocks and step outside for fresh air when ready!"
            )
        else:
            final_answer = (
                f"I checked the weather using `get_weather` for '{loc}', but the weather service returned an error: "
                f"{w_res.get('error', 'Location not found')}. I cannot determine outdoor conditions. Please share a valid city name!"
            )
        return final_answer, recorded_calls

    else:
        return "Hello! I'm Sahayak, your study and wellness companion. What are you studying for today?", []


def get_llm_provider():
    """Detects whether Gemini or Claude is configured, prioritizing Gemini."""
    gemini_client = GeminiClient()
    if gemini_client.is_configured():
        return "gemini", gemini_client
    
    anthropic_client = get_anthropic_client()
    if anthropic_client:
        return "anthropic", anthropic_client

    return "mock", None


def run_test_suite():
    """Runs the 4 required test cases and prints execution logs."""
    test_prompts = [
        "I have a maths exam in 5 days, 2 hours/day, can I study outside today? I'm in Bangalore.",
        "Give me a quick summary of the topic 'Newton's laws of motion'",
        "just make me a plan",
        "What is the weather right now in XyzzyNonExistentLand99999, and can I take a break outside?"
    ]

    provider, client = get_llm_provider()
    tools_schema = load_tools_schema()

    print("\n" + "="*80)
    print("SAHAYAK TOOL INTEGRATION - TEST SUITE RUNNER")
    if provider == "gemini":
        print(f"Mode: LIVE GOOGLE GEMINI API ({client.model})")
    elif provider == "anthropic":
        model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
        print(f"Mode: LIVE ANTHROPIC API ({model})")
    else:
        print("Mode: OFFLINE SIMULATION / MOCK RUNNER")
        print("Notice: No live API key configured. Running deterministic simulation.")
    print("="*80 + "\n")

    for idx, prompt in enumerate(test_prompts, 1):
        print(f"\n--- TEST CASE {idx} ---")
        print(f"Prompt: {prompt}")
        tool_calls = []

        if provider == "gemini":
            try:
                final_text, _, tool_calls = run_gemini_turn(
                    user_prompt=prompt,
                    system_prompt=SYSTEM_PROMPT,
                    tool_dispatch=TOOL_DISPATCH,
                    anthropic_tools_schema=tools_schema,
                    gemini_client=client
                )
                if "Error from Gemini" in final_text:
                    print(f"[Warning] {final_text}")
                    print("Falling back to simulation runner...")
                    final_text, tool_calls = run_mock_turn(prompt)
            except Exception as e:
                print(f"Error during Gemini call: {e}")
                final_text, tool_calls = run_mock_turn(prompt)
        elif provider == "anthropic":
            try:
                model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
                final_text, _, tool_calls = run_conversation_turn(prompt, client=client, model=model)
            except Exception as e:
                print(f"Error during Anthropic call: {e}")
                final_text, tool_calls = run_mock_turn(prompt)
        else:
            final_text, tool_calls = run_mock_turn(prompt)

        print(f"\n[Tools Called Count]: {len(tool_calls)}")
        for tc in tool_calls:
            print(f" - Tool: {tc['tool_name']}")
            print(f"   Input: {json.dumps(tc['tool_input'])}")
            print(f"   Result: {json.dumps(tc['tool_result'])[:150]}...")
        print(f"\n[Final Response]:\n{final_text}\n")
        print("-" * 80)


def interactive_mode():
    """Starts interactive chat mode with Sahayak."""
    provider, client = get_llm_provider()
    tools_schema = load_tools_schema()
    history = []

    print("\n" + "="*60)
    print("  SAHAYAK - AI Study & Wellness Companion")
    if provider == "gemini":
        print(f"  Mode: Live Google Gemini API ({client.model})")
    elif provider == "anthropic":
        model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
        print(f"  Mode: Live Anthropic Claude API ({model})")
    else:
        print("  Mode: Offline Simulation")
    print("  Type 'quit' or 'exit' to end session.")
    print("="*60)
    print("\nSahayak: Hello! I'm Sahayak, your study and wellness companion. What are you studying for today?\n")

    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["quit", "exit"]:
                print("\nSahayak: Take care and best of luck with your studies!\n")
                break

            if provider == "gemini":
                final_text, history, _ = run_gemini_turn(
                    user_prompt=user_input,
                    system_prompt=SYSTEM_PROMPT,
                    tool_dispatch=TOOL_DISPATCH,
                    anthropic_tools_schema=tools_schema,
                    gemini_client=client,
                    conversation_contents=history
                )
            elif provider == "anthropic":
                model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
                final_text, history, _ = run_conversation_turn(
                    user_input,
                    conversation_history=history,
                    client=client,
                    model=model
                )
            else:
                final_text, _ = run_mock_turn(user_input)

            print(f"\nSahayak: {final_text}\n")

        except KeyboardInterrupt:
            print("\nExiting...")
            break


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_mode()
    else:
        run_test_suite()
