import asyncio
import boto3
import os
import subprocess
import shlex
import socket
from textual.app import App
from textual.widgets import Header, SearchToolbar, Footer, ListBox
from textual import events
from rich.text import Text

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

class InstanceListBox(ListBox):
    def __init__(self, instances):
        self.instances = instances
        self.filtered_instances = instances
        super().__init__(self.get_instance_names())

    def get_instance_names(self):
        return [Text(instance["InstanceId"]) for instance in self.filtered_instances]

    def filter_instances(self, search_term: str):
        self.filtered_instances = [
            i for i in self.instances if search_term.lower() in i["InstanceId"].lower()
        ]
        self.update(self.get_instance_names())

class EC2InstanceManager(App):
    async def on_mount(self) -> None:
        instances = get_ec2_instances()
        self.instance_list = InstanceListBox(instances)
        await self.view.dock(Header("EC2 Instance Manager"), edge="top")
        await self.view.dock(SearchToolbar(name="search"), edge="top")
        await self.view.dock(Footer("Press ESC to exit"), edge="bottom")
        await self.view.dock(self.instance_list, edge="left", size=40)

    async def on_text_changed(self, event: events.TextChanged) -> None:
        if event.sender.name == "search":
            self.instance_list.filter_instances(event.text)

    async def action_select_instance(self):
        instance_id = self.instance_list.choice
        if instance_id:
            local_port = find_available_port()
            print(f"Starting port forwarding session on local port {local_port}...")
            start_port_forwarding(instance_id, local_port)
        else:
            print("No instance selected.")

    async def on_key(self, event: events.Key) -> None:
        if event.key == "enter":
            await self.action_select_instance()
        elif event.key == "escape":
            await self.quit()
        else:
            await super().on_key(event)

if __name__ == "__main__":
    app = EC2InstanceManager()
    app.run()
