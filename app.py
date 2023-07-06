#!/usr/bin/env python3
import yaml
import os

import aws_cdk as cdk

from pdm_cdk.pdm_cdk_stack import PdmCdkStack

app = cdk.App()

environment = app.node.try_get_context("env")

if environment is None:
    print(
        'Environment or client context is missing. Please add context by using "-c env=value" to your cdk command'
    )
    exit(1)


with open(f"config/config.yaml", "r") as stream:
    try:
        config = yaml.safe_load(stream)
    except yaml.YAMLError as e:
        print(e)
        exit(1)

environment_config = config.get(environment)
account = environment_config.get("account")
region = environment_config.get("region")
app_name = environment_config.get("app_name")

tags = {"env": environment}

stack_vpc = PdmCdkStack(
    app,
    f"{app_name}-{environment}-stack",
    env=cdk.Environment(account=account, region=region),
    stack_name=f"{app_name}-{environment}-stack",
    app_name=app_name,
    config=environment_config,
    environment=environment,
    tags=tags,
    description=config.get("description"),
)

app.synth()
