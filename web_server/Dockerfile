FROM python:3.10

ENV WEB_SERVER /web_server

WORKDIR $WEB_SERVER

COPY web_server web_server
COPY front-init front-init

VOLUME /web_server/front-init/storage

EXPOSE 3000

ENTRYPOINT ["python", "web_server/main.py"]