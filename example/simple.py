#   Copyright 2022 Modelyst LLC
#   All Rights Reserved

from datetime import datetime

from eventyst import Command, Dependency, Event, EventystApplication, HandlerRegistry, MessageBus

handler_registry = HandlerRegistry()


class CreateOrder(Command):
    order_id: str


class OrderCreated(Event):
    order_id: str
    timestamp: datetime


class RepositoryTouched(Event):
    repository_name: str


class OrderRepository(Dependency):
    def __init__(self):
        super().__init__(
            dependencies={
                'message_bus': MessageBus,
            }
        )

    def __call__(self, message_bus: MessageBus):
        return {}


def order_repository(message_bus: MessageBus):
    yield {}
    message_bus.emit(RepositoryTouched(repository_name='order_repository'))


@handler_registry.register_command(CreateOrder)
def create_order(command: CreateOrder, order_repository=Dependency(order_repository)):
    return OrderCreated(command.order_id, datetime.now())


@handler_registry.register_event(OrderCreated)
def handle_order_created(event: OrderCreated):
    print(f"Order created: {event.order_id}")


application = EventystApplication(handler_registry=handler_registry)


if __name__ == "__main__":
    application.run()
