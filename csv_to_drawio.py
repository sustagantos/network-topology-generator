import csv
import uuid
import xml.etree.ElementTree as ET
import argparse


# aux to get a file named .csv and make it .drawio
def get_output_file(csv_file):
    drawio_file = csv_file.replace(".csv", ".drawio")
    return drawio_file

def csv_to_drawio(csv_file):

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

    # xml
    root = ET.Element("mxfile", host="app.diagrams.net")
    diagram = ET.SubElement(root, "diagram", name="Network Topology")
    mxGraphModel = ET.SubElement(diagram, "mxGraphModel")
    root_cell = ET.SubElement(mxGraphModel, "root")

    ET.SubElement(root_cell, "mxCell", id="0")
    ET.SubElement(root_cell, "mxCell", id="1", parent="0")

    # registries
    devices_by_ip = {}
    devices_by_name = {}

    rows = []
    with open(csv_file, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            for k in list(row.keys()):
                if isinstance(row[k], str):
                    row[k] = row[k].strip()
            rows.append(row)

    geos = {}
    for row in rows:
        geo = row.get("Geolocation", "") or "Unspecified Region"
        loc = row.get("Location", "") or "Unspecified"
        geos.setdefault(geo, {}).setdefault(loc, []).append(row)

    current_geo_x = GEO_X_START

    for geo_name, loc_map in geos.items():
        location_specs = []  
        for loc_name, devs in loc_map.items():
            seen_ips = set()
            for r in devs:
                ip = r.get("IP", "")
                if ip and ip not in seen_ips:
                    seen_ips.add(ip)
            num_devices = len(seen_ips)
            rack_height = HEADER_PADDING + (num_devices * (DEVICE_HEIGHT + VERTICAL_SPACING)) + RACK_PADDING_BOTTOM
            location_specs.append((loc_name, devs, rack_height))

        total_locations_height = 0
        for idx, (_, __, h) in enumerate(location_specs):
            if idx > 0:
                total_locations_height += GEO_VERTICAL_SPACING
            total_locations_height += h

        geo_height = GEO_HEADER_PADDING + total_locations_height + GEO_PADDING_BOTTOM

        geo_id = str(uuid.uuid4())
        geo_cell = ET.SubElement(
            root_cell,
            "mxCell",
            id=geo_id,
            value=geo_name,
            style="shape=rectangle;fillColor=#f5f5f5;rounded=1;verticalAlign=top;whiteSpace=wrap;",
            vertex="1",
            parent="1"
        )
        geo_geom = ET.SubElement(
            geo_cell,
            "mxGeometry",
            x=str(current_geo_x),
            y=str(GEO_Y),
            width=str(GEO_WIDTH),
            height=str(geo_height)
        )
        geo_geom.set("as", "geometry")

        current_loc_y = GEO_HEADER_PADDING
        for loc_name, devs, rack_height in location_specs:
            rack_id = str(uuid.uuid4())
            rack_cell = ET.SubElement(
                root_cell,
                "mxCell",
                id=rack_id,
                value=loc_name,
                style="shape=rectangle;fillColor=#eeeeee;rounded=1;verticalAlign=top;whiteSpace=wrap;",
                vertex="1",
                parent=geo_id
            )
            rack_geom = ET.SubElement(
                rack_cell,
                "mxGeometry",
                x=str(GEO_INNER_LEFT),
                y=str(current_loc_y),
                width=str(RACK_WIDTH),
                height=str(rack_height)
            )
            rack_geom.set("as", "geometry")

            device_row_by_ip = {}
            order_ips = []
            for r in devs:
                ip = r.get("IP", "")
                if ip and ip not in device_row_by_ip:
                    device_row_by_ip[ip] = r
                    order_ips.append(ip)

            for j, ip in enumerate(order_ips):
                row = device_row_by_ip[ip]
                device_id = str(uuid.uuid4())
                name = row.get("Name", "")
                model = row.get("Model", "")

                if ip:
                    devices_by_ip[ip] = device_id
                if name:
                    devices_by_name[name] = device_id

                label_parts = []
                if name and ip:
                    label_parts.append(f"{name} ({ip})")
                else:
                    label_parts.append(name or ip or "Unknown")
                if model:
                    label_parts.append(model)
                label = "\n".join(label_parts)

                cell = ET.SubElement(
                    root_cell,
                    "mxCell",
                    id=device_id,
                    value=label,
                    style="shape=rectangle;whiteSpace=wrap;",
                    vertex="1",
                    parent=rack_id
                )

                x_pos = (RACK_WIDTH / 2) - (DEVICE_WIDTH / 2)
                y_pos = HEADER_PADDING + j * (DEVICE_HEIGHT + VERTICAL_SPACING)

                geom = ET.SubElement(
                    cell,
                    "mxGeometry",
                    x=str(x_pos),
                    y=str(y_pos),
                    width=str(DEVICE_WIDTH),
                    height=str(DEVICE_HEIGHT)
                )
                geom.set("as", "geometry")

            current_loc_y += rack_height + GEO_VERTICAL_SPACING

        current_geo_x += GEO_X_STEP

    for row in rows:
        src_ip = row.get("IP", "")
        src_id = devices_by_ip.get(src_ip)
        if not src_id:
            continue

        target_ref = row.get("ConnectedDevice", "")
        target_id = devices_by_name.get(target_ref)
        if not target_id and target_ref:
            target_id = devices_by_ip.get(target_ref)
        if not target_id:
            continue

        local_port = row.get("LocalPort", "") or ""
        remote_port = row.get("RemotePort", "") or ""
        if local_port or remote_port:
            edge_label = f"{local_port} -> {remote_port}".strip()
        else:
            edge_label = row.get("ConnectedPort", "") or ""

        edge_id = str(uuid.uuid4())
        edge = ET.SubElement(
            root_cell,
            "mxCell",
            id=edge_id,
            value=edge_label,
            edge="1",
            parent="1",
            source=src_id,
            target=target_id
        )
        geom = ET.SubElement(edge, "mxGeometry", relative="1")
        geom.set("as", "geometry")

    output_file = get_output_file(csv_file)
    tree = ET.ElementTree(root)
    tree.write(output_file, encoding="utf-8", xml_declaration=True)

def main():
    parser = argparse.ArgumentParser(description="Convert CSV to Draw.io diagram")
    parser.add_argument("csv_file", help="Path to input CSV file")

    args = parser.parse_args()

    csv_to_drawio(args.csv_file)

if __name__ == "__main__":
    main()