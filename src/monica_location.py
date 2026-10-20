"""Location classification independent of candidate skill score."""
from src.monica_match import norm, REGIONAL

FOREIGN = ("vietnam","india","hungary","angola","portugal","united states","japan",
           "germany","france","united kingdom","canada","australia","philippines")
BRAZIL = ("brasil","brazil")
GLOBAL = ("worldwide","anywhere","global","latam")
def location_category(job):
    loc = norm(job.get("location"))
    title = norm(job.get("title"))
    desc = norm(job.get("description"))
    if any(city in loc for city in REGIONAL):
        return "regional"
    remote = any(token in loc for token in ("remote","remoto","home office"))
    if remote and any(token in loc for token in BRAZIL):
        return "remote_br"
    if remote and any(token in loc for token in GLOBAL) and not any(country in loc for country in FOREIGN):
        return "remote_review"
    if any(country in loc for country in FOREIGN):
        return "out_of_scope"
    return "unknown"
