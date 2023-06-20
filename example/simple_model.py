#   Copyright 2023 Modelyst LLC
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from eventyst import Command, Event, Eventyst, MessageBus

app = Eventyst()


class MyTestEvent(Event):
    param_1: str


class MyTestCommand(Command):
    param_1: str
    param_2: str | None
    param_3: str | None


@app.register(entrypoint=True, emitted_types=[MyTestEvent])
def handle_my_test_command(command: MyTestCommand, bus: MessageBus):
    print(f"Handling {command}")
    bus.enqueue_sync(MyTestEvent(param_1=command.param_1))


app.register_with_broker(MyTestEvent)
