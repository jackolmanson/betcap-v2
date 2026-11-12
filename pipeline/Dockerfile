FROM tensorflow/tensorflow:2.11.0

WORKDIR /app

COPY pipeline/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY pipeline/ ./pipeline/
COPY spread_model/ ./spread_model/
COPY output/ ./output/

WORKDIR /app/pipeline

# TEMPORARY (one run): backfill Nov 11 games missed by the late run. Revert to: CMD ["python", "run_picks.py"]
CMD ["sh", "-c", "python backfill_history.py 2026-11-11 2026-11-11; python run_picks.py"]
