import boto3
import random
import subprocess
import time
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.shortcuts import clear

# Define some constants for document name, port number and region
DOCUMENT_NAME = 'AWS-StartPortForwardingSession'
PORT_NUMBER = '22' # The port number on the instance to forward (SSH by default)
REGION = 'eu-west-1' # The AWS region

# Create boto3 clients for ec2 and ssm
ec2_client = boto3.client('ec2')
ssm_client = boto3.client('ssm')

# Define a function to get all ec2 instances by name
def get_ec2_instances():
    """Return a list of ec2 instances by name and id."""
    # Get all ec2 instances in the account
    response = ec2_client.describe_instances()
    # Create an empty list to store instance names and ids
    instances = []
    # Loop through the response and extract instance names and ids
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            # Get the instance id
            instance_id = instance['InstanceId']
            # Get the instance name from tags if exists
            instance_name = ''
            if 'Tags' in instance:
                for tag in instance['Tags']:
                    if tag['Key'] == 'Name':
                        instance_name = tag['Value']
                        break
            # Append the instance name and id to the list
            instances.append(f'{instance_name} ({instance_id})')
    # Return the list of instances
    return instances

# Define a function to start a port forwarding session using ssm
def start_port_forwarding(instance_id, local_port):
    """Start a port forwarding session using ssm and return the session id."""
    # Create a parameter dictionary for port forwarding
    parameters = {
        'portNumber': [PORT_NUMBER],
        'localPortNumber': [str(local_port)]
    }
    # Start a session using ssm client
    response = ssm_client.start_session(
        Target=instance_id,
        DocumentName=DOCUMENT_NAME,
        Parameters=parameters
    )
    # Get the session id from the response
    session_id = response['SessionId']
    # Return the session id
    return session_id

# Define a function to renew a port forwarding session using ssm
def renew_port_forwarding(session_id):
    """Send a command using ssm client to renew the session and return the command id."""
    # Create a parameter dictionary for port forwarding
    parameters = {
        'portNumber': [PORT_NUMBER],
        'localPortNumber': ['0'] # 0 means any available port
    }
    # Send a command using ssm client to renew the session
    response = ssm_client.send_command(
        InstanceIds=[session_id],
        DocumentName=DOCUMENT_NAME,
        Parameters=parameters,
        TimeoutSeconds=30 # The timeout for the command execution (30 seconds by default)
    )
    # Get the command id from the response
    command_id = response['Command']['CommandId']
    # Return the command id
    return command_id

# Define a function to terminate a port forwarding session using ssm
def terminate_port_forwarding(session_id):
    """Terminate a session using ssm client and return True if successful, False otherwise."""
    # Terminate a session using ssm client
    response = ssm_client.terminate_session(
        SessionId=session_id
    )
    # Return True if successful, False otherwise
    return response['SessionId'] == session_id

# Define a function to run a subprocess for port forwarding using session manager plugin
def run_subprocess(session_id, local_port):
    """Run a subprocess for port forwarding using session manager plugin and wait for it to finish."""
    # Create a command list for subprocess
    command = [
        'session-manager-plugin', # The session manager plugin executable
        session_id, # The session id
        REGION, # The AWS region
        'StartSession', # The action
        '', # The target (empty for port forwarding)
        '', # The working directory (empty for port forwarding)
        str(local_port), # The local port number
        'localhost', # The host name
        PORT_NUMBER # The remote port number (SSH by default)
    ]
    # Run the subprocess and wait for it to finish
    subprocess.run(command)

# Define a function to list all active sessions and local ports
def list_sessions(sessions):
    """Print a table of active sessions and local ports."""
    # Print a header for the table
    print('Active sessions and local ports:')
    print('Session ID\t\t\t\tLocal Port')
    print('-' * 80)
    # Loop through the sessions dictionary and print its values
    for session_id, local_port in sessions.items():
        print(f'{session_id}\t{local_port}')
    print('-' * 80)

# Define a function to terminate a session by session id
def terminate_session(session_id, sessions):
    """Terminate a session and delete it from the sessions dictionary."""
    # Check if the session id exists in the sessions dictionary
    if session_id in sessions:
        # Get the local port from the sessions dictionary
        local_port = sessions[session_id]
        # Terminate the port forwarding session using ssm
        result = terminate_port_forwarding(session_id)
        # Check if the termination was successful
        if result:
            # Print a success message
            print(f'Successfully terminated session {session_id} on local port {local_port}')
            # Delete the session id from the sessions dictionary
            del sessions[session_id]
        else:
            # Print an error message
            print(f'Failed to terminate session {session_id}')
    else:
        # Print an error message
        print(f'Invalid session id: {session_id}')

# Create an empty dictionary to store active sessions and their local ports
sessions = {}

# Get all ec2 instances by name and create a word completer for prompt toolkit
instances = get_ec2_instances()
completer = WordCompleter(instances)

# Start an infinite loop for user input
while True:
    try:
        # Clear the screen before each prompt
        clear()
        # Prompt the user to enter an ec2 instance name or id or a command using prompt toolkit with word completion enabled
        user_input = prompt('Enter an EC2 instance name or ID or a command: ', completer=completer)
        # Check if the user input is a valid ec2 instance name or id by removing any whitespace and parentheses 
        instance_input = user_input.replace(' ', '').replace('(', '').replace(')', '')
        if instance_input in instances:
            # Get the instance id from the user input by splitting it by parentheses and taking the second element 
            instance_id = user_input.split('(')[1].split(')')[0]
            # Generate a random available port on the machine between 1024 and 65535 
            local_port = random.randint(1024, 65535)
            # Start a port forwarding session using ssm and get the session id
            session_id = start_port_forwarding(instance_id, local_port)
            # Print a success message
            print(f'Successfully started session {session_id} on local port {local_port}')
            print(f'You can now connect to localhost:{local_port} to access your EC2 instance')
            print(f'To terminate this session, enter /terminate {session_id}')
            # Store the session id and local port in the sessions dictionary
            sessions[session_id] = local_port
            # Run a subprocess for port forwarding using session manager plugin in the background by adding '&' at the end of the command list
            command = [
                'session-manager-plugin', 
                session_id,
                REGION,
                'StartSession',
                '',
                '',
                str(local_port),
                'localhost',
                PORT_NUMBER,
                '&'
            ]
            subprocess.run(command)

# Check if the user input is a command
        elif user_input.startswith('/'):
            # Get the command name and argument by splitting the user input by whitespace
            command_name, command_arg = user_input.split(' ', 1)
            # Check if the command name is /list
            if command_name == '/list':
                # List all active sessions and local ports
                list_sessions(sessions)
            # Check if the command name is /terminate
            elif command_name == '/terminate':
                # Terminate a session by session id
                terminate_session(command_arg, sessions)
            # Check if the command name is /exit
            elif command_name == '/exit':
                # Exit the program by breaking the loop
                break
            # Otherwise, print an error message
            else:
                print(f'Invalid command: {command_name}')
        # Otherwise, print an error message
        else:
            print(f'Invalid input: {user_input}')
        # Wait for the user to press enter before continuing the loop
        input('Press enter to continue...')
    except KeyboardInterrupt:
        # Exit the program by breaking the loop if the user presses Ctrl-C
        break

# Print a goodbye message
print('Goodbye!')