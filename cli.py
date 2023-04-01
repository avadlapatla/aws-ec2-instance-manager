import sys
import random
import boto3
from botocore.exceptions import ClientError
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.shortcuts import ProgressBar


def get_instance_name(instance):
    for tag in instance.tags:
        if tag["Key"] == "Name":
            return tag["Value"]
    return instance.id


def get_instances(filter_text=""):
    ec2 = boto3.resource("ec2")
    instances = ec2.instances.all()

    if filter_text:
        instances = [
            instance
            for instance in instances
            if filter_text.lower() in get_instance_name(instance).lower()
        ]

    return instances


def select_instance(instances):
    instance_ids = [instance.id for instance in instances]
    completer = WordCompleter(instance_ids)
    instance_id = prompt("Select instance: ", completer=completer)
    return instance_id


def start_port_forwarding(instance_id, port):
    ssm = boto3.client("ssm")
    response = ssm.start_session(
        Target=instance_id,
        DocumentName="AWS-StartPortForwardingSession",
        Parameters={"portNumber": [str(port)], "localPortNumber": ["0"]},
    )
    session_id = response["SessionId"]
    return session_id


def refresh_port_forwarding(session_id):
    ssm = boto3.client("ssm")
    try:
        response = ssm.send_command(
            InstanceId=session_id,
            DocumentName="AWS-RefreshPortForwardingSession",
            Parameters={},
        )
        command_id = response["Command"]["CommandId"]
    except ClientError as e:
        if "Session is not found" in str(e):
            raise Exception("Session has expired or was terminated.")
        else:
            raise e

    while True:
        output = ssm.get_command_invocation(
            InstanceId=session_id, CommandId=command_id
        )
        status = output["Status"]
        if status == "Success":
            break
        elif status == "Failed":
            raise Exception("Command failed")
        else:
            time.sleep(1)
    return session_id


def stop_port_forwarding(session_id):
    ssm = boto3.client("ssm")
    response = ssm.terminate_session(SessionId=session_id)
    return response


def list_sessions(sessions):
    print("Active sessions:")
    print("Session ID\tTarget\t\tStatus")
    for session in sessions:
        print(f"{session['SessionId']}\t{session['Target']}\t{session['Status']}")


def main():
    while True:
        filter_text = prompt("Filter instances: ")
        instances = get_instances(filter_text)
        if not instances:
            print("No instances found.")
            continue
        instance_id = select_instance(instances)
        port = random.randint(10000, 60000)
        session_id = start_port_forwarding(instance_id, port)
        print(f"Session ID: {session_id}")
        progress_bar = ProgressBar(title="Establishing connection")
        with progress_bar:
            try:
                while True:
                    session = boto3.client("ssm").describe_sessions(SessionIds=[session_id])
                    if session["Sessions"][0]["Status"] == "Terminated":
                        break
                    refresh_port_forwarding(session_id)
                    progress_bar.advance(1)
            except KeyboardInterrupt:
                stop_port_forwarding(session_id)
                sys.exit(0)
            except Exception as e:
                print(e)
                sys.exit(1)


if __name__ == "__main__":
    main()
