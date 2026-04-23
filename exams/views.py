"""
exams/views.py
"""

from decimal import Decimal

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, F

from .models import Exam, Marks, Result
from .serializers import (
    ExamSerializer,
    MarksSerializer,
    BulkMarksEntrySerializer,
    ResultSerializer,
)
from students.models import Student, Enrollment
from academics.models import Subject


class ExamViewSet(viewsets.ModelViewSet):
    """CRUD for Exam definitions."""
    queryset = Exam.objects.all()
    serializer_class = ExamSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["exam_type", "semester", "academic_year"]
    search_fields = ["name"]
    ordering_fields = ["semester", "date_conducted"]


class MarksViewSet(viewsets.ModelViewSet):
    """
    CRUD for individual Marks entries.
    Also provides:
      POST /marks/bulk-entry/  – enter marks for a full class in one call
    """
    queryset = Marks.objects.select_related(
        "student", "subject", "exam", "entered_by"
    ).all()
    serializer_class = MarksSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["student", "subject", "exam", "is_absent"]
    search_fields = ["student__usn", "subject__code"]
    ordering_fields = ["marks_obtained"]

    def perform_create(self, serializer):
        serializer.save(entered_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(entered_by=self.request.user)

    @action(detail=False, methods=["post"], url_path="bulk-entry")
    def bulk_entry(self, request):
        """
        Payload:
        {
            "exam": 1,
            "subject": 3,
            "entries": [
                {"student": 1, "marks_obtained": 35, "is_absent": false},
                {"student": 2, "marks_obtained": 0, "is_absent": true}
            ]
        }
        """
        serializer = BulkMarksEntrySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        created_ids = []
        for entry in data["entries"]:
            obj, _ = Marks.objects.update_or_create(
                student_id=entry["student"],
                subject_id=data["subject"],
                exam_id=data["exam"],
                defaults={
                    "marks_obtained": entry["marks_obtained"],
                    "is_absent": entry.get("is_absent", False),
                    "remarks": entry.get("remarks", ""),
                    "entered_by": request.user,
                },
            )
            created_ids.append(obj.id)

        return Response(
            {"detail": f"Saved {len(created_ids)} marks entries.", "ids": created_ids},
            status=status.HTTP_201_CREATED,
        )


class ResultViewSet(viewsets.ModelViewSet):
    """
    CRUD for Results.
    Also provides:
      POST /results/calculate-sgpa/  – compute SGPA for a student + semester
    """
    queryset = Result.objects.select_related("student").all()
    serializer_class = ResultSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["student", "semester", "academic_year", "is_published"]
    search_fields = ["student__usn"]
    ordering_fields = ["semester", "sgpa", "cgpa"]

    @action(detail=False, methods=["post"], url_path="calculate-sgpa")
    def calculate_sgpa(self, request):
        """
        Calculate SGPA for a given student and semester.
        Payload: { "student": <id>, "semester": 5, "academic_year": "2025-2026" }

        Grade-point mapping (VTU-style, 10-point scale):
          >=90 → 10, >=80 → 9, >=70 → 8, >=60 → 7, >=50 → 6,
          >=40 → 5 (pass), <40 → 0 (fail)

        SGPA = Σ(grade_point × credits) / Σ(credits)
        """
        student_id = request.data.get("student")
        semester = request.data.get("semester")
        academic_year = request.data.get("academic_year", "")

        if not student_id or not semester:
            return Response(
                {"detail": "'student' and 'semester' are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            student = Student.objects.get(pk=student_id)
        except Student.DoesNotExist:
            return Response(
                {"detail": "Student not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Enrolled subjects for this semester
        subjects = Subject.objects.filter(
            enrollments__student=student,
            semester=semester,
        ).distinct()

        if not subjects.exists():
            return Response(
                {"detail": "No enrolled subjects found for this semester."},
                status=status.HTTP_404_NOT_FOUND,
            )

        total_credits = 0
        weighted_sum = Decimal("0")
        credits_earned = 0

        for subj in subjects:
            # Sum all marks for this student + subject (internals + externals)
            total_marks_agg = Marks.objects.filter(
                student=student, subject=subj
            ).aggregate(total=Sum("marks_obtained"))

            total_marks = total_marks_agg["total"] or Decimal("0")

            # Compute percentage out of (max_internal + max_external)
            max_total = subj.max_internal_marks + subj.max_external_marks
            percentage = (
                (total_marks / Decimal(max_total)) * 100 if max_total else Decimal("0")
            )

            grade_point = self._percentage_to_grade_point(percentage)
            weighted_sum += grade_point * subj.credits
            total_credits += subj.credits
            if grade_point > 0:
                credits_earned += subj.credits

        sgpa = (
            round(weighted_sum / Decimal(total_credits), 2)
            if total_credits else Decimal("0")
        )

        # Compute CGPA across all semesters
        previous_results = Result.objects.filter(
            student=student, semester__lt=semester
        )
        all_sgpa_credits = sum(
            (r.sgpa or Decimal("0")) * (r.total_credits or 0)
            for r in previous_results
        )
        all_credits = sum(r.total_credits or 0 for r in previous_results)

        cgpa_numerator = all_sgpa_credits + (sgpa * total_credits)
        cgpa_denominator = all_credits + total_credits
        cgpa = (
            round(cgpa_numerator / Decimal(cgpa_denominator), 2)
            if cgpa_denominator else sgpa
        )

        result, _ = Result.objects.update_or_create(
            student=student,
            semester=semester,
            academic_year=academic_year,
            defaults={
                "sgpa": sgpa,
                "cgpa": cgpa,
                "total_credits": total_credits,
                "credits_earned": credits_earned,
            },
        )

        return Response(ResultSerializer(result).data, status=status.HTTP_200_OK)

    @staticmethod
    def _percentage_to_grade_point(percentage):
        """VTU-style 10-point grade mapping."""
        if percentage >= 90:
            return Decimal("10")
        elif percentage >= 80:
            return Decimal("9")
        elif percentage >= 70:
            return Decimal("8")
        elif percentage >= 60:
            return Decimal("7")
        elif percentage >= 50:
            return Decimal("6")
        elif percentage >= 40:
            return Decimal("5")
        return Decimal("0")
