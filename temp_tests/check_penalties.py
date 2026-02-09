#!/usr/bin/env python3
"""Check penalties structure in interface HTML."""
import json
import re

with open("interface_volley.html", "r") as f:
    content = f.read()

# Le format est: <script id="solution-data" type="application/json">
match = re.search(r'<script id="solution-data" type="application/json">(.*?)</script>', content, re.DOTALL)
if match:
    print("Found solution data!")
    data = json.loads(match.group(1))
    matches = data.get("matchs", [])[:3]
    for m in matches:
        mid = m.get("match_id")
        pen = m.get("penalties")
        print(f"Match {mid}:")
        print(json.dumps(pen, indent=2))
        print()
else:
    print("Solution data not found")
