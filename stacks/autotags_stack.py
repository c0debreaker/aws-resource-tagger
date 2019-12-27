from aws_cdk import (
    core,
    aws_iam as _iam,
    aws_lambda as _lambda,
    aws_events as _events,
    aws_events_targets as _targets
)

class AutoTagsStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        eventTargets = []

        policyStatement = _iam.PolicyStatement(
            resources = ['*'],
            actions = [
                "cloudwatch:PutMetricAlarm",
                "cloudwatch:ListMetrics",
                "cloudwatch:DeleteAlarms",
                "ec2:CreateTags",
                "ec2:Describe*",
                "ec2:Attach*",
                "elasticloadbalancing:Describe*",
                "elasticloadbalancing:Create*",
                "elasticloadbalancing:AddTags"
            ],
            effect = _iam.Effect.ALLOW
        )

        glom_layer = _lambda.LayerVersion.from_layer_version_attributes(
            self,
            "glom_api_layer",
            layer_version_arn="arn:aws:lambda:us-east-1:<AWS ACCOUNT>:layer:python-glom-layer:1",
            compatible_runtimes=[
                _lambda.Runtime.PYTHON_3_6,
                _lambda.Runtime.PYTHON_3_7
            ]
        )

        eventHandler = _lambda.Function(
            self,
            'resourceTagger',
            runtime = _lambda.Runtime.PYTHON_3_7,
            code = _lambda.Code.asset('lambda'),
            handler = 'auto_tag.handler',
            layers=[glom_layer]
        )

        eventHandler.add_to_role_policy(policyStatement)

        eventTargets.append(_targets.LambdaFunction(handler = eventHandler))

        pattern = _events.EventPattern(
            source = ['aws.ec2', 'aws.elasticloadbalancing'],
            detail_type = [ "AWS API Call via CloudTrail"],
            detail = {
                "eventSource": [
                  "ec2.amazonaws.com",
                  "elasticloadbalancing.amazonaws.com"
                ],
                "eventName": [
                    "RunInstances",
                    "CreateSnapshot",
                    "CreateVolume",
                    "CreateImage",
                    "CreateLoadBalancer",
                    "AttachNetworkInterface"
                ]
            }
        )

        _events.Rule(
            scope = self,
            id = 'AutoTagsRule',
            description = 'Monitor EC2 and ELB events',
            rule_name = 'AutoTagsRule',
            event_pattern = pattern,
            targets = eventTargets
        )