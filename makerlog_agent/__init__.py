"""
makerlog_agent — Agent framework for makerlog.ai

Project tracking, tools inventory, and build logs for makerspaces
and hardware hackers. Integrates with the PLATO memory layer.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from typing import Optional
import json

__version__ = "0.1.0"
__all__ = [
    "Project",
    "ProjectStatus",
    "Tool",
    "ToolCategory",
    "BuildLog",
    "BuildStatus",
    "MakerLogAgent",
]


class ProjectStatus(Enum):
    """Lifecycle status of a project."""
    Idea = "idea"
    Planning = "planning"
    InProgress = "in_progress"
    OnHold = "on_hold"
    Completed = "completed"
    Abandoned = "abandoned"


class ToolCategory(Enum):
    """Categories for workshop tools."""
    HandTool = "hand_tool"
    PowerTool = "power_tool"
    Electronic = "electronic"
    CNC = "cnc"
    3DPrinter = "3d_printer"
    LaserCutter = "laser_cutter"
    Sewing = "sewing"
    Woodworking = "woodworking"
    Metalworking = "metalworking"
    Safety = "safety"
    Measurement = "measurement"
    Other = "other"


class BuildStatus(Enum):
    """Status of a build step or log entry."""
    Planned = "planned"
    InProgress = "in_progress"
    Success = "success"
    Failed = "failed"
    Skipped = "skipped"


@dataclass
class Tool:
    """
    A tool or equipment item in the inventory.

    Attributes:
        name: Display name of the tool
        category: High-level category
        description: What the tool does
        location: Where it's stored
        condition: Current condition (0.0 to 1.0)
        maintenance_due: Next maintenance date (optional)
        consumable: Whether the tool is consumable (sandpaper, filament, etc.)
        notes: Additional notes
    """
    name: str
    category: ToolCategory
    description: str = ""
    location: str = ""
    condition: float = 1.0
    maintenance_due: Optional[date] = None
    consumable: bool = False
    notes: str = ""
    acquired_date: Optional[date] = None

    def needs_maintenance(self) -> bool:
        """Check if maintenance is due or overdue."""
        if self.maintenance_due is None:
            return False
        return date.today() >= self.maintenance_due

    def update_condition(self, new_condition: float) -> None:
        """Update tool condition. Value clamped to [0.0, 1.0]."""
        self.condition = max(0.0, min(1.0, new_condition))

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "category": self.category.value,
            "description": self.description,
            "location": self.location,
            "condition": self.condition,
            "maintenance_due": self.maintenance_due.isoformat() if self.maintenance_due else None,
            "consumable": self.consumable,
            "notes": self.notes,
            "acquired_date": self.acquired_date.isoformat() if self.acquired_date else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Tool":
        data = data.copy()
        data["category"] = ToolCategory(data["category"])
        if data.get("maintenance_due"):
            data["maintenance_due"] = date.fromisoformat(data["maintenance_due"])
        if data.get("acquired_date"):
            data["acquired_date"] = date.fromisoformat(data["acquired_date"])
        return cls(**data)


@dataclass
class BuildLog:
    """
    A single step or entry in a build log.

    Attributes:
        timestamp: When this log entry was made
        status: Current status of this step
        title: Brief title of the step
        description: What was done or attempted
        duration_minutes: How long the step took
        materials_used: List of materials consumed
        tools_used: List of tool names used
        problems: Issues encountered
        solutions: How problems were solved
        attachments: File paths or URLs to photos/schematics
    """
    timestamp: datetime = field(default_factory=datetime.now)
    status: BuildStatus = BuildStatus.Planned
    title: str = ""
    description: str = ""
    duration_minutes: Optional[int] = None
    materials_used: list[str] = field(default_factory=list)
    tools_used: list[str] = field(default_factory=list)
    problems: str = ""
    solutions: str = ""
    attachments: list[str] = field(default_factory=list)

    def complete(self, success: bool = True, notes: str = "") -> None:
        """Mark this build step as complete."""
        self.status = BuildStatus.Success if success else BuildStatus.Failed
        if notes:
            self.description = notes

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "status": self.status.value,
            "title": self.title,
            "description": self.description,
            "duration_minutes": self.duration_minutes,
            "materials_used": self.materials_used,
            "tools_used": self.tools_used,
            "problems": self.problems,
            "solutions": self.solutions,
            "attachments": self.attachments,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BuildLog":
        data = data.copy()
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        data["status"] = BuildStatus(data["status"])
        return cls(**data)


@dataclass
class Project:
    """
    A maker project with build logs and metadata.

    Attributes:
        name: Project name
        description: What the project is
        status: Current project status
        start_date: When the project started
        target_date: Target completion date (optional)
        tags: Categorization tags
        tools_required: Tool names needed for this project
        materials: List of materials needed
        budget: Estimated budget in USD
        actual_cost: Actual spent amount
        build_logs: Ordered list of build log entries
        links: Related URLs (schematics, tutorials, repos)
        collaborators: Names of other makers
        notes: General notes
    """
    name: str
    description: str = ""
    status: ProjectStatus = ProjectStatus.Idea
    start_date: date = field(default_factory=date.today)
    target_date: Optional[date] = None
    tags: list[str] = field(default_factory=list)
    tools_required: list[str] = field(default_factory=list)
    materials: list[str] = field(default_factory=list)
    budget: float = 0.0
    actual_cost: float = 0.0
    build_logs: list[BuildLog] = field(default_factory=list)
    links: list[str] = field(default_factory=list)
    collaborators: list[str] = field(default_factory=list)
    notes: str = ""

    def add_build_log(self, log: BuildLog) -> None:
        """Append a build log entry."""
        self.build_logs.append(log)

    def add_tag(self, tag: str) -> None:
        if tag not in self.tags:
            self.tags.append(tag)

    @property
    def completed_steps(self) -> int:
        return sum(1 for log in self.build_logs if log.status == BuildStatus.Success)

    @property
    def failed_steps(self) -> int:
        return sum(1 for log in self.build_logs if log.status == BuildStatus.Failed)

    @property
    def total_duration_minutes(self) -> Optional[int]:
        total = sum(log.duration_minutes or 0 for log in self.build_logs)
        return total if total > 0 else None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "start_date": self.start_date.isoformat(),
            "target_date": self.target_date.isoformat() if self.target_date else None,
            "tags": self.tags,
            "tools_required": self.tools_required,
            "materials": self.materials,
            "budget": self.budget,
            "actual_cost": self.actual_cost,
            "build_logs": [log.to_dict() for log in self.build_logs],
            "links": self.links,
            "collaborators": self.collaborators,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Project":
        data = data.copy()
        data["status"] = ProjectStatus(data["status"])
        data["start_date"] = date.fromisoformat(data["start_date"])
        if data.get("target_date"):
            data["target_date"] = date.fromisoformat(data["target_date"])
        data["build_logs"] = [BuildLog.from_dict(l) for l in data.get("build_logs", [])]
        return cls(**data)


class MakerLogAgent:
    """
    Agent for tracking maker projects, tools, and build logs.

    Manages a workshop inventory, project timelines, and build
    documentation. Integrates with PLATO for persistent memory.

    Example:
        agent = MakerLogAgent()
        agent.register_tool("Soldering Iron", ToolCategory.Electronic)
        project = agent.create_project("LED Cube", budget=50.0)
        agent.add_build_log("LED Cube", "Soldered LED matrix")
        inventory = agent.get_tools_needing_maintenance()
    """

    def __init__(self, Plato_URL: str = "http://localhost:8847"):
        self.plato_url = Plato_URL
        self.projects: list[Project] = []
        self.tools: list[Tool] = []

    def register_tool(
        self,
        name: str,
        category: ToolCategory,
        description: str = "",
        location: str = "",
        condition: float = 1.0,
        maintenance_due: Optional[date] = None,
        consumable: bool = False,
        notes: str = "",
        acquired_date: Optional[date] = None,
    ) -> Tool:
        """
        Add a tool to the workshop inventory.

        Args:
            name: Tool name
            category: Tool category
            description: What it does
            location: Storage location
            condition: Current condition (0.0-1.0)
            maintenance_due: Next maintenance date
            consumable: Is it a consumable item
            notes: Additional notes
            acquired_date: When the tool was acquired

        Returns:
            The created Tool
        """
        tool = Tool(
            name=name,
            category=category,
            description=description,
            location=location,
            condition=condition,
            maintenance_due=maintenance_due,
            consumable=consumable,
            notes=notes,
            acquired_date=acquired_date,
        )
        self.tools.append(tool)
        return tool

    def get_tools_needing_maintenance(self) -> list[Tool]:
        """Return all tools with overdue or due-today maintenance."""
        return [t for t in self.tools if t.needs_maintenance()]

    def get_tools_by_category(self, category: ToolCategory) -> list[Tool]:
        """Return tools in a specific category."""
        return [t for t in self.tools if t.category == category]

    def create_project(
        self,
        name: str,
        description: str = "",
        status: ProjectStatus = ProjectStatus.Idea,
        start_date: Optional[date] = None,
        target_date: Optional[date] = None,
        tags: Optional[list[str]] = None,
        tools_required: Optional[list[str]] = None,
        materials: Optional[list[str]] = None,
        budget: float = 0.0,
        links: Optional[list[str]] = None,
        collaborators: Optional[list[str]] = None,
        notes: str = "",
    ) -> Project:
        """
        Create a new maker project.

        Args:
            name: Project name
            description: What it does
            status: Starting status
            start_date: When it started (defaults to today)
            target_date: Target completion date
            tags: Categorization tags
            tools_required: Tools needed
            materials: Materials list
            budget: Budget in USD
            links: Related URLs
            collaborators: Maker names
            notes: General notes

        Returns:
            The created Project
        """
        project = Project(
            name=name,
            description=description,
            status=status,
            start_date=start_date or date.today(),
            target_date=target_date,
            tags=tags or [],
            tools_required=tools_required or [],
            materials=materials or [],
            budget=budget,
            links=links or [],
            collaborators=collaborators or [],
            notes=notes,
        )
        self.projects.append(project)
        return project

    def find_project(self, name: str) -> Optional[Project]:
        """Find a project by name (exact match)."""
        for p in self.projects:
            if p.name == name:
                return p
        return None

    def add_build_log(
        self,
        project_name: str,
        title: str,
        description: str = "",
        status: BuildStatus = BuildStatus.Planned,
        duration_minutes: Optional[int] = None,
        materials_used: Optional[list[str]] = None,
        tools_used: Optional[list[str]] = None,
        problems: str = "",
        solutions: str = "",
        attachments: Optional[list[str]] = None,
    ) -> Optional[BuildLog]:
        """
        Add a build log entry to a project.

        Args:
            project_name: Name of the project
            title: Brief title for this step
            description: What was done
            status: Status of this step
            duration_minutes: Time spent
            materials_used: Materials consumed
            tools_used: Tools used in this step
            problems: Issues encountered
            solutions: How they were solved
            attachments: Photos/schematics URLs

        Returns:
            The created BuildLog, or None if project not found
        """
        project = self.find_project(project_name)
        if project is None:
            return None

        log = BuildLog(
            status=status,
            title=title,
            description=description,
            duration_minutes=duration_minutes,
            materials_used=materials_used or [],
            tools_used=tools_used or [],
            problems=problems,
            solutions=solutions,
            attachments=attachments or [],
        )
        project.add_build_log(log)
        return log

    def get_projects_by_status(self, status: ProjectStatus) -> list[Project]:
        """Return projects filtered by status."""
        return [p for p in self.projects if p.status == status]

    def get_projects_by_tag(self, tag: str) -> list[Project]:
        """Return projects with a given tag."""
        return [p for p in self.projects if tag in p.tags]

    def get_active_projects(self) -> list[Project]:
        """Return projects that are in progress."""
        return self.get_projects_by_status(ProjectStatus.InProgress)

    def get_statistics(self) -> dict:
        """
        Compute overall maker statistics.

        Returns:
            Dictionary with project counts, tool inventory, budget summaries
        """
        total_cost = sum(p.actual_cost for p in self.projects)
        total_budget = sum(p.budget for p in self.projects)

        status_counts = {}
        for p in self.projects:
            status_counts[p.status.value] = status_counts.get(p.status.value, 0) + 1

        total_logs = sum(len(p.build_logs) for p in self.projects)
        total_steps = sum(p.completed_steps for p in self.projects)
        failed_steps = sum(p.failed_steps for p in self.projects)

        category_counts = {}
        for t in self.tools:
            category_counts[t.category.value] = category_counts.get(t.category.value, 0) + 1

        return {
            "total_projects": len(self.projects),
            "status_distribution": status_counts,
            "total_budget": total_budget,
            "total_actual_cost": total_cost,
            "budget_utilization": round(total_cost / total_budget, 3) if total_budget > 0 else 0.0,
            "total_build_logs": total_logs,
            "completed_steps": total_steps,
            "failed_steps": failed_steps,
            "tool_count": len(self.tools),
            "tools_by_category": category_counts,
            "tools_needing_maintenance": len(self.get_tools_needing_maintenance()),
        }

    def export_json(self) -> str:
        """Export all data as JSON."""
        data = {
            "version": __version__,
            "projects": [p.to_dict() for p in self.projects],
            "tools": [t.to_dict() for t in self.tools],
        }
        return json.dumps(data, indent=2, default=str)

    def import_json(self, json_str: str) -> None:
        """Import data from JSON string."""
        data = json.loads(json_str)
        self.projects = [Project.from_dict(p) for p in data.get("projects", [])]
        self.tools = [Tool.from_dict(t) for t in data.get("tools", [])]
