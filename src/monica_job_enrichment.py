"""Bounded, public-ATS-only job-location enrichment with source evidence."""
import json
import re
from html.parser import HTMLParser
from urllib.request import Request, build_opener
from src.monica_verify import allowed, NoRedirect
from src.monica_match import norm, REGIONAL

class Page(HTMLParser):
    def __init__(self):
        super().__init__(); self.visible=[]; self.jsonld=[]; self.in_script=False; self.buffer=[]
    def handle_starttag(self,tag,attrs):
        if tag=="script":
            self.in_script=dict(attrs).get("type")=="application/ld+json";self.buffer=[]
    def handle_data(self,data):
        if self.in_script:self.buffer.append(data)
        else:self.visible.append(data)
    def handle_endtag(self,tag):
        if tag=="script":
            if self.in_script:self.jsonld.append("".join(self.buffer))
            self.in_script=False

def fetch(url):
    if not allowed(url):raise ValueError("Unsupported ATS hostname")
    req=Request(url,headers={"User-Agent":"AIJobHunter/1.0 public job metadata","Accept":"text/html"})
    with build_opener(NoRedirect()).open(req,timeout=12) as response:
        if response.headers.get_content_type()!="text/html":raise ValueError("Non HTML")
        return response.read(350_000).decode("utf-8","replace")

def job_postings(value):
    if isinstance(value,list):
        for x in value:yield from job_postings(x)
    if isinstance(value,dict):
        types=value.get("@type",[])
        if isinstance(types,str):types=[types]
        if "JobPosting" in types:yield value
        for key in ("@graph","mainEntity"):
            if key in value:yield from job_postings(value[key])

def enrich(job,getter=fetch):
    """Only explicit JobPosting locality, never employer address or speculative body text."""
    result=dict(job)
    result["location_evidence"]="unknown"
    url=str(result.get("url") or "")
    if not allowed(url):return result
    try:
        parser=Page();parser.feed(getter(url))
        for blob in parser.jsonld:
            try:data=json.loads(blob)
            except (ValueError,TypeError):continue
            for posting in job_postings(data):
                locs=posting.get("jobLocation") or []
                if isinstance(locs,dict):locs=[locs]
                places=[]
                for entry in locs:
                    address=entry.get("address") or {}
                    if not isinstance(address,dict):continue
                    city=str(address.get("addressLocality") or "")
                    region=str(address.get("addressRegion") or "")
                    country=str(address.get("addressCountry") or "")
                    if isinstance(address.get("addressCountry"),dict):
                        country=str(address["addressCountry"].get("name") or "")
                    if city:places.append(", ".join(x for x in (city,region,country) if x))
                if places:
                    result["location"]="; ".join(places)
                    result["location_evidence"]="JobPosting.jobLocation"
                    return result
                if posting.get("jobLocationType")=="TELECOMMUTE":
                    restrictions=posting.get("applicantLocationRequirements") or []
                    if isinstance(restrictions,dict):restrictions=[restrictions]
                    countries=[str(x.get("name") or "") for x in restrictions if isinstance(x,dict)]
                    if any(norm(x) in ("brazil","brasil") for x in countries):
                        result["location"]="Remote, Brazil"
                        result["location_evidence"]="JobPosting.applicantLocationRequirements"
                        return result
                    result["location_evidence"]="Remote, eligibility not confirmed"
        result["location_evidence"]="No explicit JobPosting location"
    except (OSError,ValueError,TimeoutError,UnicodeError):
        result["location_evidence"]="ATS unavailable"
    return result
