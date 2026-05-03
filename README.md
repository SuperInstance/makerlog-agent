# makerlog-agent

Agent framework for [makerlog.ai](https://makerlog.ai) — project tracking, tools inventory, and build logs for makerspaces and hardware hackers.

## Features

- **Project Management** — Track projects from idea to completion with status, budget, and tags
- **Build Logs** — Document every step with materials, tools, problems, and solutions
- **Tools Inventory** — Manage workshop equipment with condition tracking and maintenance alerts
- **Budget Tracking** — Estimated vs actual cost tracking
- **Export/Import** — JSON serialization for backup

## Installation

```bash
pip install makerlog-agent
```

## Quick Start

```python
from makerlog_agent import (
    MakerLogAgent,
    Project,
    ProjectStatus,
    Tool,
    ToolCategory,
    BuildLog,
    BuildStatus,
)

agent = MakerLogAgent()

# Register workshop tools
agent.register_tool(
    name="Soldering Iron",
    category=ToolCategory.Electronic,
    location="Electronics bench",
    condition=0.9,
)
agent.register_tool(
    name="PLA Filament",
    category=ToolCategory.Other,
    consumable=True,
    notes="1.75mm, various colors",
)

# Create a project
project = agent.create_project(
    name="LED Matrix Display",
    description="16x16 RGB LED matrix driven by ESP32",
    status=ProjectStatus.InProgress,
    budget=45.0,
    tools_required=["Soldering Iron", "ESP32 Dev Board", "PLA Filament"],
    materials=["WS2812B LEDs", "ESP32", "Power supply"],
)

# Log build steps
agent.add_build_log(
    "LED Matrix Display",
    title="Solder LED matrix",
    description="Soldered 256 WS2812B LEDs in a 16x16 grid.",
    status=BuildStatus.Success,
    duration_minutes=120,
    tools_used=["Soldering Iron"],
    materials_used=["WS2812B LEDs", "Solder wire"],
    problems="Some LEDs were polarity sensitive.",
    solutions="Checked orientation before soldering each row.",
)

# Get tools needing maintenance
maintenance_needed = agent.get_tools_needing_maintenance()

# Stats
stats = agent.get_statistics()
print(f"Active projects: {stats['status_distribution'].get('in_progress', 0)}")
```

## API Overview

### Tools

```python
tool = agent.register_tool(
    name="3D Printer",
    category=ToolCategory.3DPrinter,
    location="Fab lab corner",
    condition=0.95,
    maintenance_due=date(2024, 6, 1),
)
```

### Projects

```python
project = agent.create_project(
    name="Botanical Timer",
    description="Automated plant watering system",
    status=ProjectStatus.Planning,
    target_date=date(2024, 12, 1),
    tags=["electronics", "garden"],
    budget=30.0,
)
```

### Build Logs

```python
agent.add_build_log(
    "Botanical Timer",
    title="Assembled relay circuit",
    status=BuildStatus.Success,
    duration_minutes=45,
    materials_used=["Relay module", "Wires"],
    tools_used=["Soldering Iron"],
    problems="Relay triggered unexpectedly.",
    solutions="Added flyback diode to suppress back-EMF.",
)
```

## Development

```bash
pip install -e .
pytest tests/
```

## License

MIT

## Related

- [makerlog.ai](https://makerlog.ai) — Live site
- [makerlog-ai-pages](https://github.com/SuperInstance/makerlog-ai-pages) — GitHub Pages source
