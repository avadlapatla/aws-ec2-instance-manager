# AWS SSM Port Forwarding CLI

This is a CLI application that allows users to list all EC2 instances in their AWS account by name, filter EC2 instances as the user starts typing characters, and establish AWS SSM port forwarding sessions. The application will use a random available port on the machine to establish a port forwarding session using AWS SSM. The session will auto-renew before expiry and allow the user to list active sessions and terminate them.

## Requirements

- Python 3.6 or higher
- AWS CLI
- AWS SSM plugin for the AWS CLI
- Python Prompt Toolkit (`pip install prompt-toolkit`)

## Setup

1. Set up AWS credentials using `aws configure`
2. Install the AWS SSM plugin for the AWS CLI using `aws configure add-plugin ssm`
3. Install the required Python packages using `pip install prompt-toolkit boto3 pygments`
4. Clone the repository using `git clone https://github.com/<username>/<repository>`
5. Navigate to the directory using `cd <repository>`

## Usage

2. Filter instances by typing characters
3. Select an instance from the list
4. The application will establish a port forwarding session using AWS SSM on a random available port
5. The session will auto-renew before expiry
6. List active sessions and terminate them by pressing `Ctrl+C`
