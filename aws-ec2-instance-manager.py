import asyncio
import boto3
import os
import subprocess
import shlex
import socket
from textual.app import App
from textual.widgets import Placeholder, ScrollView, TextField
from textual import events
from textual.reactive import Reactive
from rich.table import Table

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

class InstanceTable(ScrollView):
    def __init__(self, instances):
        super().__init__()
        self.instances = instances
        self.filtered_instances = instances
        self.table = Table(expand=True, show_footer=False)
        self.table.add_column("Instance ID")
        self._update_table()

    def _update_table(self):
        self.table.rows = []
        for instance in self.filtered_instances:
            self.table.add_row(instance['InstanceId'])
        self.update(self.table)

    def filter_instances(self, search_term: str):
        self.filtered_instances = [
            i for i in self.instances if search_term.lower() in i['InstanceId'].lower()
        ]
        self._update_table()

class EC2InstanceManager(App):
    def __init__(self, instances):
        super().__init__()
        self.instances = instances

    async def on_mount(self, event: events.Mount) -> None:
        await self.view.dock(TextField(name="search_field", placeholder="Search Instances..."), edge="top")
        await self.view.dock(InstanceTable(self.instances), edge="bottom")

    async def on_text(self, event: events.Text) -> None:
        search_field: TextField = self.layout.get_widget("search_field")
        instance_table: InstanceTable = self.layout.get_widget("instance_table")
        instance_table.filter_instances(search_field.value)

    async def action_connect(self):
        instance_table: InstanceTable = self.layout.get_widget("instance_table")
        instance_id = instance_table.table.get_selection_value()
        if instance_id:
            local_port = find_available_port()
            print(f"Starting port forwarding session on local port {local_port}...")
            start_port_forwarding(instance_id, local_port)
        else:
            print("No instance selected.")

    async def on_key(self, event: events.Key) -> None:
        if event.key == "enter":
            await self.action_connect()
        else:
            await super().on_key(event)

async def main():
    instances = get_ec2_instances()
    app = EC2InstanceManager(instances)
    await app.run()

if __name__ == "__main__":
    asyncio.run(main())