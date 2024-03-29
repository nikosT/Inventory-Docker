# Dockerfile for Inventory Service
# Useful Docker commands:
# sudo docker build -t "inventory:1" .
# sudo docker run -it --name inventory inventory:1 /bin/bash
# sudo docker rm inventory
# sudo docker start/stop inventory
# sudo docker exec -it inventory /bin/bash


# ******************** Base OS ***********************************************
# get Ubuntu 18.04 image
FROM ubuntu:18.04
RUN apt update


# ******************** METADATA **********************************************
LABEL version="1.0"
LABEL software="Inventory Docker"
LABEL software.version="1.0"
LABEL about.summary="Docker containerization of the inventory software"
LABEL about.license_file="https://www.gnu.org/licenses/gpl-3.0.html"
LABEL about.license="SPDX:GPL-3.0-only"
LABEL maintainer="triantafyl@noa.gr"


# ******************** INSTALLATION ******************************************

# install dependencies
ENV DEBIAN_FRONTEND=noninteractive
RUN apt install -y python python-pip python-dev libxft-dev libfreetype6 \
libfreetype6-dev wget python-numpy python-matplotlib

RUN apt install -y lsb-release

RUN echo "deb http://deb.obspy.org `lsb_release -cs` main" > /etc/apt/sources.list

RUN wget --quiet -O - https://raw.github.com/obspy/obspy/master/misc/debian/public.key | apt-key add -
RUN apt update

RUN echo "deb http://in.archive.ubuntu.com/ubuntu/ `lsb_release -cs` main restricted universe multiverse" >> /etc/apt/sources.list

RUN apt update;
RUN apt install -y nano iputils-ping net-tools

RUN apt install -y libev-dev
COPY ./requirements.txt ./requirements.txt
RUN pip install -r ./requirements.txt

COPY ./inventory.py ./inventory.py
COPY ./config.json ./config.json

CMD python ./inventory.py 0.0.0.0
#CMD python ./inventory.py `ifconfig eth0 | grep inet | awk '{print $2}'`

