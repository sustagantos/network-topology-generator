# CSV → Draw.io Network Generator
 

## Overview

This tool reads a structured CSV file describing network devices and connections, and generates a `.drawio` diagram that can be opened in:

- https://app.diagrams.net/
- Draw.io Desktop

It automatically organizes devices into:

- **Geolocations**
- **Locations (racks/sites)**
- **Devices**
- **Connections (edges)**


## Features

- Automatic grouping by **Geolocation → Location**
- Automatic layout positioning
- Connection mapping between devices
- Clean Draw.io XML generation


## Installation

Clone the repository:

```bash
git clone https://github.com/sustagantos/network-topology-generator.git
cd network-topology-generator
```

No external dependencies required (uses only Python standard library).


## Usage

Run in the root:

```bash
python csv_to_drawio.py example.csv
```

After running, a `.drawio` file will be generated in the same folder.


## CSV Format

Your CSV must contain the following columns in the same order:

| Column            | Description                          |
|------------------|--------------------------------------|
| IP               | Device IP address                    |
| Name             | Device name                          |
| Model            | Device model (optional)              |
| ConnectedDevice  | Target device (name or IP)           |
| LocalPort        | Source port                          |
| RemotePort       | Target port                          |
| Location         | Site or rack name                    |
| Geolocation      | Region (e.g., Office X)              |


### Example:

```csv
IP,Name,Model,ConnectedDevice,LocalPort,RemotePort,Location,Geolocation
10.204.19.1,HF-ADM,SG300-52,10.204.19.11,GE1,gi26,HF-ADM,Fab3 HF
10.204.19.1,HF-ADM,SG300-52,10.204.19.7,GE24,gi25,HF-ADM,Fab3 HF
```


## Output

```
example.csv → example.drawio
```


## Tech Stack

- Python 3
- XML (Draw.io format)
- Standard Library only


## License

MIT License


## Author

Gustavo Santos
