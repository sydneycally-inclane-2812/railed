#!/usr/bin/env python3
"""Parse a saved Wikipedia HTML page of Sydney Trains stations and output a JSON
mapping of station name -> list of service codes like ["T1","T2"].

Usage:
    python parse_stations.py \
        --input ".\\.temp\\List of Sydney Trains railway stations - Wikipedia.htm" \
        --output stations.json
"""
from pathlib import Path
import re
import json
import argparse

from bs4 import BeautifulSoup

T_CODE_RE = re.compile(r"\bT\d+\b")


def parse_table(html: str):
    soup = BeautifulSoup(html, "html.parser")
    # Prefer the first wikitable sortable
    table = soup.find("table", class_=lambda c: c and "wikitable" in c)
    if table is None:
        raise SystemExit("No table with class 'wikitable' found in the HTML")

    stations = {}
    previous_services = None

    for tr in table.find_all("tr"):
        # skip header rows that just contain th headings (but rows with scope=row are data rows)
        # Find station name in a <th scope="row"> or the first <th>
        th = tr.find("th", scope="row") or tr.find("th")
        if th is None:
            continue
        # station name is usually the anchor text inside the th
        a = th.find("a")
        station = a.get_text(strip=True) if a else th.get_text(strip=True)
        if not station:
            continue

        # Find T codes in the current row (could be in <span class="tmp-color"> or just text)
        row_text = tr.get_text(separator=" ", strip=True)
        services = T_CODE_RE.findall(row_text)

        # If not found, try more targeted search for spans (some templates might render differently)
        if not services:
            spans = tr.find_all("span", class_=lambda c: c and "tmp-color" in c)
            for sp in spans:
                services.extend(T_CODE_RE.findall(sp.get_text(" ", strip=True)))

        # Deduplicate while preserving order
        seen = set()
        services_unique = []
        for s in services:
            if s not in seen:
                seen.add(s)
                services_unique.append(s)

        if not services_unique:
            # inherit from previous row when the services cell had a rowspan
            services_unique = previous_services if previous_services else []
        else:
            previous_services = services_unique

        stations[station] = services_unique

    return stations


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", "-i", type=Path,
                   default=Path(r".\.temp\List of Sydney Trains railway stations - Wikipedia.htm"),
                   help="Path to the saved Wikipedia HTML file")
    p.add_argument("--output", "-o", type=Path, default=Path("stations.json"), help="Output JSON file")
    args = p.parse_args()

    if not args.input.exists():
        raise SystemExit(f"Input file not found: {args.input}")

    html = args.input.read_text(encoding="utf-8")
    stations = parse_table(html)

    # Sort lists and keys for deterministic output
    stations_sorted = {k: sorted(v) for k, v in sorted(stations.items(), key=lambda kv: kv[0])}

    args.output.write_text(json.dumps(stations_sorted, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(stations_sorted)} stations to {args.output}")


if __name__ == "__main__":
    main()
