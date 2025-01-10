
# Используем минимальный образ Python
FROM python:3.10-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем только requirements.txt для предварительной установки зависимостей
COPY requirements.txt /app/

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы проекта в контейнер
COPY . /app

# Открываем порт 5000
EXPOSE 5000

# Указываем команду для запуска приложения
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
