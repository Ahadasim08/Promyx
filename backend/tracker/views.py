import json
import sqlite3

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import Override

DECISION_MAP = {"done": "kept", "overdue": "broken", "open": "open"}
VALID_DECISIONS = {"kept", "broken", "open"}


def load_promises():
    conn = sqlite3.connect(settings.PROMISES_DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = [dict(r) for r in conn.execute("SELECT * FROM promises ORDER BY id")]
    conn.close()
    for row in rows:
        row["tool_decision"] = DECISION_MAP[row["status"]]
    return rows


@require_http_methods(["GET"])
def promise_list(request):
    rows = load_promises()
    overrides = {o.promise_id: o.human_decision for o in Override.objects.all()}
    for row in rows:
        row["human_decision"] = overrides.get(row["id"])
        row["final_decision"] = row["human_decision"] or row["tool_decision"]
    return JsonResponse({"promises": rows})


@csrf_exempt
@require_http_methods(["POST"])
def set_override(request, promise_id):
    body = json.loads(request.body or "{}")
    decision = body.get("decision")
    if decision not in VALID_DECISIONS:
        return JsonResponse({"error": f"decision must be one of {sorted(VALID_DECISIONS)}"}, status=400)

    obj, _ = Override.objects.update_or_create(
        promise_id=promise_id,
        defaults={"human_decision": decision},
    )
    return JsonResponse({"promise_id": promise_id, "human_decision": obj.human_decision})
