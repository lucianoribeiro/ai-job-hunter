"""Publication-date handling: only parse explicit source dates, never collection dates."""
from datetime import datetime, date, timezone

def publication_date(value):
    if not isinstance(value,str) or not value.strip():
        return None
    raw=value.strip()
    try:
        parsed=datetime.fromisoformat(raw.replace("Z","+00:00"))
        day=parsed.date()
    except ValueError:
        try: day=date.fromisoformat(raw)
        except ValueError:return None
    # Reject implausible dates, never convert today's fetch time into publication date.
    if day.year < 2000 or day > datetime.now(timezone.utc).date():return None
    return day.isoformat()

def display_date(value):
    normalized=publication_date(value)
    return date.fromisoformat(normalized).strftime("%d/%m/%Y") if normalized else "Data não informada"
