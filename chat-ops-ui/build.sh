#! /bin/bash

ng build --prod
docker build -t ${1} .
