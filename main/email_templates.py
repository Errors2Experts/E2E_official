import logging
import os
from html import escape
from urllib.parse import urljoin

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction

from .brevo_mail import send_brevo_email
from .models import (
    Contact,
    CourseBooking,
    ServiceBooking,
    InternshipBooking,
    WorkshopRegistration,
)

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Official Errors2Experts links
# -----------------------------------------------------------------------------

WEBSITE_URL = os.getenv(
    "WEBSITE_URL",
    "https://errors2experts.up.railway.app/",
).rstrip("/")

INSTAGRAM_URL = os.getenv(
    "INSTAGRAM_URL",
    "https://www.instagram.com/errors2experts_2026/",
).strip()

LINKEDIN_URL = os.getenv(
    "LINKEDIN_URL",
    "https://www.linkedin.com/company/errors2experts/",
).strip()

YOUTUBE_URL = os.getenv(
    "YOUTUBE_URL",
    "https://www.youtube.com/@errors2experts",
).strip()

FACEBOOK_URL = os.getenv(
    "FACEBOOK_URL",
    "https://www.facebook.com/profile.php?id=61591756388630",
).strip()

WHATSAPP_URL = os.getenv(
    "WHATSAPP_URL",
    "",
).strip()

WHATSAPP_NUMBER = os.getenv(
    "WHATSAPP_NUMBER",
    "919363342646",
).strip()


# -----------------------------------------------------------------------------
# Errors2Experts brand colours
# -----------------------------------------------------------------------------

BRAND_RED = "#C62828"
BRAND_GOLD = "#C9A227"
BRAND_GREEN = "#2E7D32"
BRAND_BLUE = "#1D668E"
BRAND_DARK = "#172033"
BRAND_MUTED = "#5F6878"

PAGE_BACKGROUND = "#F2F5FA"
FOOTER_BACKGROUND = "#EEF2F6"
CARD_BORDER = "#DDE3EA"


# -----------------------------------------------------------------------------
# New update email settings
# -----------------------------------------------------------------------------

EMAIL_CONFIG = {
    "Course": {
        "subject": "New Course Available | Errors2Experts",
        "badge": "NEW COURSE",
        "icon": "📘",
        "accent": "#3157A5",
        "intro": ("A new learning opportunity is now available " "at Errors2Experts."),
        "closing": (
            "Take the next step towards building practical, " "industry-ready skills."
        ),
        "button_text": "Explore This Course",
    },
    "Service": {
        "subject": "New Professional Service | Errors2Experts",
        "badge": "NEW SERVICE",
        "icon": "⚙️",
        "accent": "#147A8A",
        "intro": (
            "We have added a new professional service designed "
            "to help businesses and individuals grow digitally."
        ),
        "closing": (
            "Let us transform your idea into a reliable, " "modern digital solution."
        ),
        "button_text": "Explore This Service",
    },
    "Internship": {
        "subject": "New Internship Opportunity | Errors2Experts",
        "badge": "NEW INTERNSHIP",
        "icon": "🎓",
        "accent": "#9A6812",
        "intro": (
            "A new internship opportunity is available for students "
            "who want to learn through practical projects."
        ),
        "closing": (
            "Gain practical exposure, improve your confidence, "
            "and strengthen your career profile."
        ),
        "button_text": "View This Internship",
    },
    "Workshop": {
        "subject": "New Workshop Announcement | Errors2Experts",
        "badge": "NEW WORKSHOP",
        "icon": "🎯",
        "accent": "#8A365E",
        "intro": (
            "Registration is now open for our latest " "hands-on learning workshop."
        ),
        "closing": (
            "Reserve your place and enjoy an interactive "
            "learning experience guided by industry professionals."
        ),
        "button_text": "View Workshop Details",
    },
}


# -----------------------------------------------------------------------------
# General helpers
# -----------------------------------------------------------------------------


def clean_text(value):
    """Escape dynamic text and preserve line breaks."""

    if value in (None, ""):
        return ""

    text = (
        str(value)
        .replace(
            "\r\n",
            "\n",
        )
        .replace(
            "\r",
            "\n",
        )
    )

    return escape(text).replace(
        "\n",
        "<br>",
    )


def safe_html(value, empty_value=""):
    """
    Safely prepare user-provided content for an HTML email.

    Empty values are replaced with empty_value.
    HTML characters are escaped and line breaks are preserved.
    """

    if value is None:
        value = empty_value

    elif isinstance(value, str) and not value.strip():
        value = empty_value

    return clean_text(value)


def clean_plain_text(value):
    """Return a clean value for plain-text email content."""

    if value in (None, ""):
        return ""

    return str(value).strip()


def _first_non_empty(*values):
    """Return the first value that is not empty."""

    for value in values:
        if value is None:
            continue

        if isinstance(value, str) and not value.strip():
            continue

        return value

    return ""


def format_price(value):
    """Format integer and decimal prices."""

    if value in (None, ""):
        return ""

    try:
        number = float(value)
    except (TypeError, ValueError):
        return f"₹{value}"

    if number.is_integer():
        return f"₹{number:,.0f}"

    return f"₹{number:,.2f}"


def get_image_url(instance):
    """
    Return an absolute image URL.

    This supports local media and Cloudinary-backed media.
    It does not use image.path.
    """

    image = getattr(
        instance,
        "image",
        None,
    )

    if not image:
        return ""

    try:
        image_url = image.url
    except (AttributeError, ValueError):
        return ""

    if not image_url:
        return ""

    return urljoin(
        f"{WEBSITE_URL}/",
        str(image_url),
    )


def get_whatsapp_url():
    """Return the configured WhatsApp chat URL."""

    if WHATSAPP_URL:
        return WHATSAPP_URL

    cleaned_number = "".join(
        character for character in WHATSAPP_NUMBER if character.isdigit()
    )

    if not cleaned_number:
        return ""

    return f"https://wa.me/{cleaned_number}"


def brand_name_html(font_size="20px"):
    """Render Errors2Experts in official company colours."""

    return f"""
    <span
        style="
            display:inline-block;
            font-family:Arial,Helvetica,sans-serif;
            font-size:{font_size};
            line-height:1.1;
            font-weight:800;
            letter-spacing:-0.6px;
            white-space:nowrap;
        "
    >
        <span style="color:{BRAND_RED};">
            Errors
        </span><span style="color:{BRAND_GOLD};">2</span><span
            style="color:{BRAND_GREEN};"
        >Experts</span>
    </span>
    """


def get_registered_emails():
    """
    Collect unique and valid email addresses from registration models.
    """

    email_models = (
        CourseBooking,
        InternshipBooking,
        WorkshopRegistration,
        ServiceBooking,
        Contact,
    )

    unique_emails = set()

    for model in email_models:
        stored_emails = (
            model.objects.exclude(email="")
            .exclude(email__isnull=True)
            .values_list(
                "email",
                flat=True,
            )
            .iterator()
        )

        for stored_email in stored_emails:
            email = (
                str(
                    stored_email,
                )
                .strip()
                .lower()
            )

            if not email:
                continue

            try:
                validate_email(email)

            except ValidationError:
                logger.warning(
                    "Skipped invalid email from %s: %s",
                    model.__name__,
                    email,
                )
                continue

            unique_emails.add(email)

    return sorted(unique_emails)


# -----------------------------------------------------------------------------
# Social links
# -----------------------------------------------------------------------------


def build_social_links():
    """
    Build circular social icons with labels.

    External PNG favicon images are used because Bootstrap icon
    classes do not work inside email clients.
    """

    social_links = (
        (
            "LinkedIn",
            LINKEDIN_URL,
            (
                "https://www.google.com/s2/favicons"
                "?sz=64&domain_url=https://www.linkedin.com"
            ),
        ),
        (
            "YouTube",
            YOUTUBE_URL,
            (
                "https://www.google.com/s2/favicons"
                "?sz=64&domain_url=https://www.youtube.com"
            ),
        ),
        (
            "Facebook",
            FACEBOOK_URL,
            (
                "https://www.google.com/s2/favicons"
                "?sz=64&domain_url=https://www.facebook.com"
            ),
        ),
        (
            "Instagram",
            INSTAGRAM_URL,
            (
                "https://www.google.com/s2/favicons"
                "?sz=64&domain_url=https://www.instagram.com"
            ),
        ),
        (
            "WhatsApp",
            get_whatsapp_url(),
            (
                "https://www.google.com/s2/favicons"
                "?sz=64&domain_url=https://www.whatsapp.com"
            ),
        ),
    )

    cells = []

    for name, url, icon_url in social_links:
        if not url:
            continue

        safe_name = escape(
            name,
            quote=True,
        )

        safe_url = escape(
            str(url),
            quote=True,
        )

        safe_icon_url = escape(
            icon_url,
            quote=True,
        )

        cells.append(f"""
            <td
                align="center"
                valign="top"
                style="padding:0 7px;"
            >
                <a
                    href="{safe_url}"
                    target="_blank"
                    rel="noopener noreferrer"
                    title="{safe_name}"
                    style="
                        display:inline-block;
                        color:#5E6671;
                        font-family:Arial,Helvetica,sans-serif;
                        text-align:center;
                        text-decoration:none;
                    "
                >
                    <span
                        style="
                            display:inline-block;
                            width:50px;
                            height:50px;
                            line-height:50px;
                            background-color:#FFFFFF;
                            border:1px solid #D8DEE6;
                            border-radius:50%;
                            text-align:center;
                        "
                    >
                        <img
                            src="{safe_icon_url}"
                            alt="{safe_name}"
                            width="30"
                            height="30"
                            style="
                                display:inline-block;
                                width:30px;
                                height:30px;
                                margin-top:10px;
                                border:0;
                                border-radius:6px;
                            "
                        >
                    </span>

                    <span
                        style="
                            display:block;
                            margin-top:7px;
                            color:#5E6671;
                            font-size:11px;
                            line-height:1.2;
                            white-space:nowrap;
                        "
                    >
                        {safe_name}
                    </span>
                </a>
            </td>
            """)

    if not cells:
        return ""

    return f"""
    <table
        role="presentation"
        align="center"
        cellspacing="0"
        cellpadding="0"
        border="0"
        style="margin:16px auto 0;"
    >
        <tr>
            {''.join(cells)}
        </tr>
    </table>
    """


def build_text_social_links():
    """Return company links for plain-text emails."""

    social_links = (
        ("Website", WEBSITE_URL),
        ("LinkedIn", LINKEDIN_URL),
        ("YouTube", YOUTUBE_URL),
        ("Facebook", FACEBOOK_URL),
        ("Instagram", INSTAGRAM_URL),
        ("WhatsApp", get_whatsapp_url()),
    )

    return "\n".join(f"{name}: {url}" for name, url in social_links if url)


# -----------------------------------------------------------------------------
# Reusable detail sections
# -----------------------------------------------------------------------------


def build_detail_rows(
    details,
    accent=BRAND_BLUE,
    **kwargs,
):
    """
    Build the two-column details table used for candidate,
    booking and registration information.
    """

    accent = kwargs.get(
        "accent_color",
        accent,
    )

    valid_details = [
        (label, value) for label, value in (details or []) if value not in (None, "")
    ]

    if not valid_details:
        return ""

    rows = []
    last_index = len(valid_details) - 1

    for index, (label, value) in enumerate(valid_details):
        if index == last_index:
            border = "none"
        else:
            border = f"1px solid {CARD_BORDER}"

        rows.append(f"""
            <tr>
                <td
                    valign="top"
                    style="
                        width:35%;
                        padding:12px 14px;
                        border-bottom:{border};
                        background-color:#F5F7FA;
                        color:#404A57;
                        font-family:Arial,Helvetica,sans-serif;
                        font-size:13px;
                        font-weight:700;
                        line-height:1.5;
                    "
                >
                    {escape(str(label))}
                </td>

                <td
                    valign="top"
                    style="
                        padding:12px 14px;
                        border-bottom:{border};
                        color:#242A33;
                        font-family:Arial,Helvetica,sans-serif;
                        font-size:13px;
                        line-height:1.55;
                    "
                >
                    {clean_text(value)}
                </td>
            </tr>
            """)

    return f"""
    <table
        role="presentation"
        width="100%"
        cellspacing="0"
        cellpadding="0"
        border="0"
        style="
            width:100%;
            margin-top:20px;
            border:1px solid {CARD_BORDER};
            border-left:3px solid {accent};
            border-radius:6px;
            border-collapse:separate;
            border-spacing:0;
            overflow:hidden;
        "
    >
        {''.join(rows)}
    </table>
    """


def build_detail_table(
    details,
    accent=BRAND_BLUE,
):
    """Compatibility helper for existing views."""

    return build_detail_rows(
        details,
        accent,
    )


def build_details_table(
    details,
    accent=BRAND_BLUE,
):
    """Compatibility helper for existing views."""

    return build_detail_rows(
        details,
        accent,
    )


def build_information_table(
    details,
    accent=BRAND_BLUE,
):
    """Compatibility helper for existing views."""

    return build_detail_rows(
        details,
        accent,
    )


def build_syllabus_section(
    syllabus,
    accent,
):
    """Build internship syllabus content."""

    if not syllabus:
        return ""

    if isinstance(
        syllabus,
        (list, tuple),
    ):
        items = syllabus
    else:
        items = [syllabus]

    list_items = []

    for item in items:
        if item in (None, ""):
            continue

        list_items.append(f"""
            <li
                style="
                    margin:0 0 8px;
                    color:#3E4651;
                    font-size:13px;
                    line-height:1.6;
                "
            >
                {clean_text(item)}
            </li>
            """)

    if not list_items:
        return ""

    return f"""
    <div
        style="
            margin-top:21px;
            padding:17px 18px;
            background-color:#F5F7FA;
            border-left:3px solid {accent};
            border-radius:6px;
        "
    >
        <p
            style="
                margin:0 0 11px;
                color:{accent};
                font-family:Arial,Helvetica,sans-serif;
                font-size:14px;
                font-weight:700;
            "
        >
            What you will learn
        </p>

        <ul
            style="
                margin:0;
                padding-left:20px;
                font-family:Arial,Helvetica,sans-serif;
            "
        >
            {''.join(list_items)}
        </ul>
    </div>
    """


# -----------------------------------------------------------------------------
# Reusable transactional email layout
# -----------------------------------------------------------------------------


def build_email_layout(
    title=None,
    content="",
    *,
    heading=None,
    subtitle="",
    greeting="Hello,",
    body_html="",
    content_html="",
    body_content="",
    main_content="",
    message="",
    message_html="",
    details="",
    details_html="",
    extra_html="",
    actions_html="",
    button_text="",
    button_url="",
    secondary_button_text="",
    secondary_button_url="",
    badge="ERRORS2EXPERTS",
    icon="",
    preheader="",
    closing="",
    footer_text=("Thank you for connecting with Errors2Experts."),
    accent=BRAND_BLUE,
    accent_color=None,
    **kwargs,
):
    """
    Build the compact Errors2Experts transactional email.

    Multiple aliases are accepted because different views may pass
    body or details using different keyword names.
    """

    if accent_color:
        accent = accent_color

    resolved_title = _first_non_empty(
        title,
        heading,
        kwargs.get("email_title"),
        kwargs.get("subject"),
        "Errors2Experts Notification",
    )

    resolved_subtitle = _first_non_empty(
        subtitle,
        kwargs.get("subheading"),
        kwargs.get("header_text"),
        kwargs.get("header_description"),
        kwargs.get("description"),
    )

    # This ensures candidate/customer content is not removed.
    resolved_content = _first_non_empty(
        body_html,
        content_html,
        body_content,
        main_content,
        message_html,
        content,
        message,
        kwargs.get("body"),
        kwargs.get("email_body"),
        kwargs.get("main_html"),
        kwargs.get("content_block"),
        kwargs.get("user_content"),
        kwargs.get("body_text"),
        kwargs.get("html_content"),
    )

    resolved_details = _first_non_empty(
        details_html,
        details,
        kwargs.get("detail_html"),
        kwargs.get("detail_table"),
        kwargs.get("details_table"),
        kwargs.get("information_table"),
        kwargs.get("table_html"),
    )

    if isinstance(
        resolved_details,
        (list, tuple),
    ):
        resolved_details = build_detail_rows(
            resolved_details,
            accent,
        )

    extra_parts = (
        extra_html,
        actions_html,
        kwargs.get("extra_content"),
        kwargs.get("buttons_html"),
        kwargs.get("action_buttons"),
        kwargs.get("actions"),
    )

    resolved_extra_html = "".join(
        str(part) for part in extra_parts if part not in (None, "")
    )

    resolved_preheader = _first_non_empty(
        preheader,
        kwargs.get("preview_text"),
        resolved_subtitle,
        resolved_title,
    )

    safe_title = safe_html(
        resolved_title,
    )

    safe_subtitle = safe_html(
        resolved_subtitle,
    )

    safe_greeting = safe_html(
        greeting,
    )

    safe_badge = safe_html(
        badge,
    )

    safe_preheader = safe_html(
        resolved_preheader,
    )

    safe_icon = safe_html(
        icon,
    )

    if resolved_content:
        content_section = str(
            resolved_content,
        )
    else:
        content_section = ""

    if resolved_details:
        details_section = str(
            resolved_details,
        )
    else:
        details_section = ""

    greeting_section = ""

    if safe_greeting:
        greeting_section = f"""
        <p
            style="
                margin:0 0 18px;
                color:#242A33;
                font-size:16px;
                line-height:1.5;
                font-weight:700;
            "
        >
            {safe_greeting}
        </p>
        """

    subtitle_section = ""

    if safe_subtitle:
        subtitle_section = f"""
        <p
            style="
                margin:7px 0 0;
                color:#E4F1F8;
                font-family:Arial,Helvetica,sans-serif;
                font-size:13px;
                line-height:1.55;
            "
        >
            {safe_subtitle}
        </p>
        """

    closing_section = ""

    if closing:
        closing_section = f"""
        <p
            style="
                margin:23px 0 0;
                color:#515B68;
                font-family:Arial,Helvetica,sans-serif;
                font-size:14px;
                line-height:1.7;
            "
        >
            {safe_html(closing)}
        </p>
        """

    header_icon = ""

    if safe_icon:
        header_icon = f"""
        <span
            style="
                display:inline-block;
                margin-right:7px;
            "
        >
            {safe_icon}
        </span>
        """

    button_rows = []

    if button_text and button_url:
        button_rows.append(f"""
            <tr>
                <td
                    align="left"
                    style="padding:0 0 11px;"
                >
                    <a
                        href="{escape(str(button_url), quote=True)}"
                        target="_blank"
                        rel="noopener noreferrer"
                        style="
                            display:inline-block;
                            padding:12px 18px;
                            border-radius:6px;
                            background-color:{accent};
                            color:#FFFFFF;
                            font-family:Arial,Helvetica,sans-serif;
                            font-size:13px;
                            font-weight:700;
                            text-decoration:none;
                        "
                    >
                        {safe_html(button_text)}
                    </a>
                </td>
            </tr>
            """)

    if secondary_button_text and secondary_button_url:
        button_rows.append(f"""
            <tr>
                <td
                    align="left"
                    style="padding:0;"
                >
                    <a
                        href="{escape(
                            str(secondary_button_url),
                            quote=True,
                        )}"
                        target="_blank"
                        rel="noopener noreferrer"
                        style="
                            display:inline-block;
                            padding:12px 18px;
                            border-radius:6px;
                            background-color:{accent};
                            color:#FFFFFF;
                            font-family:Arial,Helvetica,sans-serif;
                            font-size:13px;
                            font-weight:700;
                            text-decoration:none;
                        "
                    >
                        {safe_html(secondary_button_text)} →
                    </a>
                </td>
            </tr>
            """)

    button_section = ""

    if button_rows:
        button_section = f"""
        <table
            role="presentation"
            cellspacing="0"
            cellpadding="0"
            border="0"
            style="margin-top:22px;"
        >
            {''.join(button_rows)}
        </table>
        """

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <meta
        name="color-scheme"
        content="light only"
    >

    <meta
        name="supported-color-schemes"
        content="light only"
    >

    <title>{safe_title}</title>
</head>

<body
    style="
        margin:0;
        padding:0;
        background-color:{PAGE_BACKGROUND};
        color:#242A33;
    "
>
    <div
        style="
            display:none;
            max-height:0;
            overflow:hidden;
            opacity:0;
            color:transparent;
        "
    >
        {safe_preheader}
    </div>

    <table
        role="presentation"
        width="100%"
        cellspacing="0"
        cellpadding="0"
        border="0"
        style="
            width:100%;
            background-color:{PAGE_BACKGROUND};
        "
    >
        <tr>
            <td
                align="center"
                style="padding:30px 12px;"
            >
                <table
                    role="presentation"
                    width="640"
                    cellspacing="0"
                    cellpadding="0"
                    border="0"
                    style="
                        width:100%;
                        max-width:640px;
                        background-color:#FFFFFF;
                        border:1px solid {CARD_BORDER};
                        border-radius:11px;
                        border-collapse:separate;
                        border-spacing:0;
                        overflow:hidden;
                    "
                >
                    <!-- Blue header -->
                    <tr>
                        <td
                            style="
                                padding:26px 30px 25px;
                                background-color:{accent};
                                font-family:
                                    Arial,Helvetica,sans-serif;
                            "
                        >
                            <a
                                href="{escape(
                                    WEBSITE_URL,
                                    quote=True,
                                )}"
                                target="_blank"
                                rel="noopener noreferrer"
                                style="
                                    display:inline-block;
                                    padding:6px 9px;
                                    background-color:#FFFFFF;
                                    border-radius:5px;
                                    text-decoration:none;
                                "
                            >
                                {brand_name_html("16px")}
                            </a>

                            <div
                                style="margin-top:16px;"
                            >
                                <span
                                    style="
                                        display:inline-block;
                                        padding:5px 9px;
                                        border-radius:20px;
                                        background-color:
                                            rgba(255,255,255,0.18);
                                        color:#FFFFFF;
                                        font-size:9px;
                                        font-weight:700;
                                        letter-spacing:0.8px;
                                    "
                                >
                                    {safe_badge}
                                </span>
                            </div>

                            <h1
                                style="
                                    margin:12px 0 0;
                                    color:#FFFFFF;
                                    font-family:
                                        Arial,Helvetica,sans-serif;
                                    font-size:23px;
                                    line-height:1.3;
                                    font-weight:800;
                                "
                            >
                                {header_icon}{safe_title}
                            </h1>

                            {subtitle_section}
                        </td>
                    </tr>

                    <!-- Complete submitted content -->
                    <tr>
                        <td
                            style="
                                padding:27px 30px 31px;
                                color:#242A33;
                                font-family:
                                    Arial,Helvetica,sans-serif;
                                font-size:14px;
                                line-height:1.7;
                            "
                        >
                            {greeting_section}

                            <div
                                style="
                                    color:#3E4651;
                                    font-size:14px;
                                    line-height:1.75;
                                "
                            >
                                {content_section}
                            </div>

                            {details_section}

                            {resolved_extra_html}

                            {button_section}

                            {closing_section}

                            <p
                                style="
                                    margin:27px 0 0;
                                    color:#242A33;
                                    font-size:13px;
                                    line-height:1.65;
                                "
                            >
                                Best Regards,<br>
                                <strong>
                                    Errors2Experts Team
                                </strong>
                            </p>
                        </td>
                    </tr>

                    <!-- Social footer -->
                    <tr>
                        <td
                            align="center"
                            style="
                                padding:25px 14px 26px;
                                background-color:
                                    {FOOTER_BACKGROUND};
                                border-top:
                                    1px solid {CARD_BORDER};
                                font-family:
                                    Arial,Helvetica,sans-serif;
                            "
                        >
                            <p
                                style="
                                    margin:0;
                                    color:#4D5662;
                                    font-size:14px;
                                "
                            >
                                Follow us and stay connected
                            </p>

                            {build_social_links()}

                            <p
                                style="
                                    margin:20px 0 0;
                                    color:#737C87;
                                    font-size:11px;
                                    line-height:1.6;
                                "
                            >
                                {safe_html(footer_text)}<br>

                                © Errors2Experts.
                                All rights reserved.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
""".strip()


# -----------------------------------------------------------------------------
# Course, service, internship and workshop update emails
# -----------------------------------------------------------------------------


def get_email_record_data(
    update_type,
    instance,
):
    """Convert model data into a common email structure."""

    if update_type == "Course":
        return {
            "title": instance.title,
            "description": instance.description,
            "image_url": get_image_url(instance),
            "details": [
                (
                    "Duration",
                    getattr(
                        instance,
                        "duration",
                        "",
                    ),
                ),
                (
                    "Course Fee",
                    format_price(
                        getattr(
                            instance,
                            "price",
                            "",
                        )
                    ),
                ),
                (
                    "Discount",
                    getattr(
                        instance,
                        "discount",
                        "",
                    ),
                ),
            ],
            "extra_section": "",
            "page_url": (f"{WEBSITE_URL}/course/{instance.pk}/"),
        }

    if update_type == "Service":
        return {
            "title": instance.title,
            "description": instance.description,
            "image_url": get_image_url(instance),
            "details": [
                (
                    "Technologies",
                    getattr(
                        instance,
                        "technologies",
                        "",
                    ),
                ),
            ],
            "extra_section": "",
            "page_url": (f"{WEBSITE_URL}/services/{instance.pk}/"),
        }

    if update_type == "Internship":
        config = EMAIL_CONFIG["Internship"]

        return {
            "title": instance.title,
            "description": instance.description,
            "image_url": get_image_url(instance),
            "details": [
                (
                    "Duration",
                    getattr(
                        instance,
                        "duration",
                        "",
                    ),
                ),
                (
                    "Internship Fee",
                    format_price(
                        getattr(
                            instance,
                            "price",
                            "",
                        )
                    ),
                ),
            ],
            "extra_section": build_syllabus_section(
                getattr(
                    instance,
                    "syllabus",
                    None,
                ),
                config["accent"],
            ),
            "page_url": (f"{WEBSITE_URL}/internships/{instance.pk}/"),
        }

    if update_type == "Workshop":
        event_date_value = getattr(
            instance,
            "event_date",
            None,
        )

        event_time_value = getattr(
            instance,
            "event_time",
            None,
        )

        if event_date_value:
            event_date = event_date_value.strftime(
                "%d %B %Y",
            )
        else:
            event_date = ""

        if event_time_value:
            event_time = event_time_value.strftime(
                "%I:%M %p",
            )
        else:
            event_time = ""

        return {
            "title": instance.title,
            "description": instance.description,
            "image_url": get_image_url(instance),
            "details": [
                (
                    "Workshop Date",
                    event_date,
                ),
                (
                    "Workshop Time",
                    event_time,
                ),
                (
                    "Location",
                    getattr(
                        instance,
                        "location",
                        "",
                    ),
                ),
                (
                    "Registration",
                    getattr(
                        instance,
                        "registration_info",
                        "",
                    ),
                ),
            ],
            "extra_section": "",
            "page_url": (f"{WEBSITE_URL}/workshops/"),
        }

    return None


def build_update_email(
    update_type,
    instance,
):
    """Build HTML and text versions of an update email."""

    config = EMAIL_CONFIG.get(
        update_type,
    )

    if config is None or instance is None:
        return None

    record = get_email_record_data(
        update_type,
        instance,
    )

    if record is None:
        return None

    image_html = ""

    if record["image_url"]:
        image_html = f"""
        <div
            style="
                margin:0 0 20px;
            "
        >
            <img
                src="{escape(
                    str(record['image_url']),
                    quote=True,
                )}"
                alt="{escape(
                    str(record['title']),
                    quote=True,
                )}"
                width="580"
                style="
                    display:block;
                    width:100%;
                    max-width:580px;
                    height:auto;
                    border:0;
                    border-radius:8px;
                "
            >
        </div>
        """

    body_html = f"""
    {image_html}

    <p
        style="
            margin:0 0 15px;
        "
    >
        {safe_html(config["intro"])}
    </p>

    <p
        style="
            margin:0;
        "
    >
        {safe_html(record["description"])}
    </p>
    """

    details_html = build_detail_rows(
        record["details"],
        config["accent"],
    )

    html_content = build_email_layout(
        title=record["title"],
        subtitle=config["intro"],
        greeting="Hello,",
        badge=config["badge"],
        icon=config["icon"],
        body_html=body_html,
        details_html=details_html,
        extra_html=record["extra_section"],
        button_text=config["button_text"],
        button_url=record["page_url"],
        closing=config["closing"],
        accent=config["accent"],
        preheader=config["intro"],
        footer_text=("Thank you for being part of the " "Errors2Experts community."),
    )

    text_content = f"""
Hello,

{clean_plain_text(config["intro"])}

{update_type}: {clean_plain_text(record["title"])}

{clean_plain_text(record["description"])}

{clean_plain_text(config["closing"])}

{config["button_text"]}:
{record["page_url"]}

{build_text_social_links()}

Best Regards,
Errors2Experts Team
""".strip()

    return {
        "subject": config["subject"],
        "html_content": html_content,
        "text_content": text_content,
    }


# -----------------------------------------------------------------------------
# Sending helpers used by signals.py
# -----------------------------------------------------------------------------


def send_update_email(
    update_type,
    instance,
):
    """Send update emails separately to every recipient."""

    email_content = build_update_email(
        update_type,
        instance,
    )

    if email_content is None:
        logger.warning(
            "No email template found for: %s",
            update_type,
        )

        return {
            "sent": 0,
            "failed": 0,
        }

    sent_count = 0
    failed_count = 0

    for recipient in get_registered_emails():
        try:
            send_brevo_email(
                to_email=recipient,
                subject=email_content["subject"],
                html_content=(email_content["html_content"]),
                text_content=(email_content["text_content"]),
            )

            sent_count += 1

        except Exception:
            failed_count += 1

            logger.exception(
                "Failed to send %s update email to %s",
                update_type,
                recipient,
            )

    logger.info(
        "%s update completed: %s sent, %s failed",
        update_type,
        sent_count,
        failed_count,
    )

    return {
        "sent": sent_count,
        "failed": failed_count,
    }


def schedule_update_email(
    update_type,
    instance,
):
    """
    Send the email only after the database transaction succeeds.
    """

    transaction.on_commit(
        lambda: send_update_email(
            update_type,
            instance,
        )
    )
