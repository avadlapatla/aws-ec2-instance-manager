# AWS EC2 Instance Manager

A command-line interface (CLI) application in Python that helps you manage Amazon EC2 instances in your AWS account. This tool allows you to list running instances, search instances by name, establish port forwarding sessions using AWS SSM, and manage active sessions.

## Features

- List all running EC2 instances in the AWS account
- Search EC2 instances by name with autocompletion
- Establish a port forwarding session to an EC2 instance using a random available local port
- List all active SSM sessions
- Automatically renew sessions before they expire
- Terminate active SSM sessions

## Requirements

- Python 3.6 or higher
- [AWS CLI version 2](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html)
- AWS credentials configured (use `aws configure` or the `~/.aws/credentials` file)
- AWS Systems Manager agent installed on the target EC2 instances

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/aws-ec2-instance-manager.git
cd aws-ec2-instance-manager
```

2. Create a virtual environment (optional):

```bash
python -m venv venv
source venv/bin/activate
```

3. Install the required packages:

```bash
pip install -r requirements.txt
```

4. Make the script executable (optional):

```bash
chmod +x ec2_instance_manager.py
```

## Usage

Run the application:

```bash
python ec2_instance_manager.py
```

Or, if you made the script executable:

```bash
./ec2_instance_manager.py
```

The application will prompt you to choose an action:

- `list`: List all active SSM sessions
- `search`: Search for EC2 instances by name
- `connect`: Establish a port forwarding session to an EC2 instance
- `terminate`: Terminate an active SSM session
- `exit`: Exit the application

## License

MIT License. See [LICENSE](LICENSE) for more details.
