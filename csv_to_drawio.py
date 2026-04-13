import csv
import uuid
import argparse
import xml.etree.ElementTree as ET
from collections import defaultdict

class LayoutConfig:
    RACK_WIDTH = 175
    DEVICE_WIDTH = 120
    DEVICE_HEIGHT = 60
    VERTICAL_SPACING = 20
    HEADER_PADDING = 40
    RACK_PADDING_BOTTOM = 20

    GEO_WIDTH = 450
    GEO_X_START = 100
    GEO_Y = 60
    GEO_X_STEP = 520
    GEO_INNER_LEFT = 40
    GEO_VERTICAL_SPACING = 30
    GEO_HEADER_PADDING = 40
    GEO_PADDING_BOTTOM = 30

def new_id():
    return str(uuid.uuid4())

def create_cell(root, **attrs):
    return ET.SubElement(root, "mxCell", **attrs)

def set_geometry(cell, x, y, width, height):
    geom = ET.SubElement(
        cell,
        "mxGeometry",
        x=str(x),
        y=str(y),
        width=str(width),
        height=str(height)
    )
    geom.set("as", "geometry")

def build_label(name, ip, model):
    main = f"{name} ({ip})" if name and ip else name or ip or "Unknown"
    return "\n".join(filter(None, [main, model]))

def get_output_file(csv_file):
    return csv_file.replace(".csv", ".drawio")


def read_csv(csv_file):
    rows = []
    with open(csv_file, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cleaned = {
                k: v.strip() if isinstance(v, str) else v
                for k, v in row.items()
            }
            rows.append(cleaned)
    return rows

def group_by_geo(rows):
    geos = defaultdict(lambda: defaultdict(list))

    for row in rows:
        geo = row.get("Geolocation") or "Unspecified Region"
        loc = row.get("Location") or "Unspecified"
        geos[geo][loc].append(row)

    return geos

def init_xml():
    root = ET.Element("mxfile", host="app.diagrams.net")
    diagram = ET.SubElement(root, "diagram", name="Network Topology")
    model = ET.SubElement(diagram, "mxGraphModel")
    root_cell = ET.SubElement(model, "root")

    create_cell(root_cell, id="0")
    create_cell(root_cell, id="1", parent="0")

    return root, root_cell

def create_device(root_cell, rack_id, row, index, devices, cfg):
    ip = row.get("IP", "")
    name = row.get("Name", "")
    model = row.get("Model", "")

    device_id = new_id()

    key = ip or name
    if key:
        devices[key] = device_id

    label = build_label(name, ip, model)

    cell = create_cell(
        root_cell,
        id=device_id,
        value=label,
        style="shape=rectangle;whiteSpace=wrap;",
        vertex="1",
        parent=rack_id
    )

    x = (cfg.RACK_WIDTH / 2) - (cfg.DEVICE_WIDTH / 2)
    y = cfg.HEADER_PADDING + index * (cfg.DEVICE_HEIGHT + cfg.VERTICAL_SPACING)

    set_geometry(cell, x, y, cfg.DEVICE_WIDTH, cfg.DEVICE_HEIGHT)

def create_edge(root_cell, row, devices):
    src_ip = row.get("IP")
    src_id = devices.get(src_ip)

    if not src_id:
        return

    target_ref = row.get("ConnectedDevice")
    target_id = devices.get(target_ref)

    if not target_id:
        return

    local = row.get("LocalPort", "")
    remote = row.get("RemotePort", "")

    label = f"{local} -> {remote}".strip() if (local or remote) else ""

    edge = create_cell(
        root_cell,
        id=new_id(),
        value=label,
        edge="1",
        parent="1",
        source=src_id,
        target=target_id
    )

    geom = ET.SubElement(edge, "mxGeometry", relative="1")
    geom.set("as", "geometry")


def csv_to_drawio(csv_file):
    cfg = LayoutConfig()

    rows = read_csv(csv_file)
    geos = group_by_geo(rows)

    root, root_cell = init_xml()
    devices = {}

    current_geo_x = cfg.GEO_X_START

    for geo_name, locs in geos.items():

        geo_id = new_id()

        geo_cell = create_cell(
            root_cell,
            id=geo_id,
            value=geo_name,
            style="shape=rectangle;fillColor=#f5f5f5;rounded=1;verticalAlign=top;",
            vertex="1",
            parent="1"
        )

        current_loc_y = cfg.GEO_HEADER_PADDING

        for loc_name, devs in locs.items():

            rack_id = new_id()

            rack_cell = create_cell(
                root_cell,
                id=rack_id,
                value=loc_name,
                style="shape=rectangle;fillColor=#eeeeee;rounded=1;verticalAlign=top;",
                vertex="1",
                parent=geo_id
            )

            unique_ips = list({d.get("IP") for d in devs if d.get("IP")})
            rack_height = (
                cfg.HEADER_PADDING +
                len(unique_ips) * (cfg.DEVICE_HEIGHT + cfg.VERTICAL_SPACING) +
                cfg.RACK_PADDING_BOTTOM
            )

            set_geometry(
                rack_cell,
                cfg.GEO_INNER_LEFT,
                current_loc_y,
                cfg.RACK_WIDTH,
                rack_height
            )

            for i, row in enumerate(devs):
                create_device(root_cell, rack_id, row, i, devices, cfg)

            current_loc_y += rack_height + cfg.GEO_VERTICAL_SPACING

        geo_height = current_loc_y + cfg.GEO_PADDING_BOTTOM

        set_geometry(
            geo_cell,
            current_geo_x,
            cfg.GEO_Y,
            cfg.GEO_WIDTH,
            geo_height
        )

        current_geo_x += cfg.GEO_X_STEP

    # edges
    for row in rows:
        create_edge(root_cell, row, devices)

    # save
    output = get_output_file(csv_file)
    ET.ElementTree(root).write(output, encoding="utf-8", xml_declaration=True)

    print(f"File generated: {output}")

def main():
    parser = argparse.ArgumentParser(description="CSV → Draw.io generator")
    parser.add_argument("csv_file", help="Input CSV file")

    args = parser.parse_args()

    csv_to_drawio(args.csv_file)

if __name__ == "__main__":
    main()