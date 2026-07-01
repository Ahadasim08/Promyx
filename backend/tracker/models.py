from django.db import models

DECISIONS = [
    ("kept", "Kept"),
    ("broken", "Broken"),
    ("open", "Open"),
]


class Override(models.Model):
    """A human reviewer's final call on one promise from data/promises.db.

    Stored separately from promises.db (owned by store.py/check.py) so
    rebuilding that db never wipes human review history.
    """
    promise_id = models.IntegerField(unique=True)
    human_decision = models.CharField(max_length=10, choices=DECISIONS)
    reviewed_at = models.DateTimeField(auto_now=True)
