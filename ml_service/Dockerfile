FROM python:3.10-slim

WORKDIR /app

COPY requirements_simple.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY app_simple.py .

EXPOSE 8000

CMD ["uvicorn", "app_simple:app", "--host", "0.0.0.0", "--port", "8000"]
