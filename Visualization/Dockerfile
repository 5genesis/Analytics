FROM python:3.8-slim
WORKDIR /usr/src/app/visualization
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./visualization/*  ./visualization/
EXPOSE 5000
CMD ["python", "-m", "visualization"]
