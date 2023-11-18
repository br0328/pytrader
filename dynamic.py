import backtrader as bt
import ast

# Read the code from the text file
with open("code.txt", "r") as file:
    code = file.read()

# Using the ast module to parse the code
tree = ast.parse(code)

# Find the class definition for class A
class_def = None
for node in tree.body:
    if isinstance(node, ast.ClassDef) and issubclass(bt.Strategy, eval(node.bases[0].id)):
        class_def = node
        break

# Find the constructor (__init__) function within the class definition
constructor_def = None
for node in class_def.body:
    if isinstance(node, ast.FunctionDef) and node.name == "__init__":
        constructor_def = node
        break

# Get the parameters and their types from constructor_def
parameters = []
for param in constructor_def.args.args:
    if param.annotation is None: continue

    param_name = param.arg  # parameter name
    param_type = param.annotation.id  # parameter type
    parameters.append((param_name, param_type))

# Print the list of parameters and their types
for param_name, param_type in parameters:
    print(f"Parameter: {param_name}, Type: {param_type}")
