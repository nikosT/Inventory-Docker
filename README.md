# Inventory-Docker
Dockerization of the Inventory microservice (created by Orfeus).

* ## Dependencies
You must have Docker installed.
```
sudo apt install docker
```

Other Docker installation for Ubuntu can be find here: https://docs.docker.com/install/linux/docker-ce/ubuntu/.

### Include the ```inventory.py``` file
You need to include at the same directory, the ```inventory.py``` file, created by Orfeus.


* ## Download
```
git clone https://github.com/nikosT/Inventory-Docker.git
```

* ## Start the container
```
cd Inventory-Docker
make start
```

* ## Stop and remove the container

```
cd Inventory-Docker
make stop
```
