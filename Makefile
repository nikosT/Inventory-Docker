.PHONY: help
.DEFAULT_GOAL := help
ARCHIVE=/archive
APP_NAME=inventory

help: ## This help
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

start: ## Build the container
	sudo docker build -t $(APP_NAME):1 .;
	sudo docker run -d --restart unless-stopped --name="$(APP_NAME)" $(APP_NAME):1

stop: ## Stop and remove the container
	sudo docker stop $(APP_NAME); sudo docker rm $(APP_NAME);


