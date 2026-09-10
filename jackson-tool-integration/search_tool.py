"""
Wikipedia Search Tool for SAHAYAK.
Fetches concise encyclopedic topic summaries and source references using the Wikipedia REST API.
Does not require an API key.
"""

import urllib.parse
import requests
import urllib3
from typing import Dict, Any
import json


def search_topic_summary(topic: str) -> Dict[str, Any]:
    """
    Fetches a concise topic summary and canonical article URL from Wikipedia REST API.

    Args:
        topic: Concept, academic term, or subject name (e.g. "Newton's laws of motion").

    Returns:
        Dict containing title, summary extract, source URL, and query status.
    """
    if not topic or not topic.strip():
        return {
            "status": "error",
            "error": "Topic cannot be empty. Please provide a subject or topic name."
        }

    clean_topic = topic.strip()
    # Wikipedia page titles use underscores instead of spaces
    formatted_title = urllib.parse.quote(clean_topic.replace(" ", "_"))
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{formatted_title}"

    headers = {
        "User-Agent": "SahayakStudentAssistant/1.0 (https://github.com/vedhanayagam07/SAHAYAK; academic-study-tool) requests/2.31"
    }

    try:
        # Try standard SSL verification first
        try:
            response = requests.get(url, headers=headers, timeout=10)
        except requests.exceptions.SSLError:
            # Fallback for environments with untrusted root certificates or corporate proxies
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            response = requests.get(url, headers=headers, timeout=10, verify=False)

        if response.status_code == 404:
            return {
                "status": "error",
                "error": f"Topic '{clean_topic}' was not found on Wikipedia. Please check spelling or try a more general term.",
                "topic": clean_topic
            }

        response.raise_for_status()
        data = response.json()

        page_type = data.get("type", "standard")
        title = data.get("title", clean_topic)
        extract = data.get("extract", "")
        description = data.get("description", "")
        
        content_urls = data.get("content_urls", {})
        desktop_url = content_urls.get("desktop", {}).get("page") or f"https://en.wikipedia.org/wiki/{formatted_title}"

        if page_type == "disambiguation":
            return {
                "status": "disambiguation",
                "title": title,
                "description": description,
                "summary": extract or f"'{title}' may refer to multiple concepts. Please specify a more precise academic term.",
                "source_url": desktop_url,
                "topic": clean_topic
            }

        return {
            "status": "success",
            "title": title,
            "description": description,
            "summary": extract if extract else "No summary extract available for this topic.",
            "source_url": desktop_url,
            "topic": clean_topic
        }

    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "error": "Request to Wikipedia timed out. Please try again later.",
            "topic": clean_topic
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error": f"Failed to retrieve topic summary from Wikipedia: {str(e)}",
            "topic": clean_topic
        }


if __name__ == "__main__":
    import sys
    test_q = sys.argv[1] if len(sys.argv) > 1 else "Newton's laws of motion"
    print(f"Testing search_topic_summary('{test_q}')...")
    res = search_topic_summary(test_q)
    print(json.dumps(res, indent=2))
