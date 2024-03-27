FROM python:3.9.17-slim

ARG WEB_UI_PORT=$WEB_UI_PORT

COPY requirements.txt /service/requirements.txt

RUN pip install -r /service/requirements.txt

COPY app/ /service/app/

EXPOSE $WEB_UI_PORT

WORKDIR /service/app

CMD streamlit run main.py --server.port $WEB_UI_PORT --server.address 0.0.0.0