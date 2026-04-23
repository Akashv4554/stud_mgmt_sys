"""
attendance/models.py
Attendance tracking – works for both theory and lab subjects via the
Subject.subject_type field.
"""

from django.db import models


class Attendance(models.Model):
    """
    One row = one student's attendance for one subject on one date and period.
    - Linked to Student (FK)
    - Linked to Subject (FK)
    Theory vs Lab distinction is derived from Subject.subject_type.
    """

    class Status(models.TextChoices):
        PRESENT = "present", "Present"
        ABSENT = "absent", "Absent"

    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )
    subject = models.ForeignKey(
        "academics.Subject",
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )
    date = models.DateField(db_index=True)
    period = models.PositiveSmallIntegerField(
        default=1,
        help_text="Period/hour number in the day (1-8)",
    )
    status = models.CharField(
        max_length=7,
        choices=Status.choices,
        default=Status.PRESENT,
    )
    marked_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attendance_marked",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "subject", "date", "period")
        ordering = ["-date", "period"]
        verbose_name = "Attendance"
        verbose_name_plural = "Attendance Records"
        indexes = [
            models.Index(fields=["student", "subject", "date"]),
        ]

    def __str__(self):
        return (
            f"{self.student.usn} | {self.subject.code} | "
            f"{self.date} P{self.period} – {self.get_status_display()}"
        )


from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender=Attendance)
@receiver(post_delete, sender=Attendance)
def update_student_attendance(sender, instance, **kwargs):
    """Update student's global attendance percentage whenever a record is modified."""
    if instance.student:
        instance.student.update_attendance_percentage()
