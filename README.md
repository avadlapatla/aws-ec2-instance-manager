# EC2 Instance Manager

EC2 Instance Manager is a command-line interface (CLI) application written in Python that allows users to interact with their Amazon EC2 instances. The application lists all running instances in the user's AWS account and enables the user to filter the list by typing characters. The user can interactively select an instance from the list using arrow keys and the Enter button. When an instance is selected, the application establishes a port forwarding session using AWS Systems Manager (SSM).

## Features

- List all running EC2 instances
- Filter instances by typing characters
- Interactively select instances using arrow keys and the Enter button
- Establish a port forwarding session with the selected instance using AWS SSM

## Prerequisites

- Python 3.6 or higher
- An AWS account with running EC2 instances
- AWS CLI v2 installed and configured
- AWS SSM Agent installed on the EC2 instances

## Installation

1. Clone the repository:

2. Install the required Python packages:

```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:

```bash
python main.py
```

2. The application will display a list of running instances. Type characters to filter the instances.
3. Use the arrow keys to navigate the list and press Enter to select an instance.
4. The application will establish a port forwarding session with the selected instance using AWS SSM.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)
