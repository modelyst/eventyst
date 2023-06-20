#   Copyright 2022 Modelyst LLC
#   All Rights Reserved

import networkx as nx
from pyvis.network import Network

from eventyst.core.handler_registry import HandlerRegistry


def generate_graph(handler_registry: HandlerRegistry):
    G = nx.DiGraph()  # Create a directed graph

    # Add nodes and edges for command handlers
    for command, tracker in handler_registry.command_handlers.items():
        command_str = str(command.__name__)
        tracker_str = str(tracker.call.__name__)

        command_color = 'green' if command in handler_registry.entrypoints else 'lightblue'
        G.add_node(command_str, shape='square', color=command_color)

        # Add the command node and set its attributes
        G.add_node(tracker_str, shape='diamond', color='red')

        # Add an edge from the handler to the command
        G.add_edge(command_str, tracker_str)
        for event in tracker.emitted_types:
            event_str = str(event.__name__)
            # Add the event node and set its attributes
            G.add_node(event_str, shape='circle', color='orange')
            # Add an edge from the command to the emitted event
            G.add_edge(
                tracker_str,
                event_str,
            )

            # Mark broker events
            if event in handler_registry.broker_events:
                G.nodes[event_str]['color'] = 'orange'
                G.add_edge(event_str, 'Broker', color='orange')

    # Add nodes and edges for event handlers
    for event, trackers in handler_registry.event_handlers.items():
        event_str = str(event.__name__)
        # Add the event node and set its attributes
        event_color = 'orange' if event in handler_registry.broker_events else 'lightblue'

        if event in handler_registry.broker_events:
            G.add_edge(event_str, 'Broker', color='orange')

        if event in handler_registry.entrypoints:
            event_color = 'green'
        else:
            event_color = 'lightblue'

        G.add_node(event_str, shape='circle', color=event_color)

        # Add an edge from the event to the handler
        for tracker in trackers:
            tracker_str = str(tracker.call.__name__)
            G.add_node(tracker_str, shape='diamond', color='red')
            G.add_edge(event_str, tracker_str, color='lightblue')

            for emitted_event in tracker.emitted_types:
                emitted_event_str = str(emitted_event.__name__)
                # Add the emitted event node and set its attributes
                G.add_node(
                    emitted_event_str,
                    shape='circle',
                    color='lightblue',
                )

                # Add an edge from the handler to the emitted event
                G.add_edge(
                    tracker_str,
                    emitted_event_str,
                )
                if emitted_event in handler_registry.broker_events:
                    G.add_edge(emitted_event_str, 'Broker', color='orange')
    if handler_registry.broker_events:
        G.add_node('Broker', shape='oval', color='orange', size=20)

    return G


def draw_graph_pyvis(G):
    net = Network(directed=True, notebook=True, cdn_resources='in_line', layout='hierarchical')
    net.from_nx(G)
    return net
