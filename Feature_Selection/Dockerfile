FROM python:3.8-slim
WORKDIR /usr/src/app/feature_selection
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./feature_selection/*.py ./feature_selection/
EXPOSE 5000
CMD ["python", "-m", "feature_selection"]
