#!/bin/bash

set -o xtrace

kubectl delete deployment allure-deployment --namespace allure-docker-service
kubectl delete configmap allure-config-map --namespace allure-docker-service
kubectl delete secret my-domain-com-tls --namespace allure-docker-service
kubectl delete persistentvolumeclaim allure-persistent-volume-claim --namespace allure-docker-service
kubectl delete persistentvolume allure-persistent-volume
kubectl delete ingress allure-ingress-service-load-balancer --namespace allure-docker-service
kubectl delete ingress allure-ingress-service-node-port --namespace allure-docker-service
kubectl delete service allure-service-load-balancer --namespace allure-docker-service
kubectl delete service allure-service-node-port --namespace allure-docker-service


kubectl get all -o wide --namespace allure-docker-service
kubectl get configmaps --namespace allure-docker-service
kubectl get secrets --namespace allure-docker-service
kubectl get persistentvolumeclaims --namespace allure-docker-service
kubectl get persistentvolumes

kubectl delete namespace allure-docker-service
