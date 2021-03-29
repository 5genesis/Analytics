FROM python:3.8-slim
WORKDIR /usr/src/app/outlier_detection
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./prediction/*.py ./prediction/
EXPOSE 5000
CMD ["python", "-m", "prediction"]
