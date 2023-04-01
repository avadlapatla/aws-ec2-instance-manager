# This is a cli application using python-prompt-toolkit that lists all ec2 instances in the aws account by name and allows user to filter ec2 instance as user starts typing characters as well as select instance using arrow keys. Then allow user to select ec2 instance from the list and establish aws ssm port forwarding session, the application should use a random available port on machine and establish a port forwarding session using aws ssm. the session should auto-renew before expiry and allow the user to list active sessions and terminate them.

# Import required modules
import boto3
import random
import subprocess
import threading
import time
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.shortcuts import clear

# Create boto3 clients for ec2 and ssm
ec2_client = boto3.client('ec2')
ssm_client = boto3.client('ssm')

# Define a function to get all ec2 instances by name
def get_ec2_instances():
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
    # Create a document name for port forwarding
    document_name = 'AWS-StartPortForwardingSession'
    # Create a parameter dictionary for port forwarding
    parameters = {
        'portNumber': ['22'], # The port number on the instance to forward (SSH by default)
        'localPortNumber': [str(local_port)] # The local port number on your machine to use
    }
    # Start a session using ssm client
    response = ssm_client.start_session(
        Target=instance_id,
        DocumentName=document_name,
        Parameters=parameters
    )
    # Get the session id from the response
    session_id = response['SessionId']
    # Return the session id
    return session_id

# Define a function to renew a port forwarding session using ssm
def renew_port_forwarding(session_id):
    # Create a document name for port forwarding
    document_name = 'AWS-StartPortForwardingSession'
    # Create a parameter dictionary for port forwarding
    parameters = {
        'portNumber': ['22'], # The port number on the instance to forward (SSH by default)
        'localPortNumber': ['0'] # The local port number on your machine to use (0 means any available port)
    }
    # Send a command using ssm client to renew the session
    response = ssm_client.send_command(
        InstanceIds=[session_id],
        DocumentName=document_name,
        Parameters=parameters,
        TimeoutSeconds=30 # The timeout for the command execution (30 seconds by default)
    )
    # Get the command id from the response
    command_id = response['Command']['CommandId']
    # Return the command id
    return command_id

# Define a function to terminate a port forwarding session using ssm
def terminate_port_forwarding(session_id):
    # Terminate a session using ssm client
    response = ssm_client.terminate_session(
        SessionId=session_id
    )
    # Return True if successful, False otherwise
    return response['SessionId'] == session_id

# Define a function to run a subprocess for port forwarding using session manager plugin
def run_subprocess(session_id, local_port):
    # Create a command list for subprocess
    command = [
        'session-manager-plugin', # The session manager plugin executable
        session_id, # The session id
        'us-west-2', # The AWS region
        'StartSession', # The action
        '', # The target (empty for port forwarding)
        '', # The working directory (empty for port forwarding)
        str(local_port), # The local port number
        'localhost', # The host name
        '22' # The remote port number (SSH by default)
    ]
    # Run the subprocess and wait for it to finish
    subprocess.run(command)

# Define a function to create a thread for port forwarding using session manager plugin
def create_thread(session_id, local_port):
    # Create a thread object with the run_subprocess function and the session id and local port as arguments
    thread = threading.Thread(target=run_subprocess, args=(session_id, local_port))
    # Start the thread
    thread.start()
    # Return the thread object
    return thread

# Define a function to create a timer for renewing port forwarding session using ssm
def create_timer(session_id):
    # Create a timer object with the renew_port_forwarding function and the session id as argument
    # The interval is set to 10 minutes (600 seconds) by default
    timer = threading.Timer(600, renew_port_forwarding, args=(session_id,))
    # Start the timer
    timer.start()
    # Return the timer object
    return timer

# Define a function to list all active sessions and threads
def list_sessions(sessions, threads):
    # Print a header for the table
    print('Active sessions and threads:')
    print('Session ID\t\t\t\tLocal Port\tThread ID')
    print('-' * 80)
    # Loop through the sessions and threads dictionaries and print their values
    for session_id in sessions:
        local_port = sessions[session_id]
        thread_id = threads[session_id].ident
        print(f'{session_id}\t{local_port}\t\t{thread_id}')
    print('-' * 80)

# Define a function to terminate a session and thread by session id
def terminate_session(session_id, sessions, threads):
    # Check if the session id exists in the sessions dictionary
    if session_id in sessions:
        # Get the local port and thread object from the sessions and threads dictionaries
        local_port = sessions[session_id]
        thread = threads[session_id]
        # Terminate the port forwarding session using ssm
        result = terminate_port_forwarding(session_id)
        # Check if the termination was successful
        if result:
            # Print a success message
            print(f'Successfully terminated session {session_id} on local port {local_port}')
            # Delete the session id from the sessions and threads dictionaries
            del sessions[session_id]
            del threads[session_id]
            # Terminate the thread by setting its daemon attribute to True and joining it
            thread.daemon = True
            thread.join()
        else:
            # Print an error message
            print(f'Failed to terminate session {session_id}')
    else:
        # Print an error message
        print(f'Invalid session id: {session_id}')

# Create an empty dictionary to store active sessions and their local ports
sessions = {}

# Create an empty dictionary to store active threads and their session ids
threads = {}

# Create an empty dictionary to store active timers and their session ids
timers = {}

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
            # Store the session id and local port in the sessions dictionary
            sessions[session_id] = local_port
            # Create a thread for port forwarding using session manager plugin and store it in the threads dictionary
            thread = create_thread(session_id, local_port)
            threads[session_id] = thread
            # Create a timer for renewing port forwarding session using ssm and store it in the timers dictionary
            timer = create_timer(session_id)
            timers[session_id] = timer
        # Check if the user input is a command
        elif user_input.startswith('/'):
            # Get the command name and argument by splitting the user input by whitespace
            command_name, command_arg = user_input.split(maxsplit=1)
            # Check if the command name is /list
            if command_name == '/list':
                # List all active sessions and threads
                list_sessions(sessions, threads)
            # Check if the command name is /terminate
            elif command_name == '/terminate':
                # Terminate a session and thread by session id
                terminate_session(command_arg, sessions, threads)
            # Check if the command name is /exit
            elif command_name == '/exit':
                # Exit the loop and the program
                break
            # Otherwise, print an error message
            else:
                print(f'Invalid command: {command_name}')
        # Otherwise, print an error message
        else:
            print(f'Invalid input: {user_input}')
        # Wait for the user to press enter before continuing the loop
        input('Press enter to continue...')
    except (KeyboardInterrupt, EOFError):
        # Exit the loop and the program if the user presses Ctrl+C or Ctrl+D
        break

# Print a goodbye message
print('Goodbye!')