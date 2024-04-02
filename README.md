<h1 align="center"> Sales Forecast MLOps at Scale </h1>

<p align="center"><b> ▶️ Highly scalable Cloud-native Machine Learning system ◀️ </b></p>

# Overview

Scalable End-to-end MLOps system for sales forecasting.

# Development environment
1. Docker (ref: Docker version 24.0.6, build ed223bc)
2. Kubernetes (ref: v1.27.2 (via Docker Desktop))
3. Helm (ref: v3.14.3)

# Tools / Technologies
Note: Most of the ports can be customized in the `.env` file at the root of this repository (or `values.yaml` and ConfigMap for Helm). Here are the defaults.
- Machine Learning platform / Experiment tracking: [MLflow](https://mlflow.org/) [port: 5050]
- Pipeline orchestrator: [Airflow](https://airflow.apache.org/) [port: 8080]
- Model distributed training and scaling: [Ray](https://www.ray.io/) [port: 8265 & port: 4243 (training coordinator / job submitter)]
- Reverse proxy: [Nginx](https://www.nginx.com/) and [ingress-nginx](https://github.com/kubernetes/ingress-nginx) (for Kubernetes) [port: 80]
- Web Interface: [Streamlit](https://streamlit.io/) [port: 8000] *proxied by nginx
- Machine Learning service deployment: [FastAPI](https://fastapi.tiangolo.com/), [Uvicorn](https://www.uvicorn.org/), [Gunicorn](https://gunicorn.org/) [port: 4242] *proxied by nginx
- Databases: [PostgreSQL](https://www.postgresql.org/) [port: 5432], [Prometheus](https://prometheus.io/) [port: 9090]
- Database UI for Postgres: [pgAdmin](https://www.pgadmin.org/) [port: 16543]
- Overall system monitoring & dashboard: [Grafana](https://grafana.com/) [port: 3000]
- Distributed data streaming: [Kafka](https://kafka.apache.org/) [port: 9092]
- Forecast modeling framework: [Prophet](https://facebook.github.io/prophet/docs/quick_start.html)
- Stream processing: [Spark Streaming](https://spark.apache.org/streaming/)
- Cloud platform: [Google Cloud Platform](https://cloud.google.com/)
- CICD: [GitHub Actions](https://github.com/features/actions)
- Platform: [Docker](https://www.docker.com/), [Kubernetes](https://kubernetes.io/), [Helm](https://helm.sh/)

# How to use
Prerequisites: Docker and Kubernetes (in our case, it's Docker Desktop as pinned in *Development environment* section)

## With Docker Compose
1. [Optional] In case you wanna build (not pulling images): `docker-compose build`
2. `docker-compose -f docker-compose.yml -f docker-compose-airflow.yml up -d`
3. That's it!
**Note:** Most of the services' restart is left unspecified, so they won't restart on failures (cuz sometimes it's quite resource-consuming during development, you see we have a poor laptop lol).

## With Kubernetes/Helm (Local cluster)
*Note:* The system is quite large and heavy... we recommend running it locally just for testing for one go, then if it works, just go off to the cloud if you wanna play around longer OR stick with Docker Compose (it went smoother in our case)
1. Install Helm `bash install-helm.sh`
2. Create airflow namespace: `kubectl create namespace airflow`
3. Deploy the main chart:
   1. `cd sfmlops-helm` and `helm dependency build` to fetch all dependencies
   2. `helm upgrade --install --create-namespace -n mlops sfmlops-helm ./ -f values.yaml -f values-ray.yaml`
4. Deploy Kafka:
   1. [Only 1st time] `helm repo add bitnami https://charts.bitnami.com/bitnami`
   2. `helm -n kafka upgrade --install kafka-release oci://registry-1.docker.io/bitnamicharts/kafka --create-namespace --version 23.0.7 -f values-kafka.yaml`
5. Deploy Airflow:
   1. [Only 1st time] `helm repo add apache-airflow https://airflow.apache.org`
   2. `helm -n airflow upgrade --install airflow apache-airflow/airflow --create-namespace --version 1.13.1 -f values-airflow.yaml`
   3. Sometimes, you might get a timeout error from this command (if you do, it means your machine spec is too poor for this system (like mine lol)). It's totally fine. Just keep checking the status with kubectl, if all resources start up correctly, go with it otherwise try running the command again.
6. Deploy Prometheus and Grafana:
   1. [Only 1st time] `helm repo add prometheus-community https://prometheus-community.github.io/helm-charts`
   2. `helm -n monitoring upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack  --create-namespace --version 57.2.0 -f values-kube-prometheus.yaml`
   3. One of the good things about kube-prometheus-stack is that it comes with many pre-installed/pre-configured dashboards for Kubernetes. Feel free to explore!
7. That's it! Enjoy your highly scalable Machine Learning system for Sales forecasting! :)

**Note:** If you want to change namespace `kafka` and/or release name `kafka-release` of Kafka, please also change them in `values.yaml` and `KAFKA_BOOTSTRAP_SERVER` env var in `values-airflow.yaml`. They are also used in templating.

**Note 2:** In Docker Compose, Ray has already been configured to pull the embedded dashboards from Grafana, but in Kubernetes, this process involves a lot more manual steps so we intentionally left it undone for ease of setup of this project. You can follow the guide [here](https://docs.ray.io/en/latest/cluster/kubernetes/k8s-ecosystem/prometheus-grafana.html) if you want to anyway.

## With Kubernetes/Helm (on GCP)
Prerequisites: GKE Cluster (Standard cluster, *NOT* Autopilot), Artifact Registry, Service Usage API
1. Follow this Medium blog. We recommend create a new Service Account with Owner role for quick and dirty run (but of course, please consult your cloud engineer if you have security concerns).
2. Download your Service Account's JSON key
3. Activate your service account: `gcloud auth activate-service-account --key-file=<PATH_TO_JSON_KEY>`
4. Connect local kubectl to cloud: `gcloud container clusters get-credentials <GKE_CLUSTER_NAME> --zone <GKE_ZONE> --project <PROJECT_NAME>`
5. Now kubectl (and helm) will work in the context of the GKE environment.
6. Follow the steps in **With Kubernetes/Helm (Local cluster)** section
7. If you face a timeout error when running helm commands for airflow or the system struggles to setup and work correctly, I recommend trying to upgrade your machine type in the cluster.

**Note:** For the machine type of node pool in the GKE cluster, from experiments, `e2-medium` (default) is not quite enough, especially for Airflow and Ray. In our case, we're going for `e2-standard-8` with 1 node (explanation why only 1 node is in *Important note on MLflow's artifact path* section). We also found ourselves need to increase the quota for PVC in IAM too.

## Cleanup steps
1. `helm uninstall sfmlops-helm -n mlops`
2. `helm uninstall kafka-release -n kafka`
3. `helm uninstall airflow -n airflow`
4. `helm uninstall kube-prometheus-stack -n monitoring`

### Important note on MLflow's artifact path
In this setting, we set the MLflow's artifact path to point to the local path. Internally, MLflow expects this path to be accessible from both MLflow client and server side (honestly, I don't like this model too), which is meant to be an object storage path like S3 (AWS) or Cloud Storage (GCP). But for the full on-prem experience, we can create a docker volume and mount it to the EXACT same path on both client and server to remediate this. In Kubernetes local cluster, we can do the same thing by creating a PVC with `accessModes: ReadWriteOnce` (in `sfmlops-helm/templates/mlflow-pvc.yaml`). **But** for on-cloud Kubernetes with a typical multi-node cluster, if we want the PVC to be able to read and write across nodes, we need to set `accessModes: ReadWriteMany` which most cloud providers *DO NOT* support this type of PVC and encourage to use a centralized storage instead. Therefore, if you wanna just try it out and run for fun, you can use this exact setting and create a cluster with 1 node (it will behave mostly like a local Kubernetes cluster, just on the cloud). For real production environment, please create a cloud storage, remove `mlflow-pvc.yaml` and its mount paths, and change the artifact path variable `MLFLOW_ARTIFACT_ROOT` in `sfmlops-helm/templates/global-configmap.yaml` to the cloud storage path. This is an official [doc](https://mlflow.org/docs/latest/tracking/artifacts-stores.html) about this.

### Note on Kafka Docker Compose and Helm
Kafka services on Docker Compose and Halm are different in settings, mainly in Docker Compose, we use KRaft for config management (which is newer), but in Helm, we use ZooKeeper because, honestly, we're not managed to pull it off with KRaft, sorry :'( (It's quite complex).

### Note on Stream processing options
There are a few options we can do to consume the stream data from Kafka producer and save to Postgres
1. Dead and simple consumer with SQLAlchemy
    - Consume the message from a topic with KafkaConsumer class
    - Mannually use SQLAlchemy to save the new data into Postgres

    Pros:
    - Easy and Straightforward
    - Very Pythonic

    Cons:
    - Not really scalable by nature (need careful coding and designing to make sure of this)
    - Might cause a bottleneck in the process
2. Use Steam processing frameworks such as Spark Streaming or Apache Flink

    Pros:
    - Support Kafka out-of-the-box
    - Scalable and efficient (with the nature of distributed computing system)
    - Can handle complex data tranformation at scale

    Cons:
    - Another tool to learn (make the learning curve for the project steeper)
3. Kafka Connect -> Plugin tool from Kafka to connect to external tools to receive or send message (source or sink connectors in Kafka terms)

    Pros:
    - Support Kafka natively (of course)
    - Might be the fastest option of all
    - Suitable for straightforward receiving and sending message to external tools

    Cons:
    - Limited control over data transformation
    - By it own, the usage and setup is not quite intuitive and no Python API (at the time of writing)
    - Docs are limited and most of the resources online go for hosted service offered by other venders (e.g. Confluent, Aiven)
    - Which led to vendor-lockon option and limited usage due to the license

So in this project, **I went for 2nd option**, Stream processing framework, with **Spark Streaming** since I feel like this is good balance between performance and control. And if in the future, I need to do some more complex data stream transformation, this is a pretty much go-to option and I can come back to look it up from this project.

### Note on my thought about Ray training jobs submission
In fact, you can submit the training jobs directly from **ANY** service in the same network. For example, you can submit the training jobs form Streamlit UI (to train a single model on-demand) or from Airflow through DAG (to train all models). But I choose to have another FastAPI app as a middle man to handle this job submission instead. My reasons are:
- Better separation of concern: In order to submit any Ray task, the file for task execution must be available LOCALLY from the client. Meaning if you want to submit a training task from UI, your Streamlit needs to hold your training script, same thing for Airflow. With FastAPI as a middle man, you can store all required files in a single server and you make sure any one component in the whole system serve one purpose.
- Easier to maintain: Following the previous point, it makes your life a lot harder to maintain the services. For example, without FastAPI middle man, if you need to update the logic for training, you have to update both Streamlit and Airflow.
- Offer more flexibility and customizability: With my approach, you can add as many extra steps as you like to handle and process incoming Ray job submission from client. For example, you can include more an authentication step for security purpose.


### Using Ray with external Redis (in Docker Compose)
If we restart the Ray container, all previous job history will be gone because Ray store them in-memory only. We can add an external Redis to manage these variables but, from using, this seems very very unstable, this is also stated in the official doc that using external Redis supports only on-cloud / Kubernetes. But I wanna try and... from time-to-time during the development, I found that the Ray cluster do not accept the Job submission and show error `Job supervisor actor could not be scheduled: The actor is not schedulable: The node specified via NodeAffinitySchedulingStrategy doesn't exist any more or is infeasible, and soft=False was specified.`. I could fix that by removing all data in redis by running `docker-compose exec redis redis-cli FLUSHALL` AND/OR removing Ray container and rebuild it again. But it's annoying and time consuming. So in the end, I got rid of external Redis for Ray, Bye~.

## References / Useful resources
- Ray sample config: https://github.com/ray-project/kuberay/tree/master/ray-operator/config/samples
- Bitnami Kafka Helm: https://github.com/bitnami/charts/tree/main/bitnami/kafka
- Airflow Helm: https://airflow.apache.org/docs/helm-chart/stable/index.html
- Airflow Helm default values.yaml: https://github.com/apache/airflow/blob/main/chart/values.yaml
- dataset: https://www.kaggle.com/datasets/pratyushakar/rossmann-store-sales
- Original Airflow's docker-compose file: https://airflow.apache.org/docs/apache-airflow/2.8.3/docker-compose.yaml

### Modifications made to Airflow docker-compose
- Removed postgres (connect to our existing with new username and pwd)
- Added env variable `SPARK_STREAM_CHECKPOINTS_PATH` and mount volume for this checkpoint
- Connect to `forecast_network` defined in our existing docker-compose
- Note when starting: need to specify both compose files i.e. `docker-compose -f docker-compose.yml -f docker-compose-airflow.yml`
From doc: https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html
