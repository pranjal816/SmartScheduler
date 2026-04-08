import os
import sys
from pathlib import Path

from django.core.management import call_command
from django.http import HttpResponse, JsonResponse


CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
BACKEND_DIR = PROJECT_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smart_scheduler.settings")

import django


django.setup()


def app(request):
    expected_token = os.environ.get("INIT_DB_TOKEN")
    supplied_token = request.GET.get("token")

    if not expected_token:
        return JsonResponse({"error": "INIT_DB_TOKEN is not configured."}, status=500)

    if supplied_token != expected_token:
        return JsonResponse({"error": "Unauthorized."}, status=401)

    try:
        call_command("migrate", interactive=False, verbosity=1)
        if request.GET.get("seed") == "1":
            call_command("seed_demo_data", verbosity=1)
        return HttpResponse("Database initialization completed successfully.")
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=500)
