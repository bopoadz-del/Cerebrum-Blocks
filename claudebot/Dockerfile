FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY bot.py .
ENV WORK_DIR=/workspace
ENV HISTORY_DIR=/data/history
RUN mkdir -p /data/history /workspace
CMD ["python", "bot.py"]
