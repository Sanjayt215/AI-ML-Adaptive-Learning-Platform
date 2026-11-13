import os
import sys
import unittest

ROOT_DIR = os.path.dirname(__file__)
sys.path.insert(0, ROOT_DIR)

from services import llm_tutor_service
from services.catalog_service import _canonical_topic


class TestLLMTutorService(unittest.TestCase):
    def test_detect_topic_generic_ai_question_routes_to_llm(self):
        selected_topics = ['model deployment', 'nlp']
        topic = llm_tutor_service._detect_topic('What is AI?', selected_topics)
        self.assertEqual(topic, 'llm')

    def test_canonical_topic_alias_ai_maps_to_llm(self):
        self.assertEqual(_canonical_topic('ai'), 'llm')
        self.assertEqual(_canonical_topic('artificial intelligence'), 'llm')
        self.assertEqual(_canonical_topic('gpt'), 'llm')


if __name__ == '__main__':
    unittest.main()
