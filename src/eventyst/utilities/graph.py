#   Copyright 2022 Modelyst LLC
#   All Rights Reserved

from collections import defaultdict


def create_dag(pipeline_steps):
    dag = defaultdict(list)
    for step in pipeline_steps:
        source = step["source"]
        destinations = step["destinations"]
        step_id = step["id"]
        dag[(source, "topic")].append((step_id, "step"))
        dag[(step_id, "step")].extend(zip(destinations, ["topic"] * len(destinations)))
        for destination in destinations:
            if destination not in dag:
                dag[(destination, "topic")] = []
    return dag


def order_steps(dag):
    """
    Order the steps in the pipeline DAG.

    Args:
        dag (dict): A dictionary representing the DAG of the pipeline.

    Raises:
        ValueError: raised if a cycle is detected in the DAG.

    Returns:
        list: A list of the steps in the pipeline in the correct order.
    """
    in_degree = {node: 0 for node in dag}
    for node in dag:
        for neighbor in dag[node]:
            in_degree[neighbor] += 1

    queue = [node for node in dag if in_degree[node] == 0]
    order = []
    while queue:
        if len(queue) == 0:
            raise ValueError("Cycle detected in DAG")
        node = queue.pop(0)
        order.append(node)
        for neighbor in dag[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(order) != len(dag):
        raise ValueError("Cycle detected in DAG")
    steps = [node for node, node_type in order if node_type == "step"]
    return steps
