FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install uv
RUN uv pip install --system --no-cache-dir -r requirements.txt

EXPOSE 7860

CMD ["sh", "-c", "uvicorn app.main:app --host ${HOST:-0.0.0.0} --port ${PORT:-7860}"]