from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
)
from constructs import Construct
from typing import Dict

from pdm_cdk.pdm_cdk_construct import PdmCdkConstruct

class PdmCdkStack(Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        stack_name: str,
        app_name: str,
        config: Dict[str, str],
        environment: str,
        tags: Dict[str, str],
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ec2_instance = PdmCdkConstruct(
            self, stack_name, app_name, config, environment, tags
        )


