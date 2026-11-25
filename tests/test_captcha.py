import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from giga_china_crawler import captcha


class FakeLocator:
    def __init__(self, text):
        self.text = text

    async def count(self):
        return 1

    async def inner_text(self):
        return self.text


class FakePage:
    url = "https://www.alibaba.com/trade/search?SearchText=cable"

    def __init__(self, body="captcha", html="<html></html>"):
        self.body = body
        self.html = html

    async def content(self):
        return self.html

    async def title(self):
        return ""

    def locator(self, selector):
        return FakeLocator(self.body) if selector == "body" else FakeLocator("")

    async def wait_for_timeout(self, ms):
        pass

    async def reload(self):
        pass

    async def bring_to_front(self):
        pass


class CaptchaTests(unittest.TestCase):
    def test_candidates_without_endpoints(self):
        names = [s["name"] for s in captcha.candidates("behaviour", {})]
        self.assertEqual(names[0], "profile")
        self.assertEqual(names[-1], "human")
        self.assertIn("cf-solver", names)

    def test_candidates_puts_configured_first(self):
        env = {"CF_SOLVER_URL": "http://solver"}
        names = [s["name"] for s in captcha.candidates("slider", env)]
        self.assertEqual(names[:5], ["profile", "alibaba-slider", "ddddocr", "geetest-solver", "cf-solver"])
        self.assertEqual(names[-1], "human")

    def test_classify_slider(self):
        page = FakePage("slide to verify", "<html>geetest slider</html>")
        found = asyncio.run(captcha.classify(page))
        self.assertEqual(found["type"], "slider")
        self.assertIn("slide to verify", found["evidence"])

    def test_classify_token_with_sitekey(self):
        page = FakePage("captcha", '<html><div class="g-recaptcha" data-sitekey="abc123"></div></html>')
        found = asyncio.run(captcha.classify(page))
        self.assertEqual(found["type"], "token")
        self.assertEqual(found["sitekey"], "abc123")

    def test_classify_no_challenge(self):
        found = asyncio.run(captcha.classify(FakePage("cables", "<html></html>")))
        self.assertEqual(found["type"], "behaviour")

    def test_solve_escalates(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(captcha, "LOG_PATH", Path(tmp) / "wyniki.json"):
            result = asyncio.run(captcha.solve(FakePage(), max_solvers=1, attempts=1, env={}))
            self.assertEqual(result["status"], "escalate")
            self.assertEqual(result["attempts"][0]["solver"], "profile")
            self.assertFalse(result["attempts"][0]["solved"])
            entries = json.loads(captcha.LOG_PATH.read_text(encoding="utf-8"))
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0]["url"], FakePage.url)
            self.assertEqual(entries[0]["status"], "escalate")
            self.assertEqual(entries[0]["attempted"], ["profile"])
            self.assertEqual(entries[0]["skill"], "captcha-cascade")
            self.assertFalse(entries[0]["success"])
            self.assertIsNone(entries[0]["repo"])
            self.assertEqual(entries[0]["attempted_repos"], ["Giga-China-Crawler/.local/browser-profile"])

    def test_vendored_adapters_are_registered(self):
        for spec in captcha.SOLVERS:
            if spec["name"] not in ("profile", "human"):
                self.assertIn(spec["name"], captcha.ADAPTERS)
                self.assertIn(spec["name"], captcha.REPOS)
        self.assertNotIn("captchamind", [s["name"] for s in captcha.SOLVERS])

    def test_record_deduplicates(self):
        found = {"url": "https://example.com/a", "type": "slider", "sitekey": None}
        with tempfile.TemporaryDirectory() as tmp, patch.object(captcha, "LOG_PATH", Path(tmp) / "wyniki.json"):
            captcha.record(found, {"status": "escalate", "solver": None, "attempts": []})
            captcha.record(found, {"status": "solved", "solver": "profile",
                                   "attempts": [{"solver": "profile", "detail": "ponowny wczyt profilu"}]})
            entries = json.loads(captcha.LOG_PATH.read_text(encoding="utf-8"))
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0]["count"], 2)
            self.assertEqual(entries[0]["solver"], "profile")
            self.assertEqual(entries[0]["status"], "solved")
            self.assertEqual(entries[0]["attempted"], ["profile"])
            self.assertEqual(entries[0]["skill"], "captcha-cascade")
            self.assertEqual(entries[0]["repo"], "Giga-China-Crawler/.local/browser-profile")
            self.assertTrue(entries[0]["success"])


if __name__ == "__main__":
    unittest.main()
