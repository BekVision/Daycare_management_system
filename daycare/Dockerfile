## Python 3.12 asosiy tasvirini ishlatish
#FROM python:3.12-slim
#
## Muhit o'zgaruvchilarini sozlash
#ENV PYTHONDONTWRITEBYTECODE=1
#ENV PYTHONUNBUFFERED=1
#
## Ish katalogini belgilash
#WORKDIR /app
#
## Tizim paketlarini yangilash va kerakli paketlarni o'rnatish
#RUN apt-get update \
#    && apt-get install -y --no-install-recommends \
#        postgresql-client \
#        build-essential \
#        libpq-dev \
#    && apt-get clean \
#    && rm -rf /var/lib/apt/lists/*
#
## Python bog'liqliklarini o'rnatish
#COPY requirements.txt /app/
#RUN pip install --upgrade pip
#RUN pip install -r requirements.txt
#
## Loyiha fayllarini konteynerga nusxalash
#COPY . /app/
#
## Static fayllar uchun katalog yaratish
#RUN mkdir -p /app/staticfiles
#RUN mkdir -p /app/media
#
## Static fayllarni yig'ish
#RUN python manage.py collectstatic --noinput
#
## Port ochish
#EXPOSE 8000
#
## Loyihani ishga tushirish buyrug'i
#CMD ["gunicorn", "--bind", "0.0.0.0:8000", "daycare.wsgi:application"]