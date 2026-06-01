"""Salesforce access for account notes.

Logs in to Salesforce and fetches an account's notes from both the legacy ``Note``
object and modern notes (stored as ``ContentVersion``), returned as a single list of
``{title, body, created_date}`` dicts.

Credentials are read from environment variables (loaded from ``backend/.env`` by
``settings.py``). ``SF_AUTH_METHOD`` selects the login flow:

* ``client_credentials`` — server-to-server OAuth using ``SF_CONSUMER_KEY`` +
  ``SF_CONSUMER_SECRET`` only (no user/password). Requires the Connected App to have
  the Client Credentials Flow enabled with a Run-As user. This is what production
  uses, and the only flow that works on orgs with SOAP login disabled (Agentforce /
  Starter trials).
* ``password_oauth`` — OAuth username-password: ``SF_USERNAME`` + ``SF_PASSWORD`` +
  ``SF_CONSUMER_KEY`` + ``SF_CONSUMER_SECRET``. Deprecated by Salesforce; often blocked.
* ``security_token`` — SOAP login: ``SF_USERNAME`` + ``SF_PASSWORD`` +
  ``SF_SECURITY_TOKEN``. Simplest, but disabled by default on modern trial orgs.

``SF_DOMAIN``: ``login`` (production / Developer Edition) or ``test`` (sandbox) for the
password/token flows. For ``client_credentials`` it must be your **My Domain host with
the trailing ``.salesforce.com`` removed** — e.g. an instance of
``https://acme-dev-ed.develop.my.salesforce.com`` means ``SF_DOMAIN=acme-dev-ed.develop.my``
(simple-salesforce appends ``.salesforce.com`` itself).
"""
import logging
import os

from simple_salesforce import Salesforce, format_soql

logger = logging.getLogger('django')


class SalesforceConfigError(RuntimeError):
    """Raised when required Salesforce credentials are missing."""


def _require(**values: str) -> None:
    """Raise SalesforceConfigError if any named env value is missing."""
    missing = [name for name, value in values.items() if not value]
    if missing:
        raise SalesforceConfigError(
            f"Missing Salesforce credentials: {', '.join(missing)}. Set them in backend/.env."
        )


def _get_salesforce_client() -> Salesforce:
    """Build a Salesforce client using the flow named by ``SF_AUTH_METHOD``.

    A new client is created per call (no shared session) to avoid stale-session bugs;
    account-notes traffic is low, so the extra login round-trip is acceptable.

    Raises:
        SalesforceConfigError: if the selected method's credentials are incomplete.
    """
    method = os.getenv("SF_AUTH_METHOD", "client_credentials").strip().lower()
    domain = os.getenv("SF_DOMAIN", "login")
    consumer_key = os.getenv("SF_CONSUMER_KEY")
    consumer_secret = os.getenv("SF_CONSUMER_SECRET")

    if method == "client_credentials":
        _require(SF_CONSUMER_KEY=consumer_key, SF_CONSUMER_SECRET=consumer_secret)
        if domain in ("login", "test"):
            raise SalesforceConfigError(
                "client_credentials requires SF_DOMAIN to be your My Domain host without "
                "the trailing '.salesforce.com' (e.g. acme-dev-ed.develop.my), not 'login'."
            )
        return Salesforce(consumer_key=consumer_key, consumer_secret=consumer_secret, domain=domain)

    username = os.getenv("SF_USERNAME")
    password = os.getenv("SF_PASSWORD")

    if method == "password_oauth":
        _require(
            SF_USERNAME=username, SF_PASSWORD=password,
            SF_CONSUMER_KEY=consumer_key, SF_CONSUMER_SECRET=consumer_secret,
        )
        return Salesforce(
            username=username, password=password,
            consumer_key=consumer_key, consumer_secret=consumer_secret, domain=domain,
        )

    if method == "security_token":
        security_token = os.getenv("SF_SECURITY_TOKEN")
        _require(SF_USERNAME=username, SF_PASSWORD=password, SF_SECURITY_TOKEN=security_token)
        return Salesforce(
            username=username, password=password, security_token=security_token, domain=domain,
        )

    raise SalesforceConfigError(
        f"Unknown SF_AUTH_METHOD '{method}'. Use client_credentials, password_oauth, or security_token."
    )


def get_notes_for_account(account_id: str) -> list[dict]:
    """Return an account's notes, newest first.

    Merges two note types:

    * Legacy ``Note`` records, linked directly via ``ParentId``.
    * Modern notes, which Salesforce stores as ``ContentVersion`` rows with
      ``FileType = 'SNOTE'`` and links to the account through ``ContentDocumentLink``.
      We use ``ContentVersion`` (not ``ContentNote``) because it exists in every org,
      whereas ``ContentNote`` requires the Enhanced Notes feature to be enabled.

    Each note type is fetched independently: if one query fails (e.g. an object is
    not enabled in the org), it is logged and skipped so the other notes still return.

    Args:
        account_id: 15- or 18-character Salesforce Account Id.

    Returns:
        A list of ``{"title": str, "body": str, "created_date": str}`` dicts.
    """
    sf = _get_salesforce_client()
    notes: list[dict] = []
    notes.extend(_get_legacy_notes(sf, account_id))
    notes.extend(_get_modern_notes(sf, account_id))

    # CreatedDate is ISO 8601, so lexical sort orders chronologically.
    notes.sort(key=lambda note: note["created_date"] or "", reverse=True)
    return notes


def _get_legacy_notes(sf: Salesforce, account_id: str) -> list[dict]:
    """Fetch legacy ``Note`` records linked to the account via ``ParentId``."""
    try:
        result = sf.query(format_soql(
            "SELECT Title, Body, CreatedDate FROM Note WHERE ParentId = {account_id}",
            account_id=account_id,
        ))
    except Exception as exc:
        logger.warning(f"Salesforce legacy Note query failed for {account_id}: {exc}")
        return []
    return [
        {
            "title": record.get("Title") or "",
            "body": record.get("Body") or "",
            "created_date": record.get("CreatedDate"),
        }
        for record in result.get("records", [])
    ]


def _get_modern_notes(sf: Salesforce, account_id: str) -> list[dict]:
    """Fetch modern notes (``ContentVersion`` SNOTE) linked via ``ContentDocumentLink``.

    Two steps because ``ContentDocumentLink`` cannot be used in a SOQL semi-join: first
    resolve the account's linked document ids, then fetch their latest note versions.
    """
    try:
        links = sf.query(format_soql(
            "SELECT ContentDocumentId FROM ContentDocumentLink WHERE LinkedEntityId = {account_id}",
            account_id=account_id,
        ))
        document_ids = [record["ContentDocumentId"] for record in links.get("records", [])]
        if not document_ids:
            return []

        versions = sf.query(format_soql(
            "SELECT Title, TextPreview, CreatedDate FROM ContentVersion "
            "WHERE FileType = 'SNOTE' AND IsLatest = true AND ContentDocumentId IN {document_ids}",
            document_ids=document_ids,
        ))
    except Exception as exc:
        logger.warning(f"Salesforce modern note query failed for {account_id}: {exc}")
        return []
    return [
        {
            "title": record.get("Title") or "",
            "body": record.get("TextPreview") or "",
            "created_date": record.get("CreatedDate"),
        }
        for record in versions.get("records", [])
    ]
