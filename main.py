from collections import UserDict
from pathlib import Path
from typing import List

import click
import lkml
from graphviz import Digraph

INPUT_MODELS_PATH = "./input/models"
MODEL_FILE_EXTENSION = "*.model.lkml"
OUTPUT_FILE_PATH = "output/dependency_graph.gv"
RENDER_FORMAT = "pdf"


class Node(UserDict):
    def __init__(self):
        self.data = dict(depends_on=[])


def read_lookml(path: Path) -> dict:
    """Parse a LookML file"""
    with open(path) as f:
        lookml = lkml.load(f.read())
    return lookml


def build_nodes(model: Path) -> dict:
    """
    Build nodes dictionary from a LookML model.
    Each node has a unique name and a list of node names it depends on.

    Returns:
        "nodes": {
            "model.product": {
                "depends_on": [
                        "explore.user_events_cube"
                ]
            },
            ...
        }
    """
    lookml = read_lookml(model)
    model_name = model.name.split(".")[0]

    nodes = dict()
    nodes[f"model.{model_name}"] = Node()
    for explore in lookml["explores"]:
        node = Node()

        if "joins" in explore.keys():
            for view in explore["joins"]:
                node["depends_on"].append(f"view.{view['name']}")

        node["depends_on"].append(f"view.{explore['name']}")

        explore_node_name = f"explore.{explore['name']}"
        nodes[explore_node_name] = node
        nodes[f"model.{model_name}"]["depends_on"].append(explore_node_name)

    return nodes


def build_child_map(nodes: dict) -> dict:
    """
    Build child map combining all `depends_on` specifications.
    Each entry is a node with the full list of children.

    Returns:
        "child_map": {
            "explore.user_events_cube": [
                "view.user_events_cube",
                "view.dummy_view"
            ],
            ...
        }
    """
    child_map = dict()
    for node_name, contents in nodes.items():
        child_map[node_name] = contents["depends_on"]
    return child_map


def build_manifest() -> dict:
    """
    Build manifest containing nodes and child map objects.
    Expects LookML .model files to be in input/models folder.
    """
    p = Path(INPUT_MODELS_PATH)
    models = list(p.glob(f"**/{MODEL_FILE_EXTENSION}"))

    if not models:
        raise FileNotFoundError(
            f"No {MODEL_FILE_EXTENSION} files found in {INPUT_MODELS_PATH}"
        )

    manifest = dict(nodes=dict(), child_map=dict())
    for model in models:
        nodes = build_nodes(model)
        manifest["nodes"] = {**manifest["nodes"], **nodes}
        child_map = build_child_map(nodes)
        manifest["child_map"] = {**manifest["child_map"], **child_map}

    return manifest


def build_graph(manifest: dict, filters: List = []) -> Digraph:
    """
    Build directed graph of dependencies.
    Add edges by iterating over each parent/child combination in manifest child map.
    """
    g = Digraph("G", format=RENDER_FORMAT, node_attr={"color": "lightblue2", "style": "filled"})
    g.attr(rankdir="LR")

    pairs = []
    for parent in manifest["child_map"].keys():
        for child in manifest["child_map"][parent]:
            pairs.append((parent, child))

    for pair in pairs:
        if not filters or any(f in pair for f in filters):
            g.edge(*pair)

    return g


def render_graph(g: Digraph, path: Path):
    """Render a Graph saving output to a given path"""
    print(f"Rendering {path}")
    g.render(path, view=True)


@click.command()
@click.option(
    "--filters",
    help="Keep only edges connecting node passed. For multiple filters, pass a string with node names seperated by spaces",
)
def main(filters: str):
    try:
        manifest = build_manifest()
    except FileNotFoundError as e:
        print(repr(e))
        return

    parsed_filters = []
    if filters:
        parsed_filters = filters.split(" ")

    g = build_graph(
        manifest,
        filters=parsed_filters,
    )

    filename = Path(OUTPUT_FILE_PATH)
    render_graph(g, filename)


if __name__ == "__main__":
    main()
