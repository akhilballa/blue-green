FROM python:3.12-alpine

WORKDIR /srv/app

COPY service.py .

ENV SERVICE_PORT=8080

EXPOSE 8080

CMD ["python", "service.py"]
