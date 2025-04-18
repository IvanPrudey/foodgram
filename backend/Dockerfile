# FROM python:3.9
# WORKDIR /app/foodgram
# RUN pip install gunicorn==20.1.0
# COPY requirements.txt .
# RUN pip install -r requirements.txt --no-cache-dir
# COPY . .
# CMD ["gunicorn", "--bind", "0.0.0.0:8080", "foodgram.wsgi:application"]
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn==20.1.0
COPY . .
# Точка входа — папка /app, где есть поддиректория foodgram, в ней wsgi.py
ENV DJANGO_SETTINGS_MODULE=foodgram.settings
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "foodgram.wsgi:application"]
