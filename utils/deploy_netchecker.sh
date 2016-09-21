#!/bin/bash

set -e

if [ -n "$1" ] ; then
  NS="--namespace=$1"
fi

# check there are nodes in the cluster
kubectl get nodes

echo "Installing netchecker server"
echo '
apiVersion: v1
kind: Pod
metadata:
  name: netchecker-server
  labels:
    app: netchecker-server
spec:
  containers:
    - name: netchecker-server
      image: l23network/mcp-netchecker-server
      env:
      imagePullPolicy: Always
      ports:
        - containerPort: 8081
          hostPort: 8081
    - name: kubectl-proxy
      image: "gcr.io/google_containers/kubectl:v0.18.0-120-gaeb4ac55ad12b1-dirty"
      imagePullPolicy: "Always"
      args:
        - "proxy"
---
kind: "Service"
apiVersion: "v1"
metadata:
  name: "netchecker-service"
spec:
  selector:
    app: "netchecker-server"
  ports:
    -
      protocol: "TCP"
      port: 8081
      targetPort: 8081
      nodePort: 31081
  type: "NodePort"
' | kubectl create -f - $NS

echo "Installing netchecker agents"
kubectl get nodes | grep Ready | awk '{print $1}' | xargs -I {} kubectl label nodes {} netchecker=agent

echo '
apiVersion: extensions/v1beta1
kind: DaemonSet
metadata:
  labels:
    app: netchecker-agent-hostnet
  name: netchecker-agent
spec:
  template:
    metadata:
      name: netchecker-agent
      labels:
        app: netchecker-agent
    spec:
      containers:
        - name: netchecker-agent
          image: l23network/mcp-netchecker-agent
          env:
            - name: MY_POD_NAME
              valueFrom:
                fieldRef:
                  fieldPath: metadata.name
          imagePullPolicy: Always
      nodeSelector:
        netchecker: agent
---
apiVersion: extensions/v1beta1
kind: DaemonSet
metadata:
  labels:
    app: netchecker-agent-hostnet
  name: netchecker-agent-hostnet
spec:
  template:
    metadata:
      name: netchecker-agent-hostnet
      labels:
        app: netchecker-agent-hostnet
    spec:
      hostNetwork: True
      containers:
        - name: netchecker-agent
          image: l23network/mcp-netchecker-agent
          env:
            - name: MY_POD_NAME
              valueFrom:
                fieldRef:
                  fieldPath: metadata.name
          imagePullPolicy: Always
      nodeSelector:
        netchecker: agent
' | kubectl create -f - $NS

echo "DONE"
echo "use the following commands to "
echo "- check agents responses:"
echo "curl -s -X GET 'http://localhost:31081/api/v1/agents/' | python -mjson.tool"
echo "- check connectivity with agents:"
echo "curl -X GET 'http://localhost:31081/api/v1/connectivity_check'"
