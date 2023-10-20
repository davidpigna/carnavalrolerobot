FROM python:3.11-alpine
COPY . /app
WORKDIR /app
RUN pip install discord pymongo
CMD ["python", "eventos.py"]