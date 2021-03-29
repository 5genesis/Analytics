FROM python:3.8-slim
WORKDIR /usr/src/app/data_handler
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./data_handler/*.py ./data_handler/
EXPOSE 5000
CMD ["python", "-m", "data_handler"]
