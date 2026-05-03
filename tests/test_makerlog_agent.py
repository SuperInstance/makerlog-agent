"""
Tests for makerlog_agent.
"""

from datetime import date, datetime

import pytest

from makerlog_agent import (
    MakerLogAgent,
    Project,
    ProjectStatus,
    Tool,
    ToolCategory,
    BuildLog,
    BuildStatus,
)


class TestTool:
    def test_register_tool(self):
        agent = MakerLogAgent()
        tool = agent.register_tool(
            name="Drill",
            category=ToolCategory.PowerTool,
            location="Tool wall",
            condition=0.8,
        )
        assert tool.name == "Drill"
        assert tool.category == ToolCategory.PowerTool
        assert tool.condition == 0.8
        assert len(agent.tools) == 1

    def test_tool_condition_clamp(self):
        tool = Tool(name="Test", category=ToolCategory.HandTool)
        tool.update_condition(1.5)
        assert tool.condition == 1.0
        tool.update_condition(-0.5)
        assert tool.condition == 0.0

    def test_tool_needs_maintenance(self):
        agent = MakerLogAgent()
        agent.register_tool(
            name="Old Grinder",
            category=ToolCategory.PowerTool,
            maintenance_due=date.today(),
        )
        needs = agent.get_tools_needing_maintenance()
        assert len(needs) == 1
        assert needs[0].name == "Old Grinder"

    def test_tool_serialization(self):
        tool = Tool(
            name="Lathe",
            category=ToolCategory.Metalworking,
            location="Shop back",
            acquired_date=date(2023, 1, 1),
        )
        data = tool.to_dict()
        restored = Tool.from_dict(data)
        assert restored.name == tool.name
        assert restored.category == tool.category


class TestProject:
    def test_create_project(self):
        agent = MakerLogAgent()
        project = agent.create_project(
            name="Test Project",
            budget=100.0,
        )
        assert project.name == "Test Project"
        assert project.budget == 100.0
        assert project.status == ProjectStatus.Idea

    def test_find_project(self):
        agent = MakerLogAgent()
        agent.create_project("Alpha")
        agent.create_project("Beta")
        found = agent.find_project("Beta")
        assert found is not None
        assert found.name == "Beta"
        assert agent.find_project("Gamma") is None

    def test_project_build_logs(self):
        agent = MakerLogAgent()
        agent.create_project("Test")
        agent.add_build_log("Test", "Step 1", status=BuildStatus.Success)
        agent.add_build_log("Test", "Step 2", status=BuildStatus.Failed)

        project = agent.find_project("Test")
        assert project.completed_steps == 1
        assert project.failed_steps == 1

    def test_project_serialization(self):
        project = Project(
            name="JSON Test",
            description="Test",
            status=ProjectStatus.InProgress,
            budget=50.0,
        )
        data = project.to_dict()
        restored = Project.from_dict(data)
        assert restored.name == project.name
        assert restored.status == project.status


class TestBuildLogs:
    def test_add_build_log(self):
        agent = MakerLogAgent()
        agent.create_project("Build Test")
        log = agent.add_build_log(
            "Build Test",
            title="Assemble frame",
            description="Cut and join wood.",
            status=BuildStatus.InProgress,
            duration_minutes=90,
            materials_used=["2x4 lumber", "screws"],
            tools_used=["Saw", "Drill"],
        )
        assert log is not None
        assert log.title == "Assemble frame"
        assert log.duration_minutes == 90

    def test_add_build_log_project_not_found(self):
        agent = MakerLogAgent()
        log = agent.add_build_log("NonExistent", "Step 1")
        assert log is None


class TestStatistics:
    def test_statistics(self):
        agent = MakerLogAgent()
        agent.create_project("P1", budget=100.0, status=ProjectStatus.InProgress)
        agent.create_project("P2", budget=200.0, status=ProjectStatus.Completed)
        agent.register_tool("Solder", category=ToolCategory.Electronic)

        stats = agent.get_statistics()
        assert stats["total_projects"] == 2
        assert stats["status_distribution"]["in_progress"] == 1
        assert stats["total_budget"] == 300.0
        assert stats["tool_count"] == 1


class TestFiltering:
    def test_get_projects_by_status(self):
        agent = MakerLogAgent()
        agent.create_project("Idea1", status=ProjectStatus.Idea)
        agent.create_project("Active1", status=ProjectStatus.InProgress)
        agent.create_project("Active2", status=ProjectStatus.InProgress)
        agent.create_project("Done1", status=ProjectStatus.Completed)

        active = agent.get_active_projects()
        assert len(active) == 2

    def test_get_projects_by_tag(self):
        agent = MakerLogAgent()
        agent.create_project("T1", tags=["electronics"])
        agent.create_project("T2", tags=["woodworking"])
        agent.create_project("T3", tags=["electronics", "robotics"])

        tagged = agent.get_projects_by_tag("electronics")
        assert len(tagged) == 2


class TestExportImport:
    def test_export_import_json(self):
        agent = MakerLogAgent()
        agent.register_tool("Knife", category=ToolCategory.HandTool)
        agent.create_project("ExportTest", budget=75.0)

        exported = agent.export_json()
        agent2 = MakerLogAgent()
        agent2.import_json(exported)

        assert len(agent2.tools) == 1
        assert len(agent2.projects) == 1
        assert agent2.projects[0].name == "ExportTest"
