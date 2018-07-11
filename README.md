# Python Kubernetes Operator

This package is a quick way to get a working Kubernetes Operator. See bellow for an example:

```
from pykubeop import KubernetesOperator, CRDBase

class MyOperator(CRDBase):
    GROUP = 'example.clearscore.io'
    VERSION = 'v1alpha1'
    SINGULAR = `testobject`
    PLURAL = `testobjects`
    KIND = `TestObject`

    def ensure_created(self):
        // Do some custom logic for ADDED events here

    def ensure_modified(self):
        // Do some custom logic for MODIFIED events here

    def ensure_deleted(self):
        // Do some custom logic for DELETE events here


if __name__ == '__main__':
    KubernetesOperator(MyCustomResource).run()
```

## State

The operator logic will only process `ADDED` events when a `CustomObject` _doesn't_ have `status.created` set, e.g.:

Will get processed:

```
kind: MyCR
apiGroup: mycrs.crs.example.com
metadata:
  name: test-cr
spec: {}
status:
  someStatusInfo:
    moreStatusInfo: here
```

Won't get processed:

```
kind: MyCR
apiGroup: mycrs.crs.example.com
metadata:
  name: test-cr
spec: {}
status:
  state: processed <---- This will prevent processing
```

## Helpers

### self.status

the `CRDBase` object has a helper property called `status`. When written to it will updated the `status` field of the CustomObject. This allows for easy updating of the status as you process events. Example:

```
self.status = {'state': 'created', 'extraInfo': {'someMoreInfo': 'here'}}
```

### self.crd_api

A pre-configured instance of `kubernetes.client.CustomObjectsApi` is available for use at `self.crd_api`
