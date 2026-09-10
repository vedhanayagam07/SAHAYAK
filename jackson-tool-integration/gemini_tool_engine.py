"""
Gemini Tool Engine for SAHAYAK.
Provides high-performance, robust Google Gemini API integration (gemini-1.5-flash / gemini-2.0-flash)
with full support for Tool Use (Function Calling) and Multimodal (Vision) via standard HTTPS REST.
"""

import os
import json
import base64
from typing import List, Dict, Any, Tuple, Optional
import requests
import urllib3

# Disable warnings if corporate/system SSL verification fallback is needed
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def anthropic_to_gemini_schema(anthropic_tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Converts Anthropic tool specifications to Google Gemini function declarations.
    """
    function_declarations = []
    for tool in anthropic_tools:
        input_schema = tool.get("input_schema", {})
        
        # Deep copy and format properties
        def normalize_schema(sch: Dict[str, Any]) -> Dict[str, Any]:
            norm = {}
            for k, v in sch.items():
                if k == "type" and isinstance(v, str):
                    norm["type"] = v.upper()
                elif k == "properties" and isinstance(v, dict):
                    norm["properties"] = {pk: normalize_schema(pv) for pk, pv in v.items()}
                elif k == "items" and isinstance(v, dict):
                    norm["items"] = normalize_schema(v)
                else:
                    norm[k] = v
            return norm

        gemini_parameters = normalize_schema(input_schema)
        function_declarations.append({
            "name": tool["name"],
            "description": tool.get("description", ""),
            "parameters": gemini_parameters
        })

    return function_declarations


class GeminiClient:
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-1.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.model = os.getenv("GEMINI_MODEL", model)
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip() and not self.api_key.startswith("your_"))

    def generate_content(
        self,
        contents: List[Dict[str, Any]],
        system_instruction: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.4
    ) -> Dict[str, Any]:
        """
        Calls Gemini generateContent endpoint with support for system instructions and tools.
        """
        if not self.is_configured():
            raise ValueError("GEMINI_API_KEY (or GOOGLE_API_KEY) is not set.")

        headers = {"Content-Type": "application/json"}
        params = {"key": self.api_key}

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 1500
            }
        }

        if system_instruction:
            payload["system_instruction"] = {
                "parts": [{"text": system_instruction}]
            }

        if tools:
            payload["tools"] = [{"function_declarations": tools}]

        try:
            try:
                response = requests.post(self.base_url, headers=headers, params=params, json=payload, timeout=30)
            except requests.exceptions.SSLError:
                response = requests.post(self.base_url, headers=headers, params=params, json=payload, timeout=30, verify=False)

            if response.status_code != 200:
                return {
                    "error": f"Gemini API returned status {response.status_code}: {response.text}"
                }

            return response.json()

        except Exception as e:
            return {"error": f"Failed to contact Gemini API: {str(e)}"}


def run_gemini_turn(
    user_prompt: str,
    system_prompt: str,
    tool_dispatch: Dict[str, Any],
    anthropic_tools_schema: List[Dict[str, Any]],
    gemini_client: GeminiClient,
    conversation_contents: Optional[List[Dict[str, Any]]] = None,
    image_bytes: Optional[bytes] = None,
    image_mime: str = "image/png",
    max_turns: int = 5
) -> Tuple[str, List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Executes a complete multi-turn tool calling turn using Gemini API.
    """
    if conversation_contents is None:
        conversation_contents = []

    gemini_tools = anthropic_to_gemini_schema(anthropic_tools_schema)
    recorded_tool_calls = []

    # Build user message parts
    user_parts: List[Dict[str, Any]] = []
    if image_bytes:
        user_parts.append({
            "inline_data": {
                "mime_type": image_mime,
                "data": base64.b64encode(image_bytes).decode("utf-8")
            }
        })
    user_parts.append({"text": user_prompt})

    conversation_contents.append({
        "role": "user",
        "parts": user_parts
    })

    turn_count = 0
    while turn_count < max_turns:
        turn_count += 1
        print(f"\n[Gemini Turn {turn_count}] Requesting completion from {gemini_client.model}...")

        data = gemini_client.generate_content(
            contents=conversation_contents,
            system_instruction=system_prompt,
            tools=gemini_tools
        )

        if "error" in data:
            return f"Error from Gemini: {data['error']}", conversation_contents, recorded_tool_calls

        candidates = data.get("candidates", [])
        if not candidates:
            return "No response candidate generated by Gemini.", conversation_contents, recorded_tool_calls

        candidate = candidates[0]
        content = candidate.get("content", {})
        parts = content.get("parts", [])

        # Append model response to conversation history
        conversation_contents.append(content)

        function_calls = []
        text_chunks = []

        for p in parts:
            if "functionCall" in p:
                function_calls.append(p["functionCall"])
            if "text" in p:
                text_chunks.append(p["text"])

        if text_chunks:
            for txt in text_chunks:
                print(f"[Gemini Text]: {txt}")

        # If no tool was requested, we are done
        if not function_calls:
            final_text = "\n".join(text_chunks)
            return final_text, conversation_contents, recorded_tool_calls

        # Process function calls
        function_responses_parts = []
        for fc in function_calls:
            fn_name = fc.get("name")
            fn_args = fc.get("args", {})

            print(f"[Gemini Tool Call] {fn_name}({json.dumps(fn_args)})")

            if fn_name in tool_dispatch:
                try:
                    tool_res = tool_dispatch[fn_name](**fn_args)
                except Exception as ex:
                    tool_res = {"status": "error", "error": str(ex)}
            else:
                tool_res = {"status": "error", "error": f"Unknown tool: {fn_name}"}

            recorded_tool_calls.append({
                "tool_name": fn_name,
                "tool_input": fn_args,
                "tool_result": tool_res
            })

            function_responses_parts.append({
                "functionResponse": {
                    "name": fn_name,
                    "response": {
                        "name": fn_name,
                        "content": tool_res
                    }
                }
            })

        # Append tool outputs back to conversation for Gemini
        conversation_contents.append({
            "role": "user",
            "parts": function_responses_parts
        })

    return "Max conversation turns reached with Gemini.", conversation_contents, recorded_tool_calls
