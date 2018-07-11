import json
import kubernetes.client
import logging
import urllib

from op.states import (KUBERNETES_EVENT_ADDED,
                       KUBERNETES_EVENT_MODIFIED,
                       KUBERNETES_EVENT_DELETED)


class CRDMeta(type):
    @property
    def API_GROUP(self):
        return '{}.{}'.format(self.PLURAL, self.GROUP)


class CRDBase(object, metaclass=CRDMeta):
    GROUP = None
    VERSION = None
    PLURAL = None
    KIND = None
    SINGULAR = None
    RESOURCE_VERSION = None
    SCOPE = "Namespaced"

    def __init__(self, cr, crd_api=None, **kwargs):
        self.__cr = cr
        self.metadata = cr['metadata']
        self.spec = cr['spec']
        if crd_api:
            self.__customObjectsApi = crd_api
        else:
            self.__customObjectsApi = kubernetes.client.CustomObjectsApi(
                kubernetes.client.ApiClient(configuration=kubernetes.client.Configuration())
            )
        self.logger = logging.getLogger(__name__)

    @property
    def status(self):
        try:
            return self.__cr['status']
        except KeyError:
            return {}
    
    @status.setter
    def status(self, value):
        if 'status' not in value:
            value = {'status': value}
        resource = self.__customObjectsApi.patch_namespaced_custom_object(
            self.GROUP,
            self.VERSION,
            self.metadata['namespace'],
            self.PLURAL,
            self.metadata['name'],
            value
        )
        self.__cr['status'] = resource['status']

    @classmethod
    def get_watch_stream(cls, crd_api, namespace=None):
        if namespace:
            return kubernetes.watch.Watch().stream(
                crd_api.list_cluster_custom_object,
                group=cls.GROUP,
                version=cls.VERSION,
                namespace=namespace,
                plural=cls.PLURAL,
                resource_version=cls.RESOURCE_VERSION
            )
        else:
            return kubernetes.watch.Watch().stream(
                crd_api.list_cluster_custom_object,
                group=cls.GROUP,
                version=cls.VERSION,
                plural=cls.PLURAL,
                resource_version=cls.RESOURCE_VERSION
            )
    
    @classmethod
    def get_custom_resource(cls, api, name, namespace):
        try:
            return api.get_namespaced_custom_object(
                cls.GROUP,
                cls.VERSION,
                namespace,
                cls.PLURAL,
                name
            )
        except kubernetes.client.api_client.ApiException as e:
            if e.status == 404:
                return None
            raise e

    @classmethod
    def get_custom_resource_definition(cls, api_client):
        ext_client = kubernetes.client.ApiextensionsV1beta1Api(api_client=api_client)
        try:
            return ext_client.read_custom_resource_definition('{}.{}'.format(cls.PLURAL, cls.GROUP))
        except kubernetes.client.rest.ApiException as e:
            if e.status != 404:
                raise e
            return None

    @classmethod
    def create_custom_resource_definiton(cls, api_client):
        ext_client = kubernetes.client.ApiextensionsV1beta1Api(api_client=api_client)
        # Hacky workaround for
        # https://github.com/kubernetes/kubernetes/pull/64996 and
        # https://github.com/kubernetes-client/gen/issues/52
        try:
            ext_client.create_custom_resource_definition(cls.__get_custom_resource_definition())
        except ValueError as e:
            if e.args[0] == 'Invalid value for `conditions`, must not be `None`':
                pass
            else:
                raise e

    @classmethod
    def __get_custom_resource_definition(cls):
        return kubernetes.client.V1beta1CustomResourceDefinition(
            metadata={'name': '{}.{}'.format(cls.PLURAL, cls.GROUP)},
            spec=cls.__get_crd_spec()
        )


    @classmethod
    def __get_crd_spec(cls):
        return kubernetes.client.V1beta1CustomResourceDefinitionSpec(
            group=cls.GROUP,
            names=cls.__get_crd_names(),
            scope=cls.SCOPE,
            version=cls.VERSION
        )

    @classmethod
    def __get_crd_names(cls):
        return kubernetes.client.V1beta1CustomResourceDefinitionNames(
            kind=cls.KIND,
            plural=cls.PLURAL,
            singular=cls.SINGULAR
        )

    def ensure(self, action):
        self.logger.debug("Kubernetes CRD Action: %s", action)
        self.logger.debug("CustomResource State: %s", self.status.get('state', ''))
        if action == KUBERNETES_EVENT_ADDED and 'state' not in self.status:
            try:
                self.ensure_created()
                self.status = {'state': 'processed'}
            except Exception as e:
                self.status = {'state': 'error', 'error': str(e)}
        elif action == KUBERNETES_EVENT_MODIFIED:
            self.ensure_modified()
        elif action == KUBERNETES_EVENT_DELETED:
            self.ensure_deleted()
        elif 'state' in self.status:
            self.logger.debug("CustomResource state is present. No action taken")
        else:
            self.logger.warning("Unknown Kubernetes CRD event %s. Ignoring", action)

    def ensure_created(self):
        raise NotImplementedError()

    def ensure_modified(self):
        raise NotImplementedError()

    def ensure_deleted(self):
        raise NotImplementedError()

    def get_owner_reference(self):
        return [
            kubernetes.client.V1OwnerReference(
                api_version=self.VERSION,
                block_owner_deletion=True,
                controller=True,
                kind=self.KIND,
                name=self.metadata['name'],
                uid=self.metadata['uid']
            )
        ]

    def get_create_body(self, name, namespace, spec, owners=[]):
        body = {
            'kind': self.KIND,
            'apiVersion': '{}/{}'.format(self.GROUP, self.VERSION),
            'metadata': {
                'name': name,
                'namespace': namespace,
            },
            'spec': spec
        }
        if owners != []:
            body['metadata']['ownerReferences'] = owners
        return urllib.parse.urlencode(json.dumps(body))
