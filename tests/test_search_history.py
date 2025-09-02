import os
import sys

# Ensure the project root is on the Python path so the ``api_bot`` package can
# be imported when tests are executed from arbitrary working directories.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api_bot.core.discovery_bot import ComprehensiveAPIBot


def test_search_history_and_stats():
    bot = ComprehensiveAPIBot()
    bot.comprehensive_search("weather")
    bot.comprehensive_search("space")
    stats = bot.get_stats()
    assert stats["searches_last_week"] >= 2
    assert stats["recent_searches"][0] == "space"
    assert stats["recent_searches"][1] == "weather"
