FROM python:3.10

WORKDIR /app/backend

COPY ./backend /app/backend

RUN apt-get update && apt-get install -y tesseract-ocr libtesseract-dev tesseract-ocr-dan

RUN pip install --no-cache-dir -r /app/backend/requirements.txt

CMD ["python", "/app/backend/app.py"]

