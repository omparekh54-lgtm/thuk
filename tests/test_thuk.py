import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from thuk import get_text, list_topics, get_topic, search_topics
from thuk.cli import main, highlight
from thuk.reference import export_pdf, resource


class ThukTests(unittest.TestCase):
    def run_cli(self, args, answers=()):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output), patch('builtins.input', side_effect=list(answers)):
            code = main(args)
        return code, output.getvalue()

    def test_all_documents_indexed_and_full_text_preserved(self):
        for document in range(1, 6):
            topics = list_topics(document)
            lines = get_text(document).splitlines(keepends=True)
            self.assertGreater(len(topics), 5)
            major = [item for item in topics if item['level'] == 1]
            # Chapters partition every line, including introduction and last page.
            self.assertEqual(''.join(''.join(lines[t['start']:t['end']]) for t in major), get_text(document))
            for i, topic in enumerate(topics, 1):
                self.assertGreater(topic['end'], topic['start'])
                self.assertTrue(get_topic(document, i).strip())
                if i > 1:
                    self.assertEqual(lines[topic['start']].strip(), topic['title'])
            self.assertEqual(self.run_cli([str(document), '--plain'], ['0'])[0], 0)

    def test_no_false_headings_or_duplicate_numbering(self):
        titles = [t['title'] for t in list_topics(2)]
        self.assertIn('2. Why Docker Exists', titles)
        self.assertFalse(any('project is containerised' in t for t in titles))
        self.assertFalse(any('200 OK' in t['title'] for t in list_topics(1)))

    def test_read_returns_to_contents_before_documents(self):
        code, text = self.run_cli(['--plain'], ['1', '2', '0', '0'])
        self.assertEqual(code, 0)
        self.assertEqual(text.count('Unit 2 Theory - Contents'), 2)
        self.assertEqual(text.count('\nTHUK\n'), 2)
        # Reading one section doesn't print the next section's body.
        selected = text.split('Unit 2 Theory / 1. Course Orientation', 1)[1].split('Unit 2 Theory - Contents')[0]
        self.assertNotIn('A Python function can accept', selected)

    def test_search_open_highlight_and_return_to_contents(self):
        code, text = self.run_cli(['--plain'], ['3', 's', 'migrations', '1', '0', '0'])
        self.assertEqual(code, 0)
        self.assertIn('Search results in Django Code', text)
        self.assertIn('[[migrations]]', text.lower())
        self.assertEqual(text.count('Django Code - Contents'), 2)
        self.assertEqual(text.count('\nTHUK\n'), 2)

    def test_search_scope_and_specific_subsection(self):
        results = search_topics('makemigrations', 3)
        self.assertTrue(results)
        self.assertTrue(any(r['title'] == '4.2 Migrations' for r in results))
        self.assertEqual(results, search_topics('MAKEMIGRATIONS', 3))
        for result in results:
            self.assertIn('makemigrations', get_topic(3, result['topic']).lower())
        self.assertEqual(search_topics('thiskeywordneverexists123', 1), [])
        with self.assertRaises(ValueError):
            search_topics(' ', 1)

    def test_blank_no_matches_invalid_and_back(self):
        code, text = self.run_cli(['1', '--plain'], ['bad', 's', '', 's', 'thiskeywordneverexists123', '0'])
        self.assertEqual(code, 0)
        self.assertIn('No matches found in this document.', text)
        self.assertIn('Choose a section number', text)
        code, text = self.run_cli(['5', '--plain'], ['s', 'git', '99', '0', '0'])
        self.assertEqual(code, 0)
        self.assertIn('Choose a result number', text)

    def test_direct_topic_full_search_and_literal_highlighting(self):
        code, text = self.run_cli(['3', '--topic', '2', '--plain'])
        self.assertEqual(code, 0)
        self.assertIn(get_topic(3, 2), text)
        self.assertEqual(self.run_cli(['1', '--topic', '999'])[0], 1)
        self.assertEqual(self.run_cli(['5', '--full', '--plain'])[0], 0)
        self.assertIn('topic', self.run_cli(['3', '--search', 'migrations'])[1])
        self.assertEqual(highlight('a.b A.B axb', 'a.b'), '[[a.b]] [[A.B]] axb')

    def test_eof_and_interrupt_at_nested_levels(self):
        for exception in [EOFError, KeyboardInterrupt]:
            with patch('builtins.input', side_effect=exception):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(main(['1']), 0)

    def test_original_pdf_exports_exactly(self):
        with tempfile.TemporaryDirectory() as folder:
            for document in range(1, 5):
                path = export_pdf(document, Path(folder) / f'{document}.pdf')
                self.assertEqual(path.read_bytes(), resource(document, 'pdf').read_bytes())
        self.assertEqual(self.run_cli(['5', '--pdf'])[0], 1)


if __name__ == '__main__':
    unittest.main()
