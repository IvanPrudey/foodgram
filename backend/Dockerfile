FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn==20.1.0
COPY . .
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "wsgi:application"]
