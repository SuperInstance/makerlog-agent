#!/usr/bin/env python3
"""
makerlog-agent — AI-powered maker logging for project tracking and build streaks
Log commits, deploys, and milestones. Integrates with the PLATO fleet for maker intelligence.
"""

import json, time, hashlib
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Milestone:
    id: str
    project: str
    action: str  # commit, deploy, build, test, design
    description: str
    timestamp: float
    tags: List[str] = field(default_factory=list)
    duration_minutes: Optional[float] = None

@dataclass
class Project:
    name: str
    created: float
    milestones: List[Milestone] = field(default_factory=list)
    streak_days: int = 0
    last_active: Optional[float] = None
    status: str = "active"

class MakerLogAgent:
    def __init__(self, agent_name: str = "makerlog-agent", plato_url: str = "http://147.224.38.131:8847"):
        self.name = agent_name
        self.plato_url = plato_url.rstrip("/")
        self.projects: Dict[str, Project] = {}
        self.all_milestones: List[Milestone] = []
    
    def start_project(self, name: str) -> Project:
        """Start tracking a new project."""
        if name not in self.projects:
            self.projects[name] = Project(name=name, created=time.time())
        return self.projects[name]
    
    def log_milestone(self, project: str, action: str, description: str, 
                      tags: Optional[List[str]] = None, duration: Optional[float] = None):
        """Log a milestone for a project."""
        if project not in self.projects:
            self.start_project(project)
        
        ms_id = hashlib.md5(f"{project}:{action}:{description}:{time.time()}".encode()).hexdigest()[:12]
        milestone = Milestone(
            id=ms_id,
            project=project,
            action=action,
            description=description,
            timestamp=time.time(),
            tags=tags or [],
            duration_minutes=duration
        )
        
        self.projects[project].milestones.append(milestone)
        self.all_milestones.append(milestone)
        self.projects[project].last_active = time.time()
        self._update_streak(project)
        
        # Submit to PLATO
        self._submit_tile(
            question=f"What happened in project {project}?",
            answer=f"{action}: {description} (streak: {self.projects[project].streak_days} days)"
        )
        return milestone
    
    def _update_streak(self, project: str):
        """Calculate consecutive days with activity."""
        proj = self.projects[project]
        if not proj.milestones:
            return
        
        # Get unique days with activity
        days = set()
        for m in proj.milestones:
            days.add(int(m.timestamp // 86400))
        
        sorted_days = sorted(days, reverse=True)
        streak = 0
        today = int(time.time() // 86400)
        for i, day in enumerate(sorted_days):
            if day == today - i:
                streak += 1
            else:
                break
        proj.streak_days = streak
    
    def get_project_summary(self, project: str) -> Dict:
        """Summary of a project's activity."""
        if project not in self.projects:
            return {"error": f"Project '{project}' not found"}
        
        proj = self.projects[project]
        actions = {}
        for m in proj.milestones:
            actions[m.action] = actions.get(m.action, 0) + 1
        
        total_duration = sum(m.duration_minutes or 0 for m in proj.milestones)
        
        return {
            "project": project,
            "milestones": len(proj.milestones),
            "streak_days": proj.streak_days,
            "actions_breakdown": actions,
            "total_hours": round(total_duration / 60, 1),
            "last_active": datetime.fromtimestamp(proj.last_active).isoformat() if proj.last_active else None,
            "status": proj.status
        }
    
    def get_fleet_intelligence(self) -> Dict:
        """Aggregate intelligence across all projects."""
        all_actions = {}
        total_hours = 0
        for proj in self.projects.values():
            for m in proj.milestones:
                all_actions[m.action] = all_actions.get(m.action, 0) + 1
                total_hours += (m.duration_minutes or 0) / 60
        
        top_projects = sorted(self.projects.values(), 
                             key=lambda p: len(p.milestones), reverse=True)[:5]
        
        return {
            "active_projects": len([p for p in self.projects.values() if p.status == "active"]),
            "total_milestones": len(self.all_milestones),
            "total_hours": round(total_hours, 1),
            "action_distribution": all_actions,
            "top_projects": [p.name for p in top_projects],
            "fleet_avg_streak": round(sum(p.streak_days for p in self.projects.values()) / len(self.projects), 1) if self.projects else 0
        }
    
    def _submit_tile(self, question: str, answer: str):
        payload = json.dumps({
            "question": question,
            "answer": answer,
            "agent": self.name,
            "room": "makerlog"
        }).encode()
        try:
            import urllib.request
            req = urllib.request.Request(f"{self.plato_url}/submit", data=payload,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=5) as r:
                pass
        except Exception:
            pass

def demo():
    agent = MakerLogAgent()
    
    # Project 1: Building a boat
    agent.log_milestone("boat-v1", "design", "Drafted hull plans for 12ft skiff", ["design", "boat"], 120)
    agent.log_milestone("boat-v1", "build", "Cut plywood panels for hull", ["build", "wood"], 240)
    agent.log_milestone("boat-v1", "commit", "Pushed hull CAD files to repo", ["cad", "git"], 30)
    agent.log_milestone("boat-v1", "test", "Dry-fit panels, adjustments needed", ["test"], 60)
    
    # Project 2: PLATO agent
    agent.log_milestone("plato-agent", "commit", "Added tile search functionality", ["code", "plato"], 90)
    agent.log_milestone("plato-agent", "deploy", "Deployed to Cloudflare Workers", ["deploy", "edge"], 15)
    agent.log_milestone("plato-agent", "design", "Architecture diagram for v2", ["design"], 45)
    
    print("=== Project: boat-v1 ===")
    print(agent.get_project_summary("boat-v1"))
    
    print("\n=== Fleet Intelligence ===")
    intel = agent.get_fleet_intelligence()
    print(f"Active projects: {intel['active_projects']}")
    print(f"Total milestones: {intel['total_milestones']}")
    print(f"Total hours: {intel['total_hours']}")
    print(f"Action distribution: {intel['action_distribution']}")
    print(f"Top projects: {intel['top_projects']}")

if __name__ == "__main__":
    demo()
