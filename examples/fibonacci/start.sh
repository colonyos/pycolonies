#!/bin/bash

docker run -it -e COLONIES_SERVER_HOST=$COLONIES_SERVER_HOST -e COLONIES_SERVER_PORT=$COLONIES_SERVER_PORT -e COLONIES_COLONY_ID=$COLONIES_COLONY_ID -e COLONIES_COLONY_PRVKEY=$COLONIES_COLONY_PRVKEY colonyos/fibexecutor:latest
