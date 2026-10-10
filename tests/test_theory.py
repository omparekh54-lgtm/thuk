import contextlib
import io
import unittest
from unittest.mock import patch

from thuk import get_text
from thuk.cli import display_theory, main


class TheoryTests(unittest.TestCase):
    def test_both_complete_documents_in_order_and_return_to_main(self):
        for choice in ('f', 'F'):
            output = io.StringIO()
            with contextlib.redirect_stdout(output), patch('builtins.input', side_effect=[choice, '0']):
                self.assertEqual(main(['--plain']), 0)
            text = output.getvalue()
            self.assertIn('F. Theory (full Unit 2 + Unit 5)', text)
            self.assertIn(get_text(1), text)
            self.assertIn(get_text(2), text)
            self.assertLess(text.index(get_text(1)), text.index(get_text(2)))
            self.assertEqual(text.count('\nTHUK\n'), 2)
            self.assertNotIn(' - Contents\n', text)

    def test_one_pager_contains_full_theory(self):
        with patch('thuk.cli.sys.stdout.isatty', return_value=True), patch('thuk.cli.pydoc.pager') as pager:
            display_theory()
        pager.assert_called_once()
        text = pager.call_args[0][0]
        self.assertIn(get_text(1), text)
        self.assertIn(get_text(2), text)


if __name__ == '__main__':
    unittest.main()
