#!/usr/bin/python3

from graphviz import Graph
from pathlib import Path
from yaml import safe_load
import argparse
import os
import sys

__version__ = '0.2.1'

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
                print(f"Warning: device {connection.fromDevice} not found")
                continue

            if connection.toDevice not in doc.devices:
                print(f"Warning: device {connection.toDevice} not found")
                continue

            if len(connection.fromPins) != len(connection.toPins):
                if len(connection.fromPins) == 0 and len(doc.devices[connection.fromDevice].pins) != 0:
                    print(f"Warning: in connection {connection.fromDevice}:{connection.fromPins} -> {connection.toDevice}:{connection.toPins} pin not specified but device {connection.fromDevice} has pins")
                    continue

                if len(connection.toPins) == 0 and len(doc.devices[connection.toDevice].pins) != 0:
                    print(f"Warning: in connection {connection.fromDevice}:{connection.fromPins} -> {connection.toDevice}:{connection.toPins} pin not specified but device {connection.toDevice} has pins")
                    continue

                if len(connection.fromPins) != 0 and len(connection.toPins) != 0:
                    print(f"Warning: connection {connection.fromDevice}:{connection.fromPins} -> {connection.toDevice}:{connection.toPins} has different number of from/to pins")
                    continue

            if len(connection.colors) != max(len(connection.fromPins), len(connection.toPins), 1):
                print(f"Warning: connection {connection.fromDevice}:{connection.fromPins} -> {connection.toDevice}:{connection.toPins} has different number of colors and pins")
                continue

            for pin in connection.fromPins:
                if pin not in doc.devices[connection.fromDevice].pins:
                    print(f"Warning: pin {pin} not found in device {connection.fromDevice}")
                    continue

            for pin in connection.toPins:
                if pin not in doc.devices[connection.toDevice].pins:
                    print(f"Warning: pin {pin} not found in device {connection.toDevice}")
                    continue

            if doc.devices[connection.fromDevice].colors:
                # TODO This should happen somewhere else
                if len(doc.devices[connection.fromDevice].pins) != len(doc.devices[connection.fromDevice].colors):
                    print(f"Warning: device {connection.fromDevice} has different number of pins and colors")
                    continue

                for i in range(len(connection.colors)):
                    pinName = connection.fromPins[i]
                    j = 0
                    for j in range(len(doc.devices[connection.fromDevice].pins)):
                        if doc.devices[connection.fromDevice].pins[j] == pinName:
                            break

                    if get_color(doc.devices[connection.fromDevice].colors[j]) != get_color(connection.colors[i]):
                        print(f"Warning: in connection {connection.fromDevice}:{connection.fromPins} -> {connection.toDevice}:{connection.toPins} color {connection.colors[i]} doesn't match device {connection.fromDevice} color {doc.devices[connection.fromDevice].colors[j]}")
                        continue

            if doc.devices[connection.toDevice].colors:
                # TODO This should happen somewhere else
                if len(doc.devices[connection.toDevice].pins) != len(doc.devices[connection.toDevice].colors):
                    print(f"Warning: device {connection.toDevice} has different number of pins and colors")
                    continue

                for i in range(len(connection.colors)):
                    pinName = connection.toPins[i]
                    j = 0
                    for j in range(len(doc.devices[connection.toDevice].pins)):
                        if doc.devices[connection.toDevice].pins[j] == pinName:
                            break

                    if get_color(doc.devices[connection.toDevice].colors[j]) != get_color(connection.colors[i]):
                        print(f"Warning: in connection {connection.fromDevice}:{connection.fromPins} -> {connection.toDevice}:{connection.toPins} color {connection.colors[i]} doesn't match device {connection.toDevice} color {doc.devices[connection.toDevice].colors[j]}")
                        continue

    def create_table(device):
        is_node = len(device.pins) == 0

        table = '<<table border="1" cellspacing="0" cellpadding="2">'

        if is_node:
            table += f'<tr><td colspan="3" bgcolor="{title_color}">{device.name} ({device.connection_count_total})</td></tr>'
        else:
            table += f'<tr><td colspan="3" bgcolor="{title_color}">{device.name}</td></tr>'

        if device.info:
            table += f'<tr><td colspan="3">{device.info}</td></tr>'

        fmt = '<tr><td port="{1}w" bgcolor="{3}">{0}</td><td bgcolor="{3}">{1}</td><td port="{1}e" bgcolor="{3}">{2}</td></tr>'

        for i in range(len(device.pins)):
            pin_name = device.pins[i]

            if pin_name is None:
                table += f'<tr><td>{i + 1}</td><td></td><td></td></tr>'
            else:
                number_of_connections = device.connection_count[pin_name]

                bgcolor = "white"

                if number_of_connections != 1:
                    bgcolor = "pink"

                if pin_name in device.unused:
                    bgcolor = "lightgrey"

                if device.colors and device.colors[i]:
                    table += fmt.format(i + 1, pin_name, device.colors[i], bgcolor)
                else:
                    table += fmt.format(i + 1, pin_name, '', bgcolor)

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
            # ranksep='3',
            ranksep='2',
            bgcolor="#FFFFFF" if args.white else "#CCCCCC",
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

    unused_devices = []

    # Create a graph of unused devices
    for device in doc.devices.values():
        if device.connection_count_total == 0:
            unused_devices.append(device)

    if len(unused_devices) > 0:
        if not args.combine:
            dot = Graph()

            font = "Roboto"

            dot.attr('graph',
                rankdir='LR',
                ranksep='2',
                bgcolor="#FFFFFF" if args.white else "#CCCCCC",
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

        group = "Unconnected"

        groupName = 'cluster_' + group

        with dot.subgraph(name=groupName) as sg:
            sg.graph_attr['label'] = group
            for device in unused_devices:
                node = group + "_" + device.name
                sg.node(node, label=create_table(device), shape='plaintext')

        dot.format = "svg"

        filename = output_pre if args.combine or group == "default" else output_pre + "_" + group

        filename.replace(" ", "_")

        if not args.combine:
            if args.verbose:
                print("Creating " + filename + ".svg")

            dot.render(filename=filename, view=False, cleanup=True)

            if args.show:
                os.system("eom -n \"" + filename + ".svg\" &")

    # unused_devices = []

    # for device in doc.devices.values():
    #     if device.connection_count_total == 0:
    #         unused_devices.append(device)

    # if len(unused_devices) > 0:
    #     groupName = 'cluster_Unused'
    #     with dot.subgraph(name=groupName) as sg:
    #         sg.graph_attr['label'] = "Unused"
    #         for u in unused_devices:
    #             node = group + "_" + u.name
    #             sg.node(node, label=create_table(u), shape='plaintext')

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
    parser.add_argument('-w', '--white', action='store_true', default=False)
    # parser.add_argument('-n', '--no-output', action='store_true', default=False)

    args = parser.parse_args()

    args.input_file = os.path.abspath(args.input_file)

    return args

class Doc:
    def __init__(self, yaml):
        self.devices = {}
        self.groups = {}

        if yaml["devices"] is None:
            yaml["devices"] = []

        for device in yaml["devices"]:
            name = device["name"]
            if name in self.devices:
                print("Warning: Duplicate device name: " + name)
                continue
            self.devices[name] = Device(device)

        if yaml["connections"] is None:
            yaml["connections"] = []

        for connection in yaml["connections"]:
            c = Connection(connection)

            if c.fromDevice not in self.devices:
                print("Warning: " + c.fromDevice + " not defined")
                self.devices[c.fromDevice] = Device({"name": c.fromDevice})

            if c.toDevice not in self.devices:
                print("Warning: " + c.toDevice + " not defined")
                self.devices[c.toDevice] = Device({"name": c.toDevice})

            for i in range(len(c.fromPins)):
                if c.fromPins[i] not in self.devices[c.fromDevice].pins:
                    print("Warning: Pin " + c.fromPins[i] + " not found in device " + c.fromDevice)
                    continue

                self.devices[c.fromDevice].connection_count[c.fromPins[i]] += 1
                self.devices[c.fromDevice].connection_count_total += 1

            if len(c.fromPins) == 0:
                if len(self.devices[c.fromDevice].pins) != 0:
                    print("Warning: Device " + c.fromDevice + " has pins, but connection " + c.fromDevice + " -> " + c.toDevice + " does not specify any pins")
                else:
                    self.devices[c.fromDevice].connection_count_total += 1

            for i in range(len(c.toPins)):
                if c.toPins[i] not in self.devices[c.toDevice].pins:
                    print("Warning: Pin " + c.toPins[i] + " not found in device " + c.toDevice)
                    continue

                self.devices[c.toDevice].connection_count[c.toPins[i]] += 1
                self.devices[c.toDevice].connection_count_total += 1

            if len(c.toPins) == 0:
                if len(self.devices[c.toDevice].pins) != 0:
                    print("Warning: Device " + c.toDevice + " has pins, but connection " + c.fromDevice + " -> " + c.toDevice + " does not specify any pins")
                else:
                    self.devices[c.toDevice].connection_count_total += 1

            if "group" not in connection:
                connection["group"] = "default"

            if connection["group"] not in self.groups:
                self.groups[connection["group"]] = []

            self.groups[connection["group"]].append(c)

        for device in self.devices.values():
            if device.connection_count_total == 0:
                print("Warning: Device " + device.name + " is not connected to anything")
                continue

            for pin_name in device.connection_count:
                if pin_name is None:
                    continue

                if device.connection_count[pin_name] > 1:
                    # print("Warning: Pin " + pin_name + " on device " + device.name + " is connected to " + str(device.connection_count[pin_count]) + " other devices")
                    print("Warning: Pin " + device.name + ":" + pin_name + " is connected to " + str(device.connection_count[pin_name]) + " other devices")
                elif device.connection_count[pin_name] == 0:
                    if pin_name not in device.unused:
                        print("Warning: Pin " + device.name + ":" + pin_name + " is not connected to anything")
                else:
                    if pin_name in device.unused:
                        print("Warning: Pin " + device.name + ":" + pin_name + " is connected to something, but marked as unused")

# TODO Add function to create Device from yaml, and simplify Device constructor.

class Device:
    def __init__(self, yaml):
        self.name = yaml["name"]

        if "pins" in yaml:
            if type(yaml["pins"]) == str:
                self.pins = [x.strip() for x in yaml["pins"].split(',')]
            else:
                self.pins = yaml["pins"]
        else:
            self.pins = []

        self.info = yaml["info"] if "info" in yaml else ""

        if "colors" in yaml:
            if type(yaml["colors"]) == str:
                self.colors = [x.strip() for x in yaml["colors"].split(',')]
            else:
                self.colors = yaml["colors"]
        else:
            self.colors = []

        self.unused = yaml["unused"] if "unused" in yaml else []

        assert type(self.name) == str, "Device name must be a string (in device: " + self.name + ")"
        assert type(self.pins) == list, "Device pins must be a list (in device: " + self.name + ")"
        # for pin in self.pins:
        #     assert type(pin) == str, "Device pins must be a list of strings (in device: " + self.name + ")"
        assert type(self.info) == str, "Device info must be a string (in device: " + self.name + ")"
        assert type(self.colors) == list, "Device colors must be a list (in device: " + self.name + ")"
        # for color in self.colors:
        #     assert type(color) == str, "Device colors must be a list of strings (in device: " + self.name + ")"
        assert type(self.unused) == list, "Device unused pins must be a list (in device: " + self.name + ")"

        self.pins = [str(pin) if type(pin) == int else pin for pin in self.pins]

        self.unused = [str(pin) if type(pin) == int else pin for pin in self.unused]

        for unused in self.unused:
            if unused not in self.pins:
                print("Warning: Unused pin " + unused + " not found in device " + self.name)
                continue

        self.connection_count = {} # map from pin name to number of connections
        for pin in self.pins:
            self.connection_count[pin] = 0

        self.connection_count_total = 0

# TODO Possibly make each individual wire a separate connection
class Connection:
    def __init__(self, yaml):
        from_ = yaml["from"]
        to_ = yaml["to"]

        if type(from_) == str:
            self.fromDevice = from_.split(",")[0].strip()
            self.fromPins = [x.strip() for x in from_.split(",")[1:]] if len(from_.split(",")) > 1 else []
        else:
            self.fromDevice = from_["device"]
            self.fromPins = from_["pins"] if "pins" in from_ else []

        if type(to_) == str:
            self.toDevice = to_.split(",")[0].strip()
            self.toPins = [x.strip() for x in to_.split(",")[1:]] if len(to_.split(",")) > 1 else []
        else:
            self.toDevice = yaml["to"]["device"]
            self.toPins = yaml["to"]["pins"] if "pins" in yaml["to"] else []

        if "color" not in yaml:
            yaml["color"] = ["BK"] * max(len(self.fromPins), len(self.toPins), 1)

        if type(yaml["color"]) == str:
            self.colors = [c.strip() for c in yaml["color"].split(",")] if "color" in yaml else []
        else:
            self.colors = yaml["color"]

        self.group = yaml["group"] if "group" in yaml else None
        self.lineNumber = 0 # TODO

        assert type(self.fromDevice) == str, "Connection from device must be a string (in connection: " + self.fromDevice + " -> " + self.toDevice + ")"
        assert type(self.fromPins) == list, "Connection from pins must be a list (in connection: " + self.fromDevice + " -> " + self.toDevice + ")"
        assert type(self.toDevice) == str, "Connection to device must be a string (in connection: " + self.fromDevice + " -> " + self.toDevice + ")"
        assert type(self.toPins) == list, "Connection to pins must be a list (in connection: " + self.fromDevice + " -> " + self.toDevice + ")"
        assert type(self.colors) == list, "Connection colors must be a list (in connection: " + self.fromDevice + " -> " + self.toDevice + ")"
        assert type(self.group) == str or self.group is None, "Connection group must be a string (in connection: " + self.fromDevice + " -> " + self.toDevice + ")"
        assert type(self.lineNumber) == int, "Connection lineNumber must be an int (in connection: " + self.fromDevice + " -> " + self.toDevice + ")"

        for c in self.colors:
            if not valid_color(c):
                print("Warning: Invalid color:", c, "at:", "?")

def get_color(code):
    if code in [c[0] for c in color_list]:
        return color_list[[c[0] for c in color_list].index(code)][2]

    if code in [c[1] for c in color_list]:
        print("Warning: color code", code, "is deprecated, please use", color_list[[c[1] for c in color_list].index(code)][0], "instead")
        return color_list[[c[1] for c in color_list].index(code)][2]

    print(f"Warning: unknown color code {code}")

    return color_list["BK"][2]

def valid_color(code):
    return (code in [c[0] for c in color_list]) or (code in [c[1] for c in color_list])

if __name__ == '__main__':
    main()
