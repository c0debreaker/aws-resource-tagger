# AWS-Auto-Tagger

## Automatically Tag AWS Resources

The AWS Cloud Development Kit (AWS CDK) is an open source software development framework to model and provision your cloud application resources using familiar programming languages.

This project uses AWS Cloud Development Kit(CDK) to generate a CloudFormation stack which is use to deploy Lambda function and setup CloudWatch event rules to monitor events such as elasticloadbalancing:create*.

Once a rule is matched, the Lambda function is triggered. The Lambda function retrieves necessary information from the event in CloudTrail. The acquired event is in json format. We can use any property as input values for our tags like app_name, app_group and other keys we want to add.

## Prerequisites

* Python 3
* [Poetry](https://github.com/python-poetry/poetry)
* [AWS CDK cli tool](https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html)
* Properly configured AWS credentials in ~/.aws/config
* Update `<AWS ACCOUNT>` in stacks/autotags_stack.py and app.py and put your AWS account number
* 3rdParty Libraries such as glom will be deployed as AWS Layers. The glom layer has to be created and deployed first

## Deploying a CDK Python project

Install the required libraries. This also creates a virtual environment.

```sh
$ poetry install
```

Go inside the virtual environment that poetry created during the installation of the libraries.

```sh
$ poetry shell
```

Once inside the virtual env, you can now synthesize the CloudFormation template for this code. List the stacks so you can pick which one you want to work on.

```sh
$ cdk ls
AWSResourceTagger-us-east-1
AWSResourceTagger-us-east-2
AWSResourceTagger-us-west-1
AWSResourceTagger-us-west-2

$ cdk synth AWSResourceTagger-us-east-1
Resources:
  resourceTaggerServiceRoleEAB030C9:
    Type: AWS::IAM::Role
    ...
    ...


    ...
  AssetParameters*********************************************:
    Type: String
    Description: Artifact hash for asset "*********************************************"
```

If the `cdk synth` command was successful, you can deploy this stack to your default AWS account/region. If you don't specify `--profile`, it will use the default credentials defined in your config file.

```sh
$ cdk deploy AWSResourceTagger-us-east-1
```

To add additional dependencies, for example other CDK libraries, execute `poetry add <library-name>`
command. This will update pyproject.toml.

### Useful commands

* `cdk ls`          list all stacks in the app
* `cdk synth`       emits the synthesized CloudFormation template
* `cdk diff`        compare deployed stack with current state
* `cdk docs`        open CDK documentation

### Useful Resources
* https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html
* https://docs.aws.amazon.com/cdk/api/latest/docs/aws-events-readme.html
* https://docs.aws.amazon.com/cdk/api/latest/docs/aws-elasticloadbalancing-readme.html
* https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/elb.html#ElasticLoadBalancing.Client.add_tags
* https://docs.aws.amazon.com/lambda/latest/dg/lambda-python-how-to-create-deployment-package.html
