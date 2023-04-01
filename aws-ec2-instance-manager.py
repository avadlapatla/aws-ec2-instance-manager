import boto3
import os
import subprocess
import random
import shlex
import threading
import socket
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.shortcuts import radiolist_dialog
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

def find_available_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]

def filter_instances(instances, search_term):
    return [i for i in instances if search_term.lower() in i['InstanceId'].lower()]

def main():
    instances = get_ec2_instances()

    while True:
        action = input("\nChoose an action (list/connect/terminate/exit): ").lower()

        if action == 'list':
            list_sessions()
        elif action == 'connect':
            search_term = input("Enter the search term: ")
            matching_instances = filter_instances(instances, search_term)

            if not matching_instances:
                print("No matching instances found.")
                continue

            instance_choices = [(instance['InstanceId'], instance['InstanceId']) for instance in matching_instances]
            instance_id = radiolist_dialog(
                title="Select an Instance",
                text="Choose the EC2 instance you want to connect to:",
                values=instance_choices,
            ).run()

            if instance_id:
                local_port = find_available_port()
                print(f"Starting port forwarding session on local port {local_port}...")
                start_port_forwarding(instance_id, local_port)
            else:
                print("No instance selected.")
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