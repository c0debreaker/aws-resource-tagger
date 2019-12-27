#!/usr/bin/env python3

from aws_cdk import core

from stacks.autotags_stack import AutoTagsStack

app = core.App()
aws_account = "<AWS ACCOUNT>"
regions = ["us-east-1", "us-east-2", "us-west-1", "us-west-2"]

for region in regions:
    env_region = core.Environment(account=aws_account, region=region)
    AutoTagsStack(
        app,
        "AWSResourceTagger-" + region,
        env = env_region,
        tags = {
            "Team": "DevOps",
            "Project": "AWS Resource Tagger",
            "Owner": "DevOps Team"
        }
    )

app.synth()
