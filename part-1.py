"""
=========================================

Requirements:
    pip install pdfplumber
"""

import os
import re
import csv
import argparse
import pdfplumber

# --------- Column order in output CSV ---------
FIELDNAMES = [
    "route_id",          # e.g. FR-01
    "route_short_name",  # same as route_id
    "route_long_name",   # e.g. Khana Pul to NUST
    "direction",         # Forward / Backward
    "headway_minutes",   # average headway in minutes (integer)
    "total_trips",       # total trips declared in PDF
    "trip_id",           # e.g. 176064-0
    "trip_start_time",   # HH:MM:SS
    "stop_order",        # 1-based sequence within a trip
    "stop_name",         # e.g. NUST Metro Station
    "arrival_time",      # HH:MM:SS
    "departure_time",    # HH:MM:SS
]


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract all text from a PDF file using pdfplumber."""
    text_parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)
    return "\n".join(text_parts)


def parse_headway(raw: str) -> str:
    """Convert headway string like '10' or '00:20:00' to plain minutes string."""
    raw = raw.strip()
    # HH:MM:SS format
    hms = re.match(r'^(\d+):(\d+):(\d+)$', raw)
    if hms:
        h, m, s = int(hms.group(1)), int(hms.group(2)), int(hms.group(3))
        return str(h * 60 + m + (1 if s >= 30 else 0))
    # plain number
    if raw.isdigit():
        return raw
    return raw


def parse_pdf_text(text: str, filename: str) -> list[dict]:
    """
    Parse the extracted text of one CDA route PDF into a list of row dicts.
    Each row = one stop event within one trip.
    """
    rows = []
    lines = [l.strip() for l in text.splitlines()]

    # ── Read header metadata ─────────────────────────────────────────────────
    meta = {
        "route_id": "",
        "route_long_name": "",
        "direction": "",
        "headway_minutes": "",
        "total_trips": "",
    }

    for line in lines:
        if line.startswith("Short Name"):
            meta["route_id"] = re.sub(r'^Short Name\s*', '', line).strip()
        elif line.startswith("Long Name"):
            meta["route_long_name"] = re.sub(r'^Long Name\s*', '', line).strip()
        elif line.startswith("Direction"):
            meta["direction"] = re.sub(r'^Direction\s*', '', line).strip()
        elif line.startswith("Total Trips"):
            meta["total_trips"] = re.sub(r'^Total Trips\s*', '', line).strip()
        elif line.startswith("Average Headway"):
            raw_hw = re.sub(r'^Average Headway\s*\(min\)\s*', '', line).strip()
            meta["headway_minutes"] = parse_headway(raw_hw)

    # Fallback: infer route_id and direction from filename
    # Expected filename pattern: FR-01_Forward.pdf or FRG-1_Backward.pdf
    if not meta["route_id"] or not meta["direction"]:
        fname = os.path.splitext(os.path.basename(filename))[0]  # e.g. FR-01_Forward
        parts = fname.rsplit("_", 1)
        if len(parts) == 2:
            if not meta["route_id"]:
                meta["route_id"] = parts[0]
            if not meta["direction"]:
                meta["direction"] = parts[1]

    # ── Parse trips and stops ────────────────────────────────────────────────
    # Trip header pattern: "<trip_id> <HH:MM:SS>"  e.g. "176064-0 06:00:00"
    TRIP_RE = re.compile(r'^([\w\-]+)\s+(\d{2}:\d{2}:\d{2})$')
    # Time suffix pattern at end of a stop line
    STOP_RE = re.compile(r'^(.+?)\s+(\d{2}:\d{2}:\d{2})\s+(\d{2}:\d{2}:\d{2})$')

    SKIP_PREFIXES = (
        "Field", "Route ID", "Short Name", "Long Name",
        "Direction", "Total Trips", "Average Headway",
        "Trip ID", "Start Time", "stop_name",
    )

    current_trip_id = None
    current_start_time = None
    in_stops = False
    stop_order = 0

    for line in lines:
        if not line:
            continue

        # Skip metadata / header lines
        if any(line.startswith(p) for p in SKIP_PREFIXES):
            if line.startswith("stop_name"):
                in_stops = True
            else:
                in_stops = False
            continue

        # Detect trip header
        m_trip = TRIP_RE.match(line)
        if m_trip:
            current_trip_id = m_trip.group(1)
            current_start_time = m_trip.group(2)
            stop_order = 0
            in_stops = False
            continue

        # Parse stop line
        if in_stops and current_trip_id:
            m_stop = STOP_RE.match(line)
            if m_stop:
                stop_name = m_stop.group(1).strip()
                arrival = m_stop.group(2)
                departure = m_stop.group(3)
                stop_order += 1
                rows.append({
                    "route_id": meta["route_id"],
                    "route_short_name": meta["route_id"],
                    "route_long_name": meta["route_long_name"],
                    "direction": meta["direction"],
                    "headway_minutes": meta["headway_minutes"],
                    "total_trips": meta["total_trips"],
                    "trip_id": current_trip_id,
                    "trip_start_time": current_start_time,
                    "stop_order": stop_order,
                    "stop_name": stop_name,
                    "arrival_time": arrival,
                    "departure_time": departure,
                })

    return rows


def process_folder(folder: str, output_csv: str) -> None:
    """Walk folder, parse every PDF, write combined routes.csv."""
    pdf_files = sorted([
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.lower().endswith(".pdf")
    ])

    if not pdf_files:
        print(f"No PDF files found in '{folder}'")
        return

    print(f" Found {len(pdf_files)} PDF(s) in '{folder}'")
    print("-" * 60)

    all_rows = []
    ok, failed = 0, 0

    for pdf_path in pdf_files:
        fname = os.path.basename(pdf_path)
        try:
            text = extract_text_from_pdf(pdf_path)
            rows = parse_pdf_text(text, pdf_path)
            if rows:
                trips = len(set(r["trip_id"] for r in rows))
                stops = len(set(r["stop_name"] for r in rows))
                route = rows[0]["route_id"]
                direction = rows[0]["direction"]
                print(f"  ✓  {fname:<35} | route={route:<8} dir={direction:<10} "
                      f"trips={trips:>3}  unique_stops={stops:>3}  rows={len(rows):>5}")
                all_rows.extend(rows)
                ok += 1
            else:
                print(f"  ⚠  {fname:<35} | parsed 0 rows — check PDF layout")
                failed += 1
        except Exception as e:
            print(f"  ✗  {fname:<35} | ERROR: {e}")
            failed += 1

    print("-" * 60)

    if not all_rows:
        print("No data extracted. CSV not written.")
        return

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(all_rows)

    # Summary stats
    routes = sorted(set(r["route_id"] for r in all_rows))
    total_trips = len(set((r["route_id"], r["direction"], r["trip_id"]) for r in all_rows))

    print(f"\n✅  Done!")
    print(f"   PDFs processed : {ok} succeeded, {failed} failed")
    print(f"   Routes found   : {len(routes)}  →  {', '.join(routes)}")
    print(f"   Total trips    : {total_trips}")
    print(f"   Total rows     : {len(all_rows)}")
    print(f"   Output CSV     : {output_csv}")


def main():
    parser = argparse.ArgumentParser(
        description="Extract CDA Islamabad bus route data from PDFs into a CSV."
    )
    parser.add_argument(
        "--folder", "-f",
        default="cda_pdfs",
        help="Path to folder containing the downloaded CDA route PDFs (default: cda_pdfs/)"
    )
    parser.add_argument(
        "--output", "-o",
        default="routes.csv",
        help="Output CSV file path (default: routes.csv)"
    )
    args = parser.parse_args()

    if not os.path.isdir(args.folder):
        print(f" Folder not found: '{args.folder}'")
        print(f" Create it and place your PDFs inside, then re-run.")
        return

    process_folder(args.folder, args.output)


if __name__ == "__main__":
    main()