from django.db.models.signals import post_save
from django.dispatch import receiver

from .email_templates import schedule_update_email
from .models import Course, Internship, Service, UpcomingWorkshop

@receiver(
    post_save,
    sender=Course,
    dispatch_uid="main.course_created_update_email",
)
def course_created_update_email(
    sender,
    instance,
    created,
    raw=False,
    **kwargs,
):
    """Email registered users when a new course is created."""

    if raw or not created:
        return

    schedule_update_email("Course", instance)


@receiver(
    post_save,
    sender=Service,
    dispatch_uid="main.service_created_update_email",
)
def service_created_update_email(
    sender,
    instance,
    created,
    raw=False,
    **kwargs,
):
    """Email registered users when a new service is created."""

    if raw or not created:
        return

    schedule_update_email("Service", instance)


@receiver(
    post_save,
    sender=Internship,
    dispatch_uid="main.internship_created_update_email",
)
def internship_created_update_email(
    sender,
    instance,
    created,
    raw=False,
    **kwargs,
):
    """Email registered users when a new internship is created."""

    if raw or not created:
        return

    schedule_update_email("Internship", instance)


@receiver(
    post_save,
    sender=UpcomingWorkshop,
    dispatch_uid="main.workshop_created_update_email",
)
def workshop_created_update_email(
    sender,
    instance,
    created,
    raw=False,
    **kwargs,
):
    """Email registered users when a new workshop is created."""

    if raw or not created:
        return

    schedule_update_email("Workshop", instance)
