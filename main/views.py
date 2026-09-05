# Python imports
import logging
import os
from collections import defaultdict
from datetime import datetime, timedelta

# Django imports
from django.http import HttpResponse
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from django.db.models import Sum
from django.utils.text import slugify

# Forms
from .forms import JobApplicationForm

# Payment
from .payment_utils import generate_upi_qr_base64

# Email helpers
from .brevo_mail import send_brevo_email
from .email_templates import (
    build_detail_rows,
    build_email_layout,
    build_text_social_links,
    safe_html,
)
from django.db.models import Prefetch

from .models import (
    TeamCategory,
    Employee,
    EmployeeRole,
)

# Models
from .models import (
    Career,
    Certificate,
    ClientProject,
    Contact,
    Course,
    CourseBooking,
    DemoBooking,
    DemoCategory,
    DemoRequest,
    Internship,
    InternshipBooking,
    Placement,
    ProcessStep,
    Service,
    ServiceBooking,
    ServiceDemoLink,
    StudentReview,
    UpcomingWorkshop,
    WorkshopPhoto,
    WorkshopRegistration,
)

logger = logging.getLogger(__name__)

def robots_txt(request):
    content = """User-agent: *
Allow: /

Sitemap: https://errors2experts.com/sitemap.xml
"""
    return HttpResponse(content, content_type="text/plain")

def send_email_safely(
    *,
    to_email,
    subject,
    html_content,
    text_content=None,
    attachment_path=None,
):
    """
    Send email without breaking the submitted form when
    Brevo is temporarily unavailable.
    """

    try:
        send_brevo_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            attachment_path=attachment_path,
        )
    except Exception:
        logger.exception(
            "Brevo email failed. Recipient=%s Subject=%s",
            to_email,
            subject,
        )
        return False

    return True


def get_admin_change_url(request, instance):
    """
    Build the Django admin change-page URL for a saved model object.
    """

    try:
        admin_path = reverse(
            (
                f"admin:{instance._meta.app_label}_"
                f"{instance._meta.model_name}_change"
            ),
            args=[instance.pk],
        )

    except NoReverseMatch:
        logger.warning(
            "Admin change URL is unavailable for %s.",
            instance._meta.label,
        )
        return ""

    return request.build_absolute_uri(admin_path)


def home(request):
    if request.method == "POST":

        success = handle_contact_submission(request)

        # AJAX submission
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            # Clear Django messages because the frontend
            # toast will display the result instead.
            list(messages.get_messages(request))

            if success:
                return JsonResponse(
                    {
                        "status": "success",
                        "message": (
                            "We received your message. " "We'll get back to you soon."
                        ),
                    }
                )

            return JsonResponse(
                {
                    "status": "error",
                    "message": ("Please complete all required fields."),
                },
                status=400,
            )

        # Normal browser fallback
        return redirect("home")

    context = {
        "courses": Course.objects.all(),
        "services": Service.objects.all(),
        "projects": ClientProject.objects.all(),
        "reviews": StudentReview.objects.all(),
        "total_bookings": CourseBooking.objects.count(),
        "workshops": WorkshopPhoto.objects.all(),
        "certificates": Certificate.objects.all(),
        "internships": Internship.objects.all(),
        "upcoming_workshop": (
            UpcomingWorkshop.objects.filter(
                event_date__gte=timezone.localdate(),
            )
            .order_by(
                "event_date",
                "event_time",
            )
            .first()
        ),
    }

    return render(
        request,
        "index.html",
        context,
    )


def review_page(request):
    reviews = StudentReview.objects.all().order_by("-created_at")
    return render(request, "reviews.html", {"reviews": reviews})


def course_detail(request, id):
    course = get_object_or_404(Course, id=id)

    context = {
        "course": course,
        "description_lines": course.description.splitlines(),
    }

    return render(request, "courses.html", context)


def allcourse(request):
    context = {
        "allcourse": Course.objects.all(),
    }
    return render(request, "allcourse.html", context)


def about(request):
    return render(request, "about.html")


def courses(request):
    context = {
        "courses": Course.objects.all(),
    }
    return render(request, "courses.html", context)


def services(request):
    context = {
        "services": Service.objects.all(),
    }
    return render(request, "services.html", context)


def service_detail(request, pk):
    """
    Display a service and all database-controlled
    information related to that service.

    Active demos are made available to the demo-request
    form. Featured demos are displayed on the page.
    """

    service = get_object_or_404(
        Service,
        pk=pk,
    )

    # -------------------------------------------------
    # Active demos belonging only to this service
    # -------------------------------------------------

    available_demos = service.demo_links.filter(
        is_active=True,
    ).order_by(
        "order",
        "title",
    )

    # -------------------------------------------------
    # Featured demos shown on service detail page
    # -------------------------------------------------

    featured_demos = available_demos.filter(
        is_featured=True,
    )

    # -------------------------------------------------
    # Context
    # -------------------------------------------------

    context = {
        "service": service,
        # All active demos for registration/request form
        "available_demos": available_demos,
        # Only featured demos for visual demo cards
        "featured_demos": featured_demos,
        "features": (service.features.all()),
        "faqs": (service.faqs.all()),
        "process_steps": (ProcessStep.objects.all()),
        # Keep existing generic demo categories
        # so we do not break older functionality.
        "demo_categories": (
            DemoCategory.objects.filter(
                is_active=True,
            )
        ),
    }

    return render(
        request,
        "service_detail.html",
        context,
    )


def contact(request):
    if request.method == "POST":

        success = handle_contact_submission(request)

        # AJAX request — stay on contact page
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            # Remove queued Django messages.
            list(messages.get_messages(request))

            if success:
                return JsonResponse(
                    {
                        "status": "success",
                        "message": (
                            "We received your message. " "We'll get back to you soon."
                        ),
                    }
                )

            return JsonResponse(
                {
                    "status": "error",
                    "message": ("Please complete all required fields."),
                },
                status=400,
            )

        return redirect("contact")

    return render(
        request,
        "contact.html",
    )


def handle_contact_submission(request):
    """
    Save a contact enquiry and send:

    1. A clean confirmation email to the visitor.
    2. A complete notification email to the administrator.
    3. A direct link to the Contact record in Django admin.

    Returns True when the request was handled successfully,
    otherwise False.
    """

    name = (request.POST.get("name") or "").strip()

    email = (request.POST.get("email") or "").strip().lower()

    message = (request.POST.get("message") or "").strip()

    # -------------------------------------------------
    # Validate required fields
    # -------------------------------------------------

    if not name or not email or not message:
        messages.error(
            request,
            "Name, email and message are required.",
        )
        return False

    # -------------------------------------------------
    # Save enquiry
    # -------------------------------------------------

    contact_record = Contact.objects.create(
        name=name,
        email=email,
        message=message,
    )

    submitted_time = timezone.localtime().strftime(
        "%d %B %Y, %I:%M %p",
    )

    contact_admin_url = get_admin_change_url(
        request,
        contact_record,
    )

    # =================================================
    # USER CONFIRMATION EMAIL
    # =================================================

    user_body = """
    <p style="margin:0 0 15px;">
        Thank you for contacting
        <strong>Errors2Experts</strong>.
    </p>

    <p style="margin:0 0 15px;">
        We have successfully received your message.
    </p>

    <p style="margin:0;">
        Our team will review your enquiry and get back
        to you as soon as possible.
    </p>

    <div
        style="
            margin-top:20px;
            padding:16px 17px;
            background-color:#F2F5FA;
            border-left:3px solid #1D668E;
            border-radius:5px;
            color:#3E4651;
            font-size:13px;
            line-height:1.7;
        "
    >
        <strong style="color:#1D668E;">
            What happens next?
        </strong>

        <ul
            style="
                margin:10px 0 0;
                padding-left:19px;
            "
        >
            <li style="margin-bottom:6px;">
                Our team will review your message.
            </li>

            <li style="margin-bottom:6px;">
                We will contact you by email or phone
                when additional information is required.
            </li>

            <li>
                We will guide you regarding the appropriate
                service, training program or next step.
            </li>
        </ul>
    </div>
    """

    user_html = build_email_layout(
        title="Message Received",
        badge="ENQUIRY RECEIVED",
        subtitle=("Your message has been submitted " "successfully."),
        greeting=f"Hello {safe_html(name)},",
        body_html=user_body,
        accent="#1D668E",
        closing=("Thank you for connecting with " "Errors2Experts."),
        preheader=("We received your message and will " "get back to you soon."),
        footer_text=("Errors2Experts — Learn. Build. Grow."),
    )

    user_text = f"""
    Hello {name},

    Thank you for contacting Errors2Experts.

    We have successfully received your message.

    Our team will review your enquiry and get back
    to you as soon as possible.

    {build_text_social_links()}

    Best Regards,
    Errors2Experts Team
    """.strip()

    user_email_sent = send_email_safely(
        to_email=email,
        subject="Message Received | Errors2Experts",
        html_content=user_html,
        text_content=user_text,
    )

    # =================================================
    # ADMIN NOTIFICATION EMAIL
    # =================================================

    admin_details = build_detail_rows(
        [
            (
                "Name",
                name,
            ),
            (
                "Email",
                email,
            ),
            (
                "Submitted On",
                submitted_time,
            ),
        ],
        accent="#1D668E",
    )

    message_html = f"""
    <div style="margin-top:22px;">

        <p
            style="
                margin:0 0 9px;
                color:#262170;
                font-size:14px;
                font-weight:700;
            "
        >
            Customer Message
        </p>

        <div
            style="
                padding:15px 16px;
                background-color:#F2F5FA;
                border-left:3px solid #262170;
                border-radius:5px;
                color:#3E4651;
                font-size:13px;
                line-height:1.7;
            "
        >
            {safe_html(message)}
        </div>

    </div>
    """

    admin_body = """
    <p
        style="
            margin:0 0 14px;
            color:#242A33;
            font-size:14px;
            font-weight:700;
        "
    >
        A new contact enquiry has been submitted through
        the Errors2Experts website.
    </p>

    <p
        style="
            margin:0;
            color:#515B68;
            font-size:14px;
            line-height:1.7;
        "
    >
        Review the visitor information and message below,
        then follow up when required.
    </p>
    """

    admin_html = build_email_layout(
        title="New Contact Enquiry",
        badge="NEW ENQUIRY",
        subtitle=(f"{safe_html(name)} sent a message " "through the website."),
        greeting="",
        body_html=admin_body,
        details_html=admin_details,
        extra_html=message_html,
        button_text=("Open Contact Enquiry in Admin" if contact_admin_url else ""),
        button_url=contact_admin_url,
        accent="#1D668E",
        preheader=(f"New contact enquiry received from {name}."),
        footer_text=(
            "This notification was generated by the " "Errors2Experts website."
        ),
    )

    admin_text = f"""
    NEW CONTACT ENQUIRY

    Name: {name}
    Email: {email}
    Submitted On: {submitted_time}

    Message:
    {message}

    Open in Admin:
    {contact_admin_url or "Admin URL unavailable."}

    Errors2Experts System
    """.strip()

    admin_email = str(
        getattr(
            settings,
            "ADMIN_NOTIFICATION_EMAIL",
            "",
        )
    ).strip()

    if admin_email:
        send_email_safely(
            to_email=admin_email,
            subject=f"New Contact Enquiry | {name}",
            html_content=admin_html,
            text_content=admin_text,
        )

    else:
        logger.warning(
            "ADMIN_NOTIFICATION_EMAIL is not configured. "
            "Contact admin email was skipped. "
            "Contact ID=%s",
            contact_record.pk,
        )

    # -------------------------------------------------
    # User feedback
    # -------------------------------------------------

    if user_email_sent:
        messages.success(
            request,
            ("Your message was sent successfully. " "We'll get back to you soon."),
        )
    else:
        messages.success(
            request,
            (
                "Your message was saved successfully, "
                "but the confirmation email could not "
                "be sent at this time."
            ),
        )

    return True


def placement(request):
    context = {
        "placements": Placement.objects.all(),
    }

    return render(request, "placement.html", context)

def career_list(request):

    careers = (
        Career.objects
        .filter(is_active=True)
        .order_by("-posted_on")
    )

    total_openings = (
        careers.aggregate(
            total=Sum("openings"),
        )["total"]
        or 0
    )

    employment_counts = []

    for value, label in Career.EMPLOYMENT_TYPES:

        count = careers.filter(
            employment_type=value,
        ).count()

        if count:

            employment_counts.append(
                {
                    "key": slugify(value),
                    "label": label,
                    "count": count,
                }
            )

    return render(
        request,
        "career.html",
        {
            "careers": careers,
            "career_count": careers.count(),
            "total_openings": total_openings,
            "employment_counts": employment_counts,
        },
    )


def career_detail(request, pk):

    career = get_object_or_404(
        Career,
        pk=pk,
        is_active=True,
    )

    return render(
        request,
        "career_detail.html",
        {
            "career": career,
        },
    )

def apply_job(request, pk):
    """
    Save a job application from the Career Detail modal.

    Email behaviour:
    ------------------------------------------------------------
    Applicant:
        - Receives a formal confirmation email only.
        - Does NOT receive resume URL.
        - Does NOT receive Django admin URL.
        - Does NOT receive internal recruitment links.

    Administrator:
        - Receives complete candidate details.
        - Receives resume URL.
        - Receives Django admin application URL.

    Frontend:
        - AJAX response keeps the applicant on the same page.
        - Success popup is shown after submission.
    """

    career = get_object_or_404(
        Career,
        pk=pk,
    )

    # =========================================================
    # ONLY POST IS USED BY THE CAREER APPLICATION MODAL
    # =========================================================

    if request.method != "POST":

        return redirect(
            "career_detail",
            pk=career.pk,
        )

    # =========================================================
    # VALIDATE FORM
    # =========================================================

    form = JobApplicationForm(
        request.POST,
        request.FILES,
    )

    if not form.is_valid():

        if (
            request.headers.get(
                "X-Requested-With",
            )
            == "XMLHttpRequest"
        ):

            errors = {}

            for field_name, field_errors in form.errors.items():

                errors[field_name] = [
                    str(error)
                    for error in field_errors
                ]

            return JsonResponse(
                {
                    "status": "error",
                    "message": (
                        "Please check the highlighted fields "
                        "and submit your application again."
                    ),
                    "errors": errors,
                },
                status=400,
            )

        messages.error(
            request,
            "Please complete all required application fields.",
        )

        return redirect(
            "career_detail",
            pk=career.pk,
        )

    # =========================================================
    # SAVE APPLICATION
    # =========================================================

    application = form.save(
        commit=False,
    )

    application.career = career

    application.save()

    applied_time = timezone.localtime(
        application.applied_on,
    ).strftime(
        "%d %B %Y, %I:%M %p",
    )

    # =========================================================
    # APPLICATION REFERENCE
    # =========================================================

    application_reference = (
        f"E2E-CAREER-{application.pk:05d}"
    )

    # =========================================================
    # RESUME URL
    #
    # IMPORTANT:
    # This URL is used ONLY in the administrator email.
    # It is never sent to the applicant.
    # =========================================================

    resume_url = ""

    if application.resume:

        try:

            resume_url = request.build_absolute_uri(
                application.resume.url,
            )

        except (AttributeError, ValueError):

            logger.warning(
                (
                    "Could not create resume URL for "
                    "job application %s."
                ),
                application.pk,
            )

    # =========================================================
    # ADMIN URL
    #
    # IMPORTANT:
    # This URL is used ONLY in the administrator email.
    # =========================================================

    admin_url = get_admin_change_url(
        request,
        application,
    )

    # =========================================================
    # APPLICANT CONFIRMATION EMAIL
    # =========================================================

    candidate_body = f"""
    <p
        style="
            margin:0 0 16px;
            color:#3E4651;
            font-size:14px;
            line-height:1.75;
        "
    >
        Thank you for your interest in joining
        <strong>Errors2Experts</strong>.
    </p>

    <p
        style="
            margin:0 0 16px;
            color:#3E4651;
            font-size:14px;
            line-height:1.75;
        "
    >
        We are pleased to confirm that your application for
        the position of
        <strong>{safe_html(career.role)}</strong>
        has been received successfully.
    </p>

    <div
        style="
            margin:22px 0;
            padding:18px;
            background:#F5FAF6;
            border:1px solid #DDEADF;
            border-left:4px solid #2E7D32;
            border-radius:8px;
        "
    >
        <p
            style="
                margin:0 0 5px;
                color:#768178;
                font-size:11px;
                font-weight:700;
                letter-spacing:0.8px;
                text-transform:uppercase;
            "
        >
            Position Applied
        </p>

        <p
            style="
                margin:0;
                color:#26342B;
                font-size:16px;
                font-weight:700;
            "
        >
            {safe_html(career.role)}
        </p>

        <div
            style="
                height:1px;
                margin:15px 0;
                background:#E0EAE2;
            "
        ></div>

        <p
            style="
                margin:0 0 5px;
                color:#768178;
                font-size:11px;
                font-weight:700;
                letter-spacing:0.8px;
                text-transform:uppercase;
            "
        >
            Application Reference
        </p>

        <p
            style="
                margin:0;
                color:#2E7D32;
                font-size:14px;
                font-weight:700;
            "
        >
            {application_reference}
        </p>
    </div>

    <p
        style="
            margin:0 0 16px;
            color:#3E4651;
            font-size:14px;
            line-height:1.75;
        "
    >
        Our recruitment team will carefully review your
        qualifications and submitted information against the
        requirements of the position.
    </p>

    <div
        style="
            margin-top:20px;
            padding:17px 18px;
            background:#F7F9F8;
            border-radius:8px;
        "
    >
        <p
            style="
                margin:0 0 10px;
                color:#26342B;
                font-size:13px;
                font-weight:700;
            "
        >
            What happens next?
        </p>

        <ol
            style="
                margin:0;
                padding-left:19px;
                color:#56635B;
                font-size:13px;
                line-height:1.75;
            "
        >
            <li style="margin-bottom:6px;">
                Our recruitment team will review your application.
            </li>

            <li style="margin-bottom:6px;">
                If your profile matches the requirements,
                you will be shortlisted for the next stage.
            </li>

            <li>
                Shortlisted candidates will be contacted
                through the email address or mobile number
                provided during application.
            </li>
        </ol>
    </div>

    <p
        style="
            margin:20px 0 0;
            color:#6E7972;
            font-size:12px;
            line-height:1.65;
        "
    >
        Please retain this email and your application reference
        for future correspondence.
    </p>
    """

    candidate_html = build_email_layout(
        title="Application Received",
        badge="CAREER APPLICATION",
        subtitle=(
            "Thank you for your interest in joining "
            "Errors2Experts."
        ),
        greeting=(
            f"Dear "
            f"{safe_html(application.full_name)},"
        ),
        body_html=candidate_body,
        accent="#2E7D32",
        closing=(
            "We appreciate the time you have taken to apply "
            "and wish you the very best in the selection process."
        ),
        preheader=(
            f"Your application for {career.role} "
            "has been received successfully."
        ),
        footer_text=(
            "This is an automated acknowledgement from "
            "Errors2Experts. Please do not send confidential "
            "information in reply to this message."
        ),
    )

    candidate_text = f"""
Dear {application.full_name},

Thank you for your interest in joining Errors2Experts.

We are pleased to confirm that your application has been
received successfully.

Position Applied:
{career.role}

Application Reference:
{application_reference}

Our recruitment team will review your qualifications and
submitted information against the requirements of the position.

What happens next?

1. Our recruitment team will review your application.

2. If your profile matches the requirements, you will be
   shortlisted for the next stage.

3. Shortlisted candidates will be contacted through the email
   address or mobile number provided during application.

Please retain this email and your application reference for
future correspondence.

We appreciate the time you have taken to apply and wish you
the very best in the selection process.

{build_text_social_links()}

Best Regards,
Errors2Experts Recruitment Team
""".strip()

    candidate_email_sent = send_email_safely(
        to_email=application.email,
        subject=(
            f"Application Received – "
            f"{career.role} | Errors2Experts"
        ),
        html_content=candidate_html,
        text_content=candidate_text,
    )

    # =========================================================
    # ADMIN EMAIL DETAILS
    # =========================================================

    admin_details = build_detail_rows(
        [
            (
                "Application Reference",
                application_reference,
            ),
            (
                "Candidate",
                application.full_name,
            ),
            (
                "Email",
                application.email,
            ),
            (
                "Mobile",
                application.mobile,
            ),
            (
                "Education",
                application.education,
            ),
            (
                "Passed Out Year",
                application.year_passed_out,
            ),
            (
                "Role",
                career.role,
            ),
            (
                "Employment Type",
                career.employment_type,
            ),
            (
                "Applied On",
                applied_time,
            ),
        ],
        accent="#2E7D32",
    )

    # =========================================================
    # COVER LETTER FOR ADMIN
    # =========================================================

    safe_cover_letter = safe_html(
        application.cover_letter
        or "No cover letter was provided."
    )

    cover_letter_html = f"""
    <div style="margin-top:22px;">

        <p
            style="
                margin:0 0 9px;
                color:#2E7D32;
                font-family:Arial,Helvetica,sans-serif;
                font-size:14px;
                font-weight:700;
            "
        >
            Cover Letter
        </p>

        <div
            style="
                padding:15px 16px;
                background:#F2F8F3;
                border-left:3px solid #2E7D32;
                border-radius:6px;
                color:#3E4651;
                font-family:Arial,Helvetica,sans-serif;
                font-size:13px;
                line-height:1.7;
            "
        >
            {safe_cover_letter}
        </div>

    </div>
    """

    # =========================================================
    # ADMIN EMAIL
    #
    # Admin receives:
    # - Candidate details
    # - Cover letter
    # - Resume URL button
    # - Django Admin URL button
    # =========================================================

    admin_body = """
    <p
        style="
            margin:0 0 14px;
            color:#242A33;
            font-size:14px;
            font-weight:700;
        "
    >
        A new candidate has submitted a career application
        through the Errors2Experts website.
    </p>

    <p
        style="
            margin:0;
            color:#515B68;
            font-size:14px;
            line-height:1.7;
        "
    >
        Review the candidate information below.
        Use the resume link to review the submitted CV
        and open the application in Django Admin for
        further recruitment action.
    </p>
    """

    admin_html = build_email_layout(
        title=(
            f"New Application: "
            f"{career.role}"
        ),
        badge="NEW CANDIDATE",
        subtitle=(
            f"{safe_html(application.full_name)} "
            f"applied for "
            f"{safe_html(career.role)}."
        ),
        greeting="",
        body_html=admin_body,
        details_html=admin_details,
        extra_html=cover_letter_html,

        # -----------------------------------------------------
        # ADMIN ONLY — RESUME URL
        # -----------------------------------------------------

        button_text=(
            "View Candidate Resume"
            if resume_url
            else ""
        ),
        button_url=resume_url,

        # -----------------------------------------------------
        # ADMIN ONLY — DJANGO ADMIN URL
        # -----------------------------------------------------

        secondary_button_text=(
            "Open Application in Admin"
            if admin_url
            else ""
        ),
        secondary_button_url=admin_url,

        accent="#2E7D32",
        preheader=(
            f"New application from "
            f"{application.full_name} for "
            f"{career.role}."
        ),
        footer_text=(
            "This recruitment notification was generated "
            "automatically by the Errors2Experts website."
        ),
    )

    admin_text = f"""
NEW JOB APPLICATION

Application Reference:
{application_reference}

Candidate:
{application.full_name}

Email:
{application.email}

Mobile:
{application.mobile}

Education:
{application.education}

Passed Out Year:
{application.year_passed_out}

Role:
{career.role}

Employment Type:
{career.employment_type}

Applied On:
{applied_time}

Cover Letter:
{application.cover_letter or "No cover letter was provided."}

Candidate Resume:
{resume_url or "Resume URL unavailable."}

Open Application in Django Admin:
{admin_url or "Admin URL unavailable."}

Errors2Experts Recruitment System
""".strip()

    admin_email = str(
        getattr(
            settings,
            "ADMIN_NOTIFICATION_EMAIL",
            "",
        )
    ).strip()

    admin_email_sent = False

    if admin_email:

        admin_email_sent = send_email_safely(
            to_email=admin_email,
            subject=(
                f"New Career Application – "
                f"{career.role} | Errors2Experts"
            ),
            html_content=admin_html,
            text_content=admin_text,
        )

    else:

        logger.warning(
            (
                "ADMIN_NOTIFICATION_EMAIL is not configured. "
                "JobApplication ID=%s"
            ),
            application.pk,
        )

    # =========================================================
    # LOG RESULT
    # =========================================================

    logger.info(
        (
            "Job application saved. "
            "ID=%s Reference=%s "
            "candidate_email_sent=%s "
            "admin_email_sent=%s"
        ),
        application.pk,
        application_reference,
        candidate_email_sent,
        admin_email_sent,
    )

    # =========================================================
    # AJAX RESPONSE
    # =========================================================

    if (
        request.headers.get(
            "X-Requested-With",
        )
        == "XMLHttpRequest"
    ):

        if candidate_email_sent:

            success_message = (
                "Your application has been submitted successfully. "
                "A formal confirmation email has been sent to "
                "your registered email address."
            )

        else:

            success_message = (
                "Your application has been submitted successfully. "
                "Our recruitment team will review your profile shortly."
            )

        return JsonResponse(
            {
                "status": "success",
                "message": success_message,
                "application_id": application.pk,
                "application_reference": application_reference,
                "candidate_email_sent": (
                    candidate_email_sent
                ),
                "admin_email_sent": (
                    admin_email_sent
                ),
            }
        )

    # =========================================================
    # NON-AJAX FALLBACK
    # =========================================================

    if candidate_email_sent:

        messages.success(
            request,
            (
                "Your application was submitted successfully. "
                "A confirmation email has been sent to you."
            ),
        )

    else:

        messages.success(
            request,
            (
                "Your application was submitted successfully. "
                "Our recruitment team will review it shortly."
            ),
        )

    return redirect(
        "career_detail",
        pk=career.pk,
    )

def demo_booking(request):
    """
    Save a demo booking and send:

    1. A simple confirmation email to the user.
    2. A complete notification email to the administrator.
    """

    if request.method != "POST":
        return JsonResponse(
            {
                "status": "failed",
                "message": "Only POST requests are allowed.",
            },
            status=405,
        )

    name = (request.POST.get("name") or "").strip()

    email = (request.POST.get("email") or "").strip().lower()

    mobile = (request.POST.get("mobile") or "").strip()

    education = (request.POST.get("education") or "").strip()

    source = (request.POST.get("source") or "").strip()

    # -------------------------------------------------
    # Validate required fields
    # -------------------------------------------------

    if not name or not email or not mobile:
        return JsonResponse(
            {
                "status": "failed",
                "message": ("Name, email and mobile number " "are required."),
            },
            status=400,
        )

    # -------------------------------------------------
    # Save demo booking
    # -------------------------------------------------

    demo_booking_record = DemoBooking.objects.create(
        name=name,
        email=email,
        mobile=mobile,
        education=education,
        source=source,
    )

    booking_time = timezone.localtime().strftime(
        "%d %B %Y, %I:%M %p",
    )

    demo_admin_url = get_admin_change_url(
        request,
        demo_booking_record,
    )

    # =================================================
    # USER CONFIRMATION EMAIL
    # =================================================

    user_body = """
    <p style="margin:0 0 15px;">
        Thank you for showing interest in learning with
        <strong>Errors2Experts</strong>.
    </p>

    <p style="margin:0 0 15px;">
        We have successfully received your demo booking.
        Our team will review your request and contact you
        regarding the next steps.
    </p>

    <div
        style="
            margin-top:20px;
            padding:16px 17px;
            background-color:#F2F5FA;
            border-left:3px solid #1D668E;
            border-radius:5px;
            color:#3E4651;
            font-size:13px;
            line-height:1.7;
        "
    >
        <strong style="color:#1D668E;">
            What happens next?
        </strong>

        <ul
            style="
                margin:10px 0 0;
                padding-left:19px;
            "
        >
            <li style="margin-bottom:6px;">
                Our team will review your demo request.
            </li>

            <li style="margin-bottom:6px;">
                You will receive a call or email from us.
            </li>

            <li>
                We will guide you through the available
                courses and learning options.
            </li>
        </ul>
    </div>
    """

    user_html = build_email_layout(
        title="Demo Booking Received",
        badge="BOOKING CONFIRMED",
        subtitle=("Your Errors2Experts demo request was " "submitted successfully."),
        greeting=f"Hello {safe_html(name)},",
        body_html=user_body,
        accent="#1D668E",
        closing=(
            "We look forward to helping you learn, " "grow and build your future."
        ),
        preheader=("Your Errors2Experts demo booking has " "been received."),
        footer_text=("Thank you for connecting with " "Errors2Experts."),
    )

    user_text = f"""
Hello {name},

Greetings from Errors2Experts.

We have successfully received your demo booking.

What happens next?

1. Our team will review your demo request.
2. You will receive a call or email from us.
3. We will guide you through the available learning options.

We look forward to helping you learn, grow and build
your future.

{build_text_social_links()}

Best Regards,
Errors2Experts Team
""".strip()

    user_email_sent = send_email_safely(
        to_email=email,
        subject="Demo Booking Received | Errors2Experts",
        html_content=user_html,
        text_content=user_text,
    )

    # =================================================
    # ADMIN NOTIFICATION EMAIL
    # =================================================

    admin_details = build_detail_rows(
        [
            (
                "Name",
                name,
            ),
            (
                "Email",
                email,
            ),
            (
                "Mobile",
                mobile,
            ),
            (
                "Education",
                education or "Not provided",
            ),
            (
                "Source",
                source or "Not specified",
            ),
            (
                "Booking Time",
                booking_time,
            ),
        ],
        accent="#1D668E",
    )

    admin_body = """
    <p
        style="
            margin:0 0 14px;
            color:#242A33;
            font-size:14px;
            font-weight:700;
        "
    >
        A new demo booking has been submitted through
        the Errors2Experts website.
    </p>

    <p
        style="
            margin:0;
            color:#515B68;
            font-size:14px;
            line-height:1.7;
        "
    >
        Review the customer information below and contact
        them regarding the requested demo session.
    </p>
    """

    admin_html = build_email_layout(
        title="New Demo Booking",
        badge="NEW DEMO REQUEST",
        subtitle=(f"{safe_html(name)} requested a demo session."),
        greeting="",
        body_html=admin_body,
        details_html=admin_details,
        button_text=("Open Demo Booking in Admin" if demo_admin_url else ""),
        button_url=demo_admin_url,
        accent="#1D668E",
        preheader=(f"New demo booking received from {name}."),
        footer_text=(
            "This notification was generated by the " "Errors2Experts website."
        ),
    )

    admin_text = f"""
    NEW DEMO BOOKING

    Name: {name}
    Email: {email}
    Mobile: {mobile}
    Education: {education or "Not provided"}
    Source: {source or "Not specified"}
    Booking Time: {booking_time}

    Open in Admin:
    {demo_admin_url or "Admin URL unavailable."}

    Please contact the customer regarding the demo session.

    Errors2Experts System
    """.strip()

    admin_email = str(
        getattr(
            settings,
            "ADMIN_NOTIFICATION_EMAIL",
            "",
        )
    ).strip()

    if admin_email:
        send_email_safely(
            to_email=admin_email,
            subject="New Demo Booking | Errors2Experts",
            html_content=admin_html,
            text_content=admin_text,
        )

    else:
        logger.warning(
            "ADMIN_NOTIFICATION_EMAIL is not configured. "
            "Admin demo-booking email was skipped. "
            "DemoBooking ID=%s",
            demo_booking_record.pk,
        )

    return JsonResponse(
        {
            "status": "success",
            "message": ("Your demo booking was submitted " "successfully."),
            "email_sent": user_email_sent,
        }
    )


def book_course(request, id):
    """
    Save a course booking and calculate the payment
    amount based on the selected payment method.

    Payment methods:
    - Full Payment: 100% of the course fee
    - Half Payment: 50% of the course fee
    - Installment: First of three installments

    After the booking is created, a dynamic UPI QR
    containing the exact payable amount is generated.
    """

    course = get_object_or_404(
        Course,
        id=id,
    )

    # -------------------------------------------------
    # Only POST requests can create a booking
    # -------------------------------------------------

    if request.method != "POST":
        return redirect(
            "course_detail",
            id=id,
        )

    # -------------------------------------------------
    # Get form values
    # -------------------------------------------------

    name = (request.POST.get("name") or "").strip()

    email = (request.POST.get("email") or "").strip().lower()

    mobile = (request.POST.get("mobile") or "").strip()

    education = (request.POST.get("education") or "").strip()

    year_passed = (request.POST.get("year_passed") or "").strip()

    payment_type = (request.POST.get("payment_type") or "").strip().lower()

    # -------------------------------------------------
    # Validate required fields
    # -------------------------------------------------

    if not name or not email or not mobile:
        messages.error(
            request,
            ("Name, email and mobile number " "are required."),
        )

        return redirect(
            "course_detail",
            id=id,
        )

    # -------------------------------------------------
    # Mobile validation
    # -------------------------------------------------

    if not mobile.isdigit() or len(mobile) != 10:
        messages.error(
            request,
            "Please enter a valid 10-digit mobile number.",
        )

        return redirect(
            "course_detail",
            id=id,
        )

    # -------------------------------------------------
    # Payment method validation
    # -------------------------------------------------

    valid_payment_types = {
        "full",
        "half",
        "installment",
    }

    if payment_type not in valid_payment_types:
        messages.error(
            request,
            "Please select a valid payment method.",
        )

        return redirect(
            "course_detail",
            id=id,
        )

    # -------------------------------------------------
    # Validate and normalize course fee
    # -------------------------------------------------

    try:
        total_course_fee = Decimal(str(course.price)).quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP,
        )

    except (
        InvalidOperation,
        TypeError,
        ValueError,
    ):
        logger.exception(
            "Invalid price configured for course ID=%s.",
            course.pk,
        )

        messages.error(
            request,
            ("The course price is unavailable. " "Please contact Errors2Experts."),
        )

        return redirect(
            "course_detail",
            id=id,
        )

    if total_course_fee <= 0:
        logger.warning(
            "Course ID=%s has invalid fee: %s",
            course.pk,
            total_course_fee,
        )

        messages.error(
            request,
            "The configured course price is invalid.",
        )

        return redirect(
            "course_detail",
            id=id,
        )

    # -------------------------------------------------
    # Calculate payment
    # -------------------------------------------------

    if payment_type == "full":

        amount_to_pay = total_course_fee

        remaining_balance = Decimal("0")

        payment_method = "Full Payment"

    elif payment_type == "half":

        amount_to_pay = (total_course_fee / Decimal("2")).quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP,
        )

        remaining_balance = total_course_fee - amount_to_pay

        payment_method = "Half Payment"

    else:

        amount_to_pay = (total_course_fee / Decimal("3")).quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP,
        )

        remaining_balance = total_course_fee - amount_to_pay

        payment_method = "Installment – 1 of 3"

    # -------------------------------------------------
    # Convert to integer because CourseBooking currently
    # stores these fields as IntegerField
    # -------------------------------------------------

    total_course_fee_value = int(total_course_fee)

    amount_to_pay_value = int(amount_to_pay)

    remaining_balance_value = int(remaining_balance)

    # -------------------------------------------------
    # Save booking
    # -------------------------------------------------

    try:
        booking = CourseBooking.objects.create(
            name=name,
            email=email,
            mobile=mobile,
            education=education,
            year_passed=year_passed,
            course=course.title,
            total_amount=total_course_fee_value,
            payment_type=payment_type,
            amount=amount_to_pay_value,
            balance=remaining_balance_value,
        )

    except Exception:
        logger.exception(
            "Failed to create CourseBooking " "for course ID=%s.",
            course.pk,
        )

        messages.error(
            request,
            ("We could not save your course booking. " "Please try again."),
        )

        return redirect(
            "course_detail",
            id=id,
        )

    # -------------------------------------------------
    # Booking time
    # -------------------------------------------------

    booking_time = timezone.localtime(booking.created_at).strftime(
        "%d %B %Y, %I:%M %p",
    )

    # -------------------------------------------------
    # Django admin URL
    # -------------------------------------------------

    course_booking_admin_url = get_admin_change_url(
        request,
        booking,
    )

    # =================================================
    # STUDENT EMAIL
    # =================================================

    student_payment_details = build_detail_rows(
        [
            (
                "Course",
                course.title,
            ),
            (
                "Payment Method",
                payment_method,
            ),
            (
                "Amount to Pay",
                f"₹{amount_to_pay_value:,}",
            ),
        ],
        accent="#1D668E",
    )

    # -------------------------------------------------
    # Extra payment information
    # -------------------------------------------------

    if payment_type == "full":

        payment_extra_html = """
        <div
            style="
                margin-top:18px;
                padding:14px 16px;
                background:#EEF8F1;
                border-left:3px solid #2E7D32;
                border-radius:6px;
                color:#3E5143;
                font-size:13px;
                line-height:1.7;
            "
        >
            <strong>
                Full Payment Selected
            </strong>

            <p style="margin:7px 0 0;">
                No remaining course fee will be due
                after this payment is verified.
            </p>
        </div>
        """

    elif payment_type == "half":

        payment_extra_html = f"""
        <div
            style="
                margin-top:18px;
                padding:14px 16px;
                background:#FFF8E8;
                border-left:3px solid #C28A1C;
                border-radius:6px;
                color:#51461F;
                font-size:13px;
                line-height:1.7;
            "
        >
            <strong>
                Half Payment Selected
            </strong>

            <p style="margin:7px 0 0;">
                Remaining balance:
                <strong>
                    ₹{remaining_balance_value:,}
                </strong>
            </p>
        </div>
        """

    else:

        payment_extra_html = f"""
        <div
            style="
                margin-top:18px;
                padding:14px 16px;
                background:#F3F5FF;
                border-left:3px solid #4455A5;
                border-radius:6px;
                color:#414866;
                font-size:13px;
                line-height:1.7;
            "
        >
            <strong>
                Installment Payment Selected
            </strong>

            <p style="margin:7px 0 0;">
                This payment represents the first
                installment of three.
            </p>

            <p style="margin:5px 0 0;">
                Remaining course balance:
                <strong>
                    ₹{remaining_balance_value:,}
                </strong>
            </p>
        </div>
        """

    student_body = f"""
    <p style="margin:0 0 15px;">
        Thank you for booking
        <strong>
            {safe_html(course.title)}
        </strong>
        with Errors2Experts.
    </p>

    <p style="margin:0 0 15px;">
        Your course booking has been received
        successfully.
    </p>

    <p style="margin:0;">
        Scan the payment QR displayed after
        registration and pay exactly
        <strong>
            ₹{amount_to_pay_value:,}
        </strong>.
    </p>

    {payment_extra_html}

    <div
        style="
            margin-top:20px;
            padding:16px 17px;
            background-color:#F2F5FA;
            border-left:3px solid #1D668E;
            border-radius:5px;
            color:#3E4651;
            font-size:13px;
            line-height:1.7;
        "
    >
        <strong style="color:#1D668E;">
            After completing the payment
        </strong>

        <p style="margin:10px 0 0;">
            Send your payment screenshot through:
        </p>

        <p style="margin:9px 0 0;">
            <strong>WhatsApp:</strong>
            +91 93633 42646
            <br>

            <strong>Email:</strong>
            errors2experts.official@gmail.com
        </p>

        <p style="margin:9px 0 0;">
            Your booking will be confirmed after
            our team verifies the payment.
        </p>
    </div>
    """

    student_html = build_email_layout(
        title="Course Booking Received",
        badge="BOOKING RECEIVED",
        subtitle=(f"Your booking for {course.title} " "was submitted successfully."),
        greeting=(f"Hello {safe_html(name)},"),
        body_html=student_body,
        details_html=student_payment_details,
        accent="#1D668E",
        closing=(
            "Your booking will be confirmed after " "our team verifies your payment."
        ),
        preheader=(
            f"Amount to pay: " f"₹{amount_to_pay_value:,} " f"using {payment_method}."
        ),
        footer_text=("Thank you for choosing Errors2Experts."),
    )

    student_text = f"""
    Hello {name},

    Your course booking has been received successfully.

    Course:
    {course.title}

    Payment Method:
    {payment_method}

    Total Course Fee:
    ₹{total_course_fee_value:,}

    Amount to Pay:
    ₹{amount_to_pay_value:,}

    Remaining Balance:
    ₹{remaining_balance_value:,}

    Please scan the payment QR shown after registration
    and complete the payment.

    After payment, send your screenshot through:

    WhatsApp: +91 93633 42646
    Email: errors2experts.official@gmail.com

    Your booking will be confirmed after our team
    verifies your payment.

    {build_text_social_links()}

    Best Regards,
    Errors2Experts Team
    """.strip()

    send_email_safely(
        to_email=email,
        subject=("Course Booking Received | " "Errors2Experts"),
        html_content=student_html,
        text_content=student_text,
    )

    # =================================================
    # ADMIN EMAIL
    # =================================================

    admin_details = build_detail_rows(
        [
            (
                "Student",
                name,
            ),
            (
                "Email",
                email,
            ),
            (
                "Mobile",
                mobile,
            ),
            (
                "Education",
                education or "Not provided",
            ),
            (
                "Passed Out Year",
                year_passed or "Not provided",
            ),
            (
                "Course",
                course.title,
            ),
            (
                "Total Course Fee",
                f"₹{total_course_fee_value:,}",
            ),
            (
                "Selected Payment Method",
                payment_method,
            ),
            (
                "Amount to Pay",
                f"₹{amount_to_pay_value:,}",
            ),
            (
                "Remaining Balance",
                f"₹{remaining_balance_value:,}",
            ),
            (
                "Payment Status",
                "Pending Verification",
            ),
            (
                "Booking Time",
                booking_time,
            ),
        ],
        accent="#1D668E",
    )

    admin_body = """
    <p
        style="
            margin:0 0 14px;
            color:#242A33;
            font-size:14px;
            font-weight:700;
        "
    >
        A new course booking has been submitted
        through the Errors2Experts website.
    </p>

    <p
        style="
            margin:0;
            color:#515B68;
            font-size:14px;
            line-height:1.7;
        "
    >
        The student selected a payment method.
        Payment verification must be completed
        manually after receiving the payment
        screenshot.
    </p>
    """

    admin_html = build_email_layout(
        title="New Course Booking",
        badge="PAYMENT PENDING",
        subtitle=(f"{safe_html(name)} booked " f"{safe_html(course.title)}."),
        greeting="",
        body_html=admin_body,
        details_html=admin_details,
        button_text=(
            "Open Course Booking in Admin" if course_booking_admin_url else ""
        ),
        button_url=course_booking_admin_url,
        accent="#1D668E",
        preheader=(f"{name} selected " f"{payment_method} for " f"{course.title}."),
        footer_text=(
            "This notification was generated by " "the Errors2Experts website."
        ),
    )

    admin_text = f"""
NEW COURSE BOOKING

Student:
{name}

Email:
{email}

Mobile:
{mobile}

Education:
{education or "Not provided"}

Passed Out Year:
{year_passed or "Not provided"}

Course:
{course.title}

Total Course Fee:
₹{total_course_fee_value:,}

Payment Method:
{payment_method}

Amount to Pay:
₹{amount_to_pay_value:,}

Remaining Balance:
₹{remaining_balance_value:,}

Payment Status:
Pending Verification

Booking Time:
{booking_time}

Open in Admin:
{course_booking_admin_url or "Admin URL unavailable."}

Errors2Experts System
""".strip()

    admin_email = str(
        getattr(
            settings,
            "ADMIN_NOTIFICATION_EMAIL",
            "",
        )
    ).strip()

    if admin_email:

        send_email_safely(
            to_email=admin_email,
            subject=(f"New Course Booking | " f"{course.title}"),
            html_content=admin_html,
            text_content=admin_text,
        )

    else:

        logger.warning(
            "ADMIN_NOTIFICATION_EMAIL is not configured. "
            "Course booking admin email skipped. "
            "CourseBooking ID=%s",
            booking.pk,
        )

    # =================================================
    # DYNAMIC UPI QR
    # =================================================

    payment_note = f"Errors2Experts Course - " f"{course.title}"

    try:

        upi_qr = generate_upi_qr_base64(
            amount=amount_to_pay_value,
            note=payment_note,
        )

    except Exception:

        # Do not destroy the successful booking
        # just because QR generation failed.
        logger.exception(
            "Dynamic UPI QR generation failed. " "CourseBooking ID=%s",
            booking.pk,
        )

        upi_qr = ""

    # -------------------------------------------------
    # Show QR payment page
    # -------------------------------------------------

    return render(
        request,
        "show_qr.html",
        {
            "booking": booking,
            "course": course,
            "course_title": course.title,
            "total_amount": (total_course_fee_value),
            "amount": (amount_to_pay_value),
            "balance": (remaining_balance_value),
            "payment_type": (payment_type),
            "payment_method": (payment_method),
            "upi_qr": (upi_qr),
        },
    )


def service_booking(request):
    """
    Save a service request and send:

    1. A simple confirmation email to the customer.
    2. A complete notification email to the administrator.
    3. A direct Django admin link in the administrator email.
    """

    if request.method != "POST":
        return redirect("services")

    # -------------------------------------------------
    # Get submitted form data
    # -------------------------------------------------

    full_name = (request.POST.get("full_name") or "").strip()

    email = (request.POST.get("email") or "").strip().lower()

    mobile = (request.POST.get("mobile") or "").strip()

    service_name = (request.POST.get("service_name") or "").strip()

    message = (request.POST.get("message") or "").strip()

    preferred_date_raw = (request.POST.get("preferred_date") or "").strip()

    # -------------------------------------------------
    # Validate required fields
    # -------------------------------------------------

    if not full_name or not email or not mobile or not service_name:
        messages.error(
            request,
            ("Name, email, mobile number and " "service are required."),
        )

        return redirect("services")

    # -------------------------------------------------
    # Validate and format preferred date
    # -------------------------------------------------

    preferred_date = None
    preferred_date_text = "Not specified"

    if preferred_date_raw:
        try:
            preferred_date = datetime.strptime(
                preferred_date_raw,
                "%Y-%m-%d",
            ).date()

            preferred_date_text = preferred_date.strftime(
                "%d %B %Y",
            )

        except ValueError:
            messages.error(
                request,
                "Please select a valid preferred date.",
            )

            return redirect("services")

    # -------------------------------------------------
    # Save service booking
    # -------------------------------------------------

    booking = ServiceBooking.objects.create(
        full_name=full_name,
        email=email,
        mobile=mobile,
        service_name=service_name,
        message=message,
        preferred_date=preferred_date,
    )

    submitted_time = timezone.localtime().strftime(
        "%d %B %Y, %I:%M %p",
    )

    service_admin_url = get_admin_change_url(
        request,
        booking,
    )

    # =================================================
    # CUSTOMER CONFIRMATION EMAIL
    # =================================================

    customer_body = f"""
    <p style="margin:0 0 15px;">
        Thank you for contacting
        <strong>Errors2Experts</strong>.
    </p>

    <p style="margin:0 0 15px;">
        We have successfully received your request for
        <strong>{safe_html(service_name)}</strong>.
    </p>

    <p style="margin:0;">
        Our team will review your requirement and contact
        you as soon as possible.
    </p>

    <div
        style="
            margin-top:21px;
            padding:16px 17px;
            background-color:#F2F5FA;
            border-left:3px solid #1D668E;
            border-radius:5px;
            color:#3E4651;
            font-family:Arial,Helvetica,sans-serif;
            font-size:13px;
            line-height:1.7;
        "
    >
        <strong style="color:#1D668E;">
            What happens next?
        </strong>

        <ul
            style="
                margin:10px 0 0;
                padding-left:19px;
            "
        >
            <li style="margin-bottom:6px;">
                Our team will review your service request.
            </li>

            <li style="margin-bottom:6px;">
                We will contact you to understand your
                requirement in detail.
            </li>

            <li>
                We will discuss the suitable solution,
                timeline and next steps.
            </li>
        </ul>
    </div>
    """

    customer_html = build_email_layout(
        title="Service Request Received",
        badge="REQUEST RECEIVED",
        subtitle=("Your service request was submitted " "successfully."),
        greeting=f"Hello {safe_html(full_name)},",
        body_html=customer_body,
        accent="#1D668E",
        closing=(
            "We look forward to helping you transform "
            "your idea into a reliable digital solution."
        ),
        preheader=(f"We received your request for " f"{service_name}."),
        footer_text=("Thank you for choosing Errors2Experts."),
    )

    customer_text = f"""
    Hello {full_name},

    Thank you for contacting Errors2Experts.

    We have successfully received your request for
    {service_name}.

    Our team will review your requirement and contact you
    as soon as possible.

    What happens next?

    1. Our team will review your service request.
    2. We will contact you to understand your requirement.
    3. We will discuss the suitable solution, timeline
    and next steps.

    {build_text_social_links()}

    Best Regards,
    Errors2Experts Team
    """.strip()

    customer_email_sent = send_email_safely(
        to_email=email,
        subject=("Service Request Received | " "Errors2Experts"),
        html_content=customer_html,
        text_content=customer_text,
    )

    # =================================================
    # ADMIN NOTIFICATION EMAIL
    # =================================================

    admin_details = build_detail_rows(
        [
            (
                "Customer",
                full_name,
            ),
            (
                "Email",
                email,
            ),
            (
                "Mobile",
                mobile,
            ),
            (
                "Requested Service",
                service_name,
            ),
            (
                "Preferred Date",
                preferred_date_text,
            ),
            (
                "Submitted On",
                submitted_time,
            ),
        ],
        accent="#1D668E",
    )

    requirement_html = f"""
    <div style="margin-top:22px;">
        <p
            style="
                margin:0 0 9px;
                color:#262170;
                font-family:Arial,Helvetica,sans-serif;
                font-size:14px;
                font-weight:700;
            "
        >
            Customer Requirement
        </p>

        <div
            style="
                padding:15px 16px;
                background-color:#F2F5FA;
                border-left:3px solid #262170;
                border-radius:5px;
                color:#3E4651;
                font-family:Arial,Helvetica,sans-serif;
                font-size:13px;
                line-height:1.7;
            "
        >
            {safe_html(
                message,
                empty_value=(
                    "No additional message was provided."
                ),
            )}
        </div>
    </div>
    """

    admin_body = """
    <p
        style="
            margin:0 0 14px;
            color:#242A33;
            font-size:14px;
            font-weight:700;
        "
    >
        A new service request has been submitted through
        the Errors2Experts website.
    </p>

    <p
        style="
            margin:0;
            color:#515B68;
            font-size:14px;
            line-height:1.7;
        "
    >
        Review the customer information and requirement
        below, then contact the customer for follow-up.
    </p>
    """

    admin_html = build_email_layout(
        title="New Service Request",
        badge="NEW SERVICE LEAD",
        subtitle=(f"{safe_html(full_name)} requested " f"{safe_html(service_name)}."),
        greeting="",
        body_html=admin_body,
        details_html=admin_details,
        extra_html=requirement_html,
        button_text=("Open Service Request in Admin" if service_admin_url else ""),
        button_url=service_admin_url,
        accent="#1D668E",
        preheader=(f"New {service_name} request from " f"{full_name}."),
        footer_text=(
            "This notification was generated by the " "Errors2Experts website."
        ),
    )

    admin_text = f"""
    NEW SERVICE REQUEST

    Customer: {full_name}
    Email: {email}
    Mobile: {mobile}
    Requested Service: {service_name}
    Preferred Date: {preferred_date_text}
    Submitted On: {submitted_time}

    Customer Requirement:
    {message or "No additional message was provided."}

    Open in Admin:
    {service_admin_url or "Admin URL unavailable."}

    Please contact the customer for follow-up.

    Errors2Experts System
    """.strip()

    admin_email = str(
        getattr(
            settings,
            "ADMIN_NOTIFICATION_EMAIL",
            "",
        )
    ).strip()

    if admin_email:
        send_email_safely(
            to_email=admin_email,
            subject=(f"New Service Request | " f"{service_name}"),
            html_content=admin_html,
            text_content=admin_text,
        )

    else:
        logger.warning(
            "ADMIN_NOTIFICATION_EMAIL is not configured. "
            "Service request admin email was skipped. "
            "ServiceBooking ID=%s",
            booking.pk,
        )

    # -------------------------------------------------
    # Success message and redirect
    # -------------------------------------------------

    if customer_email_sent:
        messages.success(
            request,
            ("Your service request was submitted " "successfully."),
        )

    else:
        messages.success(
            request,
            (
                "Your service request was saved "
                "successfully. The confirmation email "
                "could not be sent at this time."
            ),
        )

    return redirect("services")


# ---------------- WORKSHOP GALLERY ----------------
def workshop_gallery(request):
    """
    Display workshop photos and the next upcoming workshop.

    Past workshops are not shown as the active upcoming workshop.
    """

    workshops = WorkshopPhoto.objects.all()

    upcoming_workshop = (
        UpcomingWorkshop.objects.filter(
            event_date__gte=timezone.localdate(),
        )
        .order_by(
            "event_date",
            "event_time",
        )
        .first()
    )

    return render(
        request,
        "workshop.html",
        {
            "workshops": workshops,
            "upcoming_workshop": upcoming_workshop,
        },
    )


# ---------------- CERTIFICATE GALLERY ----------------
def certificate_gallery(request):
    certificates = Certificate.objects.all()

    return render(
        request,
        "certificate.html",
        {
            "certificates": certificates,
        },
    )


# ---------------- INTERNSHIP LIST ----------------
def internship_list(request):
    internships = Internship.objects.all()

    return render(
        request,
        "all_internship.html",
        {
            "internships": internships,
        },
    )


# ---------------- INTERNSHIP DETAIL ----------------
def internship_detail(request, pk):
    internship = get_object_or_404(Internship, pk=pk)

    timeline_data = defaultdict(list)

    for index, topic in enumerate(internship.syllabus):
        week = (index // 5) + 1
        timeline_data[week].append(
            {
                "day": index + 1,
                "topic": topic,
            }
        )

    return render(
        request,
        "internship_detail.html",
        {
            "internship": internship,
            "timeline_data": dict(timeline_data),
        },
    )


def internship_booking(request, pk):
    """
    Register a student for an internship.

    Payment options:
    - Full Payment: 100% of internship fee.
    - Half Payment: 50% now, 50% balance.

    Payment is initially marked as pending.
    """

    internship = get_object_or_404(
        Internship,
        pk=pk,
    )

    if request.method != "POST":
        return redirect(
            "internship_detail",
            pk=internship.pk,
        )

    # -------------------------------------------------
    # Get submitted values
    # -------------------------------------------------

    full_name = (request.POST.get("full_name") or "").strip()

    email = (request.POST.get("email") or "").strip().lower()

    mobile = (request.POST.get("mobile") or "").strip()

    education = (request.POST.get("education") or "").strip()

    year_passed = (request.POST.get("year_passed") or "").strip()

    college_name = (request.POST.get("college_name") or "").strip()

    payment_type = (request.POST.get("payment_type") or "").strip().lower()

    message = (request.POST.get("message") or "").strip()

    # -------------------------------------------------
    # Validation
    # -------------------------------------------------

    if not full_name or not email or not mobile:
        messages.error(
            request,
            ("Full name, email and mobile number " "are required."),
        )

        return redirect(
            "internship_detail",
            pk=internship.pk,
        )

    if payment_type not in {
        "full",
        "half",
    }:
        messages.error(
            request,
            "Please select a valid payment method.",
        )

        return redirect(
            "internship_detail",
            pk=internship.pk,
        )

    # -------------------------------------------------
    # Calculate payment
    # -------------------------------------------------

    try:
        total_amount = Decimal(str(internship.price)).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    except (
        TypeError,
        ValueError,
        InvalidOperation,
    ):
        logger.exception(
            "Invalid internship price. " "Internship ID=%s",
            internship.pk,
        )

        messages.error(
            request,
            ("The internship fee could not be " "calculated. Please contact us."),
        )

        return redirect(
            "internship_detail",
            pk=internship.pk,
        )

    if payment_type == "full":

        amount_to_pay = total_amount

        balance = Decimal("0.00")

        payment_method = "Full Payment"

    else:

        amount_to_pay = (total_amount / Decimal("2")).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        balance = (total_amount - amount_to_pay).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        payment_method = "Half Payment"

    # -------------------------------------------------
    # Save booking
    # -------------------------------------------------

    booking = InternshipBooking.objects.create(
        internship=internship,
        internship_name=internship.title,
        full_name=full_name,
        email=email,
        mobile=mobile,
        education=education,
        year_passed=year_passed,
        college_name=college_name,
        total_amount=total_amount,
        payment_type=payment_type,
        amount=amount_to_pay,
        balance=balance,
        payment_status="pending",
        message=message,
    )

    submitted_time = timezone.localtime(booking.created_at).strftime(
        "%d %B %Y, %I:%M %p"
    )

    admin_url = get_admin_change_url(
        request,
        booking,
    )

    # =================================================
    # STUDENT EMAIL
    # =================================================

    student_details = build_detail_rows(
        [
            (
                "Internship",
                internship.title,
            ),
            (
                "Payment Method",
                payment_method,
            ),
            (
                "Amount to Pay",
                f"₹{amount_to_pay:,.2f}",
            ),
        ],
        accent="#9A6812",
    )

    student_body = """
    <p style="margin:0 0 15px;">
        Thank you for registering for an internship
        program with <strong>Errors2Experts</strong>.
    </p>

    <p style="margin:0 0 15px;">
        Your internship registration has been
        received successfully.
    </p>

    <p style="margin:0;">
        Your payment is currently
        <strong>pending verification</strong>.
        Complete the payment using the QR code shown
        after registration.
    </p>
    """

    if payment_type == "half":
        student_extra = f"""
        <div
            style="
                margin-top:20px;
                padding:15px 16px;
                background:#FFF8E8;
                border-left:3px solid #C28A1C;
                border-radius:5px;
                color:#51461F;
                font-size:13px;
                line-height:1.7;
            "
        >
            <strong>
                Half Payment Selected
            </strong>

            <p style="margin:7px 0 0;">
                Remaining balance after this payment:
                <strong>
                    ₹{balance:,.2f}
                </strong>
            </p>
        </div>
        """
    else:
        student_extra = ""

    student_html = build_email_layout(
        title="Internship Registration Received",
        badge="REGISTRATION RECEIVED",
        subtitle=(f"{safe_html(internship.title)}"),
        greeting=(f"Hello {safe_html(full_name)},"),
        body_html=student_body,
        details_html=student_details,
        extra_html=student_extra,
        accent="#9A6812",
        closing=(
            "Our team will verify your payment and "
            "contact you regarding the next steps."
        ),
        preheader=("Your Errors2Experts internship " "registration has been received."),
        footer_text=("Errors2Experts Internship Program"),
    )

    student_text = f"""
    Hello {full_name},

    Thank you for registering for an internship
    with Errors2Experts.

    Internship: {internship.title}
    Payment Method: {payment_method}
    Amount to Pay: ₹{amount_to_pay:,.2f}

    Payment Status: Pending Verification

    {
        f"Remaining Balance: ₹{balance:,.2f}"
        if payment_type == "half"
        else ""
    }

    Complete the payment using the QR code shown
    after registration.

    {build_text_social_links()}

    Best Regards,
    Errors2Experts Team
    """.strip()

    student_email_sent = send_email_safely(
        to_email=email,
        subject=("Internship Registration Received | " "Errors2Experts"),
        html_content=student_html,
        text_content=student_text,
    )

    # =================================================
    # ADMIN EMAIL
    # =================================================

    admin_details = build_detail_rows(
        [
            (
                "Full Name",
                full_name,
            ),
            (
                "Email",
                email,
            ),
            (
                "Mobile",
                mobile,
            ),
            (
                "College / Organization",
                college_name or "Not provided",
            ),
            (
                "Education",
                education or "Not provided",
            ),
            (
                "Passed Out Year",
                year_passed or "Not provided",
            ),
            (
                "Internship",
                internship.title,
            ),
            (
                "Duration",
                internship.duration,
            ),
            (
                "Total Internship Fee",
                f"₹{total_amount:,.2f}",
            ),
            (
                "Payment Method",
                payment_method,
            ),
            (
                "Amount to Pay",
                f"₹{amount_to_pay:,.2f}",
            ),
            (
                "Remaining Balance",
                f"₹{balance:,.2f}",
            ),
            (
                "Payment Status",
                "Payment Pending",
            ),
            (
                "Submitted On",
                submitted_time,
            ),
        ],
        accent="#9A6812",
    )

    admin_extra = ""

    if message:
        admin_extra = f"""
        <div style="margin-top:22px;">

            <p
                style="
                    margin:0 0 9px;
                    color:#73510D;
                    font-size:14px;
                    font-weight:700;
                "
            >
                Student Message
            </p>

            <div
                style="
                    padding:15px 16px;
                    background:#FFF8E8;
                    border-left:3px solid #C28A1C;
                    border-radius:5px;
                    color:#51461F;
                    font-size:13px;
                    line-height:1.7;
                "
            >
                {safe_html(message)}
            </div>

        </div>
        """

    admin_body = """
    <p
        style="
            margin:0 0 14px;
            color:#242A33;
            font-size:14px;
            font-weight:700;
        "
    >
        A new internship registration has been
        submitted through the Errors2Experts website.
    </p>

    <p
        style="
            margin:0;
            color:#515B68;
            font-size:14px;
            line-height:1.7;
        "
    >
        Review the student and payment information
        below. Payment has not yet been verified.
    </p>
    """

    admin_html = build_email_layout(
        title="New Internship Registration",
        badge="NEW INTERNSHIP BOOKING",
        subtitle=(
            f"{safe_html(full_name)} registered for " f"{safe_html(internship.title)}."
        ),
        greeting="",
        body_html=admin_body,
        details_html=admin_details,
        extra_html=admin_extra,
        button_text=("Open Internship Booking in Admin" if admin_url else ""),
        button_url=admin_url,
        accent="#9A6812",
        preheader=(f"New internship registration from " f"{full_name}."),
        footer_text=(
            "This notification was generated by the " "Errors2Experts website."
        ),
    )

    admin_text = f"""
    NEW INTERNSHIP REGISTRATION

    Full Name: {full_name}
    Email: {email}
    Mobile: {mobile}
    College / Organization: {college_name or "Not provided"}
    Education: {education or "Not provided"}
    Passed Out Year: {year_passed or "Not provided"}

    Internship: {internship.title}
    Duration: {internship.duration}

    Total Fee: ₹{total_amount:,.2f}
    Payment Method: {payment_method}
    Amount to Pay: ₹{amount_to_pay:,.2f}
    Remaining Balance: ₹{balance:,.2f}
    Payment Status: Payment Pending

    Submitted On: {submitted_time}

    Message:
    {message or "No message provided."}

    Open in Admin:
    {admin_url or "Admin URL unavailable."}

    Errors2Experts System
    """.strip()

    admin_email = str(
        getattr(
            settings,
            "ADMIN_NOTIFICATION_EMAIL",
            "",
        )
    ).strip()

    if admin_email:

        send_email_safely(
            to_email=admin_email,
            subject=("New Internship Registration | " f"{internship.title}"),
            html_content=admin_html,
            text_content=admin_text,
        )

    else:

        logger.warning(
            "ADMIN_NOTIFICATION_EMAIL is not "
            "configured. Internship booking admin "
            "email skipped. Booking ID=%s",
            booking.pk,
        )

    # -------------------------------------------------
    # User message
    # -------------------------------------------------

    if not student_email_sent:
        logger.warning(
            "Internship confirmation email could not " "be sent. Booking ID=%s",
            booking.pk,
        )

    # =================================================
    # DYNAMIC UPI QR
    # =================================================

    payment_note = f"Errors2Experts Internship - " f"{internship.title}"

    try:

        upi_qr = generate_upi_qr_base64(
            amount=amount_to_pay,
            note=payment_note,
        )

    except Exception:

        # The registration has already been saved.
        # A QR-generation issue must not remove or
        # roll back the successful registration.
        logger.exception(
            "Dynamic UPI QR generation failed. " "InternshipBooking ID=%s",
            booking.pk,
        )

        upi_qr = ""

    # -------------------------------------------------
    # Show payment QR
    # -------------------------------------------------

    return render(
        request,
        "internship_payment.html",
        {
            "booking": booking,
            "internship": internship,
            "amount": amount_to_pay,
            "total_amount": total_amount,
            "balance": balance,
            "payment_type": payment_type,
            "payment_method": payment_method,
            "upi_qr": upi_qr,
        },
    )


def workshop_registration(request):
    """
    Register a participant for a free or paid workshop.

    Free workshop:
    - No payment required
    - Registration confirmation is sent immediately

    Paid workshop:
    - Payment status starts as pending
    - Participant is redirected to the QR-payment page
    """

    if request.method != "POST":
        return redirect("home")

    # -------------------------------------------------
    # Resolve selected workshop
    # -------------------------------------------------

    workshop_id = (request.POST.get("workshop_id") or "").strip()

    if workshop_id:
        workshop = get_object_or_404(
            UpcomingWorkshop,
            pk=workshop_id,
        )
    else:
        workshop = (
            UpcomingWorkshop.objects.filter(
                event_date__gte=timezone.localdate(),
            )
            .order_by(
                "event_date",
                "event_time",
            )
            .first()
        )

    if workshop is None:
        messages.error(
            request,
            "No upcoming workshop is available.",
        )
        return redirect("home")

    # -------------------------------------------------
    # Get submitted participant data
    # -------------------------------------------------

    full_name = (request.POST.get("full_name") or "").strip()

    email = (request.POST.get("email") or "").strip().lower()

    mobile = (request.POST.get("mobile") or "").strip()

    gender = (request.POST.get("gender") or "").strip()

    participation_mode = (request.POST.get("participation_mode") or "").strip()

    present_address = (request.POST.get("present_address") or "").strip()

    year_of_study = (request.POST.get("year_of_study") or "").strip()

    college_name = (request.POST.get("college_name") or "").strip()

    degree = (request.POST.get("degree") or "").strip()

    department = (request.POST.get("department") or "").strip()

    passed_out_year = (request.POST.get("passed_out_year") or "").strip()

    interested_domains = ", ".join(
        value.strip()
        for value in request.POST.getlist("interested_domains")
        if value.strip()
    )

    technical_skill = (request.POST.get("technical_skill") or "").strip()

    technical_skill_other = (request.POST.get("technical_skill_other") or "").strip()

    demo_interest = (request.POST.get("demo_interest") or "").strip()

    demo_interest_other = (request.POST.get("demo_interest_other") or "").strip()

    demo_mode = (request.POST.get("demo_mode") or "").strip()

    preferred_demo_time = ", ".join(
        value.strip()
        for value in request.POST.getlist("preferred_demo_time")
        if value.strip()
    )

    consent_value = (request.POST.get("consent") or "").strip().lower()

    consent = consent_value in {
        "true",
        "1",
        "yes",
        "on",
    }

    queries = (request.POST.get("queries") or "").strip()

    referred_by = (request.POST.get("referred_by") or "").strip()

    # -------------------------------------------------
    # Validate required fields
    # -------------------------------------------------

    if not full_name or not email or not mobile:
        messages.error(
            request,
            "Full name, email and mobile number are required.",
        )
        return redirect("home")

    # -------------------------------------------------
    # Determine payment state
    # -------------------------------------------------

    if workshop.is_paid:
        registration_type = "paid"
        amount = workshop.fee
        payment_status = "pending"
        registration_label = "Paid Registration"
        payment_label = "Payment Pending"
    else:
        registration_type = "free"
        amount = 0
        payment_status = "not_required"
        registration_label = "Free Registration"
        payment_label = "Not Required"

    # -------------------------------------------------
    # Save registration
    # -------------------------------------------------

    registration = WorkshopRegistration.objects.create(
        workshop=workshop,
        registration_type=registration_type,
        amount=amount,
        payment_status=payment_status,
        full_name=full_name,
        email=email,
        mobile=mobile,
        gender=gender,
        participation_mode=participation_mode,
        present_address=present_address,
        year_of_study=year_of_study,
        college_name=college_name,
        degree=degree,
        department=department,
        passed_out_year=passed_out_year,
        interested_domains=interested_domains,
        technical_skill=technical_skill,
        technical_skill_other=technical_skill_other,
        demo_interest=demo_interest,
        demo_interest_other=demo_interest_other,
        demo_mode=demo_mode,
        preferred_demo_time=preferred_demo_time,
        consent=consent,
        queries=queries,
        referred_by=referred_by,
    )

    registration_time = timezone.localtime().strftime(
        "%d %B %Y, %I:%M %p",
    )

    workshop_admin_url = get_admin_change_url(
        request,
        registration,
    )

    workshop_date = ""

    if workshop.event_date:
        workshop_date = workshop.event_date.strftime(
            "%d %B %Y",
        )

    workshop_time = ""

    if workshop.event_time:
        workshop_time = workshop.event_time.strftime(
            "%I:%M %p",
        )

    # =================================================
    # PARTICIPANT EMAIL
    # =================================================

    if workshop.is_paid:
        participant_body = f"""
        <p style="margin:0 0 15px;">
            Thank you for registering for
            <strong>{safe_html(workshop.title)}</strong>.
        </p>

        <p style="margin:0 0 15px;">
            Your registration has been received.
            This is a paid workshop.
        </p>

        <p style="margin:0;">
            Please scan the QR code shown after registration
            and pay
            <strong>₹{amount:,.2f}</strong>.
        </p>

        <div
            style="
                margin-top:20px;
                padding:16px 17px;
                background-color:#FFF8E8;
                border-left:3px solid #E3A008;
                border-radius:5px;
                color:#4C4540;
                font-size:13px;
                line-height:1.7;
            "
        >
            <strong style="color:#7A5700;">
                Payment required
            </strong>

            <p style="margin:10px 0 0;">
                Your workshop registration will be confirmed
                after our team verifies your payment.
            </p>

            <p style="margin:9px 0 0;">
                Send the payment screenshot through:<br>

                <strong>WhatsApp:</strong>
                +91 93633 42646<br>

                <strong>Email:</strong>
                errors2experts.official@gmail.com
            </p>
        </div>
        """

        participant_title = "Workshop Registration Received"
        participant_badge = "PAYMENT PENDING"
        participant_closing = (
            "Your registration will be confirmed after " "payment verification."
        )

    else:
        participant_body = f"""
        <p style="margin:0 0 15px;">
            Thank you for registering for
            <strong>{safe_html(workshop.title)}</strong>.
        </p>

        <p style="margin:0 0 15px;">
            Your free workshop registration has been
            completed successfully.
        </p>

        <p style="margin:0;">
            Our team will contact you with workshop updates
            and joining instructions.
        </p>

        <div
            style="
                margin-top:20px;
                padding:16px 17px;
                background-color:#EEF8F1;
                border-left:3px solid #2E7D32;
                border-radius:5px;
                color:#3E4651;
                font-size:13px;
                line-height:1.7;
            "
        >
            <strong style="color:#2E7D32;">
                No payment required
            </strong>

            <p style="margin:10px 0 0;">
                This workshop is free. You do not need to
                make any payment.
            </p>
        </div>
        """

        participant_title = "Workshop Registration Confirmed"
        participant_badge = "REGISTRATION CONFIRMED"
        participant_closing = "We look forward to welcoming you to the workshop."

    participant_html = build_email_layout(
        title=participant_title,
        badge=participant_badge,
        subtitle=(
            f"Your registration for {workshop.title} " "was submitted successfully."
        ),
        greeting=f"Hello {safe_html(full_name)},",
        body_html=participant_body,
        accent="#1D668E",
        closing=participant_closing,
        preheader=(f"Registration received for {workshop.title}."),
        footer_text=("Thank you for registering with Errors2Experts."),
    )

    participant_text = f"""
Hello {full_name},

Your registration for {workshop.title} has been received.

Registration Type: {registration_label}
Payment Status: {payment_label}
Amount to Pay: ₹{amount:,.2f}

Workshop Date: {workshop_date or "To be announced"}
Workshop Time: {workshop_time or "To be announced"}
Location: {workshop.location or "To be announced"}

{
    "Complete the payment using the QR code and send the "
    "screenshot for verification."
    if workshop.is_paid
    else "This workshop is free. No payment is required."
}

{build_text_social_links()}

Best Regards,
Errors2Experts Team
""".strip()

    participant_email_sent = send_email_safely(
        to_email=email,
        subject=(f"{participant_title} | Errors2Experts"),
        html_content=participant_html,
        text_content=participant_text,
    )

    # =================================================
    # ADMIN EMAIL
    # =================================================

    admin_details = build_detail_rows(
        [
            ("Workshop", workshop.title),
            ("Registration Type", registration_label),
            ("Workshop Fee", f"₹{amount:,.2f}"),
            ("Payment Status", payment_label),
            ("Full Name", full_name),
            ("Email", email),
            ("Mobile", mobile),
            ("Gender", gender or "Not provided"),
            (
                "Participation Mode",
                participation_mode or "Not selected",
            ),
            (
                "Present Address",
                present_address or "Not provided",
            ),
            (
                "Year of Study",
                year_of_study or "Not provided",
            ),
            (
                "College Name",
                college_name or "Not provided",
            ),
            ("Degree", degree or "Not provided"),
            (
                "Department",
                department or "Not provided",
            ),
            (
                "Passed Out Year",
                passed_out_year or "Not provided",
            ),
            (
                "Interested Domains",
                interested_domains or "Not selected",
            ),
            (
                "Technical Skill",
                technical_skill or "Not selected",
            ),
            (
                "Technical Skill - Other",
                technical_skill_other or "Not provided",
            ),
            (
                "Demo Interest",
                demo_interest or "Not selected",
            ),
            (
                "Demo Interest - Other",
                demo_interest_other or "Not provided",
            ),
            (
                "Preferred Demo Mode",
                demo_mode or "Not selected",
            ),
            (
                "Preferred Demo Time",
                preferred_demo_time or "Not selected",
            ),
            (
                "Consent",
                "Yes" if consent else "No",
            ),
            (
                "Referred By",
                referred_by or "Not provided",
            ),
            (
                "Registration Time",
                registration_time,
            ),
        ],
        accent="#1D668E",
    )

    queries_html = f"""
    <div style="margin-top:22px;">
        <p
            style="
                margin:0 0 9px;
                color:#262170;
                font-size:14px;
                font-weight:700;
            "
        >
            Questions or Additional Information
        </p>

        <div
            style="
                padding:15px 16px;
                background-color:#F2F5FA;
                border-left:3px solid #262170;
                border-radius:5px;
                color:#3E4651;
                font-size:13px;
                line-height:1.7;
            "
        >
            {safe_html(
                queries,
                empty_value=(
                    "No questions or additional "
                    "information were provided."
                ),
            )}
        </div>
    </div>
    """

    admin_body = f"""
    <p
        style="
            margin:0 0 14px;
            color:#242A33;
            font-size:14px;
            font-weight:700;
        "
    >
        A new {safe_html(registration_label.lower())}
        has been submitted for
        {safe_html(workshop.title)}.
    </p>

    <p
        style="
            margin:0;
            color:#515B68;
            font-size:14px;
            line-height:1.7;
        "
    >
        Review the participant information and payment
        status below.
    </p>
    """

    admin_html = build_email_layout(
        title="New Workshop Registration",
        badge=("PAYMENT PENDING" if workshop.is_paid else "FREE REGISTRATION"),
        subtitle=(
            f"{safe_html(full_name)} registered for " f"{safe_html(workshop.title)}."
        ),
        greeting="",
        body_html=admin_body,
        details_html=admin_details,
        extra_html=queries_html,
        button_text=(
            "Open Workshop Registration in Admin" if workshop_admin_url else ""
        ),
        button_url=workshop_admin_url,
        accent="#1D668E",
        preheader=(f"New workshop registration from {full_name}."),
        footer_text=(
            "This notification was generated by the " "Errors2Experts website."
        ),
    )

    admin_text = f"""
NEW WORKSHOP REGISTRATION

Workshop: {workshop.title}
Registration Type: {registration_label}
Workshop Fee: ₹{amount:,.2f}
Payment Status: {payment_label}

Participant: {full_name}
Email: {email}
Mobile: {mobile}
Participation Mode: {participation_mode or "Not selected"}
Interested Domains: {interested_domains or "Not selected"}
Registration Time: {registration_time}

Open in Admin:
{workshop_admin_url or "Admin URL unavailable."}

Errors2Experts System
""".strip()

    admin_email = str(
        getattr(
            settings,
            "ADMIN_NOTIFICATION_EMAIL",
            "",
        )
    ).strip()

    if admin_email:
        send_email_safely(
            to_email=admin_email,
            subject=(f"New Workshop Registration | " f"{workshop.title}"),
            html_content=admin_html,
            text_content=admin_text,
        )

    # -------------------------------------------------
    # Free or paid response
    # -------------------------------------------------

    if workshop.is_paid:

        # =================================================
        # DYNAMIC WORKSHOP UPI QR
        # =================================================

        payment_note = f"Errors2Experts Workshop - " f"{workshop.title}"

        try:

            upi_qr = generate_upi_qr_base64(
                amount=amount,
                note=payment_note,
            )

        except Exception:

            # Registration is already saved successfully.
            # A QR-generation problem must not delete or
            # roll back the participant registration.
            logger.exception(
                "Dynamic UPI QR generation failed. " "WorkshopRegistration ID=%s",
                registration.pk,
            )

            upi_qr = ""

        return render(
            request,
            "workshop_payment.html",
            {
                "workshop": workshop,
                "registration": registration,
                "amount": amount,
                "payment_status": payment_status,
                "upi_qr": upi_qr,
            },
        )

    if participant_email_sent:
        messages.success(
            request,
            "Your free workshop registration was successful.",
        )
    else:
        messages.success(
            request,
            (
                "Your registration was saved, but the "
                "confirmation email could not be sent."
            ),
        )

    return redirect("home")


def demo_request(request):
    """
    Handle demo requests.

    Supported flows:

    1. Service Demo
       User selects a specific active demo belonging
       to a specific service.

    2. Legacy Demo Category
       Keeps the existing DemoCategory system working.

    3. Custom Requirement
       User can submit a requirement when no existing
       demo matches their need.
    """

    # =========================================================
    # POST ONLY
    # =========================================================

    if request.method != "POST":
        return redirect("services")

    # =========================================================
    # FORM DATA
    # =========================================================

    organization_name = (request.POST.get("organization_name") or "").strip()

    email = (request.POST.get("email") or "").strip().lower()

    mobile = (request.POST.get("mobile") or "").strip()

    service_id = (request.POST.get("service_id") or "").strip()

    selected_demo_id = (request.POST.get("selected_demo") or "").strip()

    # Existing legacy category system
    category_id = (request.POST.get("category") or "").strip()

    custom_requirement = (request.POST.get("custom_requirement") or "").strip()

    # New confirmation checkbox
    consent = (request.POST.get("consent") or "").strip()

    # =========================================================
    # BASIC REQUIRED FIELD VALIDATION
    # =========================================================

    if not organization_name or not email or not mobile:
        messages.error(
            request,
            (
                "Please complete all required fields "
                "before submitting the demo request."
            ),
        )

        if service_id:
            return redirect(
                "service_detail",
                pk=service_id,
            )

        return redirect("services")

    # =========================================================
    # CONSENT VALIDATION
    # =========================================================

    if consent != "yes":
        messages.error(
            request,
            (
                "Please confirm that the information "
                "provided is correct before requesting "
                "the demo."
            ),
        )

        if service_id:
            return redirect(
                "service_detail",
                pk=service_id,
            )

        return redirect("services")

    # =========================================================
    # MOBILE VALIDATION
    # =========================================================

    if not mobile.isdigit() or len(mobile) != 10:
        messages.error(
            request,
            ("Please enter a valid " "10-digit mobile number."),
        )

        if service_id:
            return redirect(
                "service_detail",
                pk=service_id,
            )

        return redirect("services")

    # =========================================================
    # OBJECT RESOLUTION
    # =========================================================

    service = None
    selected_demo = None
    category = None

    # =========================================================
    # FLOW A
    # SPECIFIC SERVICE DEMO
    # =========================================================

    if selected_demo_id:

        # -----------------------------------------------------
        # Service is mandatory when requesting a ServiceDemoLink
        # -----------------------------------------------------

        if not service_id:
            messages.error(
                request,
                (
                    "Unable to identify the selected service. "
                    "Please return to the service page "
                    "and try again."
                ),
            )

            return redirect("services")

        # -----------------------------------------------------
        # Resolve service
        # -----------------------------------------------------

        service = get_object_or_404(
            Service,
            pk=service_id,
        )

        # -----------------------------------------------------
        # SECURITY VALIDATION
        #
        # Demo must:
        # - Exist
        # - Belong to selected service
        # - Be active
        #
        # Actual URL never comes from POST.
        # -----------------------------------------------------

        selected_demo = ServiceDemoLink.objects.filter(
            pk=selected_demo_id,
            service=service,
            is_active=True,
        ).first()

        if selected_demo is None:
            messages.error(
                request,
                (
                    "The selected demo is no longer available. "
                    "Please choose another demo."
                ),
            )

            return redirect(
                "service_detail",
                pk=service.pk,
            )

    # =========================================================
    # FLOW B
    # LEGACY DEMO CATEGORY
    # =========================================================

    elif category_id:

        category = DemoCategory.objects.filter(
            pk=category_id,
            is_active=True,
        ).first()

        if category is None:
            messages.error(
                request,
                ("The selected demo category " "is currently unavailable."),
            )

            return redirect("services")

        # Service may optionally exist
        if service_id:
            service = Service.objects.filter(
                pk=service_id,
            ).first()

    # =========================================================
    # FLOW C
    # CUSTOM REQUIREMENT
    # =========================================================

    else:

        if service_id:
            service = Service.objects.filter(
                pk=service_id,
            ).first()

        if not custom_requirement:
            messages.error(
                request,
                (
                    "Please select an available demo "
                    "or describe your custom requirement."
                ),
            )

            if service:
                return redirect(
                    "service_detail",
                    pk=service.pk,
                )

            return redirect("services")

        if len(custom_requirement) < 5:
            messages.error(
                request,
                (
                    "Please provide a little more information "
                    "about your demo requirement."
                ),
            )

            if service:
                return redirect(
                    "service_detail",
                    pk=service.pk,
                )

            return redirect("services")

    # =========================================================
    # SAVE DEMO REQUEST
    # =========================================================

    try:

        demo_request_obj = DemoRequest.objects.create(
            organization_name=organization_name,
            email=email,
            mobile=mobile,
            service=service,
            selected_demo=selected_demo,
            category=category,
            custom_requirement=(custom_requirement or None),
            status="Pending",
        )

    except Exception:

        logger.exception(
            ("Failed to save demo request. " "Email=%s Service=%s Demo=%s"),
            email,
            service_id or "N/A",
            selected_demo_id or "N/A",
        )

        messages.error(
            request,
            (
                "We could not submit your demo request "
                "at this time. Please try again."
            ),
        )

        if service:
            return redirect(
                "service_detail",
                pk=service.pk,
            )

        return redirect("services")

    # =========================================================
    # REQUEST METADATA
    # =========================================================

    request_time = timezone.localtime(
        demo_request_obj.created_at,
    ).strftime(
        "%d %B %Y, %I:%M %p",
    )

    demo_request_admin_url = get_admin_change_url(
        request,
        demo_request_obj,
    )

    # =========================================================
    # FLOW 1
    # EXACT SERVICE DEMO
    # =========================================================

    if selected_demo:

        demo_title = selected_demo.title

        demo_url = (selected_demo.url or "").strip()

        # =====================================================
        # USER EMAIL DETAILS
        # =====================================================

        user_details = build_detail_rows(
            [
                (
                    "Service",
                    service.title,
                ),
                (
                    "Requested Demo",
                    demo_title,
                ),
            ],
            accent="#147A8A",
        )

        # =====================================================
        # USER EMAIL BODY
        # =====================================================

        if demo_url:

            user_body = f"""
            <p style="margin:0 0 15px;">
                Thank you for requesting a demo from
                <strong>Errors2Experts</strong>.
            </p>

            <p style="margin:0 0 15px;">
                Your requested
                <strong>
                    {safe_html(demo_title)}
                </strong>
                demo is ready.
            </p>

            <p style="margin:0;">
                Use the button below to open the
                requested live demonstration.
            </p>

            <div
                style="
                    margin-top:20px;
                    padding:15px 16px;
                    background:#EEF8FA;
                    border-left:3px solid #147A8A;
                    border-radius:6px;
                    color:#465A61;
                    font-size:13px;
                    line-height:1.7;
                "
            >
                <strong style="color:#147A8A;">
                    Demo Access
                </strong>

                <p style="margin:7px 0 0;">
                    This link was selected from the
                    Errors2Experts demo library for
                    your requested service.
                </p>
            </div>
            """

            button_text = "Open Requested Demo"

            button_url = demo_url

        else:

            user_body = f"""
            <p style="margin:0 0 15px;">
                Thank you for requesting
                <strong>
                    {safe_html(demo_title)}
                </strong>.
            </p>

            <p style="margin:0;">
                We received your request successfully.
                Our team will contact you with the
                demo access details shortly.
            </p>
            """

            button_text = ""

            button_url = ""

        # =====================================================
        # USER HTML EMAIL
        # =====================================================

        user_html = build_email_layout(
            title="Your Requested Demo",
            badge="DEMO ACCESS",
            subtitle=(f"{demo_title} from " f"{service.title}"),
            greeting=(f"Hello " f"{safe_html(organization_name)},"),
            body_html=user_body,
            details_html=user_details,
            button_text=button_text,
            button_url=button_url,
            accent="#147A8A",
            closing=(
                "Explore the demo and contact our "
                "team if you would like to discuss "
                "a similar solution."
            ),
            preheader=(f"Your requested {demo_title} " "demo is ready."),
            footer_text=("Thank you for choosing " "Errors2Experts."),
        )

        # =====================================================
        # USER TEXT EMAIL
        # =====================================================

        user_text = f"""
Hello {organization_name},

Thank you for requesting a demo from Errors2Experts.

Service:
{service.title}

Requested Demo:
{demo_title}

Demo Link:
{demo_url or "Our team will provide access shortly."}

Explore the demo and contact our team if you would
like to discuss a similar solution.

{build_text_social_links()}

Best Regards,
Errors2Experts Team
""".strip()

        # =====================================================
        # SEND USER EMAIL
        # =====================================================

        send_email_safely(
            to_email=email,
            subject=(f"{demo_title} Demo | " "Errors2Experts"),
            html_content=user_html,
            text_content=user_text,
        )

        # =====================================================
        # ADMIN EMAIL DETAILS
        # =====================================================

        admin_details = build_detail_rows(
            [
                (
                    "Name / Organization",
                    organization_name,
                ),
                (
                    "Email",
                    email,
                ),
                (
                    "Mobile",
                    mobile,
                ),
                (
                    "Service",
                    service.title,
                ),
                (
                    "Requested Demo",
                    demo_title,
                ),
                (
                    "Demo URL",
                    (demo_url or "No URL configured"),
                ),
                (
                    "Custom Requirement",
                    (custom_requirement or "Not provided"),
                ),
                (
                    "Status",
                    "Pending",
                ),
                (
                    "Requested On",
                    request_time,
                ),
            ],
            accent="#147A8A",
        )

        # =====================================================
        # ADMIN BODY
        # =====================================================

        admin_body = """
        <p
            style="
                margin:0 0 14px;
                color:#242A33;
                font-size:14px;
                font-weight:700;
            "
        >
            A visitor requested access to a specific
            service demo through the Errors2Experts
            website.
        </p>

        <p
            style="
                margin:0;
                color:#515B68;
                font-size:14px;
                line-height:1.7;
            "
        >
            The requested demo link has been processed
            for the visitor's email.
        </p>
        """

        # =====================================================
        # ADMIN HTML EMAIL
        # =====================================================

        admin_html = build_email_layout(
            title="New Service Demo Request",
            badge="DEMO REQUEST",
            subtitle=(
                f"{safe_html(organization_name)} "
                f"requested "
                f"{safe_html(demo_title)}."
            ),
            greeting="",
            body_html=admin_body,
            details_html=admin_details,
            button_text=(
                "Open Demo Request in Admin" if demo_request_admin_url else ""
            ),
            button_url=demo_request_admin_url,
            accent="#147A8A",
            preheader=(f"{organization_name} requested " f"{demo_title}."),
            footer_text=(
                "This notification was generated " "by the Errors2Experts website."
            ),
        )

        # =====================================================
        # ADMIN TEXT EMAIL
        # =====================================================

        admin_text = f"""
NEW SERVICE DEMO REQUEST

Name / Organization:
{organization_name}

Email:
{email}

Mobile:
{mobile}

Service:
{service.title}

Requested Demo:
{demo_title}

Demo URL:
{demo_url or "No URL configured"}

Custom Requirement:
{custom_requirement or "Not provided"}

Status:
Pending

Requested On:
{request_time}

Open in Admin:
{demo_request_admin_url or "Admin URL unavailable."}

Errors2Experts System
""".strip()

        admin_email = str(
            getattr(
                settings,
                "ADMIN_NOTIFICATION_EMAIL",
                "",
            )
        ).strip()

        # =====================================================
        # SEND ADMIN EMAIL
        # =====================================================

        if admin_email:

            send_email_safely(
                to_email=admin_email,
                subject=(f"New Demo Request | " f"{demo_title}"),
                html_content=admin_html,
                text_content=admin_text,
            )

        else:

            logger.warning(
                ("ADMIN_NOTIFICATION_EMAIL is not " "configured. DemoRequest ID=%s"),
                demo_request_obj.pk,
            )

        # =====================================================
        # SUCCESS MESSAGE
        # =====================================================

        if demo_url:

            messages.success(
                request,
                (
                    "Demo sent successfully! "
                    "Please check your email for "
                    "the requested demo link."
                ),
            )

        else:

            messages.success(
                request,
                (
                    "Your demo request was received "
                    "successfully. Our team will contact "
                    "you with access details shortly."
                ),
            )

    # =========================================================
    # FLOW 2
    # LEGACY DEMO CATEGORY
    # =========================================================

    elif category:

        category_url = (category.demo_link or "").strip()

        # =====================================================
        # USER DETAILS
        # =====================================================

        user_details = build_detail_rows(
            [
                (
                    "Requested Demo",
                    category.name,
                ),
            ],
            accent="#147A8A",
        )

        # =====================================================
        # USER BODY
        # =====================================================

        user_body = f"""
        <p style="margin:0 0 15px;">
            Thank you for requesting the
            <strong>
                {safe_html(category.name)}
            </strong>
            demo.
        </p>

        <p style="margin:0;">
            Your requested demo is ready.
            Use the button below to open it.
        </p>
        """

        user_html = build_email_layout(
            title="Your Requested Demo",
            badge="DEMO ACCESS",
            subtitle=(f"{category.name} demo access"),
            greeting=(f"Hello " f"{safe_html(organization_name)},"),
            body_html=user_body,
            details_html=user_details,
            button_text=("Open Demo" if category_url else ""),
            button_url=category_url,
            accent="#147A8A",
            preheader=(f"Your {category.name} " "demo is ready."),
            footer_text=("Thank you for choosing " "Errors2Experts."),
        )

        user_text = f"""
Hello {organization_name},

Your requested demo is ready.

Demo:
{category.name}

Demo Link:
{category_url or "Our team will provide access shortly."}

{build_text_social_links()}

Best Regards,
Errors2Experts Team
""".strip()

        # =====================================================
        # SEND USER EMAIL
        # =====================================================

        send_email_safely(
            to_email=email,
            subject=(f"{category.name} Demo | " "Errors2Experts"),
            html_content=user_html,
            text_content=user_text,
        )

        # =====================================================
        # ADMIN DETAILS
        # =====================================================

        admin_details = build_detail_rows(
            [
                (
                    "Name / Organization",
                    organization_name,
                ),
                (
                    "Email",
                    email,
                ),
                (
                    "Mobile",
                    mobile,
                ),
                (
                    "Legacy Demo Category",
                    category.name,
                ),
                (
                    "Demo URL",
                    (category_url or "No URL configured"),
                ),
                (
                    "Status",
                    "Pending",
                ),
                (
                    "Requested On",
                    request_time,
                ),
            ],
            accent="#147A8A",
        )

        admin_html = build_email_layout(
            title="New Demo Request",
            badge="DEMO REQUEST",
            subtitle=(
                f"{safe_html(organization_name)} "
                f"requested "
                f"{safe_html(category.name)}."
            ),
            greeting="",
            body_html=(
                "<p>A new demo request was " "submitted through the website.</p>"
            ),
            details_html=admin_details,
            button_text=(
                "Open Demo Request in Admin" if demo_request_admin_url else ""
            ),
            button_url=demo_request_admin_url,
            accent="#147A8A",
            footer_text=("Errors2Experts website notification."),
        )

        admin_email = str(
            getattr(
                settings,
                "ADMIN_NOTIFICATION_EMAIL",
                "",
            )
        ).strip()

        if admin_email:

            send_email_safely(
                to_email=admin_email,
                subject=(f"New Demo Request | " f"{category.name}"),
                html_content=admin_html,
                text_content=(
                    f"New demo request from "
                    f"{organization_name}\n"
                    f"Email: {email}\n"
                    f"Mobile: {mobile}\n"
                    f"Demo: {category.name}\n"
                    f"Demo URL: "
                    f"{category_url or 'Not configured'}\n"
                    f"Admin: "
                    f"{demo_request_admin_url}"
                ),
            )

        # =====================================================
        # SUCCESS MESSAGE
        # =====================================================

        if category_url:

            messages.success(
                request,
                (
                    "Demo sent successfully! "
                    "Please check your email for "
                    "the requested demo link."
                ),
            )

        else:

            messages.success(
                request,
                (
                    "Your demo request was received "
                    "successfully. Our team will contact "
                    "you with access details shortly."
                ),
            )

    # =========================================================
    # FLOW 3
    # CUSTOM REQUIREMENT
    # =========================================================

    else:

        # =====================================================
        # USER DETAILS
        # =====================================================

        user_details = build_detail_rows(
            [
                (
                    "Service",
                    (service.title if service else "Custom Requirement"),
                ),
            ],
            accent="#147A8A",
        )

        # =====================================================
        # USER BODY
        # =====================================================

        user_body = """
        <p style="margin:0 0 15px;">
            Thank you for contacting
            <strong>Errors2Experts</strong>.
        </p>

        <p style="margin:0 0 15px;">
            We have received your custom demo
            requirement successfully.
        </p>

        <p style="margin:0;">
            Our technical team will review your
            requirement and contact you with the
            appropriate next steps.
        </p>
        """

        user_html = build_email_layout(
            title="Demo Request Received",
            badge="REQUEST RECEIVED",
            subtitle=("Your custom demo requirement " "has been received."),
            greeting=(f"Hello " f"{safe_html(organization_name)},"),
            body_html=user_body,
            details_html=user_details,
            accent="#147A8A",
            closing=("Our team will review your " "requirement and contact you."),
            preheader=("Your custom demo request " "was received."),
            footer_text=("Thank you for contacting " "Errors2Experts."),
        )

        user_text = f"""
Hello {organization_name},

We have received your custom demo request.

Service:
{service.title if service else "Custom Requirement"}

Our technical team will review your requirement
and contact you with the next steps.

{build_text_social_links()}

Best Regards,
Errors2Experts Team
""".strip()

        # =====================================================
        # SEND USER EMAIL
        # =====================================================

        send_email_safely(
            to_email=email,
            subject=("Demo Request Received | " "Errors2Experts"),
            html_content=user_html,
            text_content=user_text,
        )

        # =====================================================
        # ADMIN DETAILS
        # =====================================================

        admin_details = build_detail_rows(
            [
                (
                    "Name / Organization",
                    organization_name,
                ),
                (
                    "Email",
                    email,
                ),
                (
                    "Mobile",
                    mobile,
                ),
                (
                    "Service",
                    (service.title if service else "Not selected"),
                ),
                (
                    "Requirement",
                    custom_requirement,
                ),
                (
                    "Status",
                    "Pending",
                ),
                (
                    "Requested On",
                    request_time,
                ),
            ],
            accent="#147A8A",
        )

        admin_html = build_email_layout(
            title="New Custom Demo Request",
            badge="CUSTOM REQUEST",
            subtitle=(
                f"{safe_html(organization_name)} " "submitted a custom requirement."
            ),
            greeting="",
            body_html=(
                "<p>A visitor submitted a custom "
                "demo requirement that requires "
                "manual review.</p>"
            ),
            details_html=admin_details,
            button_text=(
                "Open Demo Request in Admin" if demo_request_admin_url else ""
            ),
            button_url=demo_request_admin_url,
            accent="#147A8A",
            preheader=("A new custom demo requirement " "was submitted."),
            footer_text=("Errors2Experts website notification."),
        )

        admin_text = f"""
NEW CUSTOM DEMO REQUEST

Name / Organization:
{organization_name}

Email:
{email}

Mobile:
{mobile}

Service:
{service.title if service else "Not selected"}

Requirement:
{custom_requirement}

Status:
Pending

Requested On:
{request_time}

Open in Admin:
{demo_request_admin_url or "Admin URL unavailable."}

Errors2Experts System
""".strip()

        admin_email = str(
            getattr(
                settings,
                "ADMIN_NOTIFICATION_EMAIL",
                "",
            )
        ).strip()

        # =====================================================
        # SEND ADMIN EMAIL
        # =====================================================

        if admin_email:

            send_email_safely(
                to_email=admin_email,
                subject=("New Custom Demo Request | " "Errors2Experts"),
                html_content=admin_html,
                text_content=admin_text,
            )

        else:

            logger.warning(
                ("ADMIN_NOTIFICATION_EMAIL is not " "configured. DemoRequest ID=%s"),
                demo_request_obj.pk,
            )

        # =====================================================
        # SUCCESS MESSAGE
        # =====================================================

        messages.success(
            request,
            (
                "Your demo requirement was submitted "
                "successfully. Our team will review it "
                "and contact you shortly."
            ),
        )

    # =========================================================
    # FINAL REDIRECT
    # =========================================================

    if service:

        return redirect(
            "service_detail",
            pk=service.pk,
        )

    return redirect("services")


def team(request):
    """
    Public Our Team page.

    Each employee is fetched once and their active category-specific
    role assignments are prefetched for efficient rendering.
    """

    active_role_assignments = (
        EmployeeRole.objects.filter(
            category__is_active=True,
        )
        .select_related(
            "category",
        )
        .order_by(
            "display_order",
            "category__display_order",
            "role_title",
        )
    )

    employees = (
        Employee.objects.filter(
            is_active=True,
            role_assignments__category__is_active=True,
        )
        .distinct()
        .prefetch_related(
            Prefetch(
                "role_assignments",
                queryset=active_role_assignments,
                to_attr="public_role_assignments",
            ),
        )
        .order_by(
            "display_order",
            "name",
        )
    )

    categories = (
        TeamCategory.objects.filter(
            is_active=True,
            employee_roles__employee__is_active=True,
        )
        .distinct()
        .order_by(
            "display_order",
            "name",
        )
    )

    team_member_count = employees.count()

    role_count = (
        EmployeeRole.objects.filter(
            employee__is_active=True,
            category__is_active=True,
        )
        .values(
            "role_title",
        )
        .distinct()
        .count()
    )

    category_count = categories.count()

    return render(
        request,
        "team.html",
        {
            "employees": employees,
            "team_categories": categories,
            "team_member_count": team_member_count,
            "role_count": role_count,
            "category_count": category_count,
        },
    )
