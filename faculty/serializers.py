"""
faculty/serializers.py
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Faculty, FacultySubjectAssignment
from accounts.serializers import UserSerializer
from academics.serializers import DepartmentSerializer

User = get_user_model()


class FacultySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    department = DepartmentSerializer(read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    full_name = serializers.SerializerMethodField()
    email = serializers.CharField(source="user.email", read_only=True)
    department_name = serializers.CharField(
        source="department.name", read_only=True
    )

    class Meta:
        model = Faculty
        fields = [
            "id", "user", "username", "full_name", "email",
            "employee_id", "department", "department_name",
            "designation", "date_of_joining", "specialization",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username


class FacultyCreateSerializer(serializers.ModelSerializer):
    """
    Creates both a User (role=faculty) and the Faculty profile in one call.
    """
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True, required=False)
    first_name = serializers.CharField(write_only=True, required=False, default="")
    last_name = serializers.CharField(write_only=True, required=False, default="")

    class Meta:
        model = Faculty
        fields = [
            "username", "password", "email", "first_name", "last_name",
            "employee_id", "department", "designation",
            "date_of_joining", "specialization",
        ]

    def create(self, validated_data):
        user_data = {
            "username": validated_data.pop("username"),
            "password": validated_data.pop("password"),
            "email": validated_data.pop("email", ""),
            "first_name": validated_data.pop("first_name", ""),
            "last_name": validated_data.pop("last_name", ""),
            "role": User.Role.FACULTY,
        }
        user = User.objects.create_user(**user_data)
        faculty = Faculty.objects.create(user=user, **validated_data)
        return faculty


class FacultySubjectAssignmentSerializer(serializers.ModelSerializer):
    faculty_name = serializers.CharField(
        source="faculty.user.get_full_name", read_only=True
    )
    subject_code = serializers.CharField(source="subject.code", read_only=True)
    subject_name = serializers.CharField(source="subject.name", read_only=True)

    class Meta:
        model = FacultySubjectAssignment
        fields = [
            "id", "faculty", "faculty_name",
            "subject", "subject_code", "subject_name",
            "academic_year", "section",
        ]
        read_only_fields = ["id"]
