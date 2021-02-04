import json
from collections import UserDict
from pathlib import Path

import lkml
from graphviz import Digraph


class Node(UserDict):
    def __init__(self):
        self.data = dict(depends_on=[])


def read_lookml(filepath):
    with open(filepath) as f:
        lookml = lkml.load(f.read())
    return lookml


def get_nodes(model):
    lookml = read_lookml(model)
    model_name = model.name

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


def build_child_map(nodes):
    child_map = dict()
    for node_name, contents in nodes.items():
        child_map[node_name] = contents["depends_on"]
    return child_map


def build_manifest():
    p = Path("./input/models")
    models = list(p.glob("**/*.model.lkml"))
    
    if not len(models) > 0:
        return None
    
    manifest = dict(nodes={}, child_map={})
    for model in models:
        nodes = get_nodes(model)
        manifest["nodes"] = {**manifest["nodes"], **nodes}
        child_map = build_child_map(nodes)
        manifest["child_map"] = {**manifest["child_map"], **child_map}
    
    return manifest


def read_example_manifest():
    with open("example_manifest.json") as f:
        manifest = json.loads(f.read())
    return manifest


def build_graph(manifest):
    g = Digraph("G", format="pdf")

    pairs = []
    for parent in manifest["child_map"].keys():
        for child in manifest["child_map"][parent]:
            pairs.append((parent, child))

    for pair in pairs:
        g.edge(*pair)

    return g


def main():
    manifest = build_manifest()

    if manifest is None:
        print("No LookML models found. Using example instead.")
        manifest = read_example_manifest()

    g = build_graph(manifest)
    g.render("output/dependency_graph.gv", view=True)


if __name__ == "__main__":
    main()
