"""
attendance/views.py
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Q

from .models import Attendance
from .serializers import (
    AttendanceSerializer,
    BulkAttendanceEntrySerializer,
    AttendanceSummarySerializer,
)
from academics.models import Subject
from students.models import Student


class AttendanceViewSet(viewsets.ModelViewSet):
    """
    CRUD for individual Attendance records.
    Also provides:
      POST /attendance/bulk-mark/   – mark attendance for a full class
      GET  /attendance/summary/     – per-subject attendance summary for a student
    """
    queryset = Attendance.objects.select_related(
        "student", "subject", "marked_by"
    ).all()
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["student", "subject", "date", "status"]
    search_fields = ["student__usn", "subject__code"]
    ordering_fields = ["date", "period"]

    def perform_create(self, serializer):
        serializer.save(marked_by=self.request.user)

    # ------------------------------------------------------------------
    # Bulk mark attendance
    # ------------------------------------------------------------------
    @action(detail=False, methods=["post"], url_path="bulk-mark")
    def bulk_mark(self, request):
        """
        Payload:
        {
            "subject": 1,
            "date": "2025-12-01",
            "period": 3,
            "records": [
                {"student": 1, "status": "present"},
                {"student": 2, "status": "absent"}
            ]
        }
        """
        serializer = BulkAttendanceEntrySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        created = []
        for rec in data["records"]:
            obj, _ = Attendance.objects.update_or_create(
                student_id=rec["student"],
                subject_id=data["subject"],
                date=data["date"],
                period=data["period"],
                defaults={
                    "status": rec["status"],
                    "marked_by": request.user,
                },
            )
            created.append(obj.id)

        return Response(
            {"detail": f"Marked {len(created)} attendance records.", "ids": created},
            status=status.HTTP_201_CREATED,
        )

    # ------------------------------------------------------------------
    # Attendance summary for a student
    # ------------------------------------------------------------------
    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        """
        Query params: ?student=<id>
        Returns per-subject attendance percentage.
        """
        student_id = request.query_params.get("student")
        if not student_id:
            return Response(
                {"detail": "Query param 'student' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = (
            Attendance.objects.filter(student_id=student_id)
            .values("subject__code", "subject__name", "subject__subject_type")
            .annotate(
                total_classes=Count("id"),
                present_count=Count("id", filter=Q(status="present")),
                absent_count=Count("id", filter=Q(status="absent")),
            )
        )

        results = []
        for row in qs:
            total = row["total_classes"]
            present = row["present_count"]
            results.append({
                "subject_code": row["subject__code"],
                "subject_name": row["subject__name"],
                "subject_type": row["subject__subject_type"],
                "total_classes": total,
                "present_count": present,
                "absent_count": row["absent_count"],
                "percentage": round((present / total) * 100, 2) if total else 0,
            })

        serializer = AttendanceSummarySerializer(results, many=True)
        return Response(serializer.data)
