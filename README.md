netchecker-server
=================

Basic network checker service to check DNS and connectivity in kubernetes
cluster. Should be used together with [netchecker-agent]
(https://github.com/adidenko/netchecker-agent).

Service listens on 8081 port (31081 nodePort) and accepts updates from agents.
You can use simple `curl` to get status (see below).

How to
------
* Build and push container:

```bash
docker build -t 127.0.0.1:31500/netchecker/server:latest .
docker push 127.0.0.1:31500/netchecker/server:latest
```

* Run netchecker server pod:

```bash
kubectl create -f k8s_resources/netchecker-server_pod.yaml
```

* Run service:

```bash
kubectl create -f k8s_resources/netchecker-server_svc.yaml
```

* Check status:

```bash
curl -s localhost:31081/api/v1/agents/
```

Examples
--------

* Get all agents:

```bash
root@k8s-02:~/ curl -s -X GET 'http://localhost:31081/api/v1/agents/' | python -mjson.tool
{
    "netchecker-agent-p6qyc": {
        "hostdate": "2016-07-01 13:02:23",
        "hostname": "netchecker-agent-p6qyc",
        "ips": " inet 127.0.0.1/8 scope host lo inet 10.233.89.23/32 scope global eth0",
        "last-updated": "2016-07-01 13:02:24",
        "nslookup": "Server: 10.233.0.2 Address 1: 10.233.0.2 Name: netchecker-service Address 1: 10.233.9.153",
        "resolvconf": "search default.svc.cluster.local svc.cluster.local cluster.local default.svc.cluster.local svc.cluster.local cluster.local nameserver 10.233.0.2 options attempts:2 options ndots:5"
    },
    "netchecker-agent-wffal": {
        "hostdate": "2016-07-01 13:02:27",
        "hostname": "netchecker-agent-wffal",
        "ips": " inet 127.0.0.1/8 scope host lo inet 10.233.80.213/32 scope global eth0",
        "last-updated": "2016-07-01 13:02:27",
        "nslookup": "Server: 10.233.0.2 Address 1: 10.233.0.2 Name: netchecker-service Address 1: 10.233.9.153",
        "resolvconf": "search default.svc.cluster.local svc.cluster.local cluster.local default.svc.cluster.local svc.cluster.local cluster.local nameserver 10.233.0.2 options attempts:2 options ndots:5"
    }
}
```

