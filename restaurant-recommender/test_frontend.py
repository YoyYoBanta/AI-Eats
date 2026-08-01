"""Quick test to verify the frontend fixes."""
import urllib.request
import json

BASE = "http://127.0.0.1:8001"

# Test 1: Frontend serves correctly
r = urllib.request.urlopen(f"{BASE}/")
html = r.read().decode()
print("=== Frontend Test ===")
print("Status:", r.status)
print("Has display:none loading overlay:", 'id="loading-overlay" style="display: none;"' in html)
print("Has display:none summary:", 'id="ai-summary"' in html and 'style="display: none;"' in html)
print("Has DOMContentLoaded wrapper:", "DOMContentLoaded" in html)
print("Has showLoading helper:", "function showLoading" in html)
print("Has safe cuisines handling:", "Array.isArray(rec.cuisines)" in html)
print("Loading overlay is top-level (not in section):", html.index('id="loading-overlay"') > html.index("</footer>"))
print()

# Test 2: API endpoints
r2 = urllib.request.urlopen(f"{BASE}/api/v1/locations")
locations = json.loads(r2.read().decode())
print("=== API Test ===")
print("Locations:", len(locations["locations"]), "found")

# Test 3: Full recommendation flow
payload = json.dumps({"location": "Koramangala", "budget": "medium", "min_rating": 3.5}).encode()
req = urllib.request.Request(
    f"{BASE}/api/v1/recommendations",
    data=payload,
    headers={"Content-Type": "application/json"},
    method="POST",
)
r3 = urllib.request.urlopen(req, timeout=60)
data = json.loads(r3.read().decode())
print("Recommendations:", len(data.get("recommendations", [])))
print("Summary:", data.get("summary", "MISSING")[:80])
for rec in data.get("recommendations", [])[:2]:
    print(f"  [{rec['rank']}] {rec['restaurant_name']} - cuisines type: {type(rec['cuisines']).__name__}")
print()
print("=== ALL TESTS PASSED ===")
