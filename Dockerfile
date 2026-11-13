FROM grafana/grafana:13.3.1 AS grafana
COPY config/grafana /etc/grafana/provisioning
COPY config/portainer/provider.yaml /etc/grafana/provisioning/dashboards/provider.yaml
COPY dashboards /opt/diddi/dashboards

FROM prom/prometheus:v3.16.0 AS prometheus
COPY generated/prometheus.yaml /etc/prometheus/prometheus.yml

FROM grafana/loki:3.7.10 AS loki
COPY config/loki.yaml /etc/loki/config.yaml

FROM grafana/tempo:3.1.1 AS tempo
COPY config/tempo.yaml /etc/tempo/config.yaml

FROM grafana/alloy:v1.21.3 AS alloy
COPY generated/config.alloy /etc/alloy/config.alloy

FROM nginx:1.31.8-alpine AS gateway
COPY generated/nginx.conf /etc/nginx/nginx.conf

FROM prom/blackbox-exporter:v0.29.1 AS blackbox
COPY config/blackbox.yaml /etc/blackbox/config.yaml

FROM python:3.13.9-alpine AS registry
WORKDIR /app
COPY app/registry.py /app/registry.py
COPY registry/services.json /registry/services.json
USER 65534:65534
CMD ["python", "registry.py"]

FROM python:3.13.9-alpine AS init-storage
RUN pip install --no-cache-dir cryptography==46.0.3 bcrypt==5.0.0
COPY app/runtime_init.py /app/runtime_init.py
COPY registry/services.json /registry/services.json
CMD ["python", "/app/runtime_init.py"]

FROM prometheus AS synthetic-prometheus
COPY config/synthetic/prometheus.yaml /etc/prometheus/prometheus.yml
FROM alloy AS synthetic-alloy
COPY config/synthetic/config.alloy /etc/alloy/config.alloy
FROM gateway AS synthetic-gateway
COPY config/synthetic/nginx.conf /etc/nginx/nginx.conf
FROM registry AS synthetic-registry
COPY config/synthetic/services.json /registry/services.json
FROM init-storage AS synthetic-init-storage
COPY config/synthetic/services.json /registry/services.json
FROM python:3.13.9-alpine AS synthetic
COPY app/pilot.py /app/pilot.py
USER 65534:65534
CMD ["python", "/app/pilot.py"]
