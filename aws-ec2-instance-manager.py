import asyncio
import boto3
import os
import subprocess
import random
from textual.app import App
from textual.widgets import Button, ScrollView, Placeholder, TextArea
from textual import events

class AwsApp(App):

    def __init__(self):
        super().__init__()

    async def on_mount(self) -> None:
        await self.view.dock(ScrollView())

    async def on_ready(self):
        await self.process_command("list")

    async def on_key(self, event: events.Key) -> None:
        if event.key == "p":
            await self.process_command("prompt")
        elif event.key == "c":
            await self.process_command("connect")
        elif event.key == "l":
            await self.process_command("list")
        else:
            await super().on_key(event)

    async def process_command(self, command: str):
        if command == "prompt":
            instance_name = await self.prompt("Enter instance name: ")
            await self.connect_instance(instance_name)
        elif command == "connect":
            instance_name = await self.prompt("Enter instance name: ")
            await self.connect_instance(instance_name)
        elif command == "list":
            instance_dict = get_ec2_instances()
            instance_names = [instance.tags[0]['Value'] for instance in instance_dict.values()]
            await self.print_instances(instance_names)

    async def print_instances(self, instance_names):
        scroll_view = self.view.children[0]
        content = "\n".join(["- " + name for name in instance_names])
        await scroll_view.update(Placeholder(content))

    async def connect_instance(self, instance_name):
        instance_dict = get_ec2_instances()
        matching_instances = search_instance_name(instance_dict, instance_name)
        if len(matching_instances) > 0:
            instance = list(matching_instances.values())[0]
            local_port = random.randint(1024, 65535)
            await self.print(f"\nEstablishing a port forwarding session to {instance_name} on local port {local_port}...")
            start_port_forwarding(instance.instance_id, local_port)
        else:
            await self.print("\nNo matching instances found.")

    async def prompt(self, message: str) -> str:
        input_widget = TextArea()
        await self.view.dock(input_widget, edge="bottom", size=3)
        await input_widget.focus()
        await self.print(message)

        while True:
            event = await self.await_key()
            if event.key == "enter":
                break

        await self.view.remove(input_widget)
        return input_widget.value

    async def print(self, message: str):
        scroll_view = self.view.children[0]
        await scroll_view.update(Placeholder(scroll_view.content.text + "\n" + message))

def get_ec2_instances():
    ec2 = boto3.resource('ec2')
    instances = ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
    instance_dict = {}
    for instance in instances:
        instance_dict[instance.id] = instance
    return instance_dict

def search_instance_name(instance_dict, search):
    matching_instances = {}
    for instance_id, instance in instance_dict.items():
        for tag in instance.tags:
            if tag['Key'] == 'Name' and search.lower() in tag['Value'].lower():
                matching_instances[instance_id] = instance
                return matching_instances

def start_port_forwarding(instance_id, local_port):
    cmd = f"aws ssm start-session --target {instance_id} --document-name AWS-StartPortForwardingSession --parameters '{\"portNumber\": [\"22\"], \"localPortNumber\": [\"{local_port}\"]}'"
    subprocess.run(cmd, shell=True)

async def main():
    app = AwsApp()
    await app.run()

if name == 'main':
    asyncio.run(main())