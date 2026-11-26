import asyncio
import unittest
from unittest.mock import patch

from giga_china_crawler import ai


class NoKeysTests(unittest.TestCase):
    def test_works_without_keys(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(asyncio.run(ai.search_terms("hammer", [])), ["hammer"])
            self.assertEqual(asyncio.run(ai.lessons({}, [])), [])
            self.assertEqual(asyncio.run(ai.match("hammer", None, {"title": "x"})), 1.0)


if __name__ == "__main__":
    unittest.main()
