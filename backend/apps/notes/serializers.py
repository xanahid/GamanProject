from rest_framework import serializers

from .models import SessionNote


class SessionNoteSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.get_full_name", read_only=True)

    class Meta:
        model = SessionNote
        fields = ["id", "booking", "client", "client_name", "content", "created_at", "updated_at"]
        read_only_fields = ["id", "client_name", "created_at", "updated_at"]
