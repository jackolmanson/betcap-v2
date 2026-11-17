FROM tensorflow/tensorflow:2.11.0

WORKDIR /app

COPY pipeline/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY pipeline/ ./pipeline/
COPY spread_model/ ./spread_model/
COPY output/ ./output/

WORKDIR /app/pipeline

CMD ["python", "run_picks.py"]
