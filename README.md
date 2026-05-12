# CDA Bus Route Analytics Dashboard

A process mining and analytics pipeline for the Capital Development Authority (CDA) Islamabad public bus network. The project extracts timetable data from PDF schedules, converts it into a standard process mining event log, and visualizes it through an interactive Streamlit dashboard.

---

## Project Structure

```
.
├── part-1.py                  # Task 1  — PDF extraction → routes.csv
├── part-2.py                  # Task 2  — routes.csv → XES event log
├── task2_pm4py.py             # Task 2  — PM4Py validation & DFG/process tree export
├── application_3_4_5_6.py    # Tasks 3–6 — Streamlit analytics dashboard
├── routes.csv                 # Generated: structured stop-time data
├── routes_event_log.xes       # Generated: XES event log for process mining tools
└── requirements.txt           # Python dependencies
```

---

## Pipeline Overview

```
CDA Route PDFs
      │
      ▼ part-1.py
  routes.csv
      │
      ▼ part-2.py
routes_event_log.xes
      │
      ├──▶ task2_pm4py.py   (offline PM4Py analysis)
      │
      └──▶ application_3_4_5_6.py  (live Streamlit dashboard)
```

---

## Task Breakdown

### Task 1 — PDF Extraction (`part-1.py`)

Reads every CDA route PDF from a local folder and writes a flat CSV file.

**How it works:**
- Uses `pdfplumber` to extract raw text from each PDF page.
- Parses route metadata (short name, long name, direction, headway, total trips) from header lines.
- Falls back to the filename (e.g. `FR-01_Forward.pdf`) when metadata fields are missing.
- Detects trip headers with the pattern `<trip_id> HH:MM:SS` and stop rows with the pattern `<stop_name> HH:MM:SS HH:MM:SS`.
- Headways expressed as `HH:MM:SS` are converted to plain minutes.

**Output columns in `routes.csv`:**

| Column | Description |
|---|---|
| `route_id` | Route code, e.g. `FR-01` |
| `route_short_name` | Same as `route_id` |
| `route_long_name` | Human-readable name, e.g. `Khana Pul to NUST` |
| `direction` | `Forward` or `Backward` |
| `headway_minutes` | Average scheduled headway (integer minutes) |
| `total_trips` | Total trips declared in the PDF |
| `trip_id` | Unique trip identifier, e.g. `176064-0` |
| `trip_start_time` | Scheduled start time `HH:MM:SS` |
| `stop_order` | 1-based stop sequence within the trip |
| `stop_name` | Bus stop name |
| `arrival_time` | Scheduled arrival `HH:MM:SS` |
| `departure_time` | Scheduled departure `HH:MM:SS` |

**Usage:**
```bash
python part-1.py --folder cda_pdfs/ --output routes.csv
```

---

### Task 2 — XES Event Log Construction (`part-2.py`)

Converts `routes.csv` into a standards-compliant XES process mining event log.

**XES mapping:**

| XES Concept | Source field | Notes |
|---|---|---|
| Case (Trace) | `trip_id` | One trace per bus trip |
| Activity | `stop_name` | Each stop visit is one event |
| `time:timestamp` | `arrival_time` | ISO 8601 UTC, anchored to 2024-01-15 |
| `departure:timestamp` | `departure_time` | Extra event attribute |
| Trace attributes | `route_id`, `route_long_name`, `direction`, `headway_minutes`, `trip_start_time` | Case-level metadata |

Times with hours ≥ 24 (overnight trips) are handled correctly via `timedelta` arithmetic.

**Usage:**
```bash
python part-2.py
# Reads: routes.csv
# Writes: routes_event_log.xes
```

---

### Task 2 — PM4Py Validation (`task2_pm4py.py`)

Imports the generated XES file and runs offline process mining analysis.

- **Statistics:** trace count, event count, unique activities, average/min/max trace length, top start and end activities, trips per route.
- **Process Model Discovery:** applies the Inductive Miner algorithm and saves a process tree as `pm4py_output/process_tree_full_log.png`.
- **DFG per Route:** discovers a Directly-Follows Graph for each route and saves frequency-annotated PNG images to `pm4py_output/dfg_<route_id>.png`.

**Usage:**
```bash
python task2_pm4py.py
# Reads: routes_event_log.xes
# Writes: pm4py_output/
```

---

### Tasks 3–6 — Streamlit Dashboard (`application_3_4_5_6.py`)

An interactive dark-themed web application with six tabs.

**Run:**
```bash
streamlit run application_3_4_5_6.py
```

Requires `routes.csv` in the working directory and a `.env` file with a `GITHUB_TOKEN` for the AI chatbot tab.

#### Tab 1 — 🗺️ Process Map (Task 3)
An interactive PyVis force-directed graph of the transit network. Each node is a bus stop; each directed edge shows the average travel time between consecutive stops. **Red edges** are bottleneck transitions (above the 75th-percentile threshold). A side panel lists the top-10 most-frequent transitions and the top-5 bottleneck edges for the selected route.

#### Tab 2 — Throughput Analysis 
Trip-level throughput time statistics: average, median, minimum, maximum, and standard deviation of end-to-end trip duration. Adapts automatically when all trips on a route have identical scheduled durations (fixed-schedule pattern).

#### Tab 3 — Bottleneck Analysis 
Detailed bottleneck report. Bottlenecks are stop-to-stop transitions whose average duration exceeds the **75th percentile** of all transitions. Displays the count of bottlenecks, their share of total transitions, the top 3 slowest transitions, a full sortable table, and a CSV download option.

#### Tab 4 — Trip Planner 
Point-to-point journey planner. Select an origin and destination stop; the app runs Dijkstra's shortest-path algorithm on a weighted directed graph (travel edges + 6-minute transfer edges at interchange stops) and displays the optimal itinerary with step-by-step instructions and an interactive PyVis route map.

#### Tab 5 — AI Chatbot 
A conversational assistant powered by **GPT-4o-mini** (via the GitHub Models API). The chatbot is grounded in a JSON knowledge base built from the live route data — routes, stops, departure times, and inter-stop travel times — so it can answer natural-language questions about routes, connections, and journey planning. Configure your `GITHUB_TOKEN` in a `.env` file to enable this tab.

#### Tab 6 — Personal Routes 
Shortest-path lookup for five pre-defined team members, each mapped from their home area's nearest bus stop to FAST University. Displays estimated travel time and a hierarchical PyVis itinerary map.

---

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure the AI chatbot (optional)
Create a `.env` file in the project root:
```
GITHUB_TOKEN=your_github_personal_access_token
```

### 3. Run the full pipeline
```bash
# Step 1: extract PDFs to CSV (skip if routes.csv already exists)
python part-1.py --folder cda_pdfs/

# Step 2: build the XES event log
python part-2.py

# Step 3 (optional): run offline PM4Py analysis
python task2_pm4py.py

# Step 4: launch the dashboard
streamlit run application_3_4_5_6.py
```

---

## Dependencies

| Package | Purpose |
|---|---|
| `pdfplumber` | PDF text extraction |
| `pm4py` | XES event log construction, process mining |
| `pandas` | Data manipulation |
| `streamlit` | Interactive web dashboard |
| `pyvis` | Interactive network graph rendering |
| `networkx` | Graph algorithms (shortest path) |
| `openai` | GPT-4o-mini chatbot via GitHub Models API |
| `python-dotenv` | `.env` file loading |

---

## Data Notes

- **Reference date:** All timestamps in the XES log are anchored to `2024-01-15` in UTC. Times with `HH ≥ 24` roll over to the next calendar day correctly.
- **Bottleneck threshold:** The 75th percentile of average inter-stop transition durations, computed dynamically per the selected route filter.
- **Transfer weight:** 360 seconds (6 minutes) is assumed for any stop-to-stop transfer between routes at the same physical stop.
