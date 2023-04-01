import asyncio
import boto3
import os
import subprocess
import shlex
import socket
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.shortcuts import CompleteStyle

def get_ec2_instances():
    client = boto3.client('ec2')
    response = client.describe_instances(
        Filters=[
            {
                'Name': 'instance-state-name',
                'Values': ['running']
            }
        ]
    )
    instances = []
    for reservation in response['Reservations']:
        instances.extend(reservation['Instances'])
    return instances

def start_port_forwarding(instance_id, local_port):
    cmd = f'aws ssm start-session --target {instance_id} --document-name AWS-StartPortForwardingSession --parameters \'{{"portNumber": ["22"], "localPortNumber": ["{local_port}"]}}\''
    subprocess.run(shlex.split(cmd))

def find_available_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]

def main():
    instances = get_ec2_instances()
    instance_ids = [instance['InstanceId'] for instance in instances]
    completer = WordCompleter(instance_ids, ignore_case=True, sentence=True)
    session = PromptSession(completer=completer, complete_style=CompleteStyle.READLINE_LIKE)

    while True:
        instance_id = session.prompt("Enter the Instance ID (partial or complete) and press Enter to connect: ")

        if instance_id:
            local_port = find_available_port()
            print(f"Starting port forwarding session on local port {local_port}...")
            start_port_forwarding(instance_id, local_port)
        else:
            print("No instance selected.")

if __name__ == "__main__":
    main()
