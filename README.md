# Red Hat OpenShift Serverless Demo

This repository is intent to provide information on Red Hat's OpenShift Serverless (Knative Serving) capabilities.

Demoing Red Hat's OpenShift Serverless/Knative Eventing power.

## Eventing

Knative Eventing uses standard HTTP POST requests to send and receive events between event producers and sinks. These events conform to the CloudEvents specifications, which enables creating, parsing, sending, and receiving events in any programming language.

### InMemoryChannel Broker

In order to send events from a system (source) to a sink, you need a component which does it for you. This is a [Broker](https://docs.redhat.com/en/documentation/red_hat_openshift_serverless/1.34/html/eventing/brokers#serverless-brokers).

![Brokers](assets/serverless-event-broker-workflow.png)

For testing and lab purposes, Knative provides the `InMemoryChannel` broker. Other types of brokers are available too. Like Kafka or RabbitMQ for example. These kind of brokers should be used for production since they are providing e.g. event delivery guarantees.

Creating the `InMemoryChannel` broker:

`kn broker create inmem-broker`

Alternatively:

```shell
oc apply -f - <<EOF
apiVersion: eventing.knative.dev/v1
kind: Broker
metadata:
  name: inmem-broker
  namespace: rguske-kn-eventing
spec:
  config:
    apiVersion: v1
    kind: ConfigMap
    name: config-br-default-channel
    namespace: knative-eventing
  delivery:
    backoffDelay: PT0.2S
    backoffPolicy: exponential
    retry: 10
EOF
```

### Creating the Knative ApiServerSource

The `ApiServerSource` is a `source` which connects to the Kubernetes Api Server (ReadOnly) and receives all created events. These events can then be forwarded to e.g. a (subscribed) `Trigger`. Triggers will be covered below.

Create a service account, role, and role binding for the event source:

```yaml
oc create -f - <<EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: events-sa
  namespace: rguske-kn-eventing
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: event-watcher
  namespace: rguske-kn-eventing
rules:
  - apiGroups:
      - ""
    resources:
      - events
    verbs:
      - get
      - list
      - watch
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: k8s-ra-event-watcher
  namespace: rguske-kn-eventing
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: event-watcher
subjects:
  - kind: ServiceAccount
    name: events-sa
    namespace: rguske-kn-eventing
EOF
```

Create the ApiServerSource using mode `Resource` via Cli:

```shell
kn source apiserver create api-server-source \
--sink broker:inmem-broker \
--resource "event:v1" \
--service-account events-sa \
--mode Resource
```

Alternatively:

```yaml
apiVersion: sources.knative.dev/v1
kind: ApiServerSource
metadata:
  name: api-server-source
  namespace: rguske-kn-eventing
  labels:
    app: api-server-source
spec:
  mode: Reference
  resources:
    - apiVersion: v1
      kind: Event
  serviceAccountName: events-sa
  sink:
    ref:
      apiVersion: eventing.knative.dev/v1
      kind: Broker
      name: inmem-broker
```

### Event-Display Applications

In order to get all incoming events displayed either on a terminal or in a webbrower, Event Display applications come in handy.

Create a Knative service that dumps incoming messages to its log:

`kn service create event-display --image quay.io/openshift-knative/showcase`

This app can be browsed via its `route`:

```shell
kn route list
NAME            URL                                                                                READY
event-display   https://event-display-rguske-kn-eventing.apps.ocp4.stormshift.coe.muc.redhat.com   True
```

2nd application:

Install [Sockeye](https://github.com/n3wscott/sockeye)

```yaml
oc create -f - <<EOF
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: sockeye
spec:
  template:
    spec:
      containerConcurrency: 0
      containers:
      - image: n3wscott/sockeye:v0.7.0
EOF
```

Incoming events can be observed via `logs` or via browsing the url:

```shell
kn route list
NAME            URL                                                                                READY
event-display   https://event-display-rguske-kn-eventing.apps.ocp4.stormshift.coe.muc.redhat.com   True
sockeye         https://sockeye-rguske-kn-eventing.apps.ocp4.stormshift.coe.muc.redhat.com         True
```

`kn service update --scale 1 sockeye`

### Triggers

After events have entered the broker, they can be filtered by CloudEvent attributes using triggers, and sent as an `HTTP POST` request to an event sink.

Event source --> Broker --> Trigger --> Sink
Kubernetes --> InMemoryChannel Broker --> Trigger --> Sockeye

Create `trigger`s for the two event-display apps:

`kn trigger create trigger-event-display --broker inmem-broker --sink ksvc:event-display`

`kn trigger create trigger-sockeye --broker inmem-broker --sink ksvc:sockeye`

```shell
kn trigger list
NAME                    BROKER         SINK                 AGE   CONDITIONS   READY   REASON
trigger-event-display   inmem-broker   ksvc:event-display   26s   7 OK / 7     True
trigger-sockeye         inmem-broker   ksvc:sockeye         17s   7 OK / 7     True
```

In `yaml`:

```yaml
oc create -f - <<EOF
apiVersion: eventing.knative.dev/v1
kind: Trigger
metadata:
  labels:
    eventing.knative.dev/broker: inmem-broker
  name: trigger-event-display
  namespace: rguske-kn-eventing
spec:
  broker: inmem-broker
  filter: {}
  subscriber:
    ref:
      apiVersion: serving.knative.dev/v1
      kind: Service
      name: event-display
      namespace: rguske-kn-eventing
EOF
```

```yaml
oc create -f - <<EOF
apiVersion: eventing.knative.dev/v1
kind: Trigger
metadata:
  labels:
    eventing.knative.dev/broker: inmem-broker
  name: trigger-sockeye
  namespace: rguske-kn-eventing
spec:
  broker: inmem-broker
  filter: {}
  subscriber:
    ref:
      apiVersion: serving.knative.dev/v1
      kind: Service
      name: sockeye
      namespace: rguske-kn-eventing
EOF
```
