all: build
.PHONY: all build

BUILD_IMAGE ?= colonyos/mlexecutor
PUSH_IMAGE ?= colonyos/mlexecutor

container:
	docker build -t $(BUILD_IMAGE) .

push:
	docker tag $(BUILD_IMAGE) $(PUSH_IMAGE) 
	docker push $(PUSH_IMAGE)

run: 
	colonies executor remove --name python-executor; make container; docker run --gpus all -it colonyos/mlexecutor:latest

