FROM python:3.8-slim
WORKDIR /usr/src/app/statistical_analysis
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./statistical_analysis/*.py  ./statistical_analysis/
EXPOSE 5000
CMD ["python", "-m", "statistical_analysis"]
