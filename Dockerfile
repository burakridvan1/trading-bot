# Temel imaj
FROM python:3.10-slim

# Çalışma dizini
WORKDIR /app

# Gereksinimleri kopyala ve yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kodları kopyala
COPY . .

# Container çalıştırıldığında botu başlat
CMD ["python", "main.py"]
