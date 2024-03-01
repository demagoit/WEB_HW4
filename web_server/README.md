BUILD
sudo docker build -t <image name> .

RUN
sudo docker run -it -p <host port>:3000 -v <host volume>:/web_server/front-init/storage <image name>