"""Thuk: offline study documents with contents and keyword search."""
from .reference import SECTIONS, get_text, search, list_topics, get_topic, search_topics
from .answers import answer_question
__version__ = '1.2.1'
__all__ = ['SECTIONS', 'get_text', 'search', 'list_topics', 'get_topic', 'search_topics', 'answer_question']

