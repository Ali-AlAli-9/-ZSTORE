from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "is_email_verified"]
        read_only_fields = ["id", "is_email_verified"]


class StaffUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "is_staff", "is_email_verified"]
        read_only_fields = ["id", "is_staff", "is_email_verified"]