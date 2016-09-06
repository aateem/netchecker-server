#!/bin/bash

set -e

if [ -n "$1" ] ; then
  NS="--namespace=$1"
fi

# check there are nodes in the cluster
kubectl get nodes

echo "Installing netchecker server"
git clone https://github.com/aateem/netchecker-server.git
pushd netchecker-server
  docker build -t 127.0.0.1:31500/netchecker/server:latest .
  docker push 127.0.0.1:31500/netchecker/server:latest

  kubectl create -f k8s_resources/netchecker-server_pod.yaml $NS
  kubectl create -f k8s_resources/netchecker-server_svc.yaml $NS
popd

echo "Installing netchecker agents"
git clone https://github.com/aateem/netchecker-agent.git
pushd netchecker-agent
  pushd docker
    docker build -t 127.0.0.1:31500/netchecker/agent:latest .
    docker push 127.0.0.1:31500/netchecker/agent:latest
  popd
  kubectl get nodes | grep Ready | awk '{print $1}' | xargs -I {} kubectl label nodes {} netchecker=agent
  kubectl create -f netchecker-agent.yaml $NS
popd

echo "DONE"
echo
echo "use the following commands to "
echo "- check agents responses:"
echo "curl -s -X GET 'http://localhost:31081/api/v1/agents/' | python -mjson.tool"
echo "- check connectivity with agents:"
echo "curl -X GET 'http://localhost:31081/api/v1/connectivity_check'"
