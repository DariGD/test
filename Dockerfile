FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt


COPY . /app/

# Команда для запуска бота
CMD ["python", "bot.py"]