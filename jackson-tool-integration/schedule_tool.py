"""
Study schedule calculation tool for SAHAYAK.
Pure computational function that plans a structured day-by-day study schedule
based on exam date, daily study capacity, and topics to be covered.
"""

from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Union
import json


def calculate_study_schedule(
    exam_date: str,
    hours_per_day: Union[int, float],
    topics: List[str]
) -> Dict[str, Any]:
    """
    Computes a day-by-day study schedule leading up to an exam date.

    Args:
        exam_date: Date of the exam in 'YYYY-MM-DD' format.
        hours_per_day: Number of study hours available each day (> 0).
        topics: List of topics or chapters to cover.

    Returns:
        Dict containing validation status, summary metrics, and day-by-day breakdown:
        {
            "status": "success" | "error",
            "days_remaining": int,
            "total_topics": int,
            "hours_per_day": float,
            "total_study_hours": float,
            "schedule": {
                "day_1": {"date": "YYYY-MM-DD", "topics": [...], "hours": X, "focus": "..."},
                ...
            }
        }
    """
    # 1. Validate hours_per_day
    try:
        hours = float(hours_per_day)
        if hours <= 0:
            return {
                "status": "error",
                "error": f"Invalid hours_per_day ({hours_per_day}). Study hours must be greater than 0."
            }
    except (TypeError, ValueError):
        return {
            "status": "error",
            "error": f"Invalid hours_per_day '{hours_per_day}'. Expected a numeric value greater than 0."
        }

    # 2. Validate topics
    if not isinstance(topics, list) or len(topics) == 0:
        return {
            "status": "error",
            "error": "Topics list cannot be empty. Please provide at least one topic to study."
        }
    
    clean_topics = [str(t).strip() for t in topics if str(t).strip()]
    if not clean_topics:
        return {
            "status": "error",
            "error": "All provided topics were empty strings. Please provide valid topic names."
        }

    # 3. Validate exam_date
    if not isinstance(exam_date, str) or not exam_date.strip():
        return {
            "status": "error",
            "error": "Exam date cannot be empty. Please provide a date in YYYY-MM-DD format."
        }

    try:
        parsed_exam_date = datetime.strptime(exam_date.strip(), "%Y-%m-%d").date()
    except ValueError:
        return {
            "status": "error",
            "error": f"Invalid exam_date format '{exam_date}'. Please use YYYY-MM-DD format (e.g., '2026-09-20')."
        }

    today = date.today()
    days_remaining = (parsed_exam_date - today).days

    if days_remaining < 0:
        return {
            "status": "error",
            "error": f"Exam date ({exam_date}) is in the past ({abs(days_remaining)} day(s) ago). Please provide a future exam date.",
            "days_remaining": days_remaining
        }
    elif days_remaining == 0:
        return {
            "status": "error",
            "error": f"Exam date is today ({exam_date})! Multi-day schedule cannot be generated. Recommended: Light review of high-yield notes and prioritize rest before the exam.",
            "days_remaining": 0
        }

    # 4. Partition topics across remaining days
    num_topics = len(clean_topics)
    schedule = {}
    
    # Even distribution algorithm:
    # If more days than topics: first N days each get 1 topic, remaining days are dedicated to revision/mock test
    # If more topics than days: topics are evenly chunked with remainder distributed across earliest days
    
    if days_remaining >= num_topics:
        # Each topic gets its own day; extra days are dedicated review & practice
        for i in range(days_remaining):
            day_num = i + 1
            current_day_date = today + timedelta(days=i)
            date_str = current_day_date.isoformat()
            key = f"day_{day_num}"

            if i < num_topics:
                schedule[key] = {
                    "date": date_str,
                    "topics": [clean_topics[i]],
                    "hours": hours,
                    "focus": f"Deep study & active recall for '{clean_topics[i]}'"
                }
            else:
                schedule[key] = {
                    "date": date_str,
                    "topics": ["Full Revision & Practice Questions"],
                    "hours": hours,
                    "focus": "Spaced repetition, solving past paper questions, and weak-area review"
                }
    else:
        # More topics than days: distribute topics into chunks
        base_chunk = num_topics // days_remaining
        remainder = num_topics % days_remaining
        start_idx = 0

        for i in range(days_remaining):
            day_num = i + 1
            current_day_date = today + timedelta(days=i)
            date_str = current_day_date.isoformat()
            key = f"day_{day_num}"

            chunk_len = base_chunk + (1 if i < remainder else 0)
            assigned_topics = clean_topics[start_idx : start_idx + chunk_len]
            start_idx += chunk_len

            schedule[key] = {
                "date": date_str,
                "topics": assigned_topics,
                "hours": hours,
                "focus": f"Study {len(assigned_topics)} topic(s) using Pomodoro blocks"
            }

    return {
        "status": "success",
        "exam_date": exam_date,
        "days_remaining": days_remaining,
        "total_topics": num_topics,
        "hours_per_day": hours,
        "total_study_hours": round(days_remaining * hours, 1),
        "schedule": schedule
    }


if __name__ == "__main__":
    test_date = (date.today() + timedelta(days=5)).isoformat()
    test_topics = ["Calculus", "Linear Algebra", "Probability", "Differential Equations", "Statistics"]
    print("Testing calculate_study_schedule with 5 days & 5 topics:")
    res = calculate_study_schedule(test_date, 2, test_topics)
    print(json.dumps(res, indent=2))
