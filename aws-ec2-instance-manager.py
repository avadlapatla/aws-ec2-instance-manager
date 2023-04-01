import boto3
import os
import subprocess
import random
import shlex
import threading
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from tabulate import tabulate

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

def search_instances(search_term, instances):
    return [i for i in instances if search_term.lower() in i['InstanceId'].lower()]

def start_port_forwarding(instance_id, local_port):
    cmd = f'aws ssm start-session --target {instance_id} --document-name AWS-StartPortForwardingSession --parameters \'{{"portNumber": ["22"], "localPortNumber": ["{local_port}"]}}\''
    subprocess.run(shlex.split(cmd))

def get_active_sessions():
    client = boto3.client('ssm')
    response = client.describe_sessions(State='Active')
    return response['Sessions']

def renew_session(session_id):
    client = boto3.client('ssm')
    client.resume_session(SessionId=session_id)

def terminate_session(session_id):
    client = boto3.client('ssm')
    client.terminate_session(SessionId=session_id)

def session_renewal_worker(session_id, expiry_time):
    while True:
        time_remaining = expiry_time - time.time()
        if time_remaining <= 60:
            renew_session(session_id)
            expiry_time = time.time() + 60 * 60
        time.sleep(10)

def list_sessions():
    sessions = get_active_sessions()
    if sessions:
        table_data = [
            [session['SessionId'], session['Target'], session['StartDate']] for session in sessions
        ]
        print(tabulate(table_data, headers=['Session ID', 'Instance ID', 'Start Date']))
    else:
        print("No active sessions found.")

def main():
    instances = get_ec2_instances()
    instances_completer = WordCompleter([i['InstanceId'] for i in instances], ignore_case=True)

    while True:
        action = input("\nChoose an action (list/search/connect/terminate/exit): ").lower()

        if action == 'list':
            list_sessions()
        elif action == 'search':
            search_term = input("Enter search term: ")
            matching_instances = search_instances(search_term, instances)
            for instance in matching_instances:
                print(instance['InstanceId'])
        elif action == 'connect':
            instance_id = prompt("Enter the Instance ID: ", completer=instances_completer)
            local_port = random.randint(1024, 65535)
            print(f"Starting port forwarding session on local port {local_port}...")
            start_port_forwarding(instance_id, local_port)
        elif action == 'terminate':
            session_id = input("Enter the session ID to terminate: ")
            terminate_session(session_id)
            print(f"Terminated session {session_id}")
        elif action == 'exit':
            break
        else:
            print("Invalid action. Please try again.")

if __name__ == '__main__':
    main()
