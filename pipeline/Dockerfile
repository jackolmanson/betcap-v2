FROM tensorflow/tensorflow:2.11.0

WORKDIR /app

COPY pipeline/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY pipeline/ ./pipeline/
COPY spread_model/ ./spread_model/
COPY output/ ./output/

WORKDIR /app/pipeline

# TEMPORARY (one run): backfill Nov 2-15 games for the 8 teams whose stats were
# missing (SR en-dash decoding). Revert to: CMD ["python", "run_picks.py"]
CMD ["sh", "-c", "python backfill_history.py 2026-11-02 2026-11-15; python run_picks.py"]
