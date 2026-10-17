"""Configurable, remote-first professional profiles; no personal details in source."""
from __future__ import annotations
import math
from dataclasses import dataclass, field

@dataclass
class CareerProfile:
    name: str
    roles: list[str]
    industries: list[str] = field(default_factory=list)
    exclude_skills: list[str] = field(default_factory=list)
    origin_city: str = "Nova Odessa, SP"
    origin_coordinates: tuple[float, float] | None = None
    max_commute_km: float = 50
    include_onsite: bool = True

def distance_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Haversine straight-line distance; not road distance or travel time."""
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    delta_lat, delta_lon = lat2-lat1, lon2-lon1
    h = math.sin(delta_lat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(delta_lon/2)**2
    return round(6371.0088 * 2 * math.asin(min(1,math.sqrt(h))), 1)

def evaluate(job: dict, profile: CareerProfile) -> dict:
    title = str(job.get("title", "")).lower()
    description = str(job.get("description", "")).lower()
    role_fit = any(role.lower() in title for role in profile.roles)
    non_it_industry = any(word.lower() in title + " " + description for word in profile.industries)
    if profile.exclude_skills and any(word.lower() in title for word in profile.exclude_skills):
        role_fit = False
    remote = bool(job.get("remote")) or "remote" in str(job.get("work_mode", "")).lower()
    location = job.get("coordinates")
    distance = distance_km(profile.origin_coordinates, tuple(location)) if (
        profile.origin_coordinates and isinstance(location, (tuple,list)) and len(location)==2
    ) else None
    eligible = remote or (profile.include_onsite and distance is not None and distance <= profile.max_commute_km)
    return {
        "role_match": role_fit, "industry_match": non_it_industry,
        "remote": remote, "distance_km_straight_line": distance,
        "location_status": "remote_check_country" if remote else (
            "within_radius" if eligible else "outside_radius" if distance is not None else "distance_unknown"
        ), "eligible_for_location_filter": eligible,
        "requires_human_review": True,
    }

MANUFACTURING_PM = CareerProfile(
    name="Gestão de projetos industriais",
    roles=["project manager","project coordinator","gerente de projetos",
           "coordenador de projetos","coordenadora de projetos",
           "industrial project manager","manufacturing project manager",
           "industrial project coordinator","manufacturing project coordinator"],
    industries=["manufacturing","industrial","manufatura","produção",
                "operations","operações","continuous improvement","melhoria contínua"],
    exclude_skills=["software engineer","developer","it project manager","technical project manager"],
)
