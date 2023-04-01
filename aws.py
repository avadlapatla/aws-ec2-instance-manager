import boto3
import time


def get_instances(filter_text=""):
    ec2 = boto3.client("ec2")
    response = ec2.describe_instances()
    instances = []
    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            if filter_text.lower() in get_instance_name(instance).lower():
                instances.append(instance)
    return instances


def get_ec2_instance_name(instance):
    for tag in instance.tags:
        if tag['Key'] == 'Name':
            return tag['Value']
    return instance.id


def start_port_forwarding(instance_id, port):
    client = boto3.client('ssm')
    response = client.start_session(
        Target=instance_id,
        DocumentName='AWS-StartPortForwardingSession',
        Parameters={
            'portNumber': [str(port)],
            'localPortNumber': ['0']
        }
    )
    session_id = response['SessionId']
    return session_id


def refresh_port_forwarding(session_id):
    client = boto3.client('ssm')
    response = client.send_command(
        InstanceId=session_id,
        DocumentName='AWS-RefreshPortForwardingSession',
        Parameters={}
    )
    command_id = response['Command']['CommandId']
    while True:
        output = client.get_command_invocation(
            InstanceId=session_id,
            CommandId=command_id
        )
        status = output['Status']
        if status == 'Success':
            break
        elif status == 'Failed':
            raise Exception('Command failed')
        else:
            time.sleep(1)
    return session_id


def stop_port_forwarding(session_id):
    client = boto3.client('ssm')
    response = client.terminate_session(SessionId=session_id)
    return response
