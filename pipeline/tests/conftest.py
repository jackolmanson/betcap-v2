import os
import sys

# Must be set before run_picks/db are imported
os.environ.setdefault("ODDS_API_KEY", "test_key")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/test")

# Make pipeline modules importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
