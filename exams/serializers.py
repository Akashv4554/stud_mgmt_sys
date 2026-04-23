"""
exams/serializers.py
"""

from rest_framework import serializers
from .models import Exam, Marks, Result


class ExamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = [
            "id", "name", "exam_type", "semester",
            "academic_year", "max_marks", "date_conducted",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class MarksSerializer(serializers.ModelSerializer):
    student_usn = serializers.CharField(source="student.usn", read_only=True)
    subject_code = serializers.CharField(source="subject.code", read_only=True)
    exam_name = serializers.CharField(source="exam.name", read_only=True)
    entered_by_username = serializers.CharField(
        source="entered_by.username", read_only=True
    )

    class Meta:
        model = Marks
        fields = [
            "id", "student", "student_usn",
            "subject", "subject_code",
            "exam", "exam_name",
            "marks_obtained", "is_absent", "remarks",
            "entered_by", "entered_by_username",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "entered_by", "created_at", "updated_at"]

    def validate(self, attrs):
        exam = attrs.get("exam") or self.instance.exam
        marks = attrs.get("marks_obtained", 0)
        if marks > exam.max_marks:
            raise serializers.ValidationError(
                {"marks_obtained": f"Cannot exceed max marks ({exam.max_marks})."}
            )
        return attrs


class BulkMarksEntrySerializer(serializers.Serializer):
    """
    Accepts a list of marks so a faculty can enter marks for
    an entire class/subject/exam in one API call.
    """
    exam = serializers.IntegerField()
    subject = serializers.IntegerField()
    entries = serializers.ListField(
        child=serializers.DictField(), min_length=1
    )

    def validate_entries(self, entries):
        for entry in entries:
            if "student" not in entry or "marks_obtained" not in entry:
                raise serializers.ValidationError(
                    "Each entry must have 'student' (id) and 'marks_obtained'."
                )
        return entries


class ResultSerializer(serializers.ModelSerializer):
    student_usn = serializers.CharField(source="student.usn", read_only=True)
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = Result
        fields = [
            "id", "student", "student_usn", "student_name",
            "semester", "academic_year",
            "sgpa", "cgpa", "total_credits", "credits_earned",
            "is_published", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_student_name(self, obj):
        return obj.student.user.get_full_name() or obj.student.user.username
