from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers
from .models import ClientProfile, SavedCard

User = get_user_model()


class ClientSignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)

    # ✅ MUST be write_only (critical fix)
    age = serializers.IntegerField(write_only=True, min_value=12, max_value=120)
    occupation = serializers.CharField(
        max_length=150,
        required=False,
        allow_blank=True,
        write_only=True   # ✅ IMPORTANT
    )

    phone_number = serializers.CharField(max_length=20)

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "password",
            "age",
            "occupation",
        ]

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("این ایمیل قبلاً ثبت شده است.")
        return value

    def validate_phone_number(self, value):
        value = value.strip()
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("این شماره موبایل قبلاً ثبت شده است.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        age = validated_data.pop("age")
        occupation = validated_data.pop("occupation", "")

        email = validated_data.pop("email").strip().lower()
        phone_number = validated_data.pop("phone_number").strip()
        first_name = validated_data.pop("first_name").strip()
        last_name = validated_data.pop("last_name").strip()

        password = validated_data.pop("password")

        username = email
        if User.objects.filter(username=username).exists():
            import uuid
            username = f"{email}_{uuid.uuid4().hex[:6]}"

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            role=User.Role.CLIENT,
        )

        ClientProfile.objects.create(
            user=user,
            age=age,
            occupation=occupation,
        )

        return user


class ClientProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    email = serializers.EmailField(source="user.email", read_only=True)
    phone_number = serializers.CharField(source="user.phone_number", read_only=True)
    recommended_therapist_name = serializers.CharField(
        source="recommended_therapist.user.get_full_name", read_only=True, default=None
    )

    class Meta:
        model = ClientProfile
        fields = [
            "first_name", "last_name", "email", "phone_number", "age",
            "occupation", "has_completed_intake_session",
            "recommended_therapist", "recommended_therapist_name",
        ]
        read_only_fields = ["has_completed_intake_session", "recommended_therapist"]


class SavedCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedCard
        fields = ["id", "masked_pan", "bank_name", "is_default", "created_at"]
        read_only_fields = ["id", "created_at"]
