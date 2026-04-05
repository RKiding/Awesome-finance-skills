import sys
import os
import unittest

# Add skill root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from scripts.sentiment_tools import SentimentTools
    from scripts.database_manager import DatabaseManager
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

class TestSentiment(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseManager(":memory:")
        self.tools = SentimentTools(self.db, mode="llm")

    def test_init(self):
        print("Testing SentimentTools Iteration...")
        self.assertIsNotNone(self.tools)
        print("SentimentTools Initialized.")

    def test_get_symbol_sentiment_empty(self):
        """Returns unknown label when no news in DB."""
        result = self.tools.get_symbol_sentiment("TRYUSDT")
        self.assertEqual(result["symbol"], "TRYUSDT")
        self.assertEqual(result["count"], 0)
        self.assertIsNone(result["avg_score"])
        self.assertEqual(result["label"], "unknown")

    def test_get_symbol_sentiment_tryusdt(self):
        """Aggregates sentiment correctly for TRYUSDT news."""
        self.db.save_daily_news([
            {"id": "n1", "source": "test", "rank": 1, "title": "TRYUSDT drops sharply",
             "url": "http://a.com/1", "sentiment_score": -0.8},
            {"id": "n2", "source": "test", "rank": 2, "title": "TRY/USDT rebounds",
             "url": "http://a.com/2", "sentiment_score": 0.4},
            {"id": "n3", "source": "test", "rank": 3, "title": "BTC rally unrelated",
             "url": "http://a.com/3", "sentiment_score": 0.9},
        ])
        result = self.tools.get_symbol_sentiment("TRYUSDT")
        self.assertEqual(result["symbol"], "TRYUSDT")
        self.assertGreaterEqual(result["count"], 2)  # n1 + n2 matched
        self.assertIsNotNone(result["avg_score"])
        self.assertIn(result["label"], ["positive", "negative", "neutral"])

    def test_get_symbol_sentiment_tryusdc(self):
        """TRYUSDC alias expansion works."""
        self.db.save_daily_news([
            {"id": "n4", "source": "test", "rank": 1, "title": "TRY/USDC market update",
             "url": "http://a.com/4", "sentiment_score": 0.2},
        ])
        result = self.tools.get_symbol_sentiment("TRYUSDC")
        self.assertEqual(result["symbol"], "TRYUSDC")
        self.assertGreaterEqual(result["count"], 1)

if __name__ == '__main__':
    unittest.main()
