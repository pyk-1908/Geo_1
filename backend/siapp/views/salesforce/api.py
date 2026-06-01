import logging
import re

from django.http import HttpRequest, JsonResponse
from ninja import Router
from ninja_jwt.authentication import JWTAuth

from siapp.models import is_employee_or_above
from siapp.views.salesforce.salesforce_service import (
    SalesforceConfigError,
    get_notes_for_account,
)
from siapp.views.salesforce.schema import AccountNotesOut

logger = logging.getLogger('django')

router_salesforce = Router()

# Salesforce record Ids are 15- or 18-character alphanumeric.
_ACCOUNT_ID_RE = re.compile(r"^[a-zA-Z0-9]{15,18}$")


@router_salesforce.get("/notes/", auth=JWTAuth(), response=AccountNotesOut)
def salesforce_account_notes(request: HttpRequest, account_id: str):
    if not is_employee_or_above(request.user):
        return JsonResponse({'error': 'User does not have permission to access this page.'}, status=403)

    if not _ACCOUNT_ID_RE.match(account_id):
        return JsonResponse({'error': 'Invalid account_id.'}, status=400)

    try:
        notes = get_notes_for_account(account_id)
    except SalesforceConfigError as exc:
        logger.error(f"Salesforce integration not configured: {exc}")
        return JsonResponse({'error': 'Salesforce integration is not configured.'}, status=503)
    except Exception as exc:
        logger.error(f"Failed to fetch Salesforce notes for account {account_id}: {exc}")
        return JsonResponse({'error': 'Failed to fetch notes from Salesforce.'}, status=502)

    return {"account_id": account_id, "notes": notes}
