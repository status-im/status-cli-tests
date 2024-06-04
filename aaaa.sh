#!/bin/bash

# Variables
PROCESS_NAME="./status-cli serve"
NETNS_NAME="ns_status_cli"
VETH_HOST="veth_host_cli"
VETH_NS="veth_ns_cli"
IP_HOST="10.200.1.1/24"
IP_NS="10.200.1.2/24"
DELAY="10000ms"

# Delete existing network namespace and veth pair if they exist
sudo ip netns delete $NETNS_NAME 2>/dev/null
sudo ip link delete $VETH_HOST 2>/dev/null

# Create network namespace
sudo ip netns add $NETNS_NAME

# Create veth pair
sudo ip link add $VETH_HOST type veth peer name $VETH_NS

# Move one end of veth pair to namespace
sudo ip link set $VETH_NS netns $NETNS_NAME

# Assign IP addresses
sudo ip addr add $IP_HOST dev $VETH_HOST
sudo ip link set $VETH_HOST up
sudo ip netns exec $NETNS_NAME ip addr add $IP_NS dev $VETH_NS
sudo ip netns exec $NETNS_NAME ip link set $VETH_NS up
sudo ip netns exec $NETNS_NAME ip link set lo up

# Apply latency
sudo ip netns exec $NETNS_NAME tc qdisc add dev $VETH_NS root netem delay $DELAY

# Move the process to the network namespace
PID=$(pgrep -f "$PROCESS_NAME")
sudo ip netns exec $NETNS_NAME kill -SIGSTOP $PID
sudo ip netns exec $NETNS_NAME nsenter --net=/proc/$PID/ns/net kill -SIGCONT $PID

echo "Applied $DELAY latency to process $PROCESS_NAME in network namespace $NETNS_NAME"
