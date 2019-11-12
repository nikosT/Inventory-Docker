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

#RUN echo "deb http://deb.obspy.org bionic main" > /etc/apt/sources.list

RUN wget --quiet -O - https://raw.github.com/obspy/obspy/master/misc/debian/public.key | apt-key add -
RUN apt update

RUN pip2 install -U obspy

RUN pip2 install -U bottle

EXPOSE 8080

COPY ./inventory.py ./inventory.py
COPY ./config.json ./config.json

CMD python ./inventory.py
