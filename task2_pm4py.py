"""
Task 2 - PM4Py Validation & Analysis

"""

import pm4py
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.statistics.start_activities.log import get as sa_get
from pm4py.statistics.end_activities.log import get as ea_get
from pm4py.algo.discovery.inductive import algorithm as inductive_miner
from pm4py.visualization.process_tree import visualizer as pt_visualizer
from pm4py.visualization.dfg import visualizer as dfg_visualizer
from pm4py.algo.discovery.dfg import algorithm as dfg_algorithm
import collections
import os

XES_FILE   = "routes_event_log.xes"
OUTPUT_DIR = "pm4py_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# STEP 1 - IMPORT XES FILE
print("  STEP 1 - Importing XES file into PM4Py")

log = xes_importer.apply(XES_FILE)
print(f"  File loaded : {XES_FILE}")
print(f"  Status      : SUCCESS\n")


# STEP 2 - TRACE & EVENT STATISTICS
print("  STEP 2 - Trace & Event Statistics")

n_traces    = len(log)
n_events    = sum(len(t) for t in log)
unique_acts = {e["concept:name"] for t in log for e in t}
lengths     = [len(t) for t in log]

print(f"  Number of traces (trips)  : {n_traces}")
print(f"  Number of events (stops)  : {n_events:,}")
print(f"  Unique activities (stops) : {len(unique_acts)}")
print(f"  Avg events per trace      : {n_events / n_traces:.1f}")
print(f"  Min trace length          : {min(lengths)}")
print(f"  Max trace length          : {max(lengths)}")

# Start activities
start_acts = sa_get.get_start_activities(log)
print(f"\n  Start activities (top 5):")
for act, cnt in sorted(start_acts.items(), key=lambda x: -x[1])[:5]:
    print(f"    {cnt:5d}  {act}")

# End activities
end_acts = ea_get.get_end_activities(log)
print(f"\n  End activities (top 5):")
for act, cnt in sorted(end_acts.items(), key=lambda x: -x[1])[:5]:
    print(f"    {cnt:5d}  {act}")

# Trips per route
routes = collections.Counter(t.attributes["route:id"] for t in log)
print(f"\n  Trips per route:")
for r, cnt in sorted(routes.items()):
    print(f"    {r:10s}  {cnt} trips")


# STEP 3 — PROCESS MODEL DISCOVERY (Inductive Miner -> Process Tree)
print("  STEP 3 - Process Model Discovery (Inductive Miner)")

# Discover process tree on the full log
tree = inductive_miner.apply(log)

# Render and save as PNG
gviz = pt_visualizer.apply(
    tree,
    parameters={pt_visualizer.Variants.WO_DECORATION.value.Parameters.FORMAT: "png"}
)
tree_path = os.path.join(OUTPUT_DIR, "process_tree_full_log.png")
pt_visualizer.save(gviz, tree_path)
print(f"  Process tree saved : {tree_path}")


# STEP 4 — DIRECTLY-FOLLOWS GRAPH (DFG) PER ROUTE
print("  STEP 4 - Directly-Follows Graph (DFG) Discovery per Route")

for route_id in sorted(routes):
    # Filter log to this route only
    filtered = pm4py.filter_trace_attribute_values(log, "route:id", [route_id])

    # Discover DFG
    dfg, start_acts_dfg, end_acts_dfg = pm4py.discover_dfg(filtered)

    nodes = len({k for pair in dfg for k in pair})
    print(f"  {route_id:8s}  nodes={nodes:3d}  edges={len(dfg):3d}  "
          f"start='{list(start_acts_dfg)[0]}'  "
          f"end='{list(end_acts_dfg)[0]}'")

    # Render DFG and save as PNG
    dfg_raw = dfg_algorithm.apply(filtered)
    gviz_dfg = dfg_visualizer.apply(
        dfg_raw,
        log=filtered,
        variant=dfg_visualizer.Variants.FREQUENCY,
        parameters={dfg_visualizer.Variants.FREQUENCY.value.Parameters.FORMAT: "png"}
    )
    dfg_path = os.path.join(OUTPUT_DIR, f"dfg_{route_id}.png")
    dfg_visualizer.save(gviz_dfg, dfg_path)

print(f"\n  DFG images saved to: {OUTPUT_DIR}/")

