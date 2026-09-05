from django import template
from django.urls import reverse
from django.utils import timezone

from main.models import (
    CourseBooking,
    DemoRequest,
    InternshipBooking,
    UpcomingWorkshop,
    WorkshopRegistration,
)

register = template.Library()


def _admin_change_url(model_name, pk):
    return reverse(
        f"admin:main_{model_name}_change",
        args=[pk],
    )


@register.simple_tag
def e2e_dashboard_data():
    """
    Dashboard metrics and recent records for the Errors2Experts
    administration home page.
    """

    recent_items = []

    # ---------------------------------------------------------
    # Course bookings
    # ---------------------------------------------------------

    for booking in CourseBooking.objects.order_by("-created_at")[:4]:

        recent_items.append(
            {
                "code": "CB",
                "color": "red",
                "title": "New course booking",
                "detail": (f"{booking.name} · " f"{booking.course}"),
                "when": booking.created_at,
                "url": _admin_change_url(
                    "coursebooking",
                    booking.pk,
                ),
            }
        )

    # ---------------------------------------------------------
    # Internship bookings
    # ---------------------------------------------------------

    for booking in InternshipBooking.objects.order_by("-created_at")[:4]:

        recent_items.append(
            {
                "code": "IB",
                "color": "gold",
                "title": "New internship booking",
                "detail": (f"{booking.full_name} · " f"{booking.internship_name}"),
                "when": booking.created_at,
                "url": _admin_change_url(
                    "internshipbooking",
                    booking.pk,
                ),
            }
        )

    # ---------------------------------------------------------
    # Workshop registrations
    # ---------------------------------------------------------

    for booking in WorkshopRegistration.objects.select_related("workshop").order_by(
        "-created_at"
    )[:4]:

        workshop_title = (
            booking.workshop.title if booking.workshop else "Workshop registration"
        )

        recent_items.append(
            {
                "code": "WB",
                "color": "green",
                "title": "New workshop registration",
                "detail": (f"{booking.full_name} · " f"{workshop_title}"),
                "when": booking.created_at,
                "url": _admin_change_url(
                    "workshopregistration",
                    booking.pk,
                ),
            }
        )

    # ---------------------------------------------------------
    # Demo requests
    # ---------------------------------------------------------

    for request_obj in DemoRequest.objects.select_related(
        "service",
        "selected_demo",
        "category",
    ).order_by("-created_at")[:4]:

        if request_obj.selected_demo:

            demo_name = request_obj.selected_demo.title

        elif request_obj.category:

            demo_name = request_obj.category.name

        elif request_obj.service:

            demo_name = request_obj.service.title

        else:

            demo_name = "Custom demo requirement"

        recent_items.append(
            {
                "code": "DR",
                "color": "blue",
                "title": "New demo request received",
                "detail": (f"{request_obj.organization_name} · " f"{demo_name}"),
                "when": request_obj.created_at,
                "url": _admin_change_url(
                    "demorequest",
                    request_obj.pk,
                ),
            }
        )

    # ---------------------------------------------------------
    # Sort combined activity
    # ---------------------------------------------------------

    recent_items.sort(
        key=lambda item: item["when"],
        reverse=True,
    )

    # ---------------------------------------------------------
    # Upcoming workshops
    # ---------------------------------------------------------

    upcoming_workshops = UpcomingWorkshop.objects.filter(
        event_date__gte=timezone.localdate(),
    ).order_by("event_date", "event_time",)[:4]

    return {
        "course_bookings": (CourseBooking.objects.count()),
        "internship_bookings": (InternshipBooking.objects.count()),
        "workshop_bookings": (WorkshopRegistration.objects.count()),
        "demo_requests": (DemoRequest.objects.count()),
        "recent_activities": (recent_items[:6]),
        "upcoming_workshops": (upcoming_workshops),
    }
