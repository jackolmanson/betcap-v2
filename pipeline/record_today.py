"""
Run manually to score today's completed games.
The daily pipeline only scores the previous day's games —
use this after games finish to update today's results without waiting.

Usage:
    python3 record_today.py
"""
import os
import sys
from datetime import datetime, timezone, timedelta

PT = timezone(timedelta(hours=-8))

sys.path.insert(0, os.path.dirname(__file__))

from record_results import record_results

if __name__ == "__main__":
    today = datetime.now(PT).date().isoformat()
    print(f"Scoring today's completed games ({today})...")
    record_results(today)
