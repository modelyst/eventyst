# eventyst

Eventyst is a flexible and maintainable event-driven data pipelining library for Python. It provides a central message broker for communicating between
pipeline steps, allowing you to easily build and update event-based data processing pipelines.

## Features

    Central message broker for communication between pipeline steps
    Automatically orders pipeline steps into a directed acyclic graph (DAG) based on data sources and production
    Asynchronous processing of events to ensure efficient data processing
    Supports large object storage for exchanging events for larger messages
    Abstracts object storage service to allow for easy switching between different storage solutions
