import unittest
from asyncouch.couchversions import Diff
from test_couchadapter import TestDocument

from tornado.testing import AsyncTestCase, LogTrapTestCase
from loremipsum import get_sentence, get_paragraph
import random


class DiffTest(AsyncTestCase, LogTrapTestCase):
    def test_diff(self):
        doc1 = TestDocument()
        original = test_text = doc1.string_attr = get_paragraph()
        print(test_text)
        test_text_words = test_text.split()
        for x in range(10):
            r1 = random.randint(0, len(test_text_words)-1)
            r2 = random.randint(0, len(test_text_words)-1)
            test_text = test_text.replace(test_text_words[r1],
                                          test_text_words[r2])
        diff = Diff()
        diff.add_diff(doc1, 'string_attr', test_text)
        print(diff.string_attr)
        prev_text = diff.prev_version(doc1, 'string_attr')
        assert prev_text[1][0] is True, "patch unsuccessful"
        assert prev_text[0] == original, \
            "reverted text does not match original"

if __name__ == '__main__':
    unittest.main()
