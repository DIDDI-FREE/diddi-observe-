FROM python:3.13.9-alpine
WORKDIR /app
COPY app /app
USER 65534:65534
EXPOSE 9108
CMD ["python", "registry.py"]
