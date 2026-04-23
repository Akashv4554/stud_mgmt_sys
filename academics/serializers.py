"""
academics/serializers.py
"""

from rest_framework import serializers
from .models import Department, Subject


class DepartmentSerializer(serializers.ModelSerializer):
    student_count = serializers.IntegerField(read_only=True, required=False)
    faculty_count = serializers.IntegerField(read_only=True, required=False)
    subject_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = Department
        fields = [
            "id", "name", "code", "description", "hod_name",
            "student_count", "faculty_count", "subject_count",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class SubjectSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(
        source="department.name", read_only=True
    )

    class Meta:
        model = Subject
        fields = [
            "id", "code", "name", "department", "department_name",
            "semester", "credits", "subject_type",
            "max_internal_marks", "max_external_marks", "is_elective",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
