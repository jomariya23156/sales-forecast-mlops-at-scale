<h1 align="center"> Sales Forecast MLOps at Scale </h1>

<p align="center"><b> ▶️ Highly scalable Cloud-native Machine Learning system ◀️ </b></p>

# Table of contents
- [Overview](#overview)
- [Key Features](#key-features)
- [Tools / Technologies](#tools--technologies)
- [Development environment](#development-environment)
- [How things work](#how-things-work)
- [How to setup](#how-to-setup)
  - [With Docker Compose](#with-docker-compose)
  - [With Kubernetes/Helm (Local cluster)](#with-kuberneteshelm-local-cluster)
  - [With Kubernetes/Helm (on GCP)](#with-kuberneteshelm-on-gcp)
  - [Cleanup steps](#cleanup-steps)
  - [Important note on MLflow on Cloud](#important-note-on-mlflow-on-cloud)
- [References / Useful resources](#references--useful-resources)
- [My notes](#my-notes)


# Overview
**"Sales Forecast MLOps at Scale"** delivers a full-stack, production-ready solution designed to streamline the entire sales forecasting system – from development and deployment to continuous improvement. It offers flexible deployment options, supporting both on-premises environments (Docker Compose, Kubernetes) and cloud-based setups (Kubernetes, Helm), ensuring adaptability to your infrastructure.

Demo on YouTube: https://youtu.be/PwV8TIsMEME

<image src="./files/sfmlops_software_diagram.png">

# Key Features
- **Dual-Mode Inference**: Supports both batch and online inference modes, providing adaptability to various use cases and real-time prediction needs.
- **Automated Forecast Generation**: Airflow DAGs orchestrate weekly model training and batch predictions, with the ability for on-demand retraining based on the latest data.
- **Data-Driven Adaptability**: Kafka handles real-time data streaming, enabling the system to incorporate the latest sales information into predictions. Models are retrained on demand to maintain accuracy.
- **Scalable Pipeline and Training**: Leverages Spark and Ray for efficient data processing and distributed model training, ensuring the system can handle large-scale datasets and training.
- **Transparent Monitoring**: Ray and Grafana provide visibility into training performance, while Prometheus enables system-wide monitoring.
- **User-Friendly Interface**: Streamlit offers a clear view of predictions. MLflow tracks experiments and model versions, ensuring reproducibility and streamlined updates.
- **Best-Practices Serving**: Robust serving stack with Nginx, Gunicorn, and FastAPI for reliable and performant model deployment.
- **CI/CD Automation**: GitHub Actions streamline the build and deployment process, automatically pushing images to Docker Hub and GCP.
- **Cloud-native, Scalability and Flexibility**: Kubernetes and Google Cloud Platform ensure adaptability to growing data and workloads. The open-source foundation (Docker, Ray, FastAPI, etc.) offers customization and extensibility.

# Tools / Technologies
Note: Most of the service ports can be found and customized in the `.env` file at the root of this repository (or `values.yaml` and `sfmlops-helm/templates/global-configmap.yaml` for Kubernetes and Helm).
- Platform: [Docker](https://www.docker.com/), [Kubernetes](https://kubernetes.io/), [Helm](https://helm.sh/)
- Cloud platform: [Google Cloud Platform](https://cloud.google.com/)
- Experiment tracking / Model registry: [MLflow](https://mlflow.org/)
- Pipeline orchestrator: [Airflow](https://airflow.apache.org/)
- Model distributed training and scaling: [Ray](https://www.ray.io/)
- Reverse proxy: [Nginx](https://www.nginx.com/) and [ingress-nginx](https://github.com/kubernetes/ingress-nginx) (for Kubernetes)
- Web Interface: [Streamlit](https://streamlit.io/)
- Machine Learning service deployment: [FastAPI](https://fastapi.tiangolo.com/), [Uvicorn](https://www.uvicorn.org/), [Gunicorn](https://gunicorn.org/)
- Databases: [PostgreSQL](https://www.postgresql.org/), [Prometheus](https://prometheus.io/)
- Database UI for Postgres: [pgAdmin](https://www.pgadmin.org/)
- Overall system monitoring & dashboard: [Grafana](https://grafana.com/)
- Distributed data streaming: [Kafka](https://kafka.apache.org/)
- Forecast modeling framework: [Prophet](https://facebook.github.io/prophet/docs/quick_start.html)
- Stream processing: [Spark Streaming](https://spark.apache.org/streaming/)
- CICD: [GitHub Actions](https://github.com/features/actions)

# Development environment
1. Docker (ref: Docker version 24.0.6, build ed223bc)
2. Kubernetes (ref: v1.27.2 (via Docker Desktop))
3. Helm (ref: v3.14.3)

# How things work
1. After you start up the system, the **data producer** will read and store the data of the last 5 months from `services/data-producer/datasets/rossman-store-sales/train_exclude_last_10d.csv` to **Postgres**. It does this by modifying the last date of the data to be *YESTERDAY*. Afterward, it will keep publishing new messages (from `train_only_last_19d.csv` in the same directory), technically *TODAY* data, to a **Kafka** topic every 10 seconds (infinite loop).
2. There are two main DAGs in **Airflow**:
   1. Daily DAG:  
       \>\> Ingest data from this Kafka topic  
       \>\> Process and transform with **Spark Streaming**  
       \>\> Store it in Postgres  
   2. Weekly DAG:  
       \>\> Pull the last four months of sales data from Postgres  
       \>\> Use it for training new **Prophet** models, with **Ray** (*1,1115* models in total), which are tracked and registered by **MLflow**  
       \>\> Use these newly trained models to predict the forecast of the upcoming week (next 7 days)  
       \>\> Store the forecasts in Postgres (another table)
3. During training, you can monitor your system and infrastructure with **Grafana** and **Prometheus**.
4. By default, the data stream from topic `sale_rossman_store` gets stored in `rossman_sales` table and forecast results in `forecast_results` table, you can use **pgAdmin** to access it.
5. After the previous steps are executed successfully, you/users can now access the **Streamlit** website proxied by **Nginx**.
6. This website fetches the latest 7 predictions (technically, the next 7 days) for each store and each product and displays them in a good-looking line chart (thanks to **Altair**)
7. From the website, users can view sales forecast of any product from any store. Notice that the subtitle of the chart contains the model ID and version.
8. Since these forecasts are made weekly, whether users access this website on Monday or Wednesday, they will see the same chart. If, during the week, the users somehow feel like the forecast prediction is out of sync or outdated, they can trigger retraining for a specific model of that product and store.
9.  When the users click a retrain button, the website will submit a model training job to the **training service** which then calls Ray to retrain this model. The retraining is pretty fast, usually done in under a minute, and it follows the same training strategy as the weekly training DAG (but of course, with the newest data possible).
10. Right after retraining is done, users can select a number of future days to predict and click a forecast button to request the **forecasting service** to use the latest model to make forecasts.
11. The result of new forecasts is then displayed in the line chart below. Notice that the model version number increased! Yoohoo! (note: For simplicity, this new forecast result won't be stored anywhere.)

# How to setup
Prerequisites: Docker, Kubernetes, and Helm

## With Docker Compose
1. *(Optional)* In case you want to build (not pulling images):
   ```
   docker-compose build
   ```
2. ```
   docker-compose -f docker-compose.yml -f docker-compose-airflow.yml up -d
   ```
3. Sometimes it can freeze or fail the first time, especially if your machine is not that high in spec (like mine T_T). But you can wait a second, try the last command again and it should start up fine.
4. That's it!

**Note:** Most of the services' restart is left unspecified, so they won't restart on failures (because sometimes it's quite resource-consuming during development, you see I have a poor laptop lol).

## With Kubernetes/Helm (Local cluster)
The system is quite large and heavy... I recommend running it locally just for setup testing purposes. Then if it works, just go off to the cloud if you want to play around longer OR stick with Docker Compose (it went smoother in my case)
1. Install Helm
   ```
   bash install-helm.sh
   ```
2. Create airflow namespace:
   ```
   kubectl create namespace airflow
   ```
3. Deploy the main chart:
   1. Fetch all dependencies
      ```
      cd sfmlops-helm
      helm dependency build
      ```
   2. ```
      helm -n mlops upgrade --install sfmlops-helm ./ --create-namespace -f values.yaml -f values-ray.yaml
      ```
4. Deploy Kafka:
   1. (1st time only)
      ```
      helm repo add bitnami https://charts.bitnami.com/bitnami
      ```
   2. ```
      helm -n kafka upgrade --install kafka-release oci://registry-1.docker.io/bitnamicharts/kafka --create-namespace --version 23.0.7 -f values-kafka.yaml
      ```
5. Deploy Airflow:
   1. (1st time only)
      ```
      helm repo add apache-airflow https://airflow.apache.org
      ```
   2. ```
      helm -n airflow upgrade --install airflow apache-airflow/airflow --create-namespace --version 1.13.1 -f values-airflow.yaml
      ```
   3. Sometimes, you might get a timeout error from this command (if you do, it means your machine spec is too poor for this system (like mine lol)). It's totally fine. Just keep checking the status with `kubectl`, if all resources start up correctly, go with it otherwise try running the command again.
6. Deploy Prometheus and Grafana:
   1. (1st time only)
      ```
      helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
      ```
   2. ```
      helm -n monitoring upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack  --create-namespace --version 57.2.0 -f values-kube-prometheus.yaml
      ```
   3. Forward port for Grafana:
      ```
      kubectl port-forward svc/kube-prometheus-stack-grafana 3000:80 -n monitoring
      ```
      *OR* assign `grafana.service.type: LoadBalancer` in `values-kube-prometheus.yaml`
   4. One of the good things about kube-prometheus-stack is that it comes with many pre-installed/pre-configured dashboards for Kubernetes. Feel free to explore!
7. That's it! Enjoy your highly scalable Machine Learning system for Sales forecasting! ;)

**Note:** If you want to change namespace `kafka` and/or release name `kafka-release` of Kafka, please also change them in `values.yaml` and `KAFKA_BOOTSTRAP_SERVER` env var in `values-airflow.yaml`. They are also used in templating.

**Note 2:** In Docker Compose, Ray has already been configured to pull the embedded dashboards from Grafana. But in Kubernetes, this process involves a lot more manual steps. So, I intentionally left it undone for ease of setup of this project. You can follow the guide [here](https://docs.ray.io/en/latest/cluster/kubernetes/k8s-ecosystem/prometheus-grafana.html) if you want to anyway.

## With Kubernetes/Helm (on GCP)
Prerequisites: GKE Cluster (Standard cluster, *NOT* Autopilot), Artifact Registry, Service Usage API, gcloud cli
1. Follow this [Medium blog](https://medium.com/@gravish316/setup-ci-cd-using-github-actions-to-deploy-to-google-kubernetes-engine-ef465a482fd). Instead of using the default Service Account (as done in the blog), I recommend creating a new Service Account with Owner role for a quick and dirty run (but of course, please consult your cloud engineer if you have security concerns).
2. Download your Service Account's JSON key
3. Activate your Service Account:
   ```
   gcloud auth activate-service-account --key-file=<PATH_TO_JSON_KEY>
   ```
4. Connect local kubectl to cloud:
   ```
   gcloud container clusters get-credentials <GKE_CLUSTER_NAME> --zone <GKE_ZONE> --project <PROJECT_NAME>
   ```
5. Now `kubectl` (and `helm`) will work in the context of the GKE environment.
6. Follow the steps in [With Kubernetes/Helm (Local cluster)](#with-kuberneteshelm-local-cluster) section
7. If you face a timeout error when running helm commands for airflow or the system struggles to set up and work correctly, I recommend trying to upgrade your machine type in the cluster.

**Note:** For the machine type of node pool in the GKE cluster, from experiments, `e2-medium` (default) is not quite enough, especially for Airflow and Ray. In my case, I went for `e2-standard-8` with 1 node (explanation on why only 1 node is in [Important note on MLflow on Cloud](#important-note-on-mlflow-on-cloud) section). I also found myself the need to increase the quota for PVC in IAM too.

## Cleanup steps
```
helm uninstall sfmlops-helm -n mlops
helm uninstall kafka-release -n kafka
helm uninstall airflow -n airflow
helm uninstall kube-prometheus-stack -n monitoring
```

## Important note on MLflow on Cloud
In this setting, I set the MLflow's artifact path to point to a local path. Internally, MLflow expects this path to be accessible from both MLflow client and server (honestly, I'm not a fan of this model either). It is meant to be an object storage path like S3 (AWS) or Cloud Storage (GCP). For a full on-premises experience, we can create a Docker volume and mount it to the EXACT same path on both client and server to address this. In a local Kubernetes cluster, we can do the same thing by creating a PVC with `accessModes: ReadWriteOnce` (in `sfmlops-helm/templates/mlflow-pvc.yaml`).

**However** for on-cloud Kubernetes with a typical multi-node cluster, if we want the PVC to be able to read and write across nodes, we need to set `accessModes: ReadWriteMany`. Most cloud providers *DO NOT* support this type of PVC and recommend using centralized storage instead. Therefore, if you want to just try it out and run for fun, you can use this exact setting and create a single-node cluster (which will behave similarly to a local Kubernetes cluster, just on the cloud). For a real production environment, please create a cloud storage bucket, remove `mlflow-pvc.yaml` and its mount paths, and change the artifact path variable `MLFLOW_ARTIFACT_ROOT` in `sfmlops-helm/templates/global-configmap.yaml` to the cloud storage path. Here's the official [doc](https://mlflow.org/docs/latest/tracking/artifacts-stores.html) for more information.

# References / Useful resources
- Ray sample config: https://github.com/ray-project/kuberay/tree/master/ray-operator/config/samples
- Bitnami Kafka Helm: https://github.com/bitnami/charts/tree/main/bitnami/kafka
- Airflow Helm: https://airflow.apache.org/docs/helm-chart/stable/index.html
- Airflow Helm default values.yaml: https://github.com/apache/airflow/blob/main/chart/values.yaml
- dataset: https://www.kaggle.com/datasets/pratyushakar/rossmann-store-sales
- Original Airflow's docker-compose file: https://airflow.apache.org/docs/apache-airflow/2.8.3/docker-compose.yaml

# My notes
If you have any comments, questions, or want to learn more, check out `notes/README.md`. I have included a lot of useful notes about how and why I made certain choices during development. Mostly, they cover tool selection, design choices, and some caveats.
