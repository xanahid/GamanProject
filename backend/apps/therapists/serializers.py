from rest_framework import serializers

from .models import Department, Specialty, TherapistProfile


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["id", "name", "slug"]


class SpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialty
        fields = ["id", "name", "slug", "department"]


class TherapistListSerializer(serializers.ModelSerializer):
    """Lightweight shape for the grid/preview blocks."""

    name = serializers.CharField(source="user.get_full_name", read_only=True)
    photo_url = serializers.SerializerMethodField()
    specialty_names = serializers.SerializerMethodField()

    class Meta:
        model = TherapistProfile
        fields = [
            "id", "name", "photo_url", "short_bio", "specialty_names",
            "years_active", "is_head_of_institute",
        ]

    def get_photo_url(self, obj):
        return obj.photo.url if obj.photo else None

    def get_specialty_names(self, obj):
        return [s.name for s in obj.specialties.all()]


class TherapistDetailSerializer(serializers.ModelSerializer):
    """Full profile shape: name, age, years active, specialty, active clients."""

    name = serializers.CharField(source="user.get_full_name", read_only=True)
    photo_url = serializers.SerializerMethodField()
    specialties = SpecialtySerializer(many=True, read_only=True)
    departments = DepartmentSerializer(many=True, read_only=True)
    active_client_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = TherapistProfile
        fields = [
            "id", "name", "photo_url", "age", "years_active", "short_bio",
            "full_bio", "specialties", "departments", "active_client_count",
            "is_head_of_institute",
        ]

    def get_photo_url(self, obj):
        return obj.photo.url if obj.photo else None
