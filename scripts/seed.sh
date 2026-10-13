#!/usr/bin/env bash
# Seed demo data through the public API (handy for screenshots and the live demo).
# Usage: ./scripts/seed.sh [BASE_URL]      e.g. http://localhost:8000  or  http://clinicq.local
set -euo pipefail

BASE="${1:-http://localhost:8000}"
API="$BASE/api"
json() { curl -fsS -X POST "$API/$1" -H 'Content-Type: application/json' -d "$2"; }
field() { python3 -c "import sys,json; print(json.load(sys.stdin)['id'])"; }

echo "Seeding ClinicQ at $BASE ..."

D1=$(json doctors '{"name":"Dr. Asha Rao","specialization":"General Medicine","room":"101"}' | field)
D2=$(json doctors '{"name":"Dr. Vikram Shah","specialization":"Pediatrics","room":"102"}' | field)
D3=$(json doctors '{"name":"Dr. Neha Kapoor","specialization":"Dermatology","room":"201"}' | field)

P1=$(json patients '{"name":"Ravi Kumar","phone":"9876543210","age":34}' | field)
P2=$(json patients '{"name":"Meera Iyer","phone":"9876501234","age":28}' | field)
P3=$(json patients '{"name":"Arjun Nair","phone":"9811122233","age":7}' | field)
P4=$(json patients '{"name":"Sana Khan","phone":"9822233344","age":45}' | field)
P5=$(json patients '{"name":"Karthik Reddy","phone":"9833344455","age":52}' | field)

TODAY=$(date +%F)
book() { json appointments "{\"doctor_id\":$1,\"patient_id\":$2,\"scheduled_at\":\"${TODAY}T$3\",\"reason\":\"$4\"}" | field; }

A1=$(book "$D1" "$P1" 09:00 "Fever and cough")
A2=$(book "$D1" "$P2" 09:15 "Follow-up visit")
book "$D1" "$P4" 09:30 "Blood pressure check" >/dev/null
book "$D2" "$P3" 09:00 "Vaccination" >/dev/null
book "$D2" "$P3" 09:20 "Growth check" >/dev/null
book "$D3" "$P5" 10:00 "Skin allergy" >/dev/null

curl -fsS -X PUT "$API/appointments/$A1" -H 'Content-Type: application/json' -d '{"status":"checked_in"}' >/dev/null
curl -fsS -X PUT "$API/appointments/$A2" -H 'Content-Type: application/json' -d '{"status":"completed"}' >/dev/null

echo "Done. Stats:"
curl -fsS "$API/appointments/stats"; echo
