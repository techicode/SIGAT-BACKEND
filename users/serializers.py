from rest_framework import serializers
from .models import Department, Employee, CustomUser


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "role",
            "password",
        ]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = CustomUser.objects.create_user(**validated_data)
        return user


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["id", "name", "created_at"]


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = [
            "id",
            "rut",
            "first_name",
            "last_name",
            "email",
            "position",
            "department",
            "created_at",
        ]
        read_only_fields = ["created_at"]


class DepartmentBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["id", "name"]


class EmployeeBasicSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = ["id", "full_name", "email"]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class SystemUserBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["id", "username", "first_name", "last_name"]
