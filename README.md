# looker-dependency-graph
Build a dependency graph based on your Looker `.model` files.

## Dependencies
```bash
sudo apt-get install graphviz
poetry install
```

## Setup
Add your model files into `input/models/`.

## Run
```
poetry shell
python main.py
```

## Example output

![example graph][./output/example_dependency_graph.gv.png]