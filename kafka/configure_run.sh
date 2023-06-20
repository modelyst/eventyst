#!/bin/sh

#   Copyright 2022 Modelyst LLC
#   All Rights Reserved

# Docker workaround: Remove check for KAFKA_ZOOKEEPER_CONNECT parameter
sed -i '/KAFKA_ZOOKEEPER_CONNECT/d' /etc/confluent/docker/configure

# Docker workaround: Ignore cub zk-ready
sed -i 's/cub zk-ready/echo ignore zk-ready/' /etc/confluent/docker/ensure

# KRaft required step: Format the storage directory with a new cluster ID
echo "kafka-storage format --ignore-formatted --cluster-id=xrx5mUMWTvaWbk157wFDKw -c /etc/kafka/kafka.properties" >> /etc/confluent/docker/ensure
