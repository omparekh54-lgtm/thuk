import contextlib
import io
import unittest
from unittest.mock import patch

from thuk import answer_question, get_text
from thuk.cli import main


class AnswerTests(unittest.TestCase):
    def test_comparison_finds_theory_and_preserves_exact_source(self):
        result = answer_question('What is the difference between containers and virtual machines?')
        self.assertTrue(result['found'])
        self.assertEqual(result['sources'][0]['title'], '3. Containers vs Virtual Machines')
        self.assertIn("shares the host's kernel", result['sources'][0]['excerpt'])
        for source in result['sources']:
            lines = get_text(source['section']).splitlines()
            self.assertEqual(source['excerpt'], '\n'.join(lines[source['line_start'] - 1:source['line_end']]))

    def test_scope_acronyms_and_command_lookup(self):
        result = answer_question('Explain MVT', 1)
        self.assertTrue(result['found'])
        self.assertTrue(all(s['section'] == 1 for s in result['sources']))
        self.assertIn('Django MVT', result['sources'][0]['title'])
        result = answer_question('git stash command', 5)
        self.assertTrue(result['found'])
        self.assertIn('git stash', result['answer'])

    def test_absent_topic_and_weak_match_refused(self):
        for question in ['photosynthesis chlorophyll', 'docker pizza recipe', 'what is it?']:
            self.assertFalse(answer_question(question)['found'])
        for question in ['', '   ', None]:
            with self.assertRaises(ValueError):
                answer_question(question)
        with self.assertRaises(ValueError):
            answer_question('Docker', 99)
        with self.assertRaises(ValueError):
            answer_question('Docker', limit=0)

    def run_cli(self, argv, answers=()):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output), \
                patch('builtins.input', side_effect=list(answers)):
            code = main(argv)
        return code, output.getvalue()

    def test_questions_repeat_and_return_to_original_menu(self):
        code, text = self.run_cli(['--plain'], ['7', 'Explain Docker', 'git stash command', '0', '0'])
        self.assertEqual(code, 0)
        self.assertEqual(text.count('\nTHUK\n'), 2)
        self.assertEqual(text.count('Relevant passages from your notes'), 2)
        code, text = self.run_cli(['1', '--plain'], ['a', 'Explain MVT', '0', '0'])
        self.assertEqual(code, 0)
        self.assertEqual(text.count('Unit 2 Theory - Contents'), 2)
        self.assertNotIn('\nTHUK\n', text)

    def test_direct_cli_and_interrupt(self):
        code, text = self.run_cli(['2', '--ask', 'containers versus virtual machines', '--plain'])
        self.assertEqual(code, 0)
        self.assertIn('Containers vs Virtual Machines', text)
        self.assertEqual(self.run_cli(['--ask', ' '])[0], 1)
        with self.assertRaises(SystemExit):
            self.run_cli(['1', '--topic', '2', '--ask', 'Docker'])
        for exception in (EOFError, KeyboardInterrupt):
            with patch('builtins.input', side_effect=['7', exception]), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(['--plain']), 0)


if __name__ == '__main__':
    unittest.main()
