"""
attendance/serializers.py
"""

from rest_framework import serializers
from .models import Attendance


class AttendanceSerializer(serializers.ModelSerializer):
    student_usn = serializers.CharField(source="student.usn", read_only=True)
    subject_code = serializers.CharField(source="subject.code", read_only=True)
    subject_type = serializers.CharField(source="subject.subject_type", read_only=True)
    marked_by_username = serializers.CharField(
        source="marked_by.username", read_only=True
    )

    class Meta:
        model = Attendance
        fields = [
            "id", "student", "student_usn",
            "subject", "subject_code", "subject_type",
            "date", "period", "status",
            "marked_by", "marked_by_username",
            "created_at",
        ]
        read_only_fields = ["id", "marked_by", "created_at"]


class BulkAttendanceEntrySerializer(serializers.Serializer):
    """
    Accepts a list of attendance records so a faculty can mark
    attendance for an entire class in one API call.
    """
    subject = serializers.IntegerField()
    date = serializers.DateField()
    period = serializers.IntegerField()
    records = serializers.ListField(
        child=serializers.DictField(), min_length=1
    )

    def validate_records(self, records):
        for rec in records:
            if "student" not in rec or "status" not in rec:
                raise serializers.ValidationError(
                    "Each record must have 'student' (id) and 'status'."
                )
            if rec["status"] not in ("present", "absent"):
                raise serializers.ValidationError(
                    f"Invalid status '{rec['status']}'. Must be 'present' or 'absent'."
                )
        return records


class AttendanceSummarySerializer(serializers.Serializer):
    """Read-only summary returned by the attendance-summary endpoint."""
    subject_code = serializers.CharField()
    subject_name = serializers.CharField()
    subject_type = serializers.CharField()
    total_classes = serializers.IntegerField()
    present_count = serializers.IntegerField()
    absent_count = serializers.IntegerField()
    percentage = serializers.FloatField()
