#!/usr/bin/python3

from graphviz import Graph
from pathlib import Path
from yaml import safe_load
import argparse
import os
import sys

__version__ = '0.2'

title_color = 'lightblue'

color_list = [
    ["WH", "white", "#ffffff"],
    ["BN", "brown", "#a52a2a"],
    ["GN", "green", "#008000"],
    ["YE", "yellow", "#ffff00"],
    ["GY", "grey", "#808080"],
    ["PK", "pink", "#ffc0cb"],
    ["BU", "blue", "#0000ff"],
    ["RD", "red", "#ff0000"],
    ["BK", "black", "#000000"],
    ["VT", "violet", "#ee82ee"],
    ["PU", "purple", "#800080"],
    ["OR", "orange", "#ffa500"],
    ["TQ", "turquoise", "#40e0d0"],
    ["SL", "silver", "#c0c0c0"],
    ["GD", "gold", "#ffd700"]
]

def main():
    args = parse_args()

    if not os.path.exists(args.input_file):
        print(f'Error: input file {args.input_file} inaccessible or does not exist, check path')
        sys.exit(1)

    if args.verbose:
        print(f'Input file: {args.input_file}')

    output_pre = os.path.splitext(args.input_file)[0]

    if args.verbose:
        print(f'Output file: {output_pre}')

    stream = open(args.input_file, 'r')

    if args.verbose:
        print(f'Parsing YAML file...')

    yaml = safe_load(stream.read())

    if args.verbose:
        print("Generating graph...")

    doc = Doc(yaml)

    if args.verbose:
        print(f"Devices: {len(doc.devices)}")

    for group, connections in doc.groups.items():
        for connection in connections:
            if connection.fromDevice not in doc.devices:
                print(f"Error: device {connection.fromDevice} not found")
                exit(-1)

            if connection.toDevice not in doc.devices:
                print(f"Error: device {connection.toDevice} not found")
                exit(-1)

            if len(connection.fromPins) != len(connection.toPins):
                if len(connection.fromPins) == 0 and len(doc.devices[connection.fromDevice].pins) != 0:
                    print(f"Error: in connection {connection.fromDevice}:{connection.fromPins} -> {connection.toDevice}:{connection.toPins} pin not specified but device {connection.fromDevice} has pins")
                    exit(-1)

                if len(connection.toPins) == 0 and len(doc.devices[connection.toDevice].pins) != 0:
                    print(f"Error: in connection {connection.fromDevice}:{connection.fromPins} -> {connection.toDevice}:{connection.toPins} pin not specified but device {connection.toDevice} has pins")
                    exit(-1)

                if len(connection.fromPins) != 0 and len(connection.toPins) != 0:
                    print(f"Error: connection {connection.fromDevice}:{connection.fromPins} -> {connection.toDevice}:{connection.toPins} has different number of from/to pins")
                    exit(-1)

            if len(connection.colors) != max(len(connection.fromPins), len(connection.toPins), 1):
                print(f"Error: connection {connection.fromDevice}:{connection.fromPins} -> {connection.toDevice}:{connection.toPins} has different number of colors and pins")
                exit(-1)

            for pin in connection.fromPins:
                if pin not in doc.devices[connection.fromDevice].pins:
                    print(f"Error: pin {pin} not found in device {connection.fromDevice}")
                    exit(-1)

            for pin in connection.toPins:
                if pin not in doc.devices[connection.toDevice].pins:
                    print(f"Error: pin {pin} not found in device {connection.toDevice}")
                    exit(-1)

            if doc.devices[connection.fromDevice].colors:
                # TODO This should happen somewhere else
                if len(doc.devices[connection.fromDevice].pins) != len(doc.devices[connection.fromDevice].colors):
                    print(f"Error: device {connection.fromDevice} has different number of pins and colors")
                    exit(-1)

                for i in range(len(connection.colors)):
                    pinName = connection.fromPins[i]
                    j = 0
                    for j in range(len(doc.devices[connection.fromDevice].pins)):
                        if doc.devices[connection.fromDevice].pins[j] == pinName:
                            break

                    if get_color(doc.devices[connection.fromDevice].colors[j]) != get_color(connection.colors[i]):
                        print(f"Warning: in connection {connection.fromDevice}:{connection.fromPins} -> {connection.toDevice}:{connection.toPins} color {connection.colors[i]} doesn't match device {connection.fromDevice} color {doc.devices[connection.fromDevice].colors[j]}")
                        # exit(-1)

            if doc.devices[connection.toDevice].colors:
                # TODO This should happen somewhere else
                if len(doc.devices[connection.toDevice].pins) != len(doc.devices[connection.toDevice].colors):
                    print(f"Error: device {connection.toDevice} has different number of pins and colors")
                    exit(-1)

                for i in range(len(connection.colors)):
                    pinName = connection.toPins[i]
                    j = 0
                    for j in range(len(doc.devices[connection.toDevice].pins)):
                        if doc.devices[connection.toDevice].pins[j] == pinName:
                            break

                    if get_color(doc.devices[connection.toDevice].colors[j]) != get_color(connection.colors[i]):
                        print(f"Warning: in connection {connection.fromDevice}:{connection.fromPins} -> {connection.toDevice}:{connection.toPins} color {connection.colors[i]} doesn't match device {connection.toDevice} color {doc.devices[connection.toDevice].colors[j]}")
                        # exit(-1)

    def create_table(device):
        table = '<<table border="1" cellspacing="0" cellpadding="2">'
        table += f'<tr><td colspan="2" bgcolor="{title_color}">{device.name}</td></tr>'

        fmt = '<tr><td port="{1}w">{0}</td><td port="{1}e">{1} ({2}{3})</td></tr>'

        for i in range(len(device.pins)):
            number_of_connections = 0

            for group, connections in doc.groups.items():
                for connection in connections:
                    if connection.fromDevice == device.name and device.pins[i] in connection.fromPins:
                        number_of_connections += 1
                    if connection.toDevice == device.name and device.pins[i] in connection.toPins:
                        number_of_connections += 1

            table += fmt.format(i + 1, device.pins[i], number_of_connections, (", " + device.colors[i]) if device.colors else '')

        table += '</table>>'

        return table

    if args.combine:
        dot = Graph()

    for group, connections in doc.groups.items():
        if not args.combine:
            dot = Graph()

        font = "Roboto"

        # graph.body.append(f'// Graph generated by APP_NAME {__version__}\n')
        # graph.body.append(f'// APP_URL\n')
        dot.attr('graph',
            rankdir='LR',
            ranksep='3',
            bgcolor="#CCCCCC",
            nodesep='0.33',
            fontname=font)
        dot.attr('node',
            shape='box',
            width='0', height='0', margin='0',  # Actual size of the node is entirely determined by the label.
            style='filled',
            fillcolor='#F0F0F0',
            fontname=font)
        dot.attr('edge',
            style='bold',
            fontname=font)

        # dot.attr(splines='polyline')

        groupName = 'cluster_' + group

        with dot.subgraph(name=groupName) as sg:
            sg.graph_attr['label'] = group if group != "default" else ""
            for connection in connections:
                fromDevice = doc.devices[connection.fromDevice]
                toDevice = doc.devices[connection.toDevice]

                nodeA = group + "_" + fromDevice.name
                nodeB = group + "_" + toDevice.name

                sg.node(nodeA, label=create_table(fromDevice), shape='plaintext')
                sg.node(nodeB, label=create_table(toDevice), shape='plaintext')

                r = max(len(connection.fromPins), len(connection.toPins), 1)

                for i in range(r):
                    if connection.fromPins:
                        a = f"{nodeA}:{connection.fromPins[i]}e:e"
                    else:
                        a = f"{nodeA}:e"

                    if connection.toPins:
                        b = f"{nodeB}:{connection.toPins[i]}w:w"
                    else:
                        b = f"{nodeB}:w"

                    hex_color = '#000000:' + get_color(connection.colors[i]) + ':#000000'

                    dot.edge(a, b, color=hex_color, penwidth="2")

        dot.format = "svg"

        filename = output_pre if args.combine or group == "default" else output_pre + "_" + group

        filename.replace(" ", "_")

        if not args.combine:
            if args.verbose:
                print("Creating " + filename + ".svg")

            dot.render(filename=filename, view=False, cleanup=True)

            if args.show:
                os.system("eom -n \"" + filename + ".svg\" &")

    if args.combine:
        if args.verbose:
            print("Creating " + filename + ".svg")

        dot.render(filename=filename, view=False, cleanup=True)

        if args.show:
            os.system("eom -n \"" + filename + ".svg\" &")

def parse_args():
    parser = argparse.ArgumentParser(description='Generate cable and wiring harness documentation from YAML descriptions')
    parser.add_argument('-V', '--version', action='version', version='%(prog)s ' + __version__)
    parser.add_argument('input_file', action='store', type=str, metavar='YAML_FILE')
    parser.add_argument('-s', '--show', action='store_true', default=False)
    parser.add_argument('-c', '--combine', action='store_true', default=False)
    parser.add_argument('-v', '--verbose', action='store_true', default=False)
    # parser.add_argument('-n', '--no-output', action='store_true', default=False)

    args = parser.parse_args()

    args.input_file = os.path.abspath(args.input_file)

    return args

class Doc:
    def __init__(self, yaml):
        self.devices = {}
        self.groups = {}

        for device in yaml["devices"]:
            name = device["name"]
            if name in self.devices:
                print("Duplicate device name: " + name)
                exit(1)
            self.devices[name] = Device(device)

        for connection in yaml["connections"]:
            if "group" in connection:
                if connection["group"] not in self.groups:
                    self.groups[connection["group"]] = []
                self.groups[connection["group"]].append(Connection(connection))
            else:
                if "default" not in self.groups:
                    self.groups["default"] = []
                self.groups["default"].append(Connection(connection))

class Device:
    def __init__(self, yaml):
        self.name = yaml["name"]
        self.pins = yaml["pins"] if "pins" in yaml else []
        self.type = yaml["type"] if "type" in yaml else ""
        self.info = yaml["info"] if "info" in yaml else ""
        if "colors" in yaml:
            for c in yaml["colors"]:
                if not valid_color(c):
                    # print("Invalid color:", c, "at:", yaml["colors"].start_line)
                    print("Invalid color:", c, "at:", "?")
                    exit(1)
            self.colors = yaml["colors"]
        else:
            self.colors = []

        assert type(self.name) == str, "Device name must be a string (in device: " + self.name + ")"
        assert type(self.pins) == list, "Device pins must be a list (in device: " + self.name + ")"
        assert type(self.type) == str, "Device type must be a string (in device: " + self.name + ")"
        assert type(self.info) == str, "Device info must be a string (in device: " + self.name + ")"
        assert type(self.colors) == list, "Device colors must be a list (in device: " + self.name + ")"

# TODO Possibly make each individual wire a separate connection
class Connection:
    def __init__(self, yaml):
        self.fromDevice = yaml["from"]["device"]
        self.fromPins = yaml["from"]["pins"] if "pins" in yaml["from"] else []
        self.toDevice = yaml["to"]["device"]
        self.toPins = yaml["to"]["pins"] if "pins" in yaml["to"] else []
        for c in yaml["color"]:
            if not valid_color(c):
                # print("Invalid color:", c, "at:", yaml["color"].start_line)
                print("Invalid color:", c, "at:", "?")
                exit(1)
        self.colors = yaml["color"]
        self.group = yaml["group"] if "group" in yaml else None
        # self.lineNumber = yaml["from"].start_line
        self.lineNumber = 0 # TODO

        assert type(self.fromDevice) == str, "Connection from device must be a string (in connection: " + self.fromDevice + " -> " + self.toDevice + ")"
        assert type(self.fromPins) == list, "Connection from pins must be a list (in connection: " + self.fromDevice + " -> " + self.toDevice + ")"
        assert type(self.toDevice) == str, "Connection to device must be a string (in connection: " + self.fromDevice + " -> " + self.toDevice + ")"
        assert type(self.toPins) == list, "Connection to pins must be a list (in connection: " + self.fromDevice + " -> " + self.toDevice + ")"
        assert type(self.colors) == list, "Connection colors must be a list (in connection: " + self.fromDevice + " -> " + self.toDevice + ")"
        assert type(self.group) == str or self.group is None, "Connection group must be a string (in connection: " + self.fromDevice + " -> " + self.toDevice + ")"
        assert type(self.lineNumber) == int, "Connection lineNumber must be an int (in connection: " + self.fromDevice + " -> " + self.toDevice + ")"

def get_color(code):
    if code in [c[0] for c in color_list]:
        return color_list[[c[0] for c in color_list].index(code)][2]

    if code in [c[1] for c in color_list]:
        return color_list[[c[1] for c in color_list].index(code)][2]

    print(f"Error: unknown color code {code}")
    exit(-1)

def valid_color(code):
    return (code in [c[0] for c in color_list]) or (code in [c[1] for c in color_list])

if __name__ == '__main__':
    main()
