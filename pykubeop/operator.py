import argparse
import kubernetes
import logging


class KubernetesOperator(object):
    arguments = []

    def __init__(self, crd):
        self.crd = crd
        parser = argparse.ArgumentParser(crd.KIND)
        parser.add_argument(
            "--scope",
            default="cluster",
            choices=["cluster", "namespaced"],
            help="Cluster or Namespace Scoped?"
        )
        parser.add_argument(
            "--namespace",
            default=None,
            help="Which namespace to monitor for {} objects".format(crd.KIND)
        )
        parser.add_argument(
            "--create-crd",
            action="store_true",
            help="Create the CustomResourceDefinition on startup if missing"
        )
        parser.add_argument(
            "--external",
            action="store_true",
            help="Run outside of the Kubernetes Cluster"
        )
        parser.add_argument(
            "-L",
            "--log-level",
            default="INFO",
            choices=["DEBUG", "INFO", "WARNING", "ERROR"]
        )
        self.add_arguments(parser)
        self.args = parser.parse_args()
        logging.basicConfig(level=getattr(logging, self.args.log_level))
        self.logger = logging.getLogger("KubernetesOperator")
        self.setup_apis()

    def add_arguments(self, parser):
        pass

    def setup_apis(self):
        if self.args.external:
            kubernetes.config.load_kube_config()
        else:
            kubernetes.config.load_incluster_config()
        self.api_client = kubernetes.client.api_client.ApiClient(
            configuration=kubernetes.client.Configuration()
        )
        self.api_extensions_client = kubernetes.client.ApiextensionsV1beta1Api(
            api_client=self.api_client
        )
        self.crd_client = kubernetes.client.CustomObjectsApi(
            api_client=self.api_client
        )

    def get_crd_object(self, obj):
        return self.crd(
            obj, self.crd_client, logger=self.logger, args=self.args
        )

    def run(self):
        self.logger.info("Starting Kubernetes Operator")
        if self.args.create_crd:
            self.logger.info(
                "Checking for CustomResourceDefintion for %s", self.crd.KIND
            )
            if not self.crd.get_custom_resource_definition(self.api_client):
                self.logger.info(
                    "Creating CustomResourceDefintion: %s", self.crd.API_GROUP
                )
                self.crd.create_custom_resource_definition(self.api_client)
                self.logger.info(
                    "CustomResourceDefinition %s created", self.crd.API_GROUP
                )
            else:
                self.logger.info(
                    "CustomResourceDefinition %s already exists", self.crd.API_GROUP
                )

        self.logger.info("Watching Kubernetes API for new %s Resources", self.crd.KIND)
        running = True
        while running:
            try:
                if self.args.scope == "cluster":
                    stream = self.crd.get_watch_stream(self.crd_client)
                else:
                    stream = self.crd.get_watch_stream(
                        self.crd_client, self.args.namespace
                    )

                for event in stream:
                    instance = self.get_crd_object(event['object'])
                    instance.ensure(event['type'])

            except KeyboardInterrupt:
                self.logger.info("Keyboard Interrupt Triggered. Exiting....")
                running = False
            except Exception as e:
                self.logger.error("Unhandled Exception: %s" % e)
                self.logger.exception(e)
