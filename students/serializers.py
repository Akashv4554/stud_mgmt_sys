"""
students/serializers.py
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Student, Enrollment
from accounts.serializers import UserSerializer
from academics.serializers import DepartmentSerializer

User = get_user_model()


class StudentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    department = DepartmentSerializer(read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    full_name = serializers.SerializerMethodField()
    email = serializers.CharField(source="user.email", read_only=True)
    department_name = serializers.CharField(
        source="department.name", read_only=True
    )
    department_code = serializers.CharField(
        source="department.code", read_only=True
    )

    class Meta:
        model = Student
        fields = [
            "id", "user", "username", "full_name", "email",
            "usn", "department", "department_name", "department_code",
            "semester", "section", "date_of_birth", "admission_year",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username


class StudentCreateSerializer(serializers.ModelSerializer):
    """
    Creates both a User (role=student) and the Student profile in one call.
    """
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True, required=False)
    first_name = serializers.CharField(write_only=True, required=False, default="")
    last_name = serializers.CharField(write_only=True, required=False, default="")

    class Meta:
        model = Student
        fields = [
            "username", "password", "email", "first_name", "last_name",
            "usn", "department", "semester", "section",
            "date_of_birth", "admission_year",
        ]

    def create(self, validated_data):
        user_data = {
            "username": validated_data.pop("username"),
            "password": validated_data.pop("password"),
            "email": validated_data.pop("email", ""),
            "first_name": validated_data.pop("first_name", ""),
            "last_name": validated_data.pop("last_name", ""),
            "role": User.Role.STUDENT,
        }
        user = User.objects.create_user(**user_data)
        student = Student.objects.create(user=user, **validated_data)
        return student


class EnrollmentSerializer(serializers.ModelSerializer):
    student_usn = serializers.CharField(source="student.usn", read_only=True)
    subject_code = serializers.CharField(source="subject.code", read_only=True)
    subject_name = serializers.CharField(source="subject.name", read_only=True)

    class Meta:
        model = Enrollment
        fields = [
            "id", "student", "student_usn",
            "subject", "subject_code", "subject_name",
            "academic_year", "enrolled_at",
        ]
        read_only_fields = ["id", "enrolled_at"]
