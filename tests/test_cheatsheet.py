import contextlib
import io
import unittest
from unittest.mock import patch

from thuk import SECTIONS, answer_question, get_text, get_topic, list_topics, search_topics
from thuk.cli import main


class CheatsheetTests(unittest.TestCase):
    def test_complete_sections_and_separate_columns(self):
        self.assertEqual(SECTIONS[6][0], 'Docker CLI Cheat Sheet')
        self.assertEqual([t['title'] for t in list_topics(6)], [
            'Document introduction', 'INSTALLATION', 'GENERAL COMMANDS',
            'IMAGES', 'CONTAINERS', 'DOCKER HUB'])
        images = get_topic(6, 4)
        self.assertIn('docker image prune', images)
        self.assertNotIn('docker run', images)
        self.assertIn('docker exec -it', get_topic(6, 5))
        self.assertIn('docker push', get_topic(6, 6))
        self.assertEqual(''.join(get_topic(6, n) for n in range(1, 7)), get_text(6))

    def test_search_and_answer_include_new_document(self):
        self.assertEqual(search_topics('docker exec', 6)[0]['title'], 'CONTAINERS')
        result = answer_question('docker container stats', 6)
        self.assertTrue(result['found'])
        self.assertTrue(all(s['section'] == 6 for s in result['sources']))
        self.assertIn('docker container stats', result['answer'])

    def test_menu_and_return_navigation(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), patch('builtins.input', side_effect=['6', '4', '0', '0']):
            self.assertEqual(main(['--plain']), 0)
        text = output.getvalue()
        self.assertIn('6. Docker CLI Cheat Sheet', text)
        self.assertIn('7. Answer a question', text)
        self.assertEqual(text.count('Docker CLI Cheat Sheet - Contents'), 2)
        self.assertEqual(text.count('\nTHUK\n'), 2)


if __name__ == '__main__':
    unittest.main()
