"""
Task 2 - Trace Log Construction

Converts routes.csv into a XES-compliant process mining event log.
XES Mapping:
  Case (Trace)  -> trip_id          (one bus trip per trace)
  Activity      -> stop_name         (bus stop visited = activity)
  Timestamp     -> arrival_time      (ISO 8601 UTC, time:timestamp)
  Extra attrs   -> departure_time, stop_order, route_id, direction
Output: routes_event_log.xes

"""

import pandas as pd
from pm4py.objects.log.obj import EventLog, Trace, Event
from pm4py.objects.log.exporter.xes import exporter as xes_exporter
from datetime import datetime, date, timedelta, timezone

#     CONFIG  
INPUT_CSV  = "routes.csv"
OUTPUT_XES = "routes_event_log.xes"
BASE_DATE  = date(2024, 1, 15)   # reference calendar date for time anchoring
TZ         = timezone.utc


#     HELPER  
def parse_time(t_str: str, base_date: date = BASE_DATE) -> datetime:
    """
    Parse a HH:MM:SS string (hours may exceed 24 for overnight trips)
    and return a timezone-aware UTC datetime anchored to base_date.
    """
    h, m, s = (int(x) for x in t_str.strip().split(":"))
    dt = datetime(base_date.year, base_date.month, base_date.day, tzinfo=TZ)
    dt += timedelta(hours=h, minutes=m, seconds=s)
    return dt


#   STEP 1 - LOAD DATA  
df = pd.read_csv(INPUT_CSV)
print(f"[1] Loaded {len(df):,} rows | {df['trip_id'].nunique()} trips | "
      f"{df['route_id'].nunique()} routes")


#    STEP 2 - CONSTRUCT XES EVENT LOG  
log = EventLog()

# Log-level metadata (required by XES standard IEEE 1849-2016)
log.attributes["concept:name"] = "Islamabad BRT Bus Route Event Log"
log.attributes["description"]  = (
    "Each trace represents a single bus trip; each event represents "
    "a stop visit (arrival/departure)."
)
log.attributes["xes.version"]  = "1.0"
log.attributes["xes.features"] = ""

# Build one Trace per trip_id, one Event per stop visit
for trip_id, grp in df.groupby("trip_id", sort=False):
    grp = grp.sort_values("stop_order")

    trace = Trace()
    first = grp.iloc[0]

    # Trace-level attributes (case metadata)
    trace.attributes["concept:name"]    = str(trip_id)
    trace.attributes["route:id"]        = str(first["route_id"])
    trace.attributes["route:name"]      = str(first["route_long_name"])
    trace.attributes["route:direction"] = str(first["direction"])
    trace.attributes["route:headway"]   = int(first["headway_minutes"])
    trace.attributes["trip:start_time"] = str(first["trip_start_time"])

    # Event-level attributes (one event per stop)
    for _, row in grp.iterrows():
        evt = Event()
        evt["concept:name"]         = str(row["stop_name"])           # activity
        evt["time:timestamp"]       = parse_time(row["arrival_time"]) # ISO 8601 UTC
        evt["departure:timestamp"]  = parse_time(row["departure_time"])
        evt["stop:order"]           = int(row["stop_order"])
        evt["route:id"]             = str(row["route_id"])
        evt["route:direction"]      = str(row["direction"])
        evt["lifecycle:transition"] = "complete"
        trace.append(evt)

    log.append(trace)

n_traces = len(log)
n_events = sum(len(t) for t in log)
print(f"[2] Event log built: {n_traces} traces, {n_events:,} events")


#    STEP 3 - EXPORT TO XES
xes_exporter.apply(log, OUTPUT_XES)
print(f"[3] XES file written: {OUTPUT_XES}")
