"""
Unit tests for SAHAYAK Tool Integration module.
Tests edge cases, error handling, and structured outputs for all tools.
"""

import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import date, timedelta
from schedule_tool import calculate_study_schedule
from search_tool import search_topic_summary
from weather_tool import get_weather


class TestStudyScheduleTool(unittest.TestCase):
    def test_valid_schedule_even_split(self):
        exam_date = (date.today() + timedelta(days=4)).isoformat()
        topics = ["Topic A", "Topic B", "Topic C", "Topic D"]
        res = calculate_study_schedule(exam_date, 2, topics)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["days_remaining"], 4)
        self.assertEqual(len(res["schedule"]), 4)

    def test_more_topics_than_days(self):
        exam_date = (date.today() + timedelta(days=2)).isoformat()
        topics = ["T1", "T2", "T3", "T4", "T5"]
        res = calculate_study_schedule(exam_date, 3, topics)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["days_remaining"], 2)
        # 5 topics across 2 days -> Day 1 gets 3 topics, Day 2 gets 2 topics
        self.assertEqual(len(res["schedule"]["day_1"]["topics"]), 3)
        self.assertEqual(len(res["schedule"]["day_2"]["topics"]), 2)

    def test_fewer_topics_than_days(self):
        exam_date = (date.today() + timedelta(days=3)).isoformat()
        topics = ["Single Topic"]
        res = calculate_study_schedule(exam_date, 1.5, topics)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["days_remaining"], 3)
        self.assertEqual(res["schedule"]["day_1"]["topics"], ["Single Topic"])
        self.assertIn("Revision", res["schedule"]["day_2"]["topics"][0])

    def test_past_exam_date(self):
        past_date = (date.today() - timedelta(days=2)).isoformat()
        res = calculate_study_schedule(past_date, 2, ["Algebra"])
        self.assertEqual(res["status"], "error")
        self.assertIn("past", res["error"])

    def test_zero_or_negative_hours(self):
        exam_date = (date.today() + timedelta(days=5)).isoformat()
        res_zero = calculate_study_schedule(exam_date, 0, ["Algebra"])
        self.assertEqual(res_zero["status"], "error")

        res_neg = calculate_study_schedule(exam_date, -2, ["Algebra"])
        self.assertEqual(res_neg["status"], "error")

    def test_empty_topics(self):
        exam_date = (date.today() + timedelta(days=5)).isoformat()
        res = calculate_study_schedule(exam_date, 2, [])
        self.assertEqual(res["status"], "error")


class TestWikipediaSearchTool(unittest.TestCase):
    def test_valid_search(self):
        res = search_topic_summary("Photosynthesis")
        self.assertIn(res["status"], ["success", "disambiguation"])
        self.assertIn("source_url", res)
        self.assertTrue("wikipedia.org" in res["source_url"])

    def test_not_found_topic(self):
        res = search_topic_summary("RandomNonExistentTopic999988887777")
        self.assertEqual(res["status"], "error")
        self.assertIn("not found", res["error"].lower())

    def test_empty_topic(self):
        res = search_topic_summary("")
        self.assertEqual(res["status"], "error")


class TestWeatherTool(unittest.TestCase):
    def test_empty_location(self):
        res = get_weather("")
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["good_for_outdoor_break"], "no")

    def test_unconfigured_api_key_graceful_handling(self):
        # Without key set, it should return an informative error, not raise an exception
        res = get_weather("Tokyo")
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["good_for_outdoor_break"], "no")


if __name__ == "__main__":
    unittest.main()
