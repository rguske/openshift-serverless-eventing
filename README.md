# Red Hat OpenShift Serverless Demo

WIP!

Demoing Red Hat's OpenShift Serverless/Knative Eventing power.

## Eventing

### RabbitMQ Operator installation

`kubectl apply -f https://github.com/rabbitmq/cluster-operator/releases/latest/download/cluster-operator.yml`

Topology and Messaging

`kubectl apply -f https://github.com/rabbitmq/messaging-topology-operator/releases/latest/download/messaging-topology-operator-with-certmanager.yaml`

Install the RabbitMQ controller

`kubectl apply -f https://github.com/knative-extensions/eventing-rabbitmq/releases/download/knative-v1.15.0/rabbitmq-broker.yaml`

`kubectl create ns rabbitmq-cluster`

### Event-Display App Sockeye

Install Sockeye

```yaml
kubectl create -f - <<EOF
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: sockeye
  namespace: rguske-functions
spec:
  template:
    spec:
      containerConcurrency: 0
      containers:
      - image: n3wscott/sockeye:v0.7.0
EOF
```

`kn service update --scale 1 sockeye -n functions`

`kn trigger create sockeye --broker kn-mtchannel-broker --sink ksvc:sockeye -n rguske-functions`

```yaml
apiVersion: eventing.knative.dev/v1
kind: Trigger
metadata:
  name: sockeye-trigger
spec:
  broker: rabbitmq-broker
  subscriber:
    ref:
      apiVersion: v1
      kind: Service
      name: sockeye
EOF
```

### Eventing Sources

#### Knative ApiServerSource (Kubernetes API)




#### Tanzu Sources for Knative (vCenter Server API)

#### Install Tanzu Sources for Knative

`kubectl apply -f https://github.com/vmware-tanzu/sources-for-knative/releases/latest/download/release.yaml`

`kubectl create ns vsphere-sources`

```code
export USER='kn-ro@vsphere.local'
export PWD='VMware1!'
```

```code
kn vsphere auth create \
--namespace knative-sources \
--username ${USER} \
--password ${PWD} \
--name vcsa-creds \
--verify-url https://vcsa.jarvis.lab \
--verify-insecure
```

```code
kn vsphere source create \
--namespace knative-sources \
--name vcsa-source \
--vc-address https://vcsa.jarvis.lab \
--skip-tls-verify \
--secret-ref vcsa-creds \
--sink-uri http://broker-ingress.knative-eventing.svc.cluster.local/redhat-functions/default \
--encoding json
```