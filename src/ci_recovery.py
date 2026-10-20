"""Conservative CI diagnosis. Never edits product code or bypasses tests."""
import json
import re
import sys

def diagnose(log):
    if re.search(r"IndexError: list index out of range",log) and "manufacturingLeadershipAlert" in log:
        return {"kind":"obsolete_ui_assertion","action":"human_review","reason":"Test expects removed UI; verify requirement before editing test"}
    if re.search(r"(429|rate.limit|timed out|connection reset|503 Service Unavailable)",log,re.I):
        return {"kind":"transient","action":"retry_once","reason":"Potential infrastructure issue; retry must be bounded"}
    if re.search(r"(FAILED \(|SyntaxError:|ModuleNotFoundError:|AssertionError:)",log):
        return {"kind":"code_failure","action":"human_review","reason":"Code/test failure cannot be auto-fixed safely"}
    return {"kind":"unknown","action":"human_review","reason":"No safe automatic recovery identified"}

if __name__=="__main__":
    print(json.dumps(diagnose(sys.stdin.read())))
