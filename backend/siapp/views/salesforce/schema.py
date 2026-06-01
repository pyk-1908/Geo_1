from typing import List, Optional

from ninja import Schema


class NoteOut(Schema):
    title: str
    body: str
    created_date: Optional[str] = None


class AccountNotesOut(Schema):
    account_id: str
    notes: List[NoteOut]
