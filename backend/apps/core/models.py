import uuid

from django.db import models


class TimeStampedModel(models.Model):
    """Adds created/updated timestamps. Inherit this in every app's models."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDPKModel(models.Model):
    """
    UUID primary keys for anything reachable by a public URL (sessions,
    payments) so IDs aren't sequentially guessable.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True
