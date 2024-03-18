FROM ubuntu:20.04
# FROM nvidia/cuda:11.4.3-cudnn8-devel-ubuntu20.04

USER root

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        libfreetype6-dev \
        libpng-dev \
        libzmq3-dev \
        pkg-config \
        python3 \
        python3-dev \
        python3-pip \
        python3-setuptools \
        rsync \
        software-properties-common \
        unzip \
        git \
        zip \
        wget \
        vim \
        nano \
        sudo \
        npm \
        libgl1 \ 
        # for DeepChecks
        libxml2-dev \
        libxslt-dev \
        # required for prefect
        tzdata \
        # lib for opencv
        libsm6 \
        libxrender1 \
        libfontconfig1 \
        # for pyspark
        default-jre-headless \
        && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ARG NB_USER=$NB_USER
ARG NB_UID=$NB_UID
ARG CONDA_DIR=$CONDA_DIR
ARG ARCH=$ARCH
ARG JUPYTER_PORT=$JUPYTER_PORT
ARG MLFLOW_ARTIFACT_ROOT=$MLFLOW_ARTIFACT_ROOT
ARG CENTRAL_STORAGE_PATH=$CENTRAL_STORAGE_PATH
ARG MAIN_CONDA_ENV_NAME=$MAIN_CONDA_ENV_NAME

# Add a new user and assign sudo privilege
RUN useradd --create-home --shell /bin/bash $NB_USER && \
    usermod -aG sudo $NB_USER
# disable password for sudo
RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

# Config path dir and permission anaconda
RUN mkdir -p $CONDA_DIR && \
    chown -R $NB_USER:$NB_USER $CONDA_DIR && \
    chmod -R go+rX $CONDA_DIR

# Config path dir and permission for mlflow artifacts storage
# NOTE: we don't need to do this for prefect storage since every file prefect produces
# they are stored in either postgresql or server's container itself
# but mlflow stores artifacts to client's container
RUN mkdir -p $MLFLOW_ARTIFACT_ROOT && \
    chown -R $NB_USER:$NB_USER $MLFLOW_ARTIFACT_ROOT && \
    chmod -R go+rX $MLFLOW_ARTIFACT_ROOT

# for model storage too!
RUN mkdir -p $CENTRAL_STORAGE_PATH/models $CENTRAL_STORAGE_PATH/ref_data && \
    chown -R $NB_USER:$NB_USER $CENTRAL_STORAGE_PATH && \
    chmod -R go+rX $CENTRAL_STORAGE_PATH

# Config permission user
USER $NB_USER
RUN chown $NB_USER /home/$NB_USER/
RUN chmod a+rwx /home/$NB_USER/
ENV HOME=/home/$NB_USER \
    SHELL=/bin/bash \
    NB_USER=$NB_USER \
    NB_UID=$NB_UID \
    NB_GID=$NB_GID
# this ENV is for installing pip package
ENV PATH=$HOME/.local/bin/:$PATH 
WORKDIR /home/$NB_USER

# Install conda
RUN curl -O https://repo.anaconda.com/miniconda/Miniconda3-py38_23.3.1-0-Linux-${ARCH}.sh && \
    bash Miniconda3-py38_23.3.1-0-Linux-${ARCH}.sh -f -b -p $CONDA_DIR

# Put conda in path 
# PIP_DEFAULT_TIMEOUT=100 to solve ReadTimeoutError when pip install large packages
ENV PATH=$CONDA_DIR/bin:$PATH \
    PIP_DEFAULT_TIMEOUT=100 

# update conda
RUN conda update -n base conda

RUN sudo -E env "PATH=$PATH" conda install -c conda-forge notebook jupyterlab jupyterhub && \
    jupyter notebook --generate-config --allow-root && \
    echo 'c.ServerApp.root_dir = "/"' >> /home/$NB_USER/.jupyter/jupyter_notebook_config.py && \
    echo 'c.ServerApp.ip = "0.0.0.0"' >> /home/$NB_USER/.jupyter/jupyter_notebook_config.py && \
    # password: 123456789
    echo "c.ServerApp.password = u'sha1:0ae9a92c3841:d81df7ba0b0224cae1230d0a9238df01e06953c9'" >> /home/$NB_USER/.jupyter/jupyter_notebook_config.py

COPY ./requirements.txt $HOME/requirements.txt
RUN conda init bash && \
    # if it's not your 1st build, sometimes conda will reuse cache which is stored in /opt/anaconda3
    # at this stage, we are not root, so it can cause permission error. the next line's served to prevent this
    conda clean --all --force-pkgs-dirs && \
    conda create -n ${MAIN_CONDA_ENV_NAME} python=3.9

# For Airflow
ENV SLUGIFY_USES_TEXT_UNIDECODE=yes

RUN conda run -n ${MAIN_CONDA_ENV_NAME} pip install -r requirements.txt && \
    conda run -n ${MAIN_CONDA_ENV_NAME} pip install jupyter -U && \
    conda run -n ${MAIN_CONDA_ENV_NAME} ipython kernel install --name ${MAIN_CONDA_ENV_NAME} --user

RUN sudo mkdir -m 777 -p ./workspace/docker_workspace ./workspace/Python-Practices

# Jupyter listens to specified port
EXPOSE $JUPYTER_PORT

# Run Jupyter lab as Docker main process
CMD jupyter lab --port ${JUPYTER_PORT}