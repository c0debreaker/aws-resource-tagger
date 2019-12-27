"""AWS Auto Resource Tagger"""

import boto3
import logging
import json
from glom import glom

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def generate_name_tag(instance_id):
    env = "sandbox"
    # If running from laptop, profile_name is required
    #session = boto3.Session(profile_name=env, region_name="us-east-1")
    session = boto3.Session(region_name="us-east-1")
    ec2 = session.client("ec2")

    # DEV
    response = ec2.describe_instances(InstanceIds=[instance_id])

    print('[generate_name_tag] ####### Start Debugging ec2.describe_instances #######')
    print(response)
    print('[generate_name_tag] ####### End Debugging ec2.describe_instances #######')

    tags = None
    try:
        tags = glom(response, "Reservations.0.Instances.0.Tags")
    except:
        print('[generate_name_tag] ' + instance_id + ' does not contain existing tags!')
        return None
    
    app_name = ""
    app_group = ""
    for tag in tags:
        if tag["Key"] == "app_name":
            app_name = tag["Value"]
        if tag["Key"] == "app_group":
            app_group = tag["Value"]

    image_id = glom(response, "Reservations.0.Instances.0.ImageId")
    first4_image_id = image_id.partition("-")[2][:4]

    private_ip_address = glom(response, "Reservations.0.Instances.0.PrivateIpAddress")
    private_ip_address_u = private_ip_address.replace(".", "_")

    availability_zone = glom(response, "Reservations.0.Instances.0.Placement.AvailabilityZone")
    region = availability_zone[:-1]

    # Generate Name tag
    name_tag = app_name + "-" + first4_image_id + "-" + private_ip_address_u + "." + region + "." + env

    print("Generated name tag: " + name_tag)
    return name_tag

def get_value_by_key_from_eventdetails(cloudtrail_event_detail, key):
    try:
        return glom(cloudtrail_event_detail, key)
    except:
        return None


def generate_kv_named_tags(tags_dict):
    tags = []

    for key in tags_dict:
        tags.append({ 'Key': key, 'Value':  tags_dict[key] })

    tags.append({ 'Key': 'tagger', 'Value': 'aws-auto-tagger' })
    return tags


def get_resource_id_by_event(cloudtrail_event_detail, event_name):
    """Returns resourceId based on CloudTrail event

    """
    resource_id_list = []
    event_to_id_mapping = {
       'CreateVolume' : 'responseElements.volumeId',
       'CreateImage' : 'responseElements.imageId',
       'CreateSnapshot' : 'responseElements.snapshotId',
       'AttachNetworkInterface' : 'requestParameters.networkInterfaceId',
       'RunInstances' : 'responseElements.instancesSet.items'
    }

    event_key = event_to_id_mapping.get(event_name)
    if event_key is not None:
        resource_ids = get_value_by_key_from_eventdetails(cloudtrail_event_detail, event_key)
        if not resource_ids:
            return None
        if isinstance(resource_ids, list):
            print("InstanceID found in list ...")
            for resource_id in resource_ids:
                resource_id_list.append(resource_id['instanceId'])
            return resource_id_list
        else:
            print("InstanceID found as string ...")
            return resource_ids
    else:
        return None


def add_ec2_tags(cloudtrail_event_detail, is_enabled):
    """Adds tags to EC2 resources

    """
    ids = []
   
    event_name = get_value_by_key_from_eventdetails(cloudtrail_event_detail, 'eventName')
    principal = get_value_by_key_from_eventdetails(cloudtrail_event_detail, 'userIdentity.principalId')
    user_type = get_value_by_key_from_eventdetails(cloudtrail_event_detail, 'userIdentity.type')

    if user_type == 'IAMUser':
        user = get_value_by_key_from_eventdetails(cloudtrail_event_detail, 'userIdentity.userName')
    else:
        user = principal.split(':')[1]

    # Let's catch and log CT events that doesn't contain responseElements or responseElements with None value
    if cloudtrail_event_detail['responseElements'] is None:
        return False
        
    if 'responseElements' not in cloudtrail_event_detail:
        logger.warning('No responseElements found')

        error_code = get_value_by_key_from_eventdetails(cloudtrail_event_detail, 'errorCode')
        error_message = get_value_by_key_from_eventdetails(cloudtrail_event_detail, 'errorMessage')

        if error_code:
            logger.error('errorCode: ' + error_code)
        if error_message:
            logger.error('errorMessage: ' + error_message)

        return False

    ec2 = boto3.resource('ec2')

    resource_id = get_resource_id_by_event(cloudtrail_event_detail, event_name)

    if resource_id is not None:
        if isinstance(resource_id, list):
            ids = resource_id
        else:
            ids.append(resource_id)
        logger.info(ids)
    
    if event_name == 'RunInstances':
        base = ec2.instances.filter(InstanceIds=ids)
        for instance in base:
            for vol in instance.volumes.all():
                ids.append(vol.id)
            for eni in instance.network_interfaces:
                ids.append(eni.id)
    else:
        logger.warning('Not supported action')

    if ids and 'responseElements' in cloudtrail_event_detail:
        for resource_id in ids:
            print('Tagging resource ' + resource_id)
        kwargs = dict(owner=user, principal_id=principal, app_name='TODO', app_group='TODO')
        if generated_name_tag is not None:
            kwargs.update(dict(NameV2=generated_name_tag))

        if is_enabled:
            tags = generate_kv_named_tags(kwargs)

            ec2.create_tags(
                Resources=ids,
                Tags=tags
            )


def add_elb_tags(cloudtrail_event_detail, is_enabled):
    """Adds tags to ELB

    """
    event_name = get_value_by_key_from_eventdetails(cloudtrail_event_detail, 'eventName')
    if event_name == 'CreateLoadBalancer':
        load_balancer_name = get_value_by_key_from_eventdetails(cloudtrail_event_detail, 'requestParameters.loadBalancerName')
        dns_name = get_value_by_key_from_eventdetails(cloudtrail_event_detail, 'responseElements.dNSName')
        application_name = dns_name.split('-')[1]
        print('Tagging ELB ' + load_balancer_name)
        
        if is_enabled:
            elb = boto3.client('elb')
            tags = generate_kv_named_tags(
                app_name=application_name,
                app_group=application_name
            )
            elb.add_tags(
                LoadBalancerNames=[load_balancer_name],
                Tags=tags
            )


def handler(event, context):
    try:
        print('Debugging EC2/ELB CloudTrail events ...')
        print(event)

        cloudtrail_event_detail = get_value_by_key_from_eventdetails(event, 'detail')
        add_ec2_tags(cloudtrail_event_detail, True)
        add_elb_tags(cloudtrail_event_detail, True)

        return True
    except Exception as e:
        logger.error('Something went wrong: ' + str(e))
        return False
