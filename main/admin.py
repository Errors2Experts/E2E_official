from django.contrib import admin
from django.utils.html import format_html

from .excel_export import export_as_excel
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
    JobApplication,
    Module,
    ProcessStep,
    Service,
    ServiceBooking,
    ServiceDemoLink,
    ServiceFAQ,
    ServiceFeature,
    SiteOffer,
    StudentReview,
    UpcomingWorkshop,
    WorkshopPhoto,
    WorkshopRegistration,
    TeamCategory,
    Employee,
    EmployeeRole,
)

# =========================================================
# ADMIN SITE BRANDING
# =========================================================

admin.site.site_header = "Errors2Experts Administration"
admin.site.site_title = "Errors2Experts Admin"
admin.site.index_title = "Management Dashboard"


# =========================================================
# COMMON ADMIN CONFIGURATION
# =========================================================


class BaseAdmin(admin.ModelAdmin):

    list_per_page = 25

    save_on_top = False

    actions_on_top = True
    actions_on_bottom = False

    empty_value_display = "—"

    preserve_filters = True


class ExportableAdmin(BaseAdmin):
    """
    Common configuration for models that support Excel export.
    """

    actions = [
        export_as_excel,
    ]


# =========================================================
# SIMPLE MODELS
# =========================================================


@admin.register(ClientProject)
class ClientProjectAdmin(BaseAdmin):
    pass


@admin.register(StudentReview)
class StudentReviewAdmin(BaseAdmin):
    pass


@admin.register(Module)
class ModuleAdmin(BaseAdmin):
    pass


# =========================================================
# UPCOMING WORKSHOP
# =========================================================


@admin.register(UpcomingWorkshop)
class UpcomingWorkshopAdmin(BaseAdmin):
    pass


# =========================================================
# CONTACT
# =========================================================


@admin.register(Contact)
class ContactAdmin(ExportableAdmin):

    list_display = (
        "name",
        "email",
    )

    search_fields = (
        "name",
        "email",
        "message",
    )


# =========================================================
# SERVICE INLINE MODELS
# =========================================================


class ServiceDemoLinkInline(admin.TabularInline):

    model = ServiceDemoLink

    extra = 0

    fields = (
        "title",
        "category",
        "url",
        "image",
        "description",
        "technologies",
        "is_active",
        "is_featured",
        "order",
    )

    ordering = (
        "order",
        "title",
    )

    show_change_link = True


class ServiceFeatureInline(admin.TabularInline):

    model = ServiceFeature

    extra = 0

    show_change_link = True


class ServiceFAQInline(admin.TabularInline):

    model = ServiceFAQ

    extra = 0

    show_change_link = True


# =========================================================
# SERVICE
# =========================================================


@admin.register(Service)
class ServiceAdmin(BaseAdmin):

    list_display = (
        "title",
        "demo_count",
        "feature_count",
        "faq_count",
    )

    search_fields = (
        "title",
        "description",
        "technologies",
    )

    ordering = ("title",)

    inlines = [
        ServiceDemoLinkInline,
        ServiceFeatureInline,
        ServiceFAQInline,
    ]

    @admin.display(
        description="Demos",
    )
    def demo_count(self, obj):

        return obj.demo_links.count()

    @admin.display(
        description="Features",
    )
    def feature_count(self, obj):

        return obj.features.count()

    @admin.display(
        description="FAQs",
    )
    def faq_count(self, obj):

        return obj.faqs.count()


# =========================================================
# SERVICE DEMO LINKS
# =========================================================


@admin.register(ServiceDemoLink)
class ServiceDemoLinkAdmin(BaseAdmin):

    list_display = (
        "title",
        "service",
        "category",
        "active_badge",
        "featured_badge",
        "order",
    )

    list_display_links = ("title",)

    list_filter = (
        "service",
        "category",
        "is_active",
        "is_featured",
    )

    search_fields = (
        "title",
        "service__title",
        "category",
        "description",
        "technologies",
        "url",
    )

    list_editable = ("order",)

    ordering = (
        "service",
        "order",
        "title",
    )

    autocomplete_fields = ("service",)

    list_per_page = 30

    @admin.display(
        description="Active",
        ordering="is_active",
        boolean=False,
    )
    def active_badge(self, obj):

        if obj.is_active:

            return format_html(
                '<span class="e2e-status ' 'e2e-status-success">' "● Active" "</span>"
            )

        return format_html(
            '<span class="e2e-status ' 'e2e-status-muted">' "● Disabled" "</span>"
        )

    @admin.display(
        description="Featured",
        ordering="is_featured",
        boolean=False,
    )
    def featured_badge(self, obj):

        if obj.is_featured:

            return format_html(
                '<span class="e2e-status ' 'e2e-status-warning">' "★ Featured" "</span>"
            )

        return format_html(
            '<span class="e2e-status ' 'e2e-status-muted">' "Normal" "</span>"
        )


# =========================================================
# PROCESS STEPS
# =========================================================


@admin.register(ProcessStep)
class ProcessStepAdmin(BaseAdmin):

    list_display = (
        "title",
        "order",
    )

    list_editable = ("order",)

    ordering = ("order",)


# =========================================================
# CAREERS
# =========================================================


@admin.register(Career)
class CareerAdmin(BaseAdmin):

    list_display = (
        "role",
        "employment_type",
        "department",
        "work_mode",
        "openings",
        "salary",
        "is_active",
        "posted_on",
    )

    list_filter = (
        "is_active",
        "employment_type",
        "department",
        "work_mode",
        "posted_on",
    )

    search_fields = (
        "role",
        "job_description",
        "department",
        "location",
    )

    list_editable = (
        "openings",
        "is_active",
    )

    ordering = ("-posted_on",)

    date_hierarchy = "posted_on"


# =========================================================
# JOB APPLICATIONS
# =========================================================


@admin.register(JobApplication)
class JobApplicationAdmin(ExportableAdmin):

    list_display = (
        "full_name",
        "career",
        "email",
        "mobile",
        "education",
        "year_passed_out",
        "applied_on",
    )

    search_fields = (
        "full_name",
        "email",
        "mobile",
    )

    list_filter = (
        "career",
        "education",
        "applied_on",
    )

    readonly_fields = ("applied_on",)

    ordering = ("-applied_on",)

    date_hierarchy = "applied_on"

    list_select_related = ("career",)


# =========================================================
# COURSE
# =========================================================


@admin.register(Course)
class CourseAdmin(BaseAdmin):

    list_display = (
        "title",
        "duration",
        "price",
        "discount",
    )

    search_fields = (
        "title",
        "description",
        "duration",
        "discount",
    )

    ordering = ("title",)

# ============================================================
# OUR TEAM ADMIN
# ============================================================

class EmployeeRoleInline(admin.TabularInline):
    """
    Add multiple public roles to the same employee directly
    from the Employee admin screen.
    """

    model = EmployeeRole

    extra = 1

    fields = (
        "category",
        "role_title",
        "role_description",
        "display_order",
    )

    ordering = (
        "display_order",
        "category",
    )


@admin.register(TeamCategory)
class TeamCategoryAdmin(BaseAdmin):
    list_display = (
        "name",
        "slug",
        "icon_class",
        "display_order",
        "is_active",
    )

    list_filter = ("is_active",)

    search_fields = (
        "name",
        "slug",
    )

    ordering = (
        "display_order",
        "name",
    )

    list_editable = (
        "display_order",
        "is_active",
    )


@admin.register(Employee)
class EmployeeAdmin(BaseAdmin):
    list_display = (
        "name",
        "public_roles",
        "portfolio_status",
        "display_order",
        "is_active",
        "updated_at",
    )

    list_filter = (
        "is_active",
        "role_assignments__category",
    )

    search_fields = (
        "name",
        "role_assignments__role_title",
        "role_assignments__category__name",
        "portfolio_url",
    )

    ordering = (
        "display_order",
        "name",
    )

    list_editable = (
        "display_order",
        "is_active",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    inlines = [
        EmployeeRoleInline,
    ]

    fieldsets = (
        (
            "Public Profile",
            {
                "fields": (
                    "name",
                    "photo",
                    "portfolio_url",
                ),
            },
        ),
        (
            "Display",
            {
                "fields": (
                    "display_order",
                    "is_active",
                ),
            },
        ),
        (
            "System Information",
            {
                "classes": ("collapse",),
                "fields": (
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

    @admin.display(
        description="Roles",
    )
    def public_roles(self, obj):
        roles = obj.role_assignments.select_related("category").order_by(
            "display_order",
            "category__display_order",
        )

        values = [f"{role.category.name}: {role.role_title}" for role in roles]

        return " | ".join(values) if values else "—"

    @admin.display(
        description="Portfolio",
        boolean=True,
    )
    def portfolio_status(self, obj):
        return bool(obj.portfolio_url)


@admin.register(EmployeeRole)
class EmployeeRoleAdmin(BaseAdmin):
    """
    Optional standalone role-management view.
    You can also manage roles inside each Employee page.
    """

    list_display = (
        "employee",
        "category",
        "role_title",
        "display_order",
    )

    list_filter = ("category",)

    search_fields = (
        "employee__name",
        "role_title",
        "category__name",
    )

    ordering = (
        "employee__display_order",
        "display_order",
    )

# =========================================================
# COURSE BOOKINGS
# =========================================================


@admin.register(CourseBooking)
class CourseBookingAdmin(ExportableAdmin):

    list_display = (
        "name",
        "course",
        "payment_type_badge",
        "total_amount_display",
        "amount_display",
        "balance_display",
        "email",
        "mobile",
        "created_at",
    )

    list_display_links = ("name",)

    search_fields = (
        "name",
        "email",
        "mobile",
        "course",
        "education",
        "year_passed",
    )

    list_filter = (
        "payment_type",
        "course",
        "education",
        "created_at",
    )

    readonly_fields = ("created_at",)

    ordering = ("-created_at",)

    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Student Information",
            {
                "fields": (
                    "name",
                    "email",
                    "mobile",
                    "education",
                    "year_passed",
                ),
            },
        ),
        (
            "Course & Payment Information",
            {
                "fields": (
                    "course",
                    "payment_type",
                    "total_amount",
                    "amount",
                    "balance",
                ),
            },
        ),
        (
            "System Information",
            {
                "fields": ("created_at",),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(
        description="Payment Type",
        ordering="payment_type",
    )
    def payment_type_badge(self, obj):

        payment_type = (obj.payment_type or "").strip().lower()

        if payment_type == "full":

            return format_html(
                '<span class="e2e-status '
                'e2e-status-success">'
                "● Full Payment"
                "</span>"
            )

        if payment_type == "half":

            return format_html(
                '<span class="e2e-status '
                'e2e-status-warning">'
                "● Half Payment"
                "</span>"
            )

        if payment_type == "installment":

            return format_html(
                '<span class="e2e-status ' 'e2e-status-info">' "● Installment" "</span>"
            )

        return format_html(
            '<span class="e2e-status ' 'e2e-status-muted">' "{}" "</span>",
            obj.get_payment_type_display(),
        )

    @admin.display(
        description="Course Fee",
        ordering="total_amount",
    )
    def total_amount_display(self, obj):

        return f"₹{obj.total_amount:,}"

    @admin.display(
        description="Pay Now",
        ordering="amount",
    )
    def amount_display(self, obj):

        return f"₹{obj.amount:,}"

    @admin.display(
        description="Balance",
        ordering="balance",
    )
    def balance_display(self, obj):

        return f"₹{obj.balance:,}"


# =========================================================
# WORKSHOP REGISTRATIONS
# =========================================================


@admin.register(WorkshopRegistration)
class WorkshopRegistrationAdmin(ExportableAdmin):

    list_display = (
        "full_name",
        "email",
        "mobile",
        "gender",
        "participation_mode",
        "college_name",
        "degree",
        "department",
        "created_at",
    )

    search_fields = (
        "full_name",
        "email",
        "mobile",
        "college_name",
        "department",
        "degree",
        "interested_domains",
        "referred_by",
    )

    list_filter = (
        "gender",
        "participation_mode",
        "technical_skill",
        "demo_interest",
        "demo_mode",
        "consent",
        "created_at",
    )

    readonly_fields = ("created_at",)

    ordering = ("-created_at",)

    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Personal Information",
            {
                "fields": (
                    "full_name",
                    "email",
                    "mobile",
                    "gender",
                    "present_address",
                ),
            },
        ),
        (
            "Education",
            {
                "fields": (
                    "year_of_study",
                    "college_name",
                    "degree",
                    "department",
                    "passed_out_year",
                ),
            },
        ),
        (
            "Technical Information",
            {
                "fields": (
                    "interested_domains",
                    "technical_skill",
                    "technical_skill_other",
                ),
            },
        ),
        (
            "Demo Preference",
            {
                "fields": (
                    "demo_interest",
                    "demo_interest_other",
                    "demo_mode",
                    "preferred_demo_time",
                ),
            },
        ),
        (
            "Additional Information",
            {
                "fields": (
                    "participation_mode",
                    "queries",
                    "referred_by",
                    "consent",
                ),
            },
        ),
        (
            "System Information",
            {
                "fields": ("created_at",),
                "classes": ("collapse",),
            },
        ),
    )


# =========================================================
# SERVICE BOOKINGS
# =========================================================


@admin.register(ServiceBooking)
class ServiceBookingAdmin(ExportableAdmin):

    list_display = (
        "full_name",
        "service_name",
        "email",
        "mobile",
        "preferred_date",
        "created_at",
    )

    search_fields = (
        "full_name",
        "email",
        "mobile",
        "service_name",
    )

    list_filter = (
        "service_name",
        "preferred_date",
        "created_at",
    )

    readonly_fields = ("created_at",)

    ordering = ("-created_at",)

    date_hierarchy = "created_at"


# =========================================================
# WORKSHOP PHOTOS
# =========================================================


@admin.register(WorkshopPhoto)
class WorkshopPhotoAdmin(BaseAdmin):

    list_display = (
        "title",
        "event_date",
        "order",
        "created_at",
    )

    list_editable = ("order",)

    search_fields = (
        "title",
        "description",
    )

    list_filter = ("event_date",)

    readonly_fields = ("created_at",)

    ordering = (
        "order",
        "-created_at",
    )

    date_hierarchy = "event_date"


# =========================================================
# CERTIFICATES
# =========================================================


@admin.register(Certificate)
class CertificateAdmin(BaseAdmin):

    list_display = (
        "course_name",
        "cert_type",
        "order",
        "created_at",
    )

    list_editable = ("order",)

    list_filter = (
        "cert_type",
        "created_at",
    )

    search_fields = ("course_name",)

    readonly_fields = ("created_at",)

    ordering = (
        "order",
        "-created_at",
    )

    date_hierarchy = "created_at"


# =========================================================
# INTERNSHIPS
# =========================================================


@admin.register(Internship)
class InternshipAdmin(BaseAdmin):

    list_display = (
        "title",
        "price",
        "duration",
    )

    search_fields = (
        "title",
        "description",
    )

    ordering = ("title",)


# =========================================================
# INTERNSHIP BOOKINGS
# =========================================================


@admin.register(InternshipBooking)
class InternshipBookingAdmin(ExportableAdmin):

    list_display = (
        "full_name",
        "internship_name",
        "payment_type",
        "amount",
        "balance",
        "payment_status_badge",
        "created_at",
    )

    list_filter = (
        "payment_type",
        "payment_status",
        "created_at",
    )

    search_fields = (
        "full_name",
        "email",
        "mobile",
        "internship_name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = ("-created_at",)

    date_hierarchy = "created_at"

    @admin.display(
        description="Payment Status",
        ordering="payment_status",
    )
    def payment_status_badge(self, obj):

        status = (obj.payment_status or "").lower()

        if status == "verified":

            return format_html(
                '<span class="e2e-status ' 'e2e-status-success">' "● Verified" "</span>"
            )

        if status == "pending":

            return format_html(
                '<span class="e2e-status ' 'e2e-status-warning">' "● Pending" "</span>"
            )

        if status == "not_required":

            return format_html(
                '<span class="e2e-status '
                'e2e-status-info">'
                "● Not Required"
                "</span>"
            )

        return format_html(
            '<span class="e2e-status ' 'e2e-status-muted">' "{}" "</span>",
            obj.payment_status or "—",
        )


# =========================================================
# SITE OFFERS
# =========================================================


@admin.register(SiteOffer)
class SiteOfferAdmin(BaseAdmin):

    list_display = (
        "title",
        "active_status",
        "created_at",
    )

    list_filter = (
        "is_active",
        "created_at",
    )

    search_fields = ("title",)

    readonly_fields = ("created_at",)

    ordering = ("-created_at",)

    date_hierarchy = "created_at"

    @admin.display(
        description="Status",
        ordering="is_active",
    )
    def active_status(self, obj):

        if obj.is_active:

            return format_html(
                '<span class="e2e-status ' 'e2e-status-success">' "● Active" "</span>"
            )

        return format_html(
            '<span class="e2e-status ' 'e2e-status-muted">' "● Inactive" "</span>"
        )


# =========================================================
# DEMO CATEGORIES
# =========================================================


@admin.register(DemoCategory)
class DemoCategoryAdmin(BaseAdmin):

    list_display = (
        "name",
        "demo_link",
        "active_status",
    )

    list_filter = ("is_active",)

    search_fields = (
        "name",
        "demo_link",
    )

    ordering = ("name",)

    @admin.display(
        description="Status",
        ordering="is_active",
    )
    def active_status(self, obj):

        if obj.is_active:

            return format_html(
                '<span class="e2e-status ' 'e2e-status-success">' "● Active" "</span>"
            )

        return format_html(
            '<span class="e2e-status ' 'e2e-status-muted">' "● Inactive" "</span>"
        )


# =========================================================
# DEMO REQUESTS
# =========================================================


@admin.register(DemoRequest)
class DemoRequestAdmin(ExportableAdmin):

    list_display = (
        "organization_name",
        "service",
        "selected_demo",
        "email",
        "mobile",
        "status_badge",
        "created_at",
    )

    list_filter = (
        "status",
        "service",
        "selected_demo",
        "category",
        "created_at",
    )

    search_fields = (
        "organization_name",
        "email",
        "mobile",
        "service__title",
        "selected_demo__title",
        "custom_requirement",
    )

    readonly_fields = ("created_at",)

    autocomplete_fields = (
        "service",
        "selected_demo",
        "category",
    )

    ordering = ("-created_at",)

    date_hierarchy = "created_at"

    list_select_related = (
        "service",
        "selected_demo",
        "category",
    )

    @admin.display(
        description="Status",
        ordering="status",
    )
    def status_badge(self, obj):

        status = (obj.status or "").strip().lower()

        if status in {
            "completed",
            "approved",
            "sent",
            "verified",
        }:

            return format_html(
                '<span class="e2e-status ' 'e2e-status-success">' "● {}" "</span>",
                obj.status,
            )

        if status == "pending":

            return format_html(
                '<span class="e2e-status ' 'e2e-status-warning">' "● Pending" "</span>"
            )

        if status in {
            "rejected",
            "cancelled",
            "failed",
        }:

            return format_html(
                '<span class="e2e-status ' 'e2e-status-danger">' "● {}" "</span>",
                obj.status,
            )

        return format_html(
            '<span class="e2e-status ' 'e2e-status-info">' "● {}" "</span>",
            obj.status or "Unknown",
        )


# =========================================================
# DEMO BOOKINGS
# =========================================================


@admin.register(DemoBooking)
class DemoBookingAdmin(ExportableAdmin):

    list_display = (
        "name",
        "email",
        "mobile",
        "education",
        "source",
        "created_at",
    )

    search_fields = (
        "name",
        "email",
        "mobile",
    )

    list_filter = (
        "education",
        "source",
        "created_at",
    )

    readonly_fields = ("created_at",)

    ordering = ("-created_at",)

    date_hierarchy = "created_at"
