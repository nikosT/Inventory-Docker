.PHONY: help
.DEFAULT_GOAL := help
ARCHIVE=/archive
APP_NAME=inventory

help: ## This help
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Dockerfile for AutostatsQ
# Useful Docker commands:
# sudo docker run -it --name autostatsq autostatsq:1 /bin/bash
# sudo docker rm autostatsq
# sudo docker start/stop autostatsq
# sudo docker exec -it autostatsq /bin/bash

start: ## Build the container
	sudo docker build -t $(APP_NAME):1 .;
	sudo docker run -dit --restart unless-stopped --name="$(APP_NAME)" -p 8080:8080 $(APP_NAME):1


