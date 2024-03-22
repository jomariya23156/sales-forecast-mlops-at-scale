FROM rayproject/ray:2.9.3-py39-cpu-aarch64

USER root

ARG MLFLOW_ARTIFACT_ROOT=$MLFLOW_ARTIFACT_ROOT
# Config path dir and permission for mlflow artifacts storage
# cuz mlflow also stores artifacts to client's container
RUN mkdir -p $MLFLOW_ARTIFACT_ROOT && \
    chown -R ray $MLFLOW_ARTIFACT_ROOT && \
    chmod -R go+rX $MLFLOW_ARTIFACT_ROOT

USER ray

COPY requirements_addon.txt requirements_addon.txt

RUN pip install -r requirements_addon.txt

CMD ray start --head --port=${RAY_HEAD_PORT} \
    --dashboard-host=0.0.0.0 \
    --dashboard-port=${RAY_DASHBOARD_PORT} \
    --ray-client-server-port=${RAY_CLIENT_SERVER_PORT} --block