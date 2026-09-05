from django.db import models

WORKSHOP_REGISTRATION_TYPE_CHOICES = [
    ("free", "Free"),
    ("paid", "Paid"),
]

class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    duration = models.CharField(max_length=100)
    price = models.IntegerField()
    discount = models.CharField(max_length=100)
    image = models.ImageField(upload_to='course_images/', blank=True, null=True)

    def __str__(self):
        return self.title

class Placement(models.Model):
    student_name = models.CharField(max_length=100)
    student_image = models.ImageField(upload_to='placements/')
    company_name = models.CharField(max_length=100)
    company_logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    job_role = models.CharField(max_length=100)
    package = models.CharField(max_length=50)
    location = models.CharField(max_length=100, blank=True)
    placed_year = models.PositiveIntegerField()
    course = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.student_name} - {self.company_name}"

class Module(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='modules'
    )
    module_name = models.CharField(max_length=200)
    description = models.TextField()

    def __str__(self):
        return self.module_name


class Service(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='course_images/', blank=True, null=True)
    technologies = models.CharField(
        max_length=400,
        blank=True,
        help_text="Comma-separated, e.g. 'Django, Bootstrap, PostgreSQL, REST API'"
    )

    def __str__(self):
        return self.title

    def tech_list(self):
        """Returns technologies as a clean list for templates: service.tech_list"""
        return [t.strip() for t in self.technologies.split(',') if t.strip()]


class ServiceDemoLink(models.Model):

    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="demo_links",
    )

    title = models.CharField(
        max_length=150,
        help_text=("Example: School Website Demo, " "CRM Demo, Portfolio Demo"),
    )

    image = models.FileField(
        upload_to="service_images/",
        blank=True,
        null=True,
    )

    url = models.URLField(
        max_length=500,
        help_text="Full URL of the live demo.",
        blank=True,
        null=True,
    )

    description = models.CharField(
        max_length=300,
        blank=True,
        help_text=("Short description shown for this demo."),
    )

    category = models.CharField(
        max_length=100,
        blank=True,
        help_text=("Example: Education, CRM, Hotel, " "Portfolio, E-commerce"),
    )

    technologies = models.CharField(
        max_length=300,
        blank=True,
        help_text=(
            "Comma-separated technologies. " "Example: HTML, CSS, JavaScript, Django"
        ),
    )

    order = models.PositiveIntegerField(
        default=0,
        help_text=("Lower numbers are displayed first."),
    )

    is_active = models.BooleanField(
        default=True,
        help_text=("Disable this to hide the demo " "without deleting it."),
    )

    is_featured = models.BooleanField(
        default=True,
        help_text=("Show this demo prominently on the " "service detail page."),
    )

    class Meta:
        ordering = [
            "order",
            "title",
        ]

        verbose_name = "Service Demo"
        verbose_name_plural = "Service Demos"

    def __str__(self):
        return f"{self.service.title} — " f"{self.title}"

    def tech_list(self):
        return [
            technology.strip()
            for technology in self.technologies.split(",")
            if technology.strip()
        ]

class ServiceFeature(models.Model):
    """3-6 per service — powers the 'Why Choose This Service' cards."""
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='features')
    icon = models.CharField(
        max_length=50, default='bi-check-circle',
        help_text="Bootstrap Icon class, e.g. 'bi-rocket-takeoff' — browse icons.getbootstrap.com"
    )
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.service.title} — {self.title}"


class ServiceFAQ(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='faqs')
    question = models.CharField(max_length=250)
    answer = models.TextField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Service FAQ'
        verbose_name_plural = 'Service FAQs'

    def __str__(self):
        return f"{self.service.title} — {self.question}"


class ProcessStep(models.Model):
    """Global — same development process shown on every service page."""
    icon = models.CharField(max_length=50, default='bi-search', help_text="Bootstrap Icon class")
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title
class Contact(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField()
    message = models.TextField()

    def __str__(self):
        return self.name

class ClientProject(models.Model):
    client_name = models.CharField(max_length=150)
    project_type = models.CharField(max_length=150)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='course_images/', blank=True, null=True)

    def __str__(self):
        return f"{self.client_name} - {self.project_type}"


class StudentReview(models.Model):
    GENDER_CHOICES = (
        ("M", "Male"),
        ("F", "Female"),
        ("O", "Other/Prefer not to say"),
    )

    student_name = models.CharField(max_length=120)
    course_name = models.CharField(max_length=150)
    review_text = models.TextField()
    rating = models.PositiveIntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(
        upload_to="reviews/",
        blank=True,
        null=True,
    )
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        default="M",
        help_text=("Used for default anime avatar if no custom image " "is uploaded"),
    )

    def __str__(self):
        return f"{self.student_name} - {self.course_name}"


# ============================================================
# OUR TEAM FEATURE
# ============================================================

class TeamCategory(models.Model):
    """
    Public team filter/category.

    Examples:
    - Development
    - Design
    - Marketing
    - Trainers
    - Management

    A single employee can belong to multiple categories through
    EmployeeRole.
    """

    name = models.CharField(
        max_length=100,
        unique=True,
    )

    slug = models.SlugField(
        max_length=110,
        unique=True,
        help_text=(
            "Used by the frontend filter. " "Examples: development, design, trainers."
        ),
    )

    icon_class = models.CharField(
        max_length=80,
        default="bi-people",
        blank=True,
        help_text=(
            "Bootstrap Icons class. "
            "Examples: bi-code-slash, bi-palette, "
            "bi-mortarboard, bi-briefcase."
        ),
    )

    display_order = models.PositiveIntegerField(
        default=0,
        help_text="Lower numbers appear first.",
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Turn off to hide this filter from the public Team page.",
    )

    class Meta:
        ordering = [
            "display_order",
            "name",
        ]
        verbose_name = "Team Category"
        verbose_name_plural = "Team Categories"

    def __str__(self):
        return self.name


class Employee(models.Model):
    """
    Public employee/team member profile.

    Role titles are NOT stored directly here because the same
    employee can have different roles in different categories.

    Example:
      Dharani G
        Development -> Software Developer
        Trainers     -> Python Trainer
    """

    name = models.CharField(
        max_length=150,
    )

    photo = models.ImageField(
        upload_to="employees/",
        help_text="Upload the employee's public profile photo.",
    )

    portfolio_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="Public portfolio URL. Leave blank if not available.",
    )

    display_order = models.PositiveIntegerField(
        default=0,
        help_text="Lower numbers appear first.",
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Turn off to hide this employee without deleting the record.",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "display_order",
            "name",
        ]
        verbose_name = "Team Member"
        verbose_name_plural = "Team Members"

    def __str__(self):
        return self.name


class EmployeeRole(models.Model):
    """
    Connects one employee to one category with a category-specific
    public role title.

    This is what makes multi-role filtering work.

    Example:
      Employee: Dharani G
      Category: Development
      Role: Software Developer

      Employee: Dharani G
      Category: Trainers
      Role: Full Stack Trainer

    On the Development filter the card will show:
      Software Developer

    On the Trainers filter the SAME card will show:
      Full Stack Trainer
    """

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="role_assignments",
    )

    category = models.ForeignKey(
        TeamCategory,
        on_delete=models.CASCADE,
        related_name="employee_roles",
    )

    role_title = models.CharField(
        max_length=150,
        help_text=(
            "Role shown only when this category is selected. "
            "Example: Software Developer or Python Trainer."
        ),
    )

    role_description = models.TextField(
        blank=True,
        max_length=350,
        help_text=(
            "Short professional description for this role. "
            "This description changes based on the selected team filter."
        ),
    )

    display_order = models.PositiveIntegerField(
        default=0,
        help_text=(
            "Order of this employee's roles. "
            "The first role becomes the default role in All Members."
        ),
    )

    class Meta:
        ordering = [
            "display_order",
            "category__display_order",
            "role_title",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "employee",
                    "category",
                    "role_title",
                ],
                name="unique_employee_category_role",
            ),
        ]

        verbose_name = "Employee Role"
        verbose_name_plural = "Employee Roles"

    def __str__(self):
        return f"{self.employee.name} — " f"{self.category.name}: " f"{self.role_title}"


class Career(models.Model):

    EMPLOYMENT_TYPES = (
        ('Full Time', 'Full Time'),
        ('Part Time', 'Part Time'),
        ('Internship', 'Internship'),
        ('Contract', 'Contract'),
    )

    WORK_MODE_CHOICES = (
        ("office", "Work From Office"),
        ("remote", "Remote"),
        ("hybrid", "Hybrid"),
    )

    role = models.CharField(max_length=200)
    job_description = models.TextField()
    employment_type = models.CharField(max_length=50, choices=EMPLOYMENT_TYPES)
    department = models.CharField(
        max_length=120,
        default="Academic Division",
        help_text=(
            "Examples: Academic Division, Development, "
            "Design, Marketing, Management."
        ),
    )

    salary = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text=(
            "Examples: Unpaid, 15000 - 25000 / month. "
            "The website adds the ₹ symbol when a value is present."
        ),
    )

    location = models.CharField(
        max_length=180,
        default="Dindigul, Tamil Nadu, India",
    )

    work_mode = models.CharField(
        max_length=20,
        choices=WORK_MODE_CHOICES,
        default="office",
    )

    openings = models.PositiveIntegerField(
        default=1,
        help_text="Number of currently available positions.",
    )

    image = models.ImageField(
        upload_to="careers/",
        blank=True,
        null=True,
    )

    is_active = models.BooleanField(
        default=True,
        help_text=(
            "Disable this when the opening is closed. "
            "It will disappear from the public Careers page."
        ),
    )

    posted_on = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = [
            "-posted_on",
        ]

    def __str__(self):
        return self.role

class JobApplication(models.Model):
    career = models.ForeignKey('Career', on_delete=models.CASCADE)
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    mobile = models.CharField(max_length=15)
    education = models.CharField(max_length=200)
    year_passed_out = models.CharField(max_length=10)
    resume = models.FileField(upload_to='resumes/')
    cover_letter = models.TextField()
    applied_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.career.role}"

class CourseBooking(models.Model):
    PAYMENT_CHOICES = [
        (
            "full",
            "Full Payment",
        ),
        (
            "half",
            "Half Payment",
        ),
        (
            "installment",
            "Installment",
        ),
    ]
    name = models.CharField(max_length=100)
    email = models.EmailField()
    mobile = models.CharField(max_length=15)
    education = models.CharField(max_length=200)
    year_passed = models.CharField(max_length=10)
    course = models.CharField(max_length=200)
    total_amount = models.IntegerField(
        default=0,
        help_text="Complete course fee.",
    )

    payment_type = models.CharField(
        max_length=20,
        choices=PAYMENT_CHOICES,
        default="full",
    )
    amount = models.IntegerField(
        default=0,
        help_text=("Amount the student must pay for the " "selected payment method."),
    )
    balance = models.IntegerField(
        default=0,
        help_text=(
            "Remaining amount after the selected "
            "payment amount."
        ),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = [
            "-created_at",
        ]

    def __str__(self):
        return (
            f"{self.name} - "
            f"{self.course} - "
            f"{self.get_payment_type_display()}"
        )


class ServiceBooking(models.Model):
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    mobile = models.CharField(max_length=20)
    service_name = models.CharField(max_length=200)
    message = models.TextField(blank=True)
    preferred_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.service_name}"

class WorkshopPhoto(models.Model):
    """
    Stores photos from workshops / events conducted by Errors2Experts.
    Upload images via Django admin → they appear in the Workshop Gallery section.
    """
    title       = models.CharField(max_length=200, help_text="e.g. 'Python Bootcamp – March 2025'")
    description = models.TextField(blank=True, help_text="Short caption shown under the photo (optional)")
    image       = models.ImageField(upload_to='workshop_photos/', help_text="Upload workshop photo")
    event_date  = models.DateField(blank=True, null=True, help_text="Date the workshop was held (optional)")
    order       = models.PositiveIntegerField(default=0, help_text="Lower number = shown first")
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name        = 'Workshop Photo'
        verbose_name_plural = 'Workshop Photos'

    def __str__(self):
        return self.title


class WorkshopRegistration(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ("not_required", "Not Required"),
        ("pending", "Payment Pending"),
        ("verified", "Payment Verified"),
    ]

    # ---------------- Participation Mode ----------------
    PARTICIPATION_MODE = [
        ("Offline", "Offline"),
        ("Online", "Online"),
    ]

    # ---------------- Technical Skill ----------------
    TECHNICAL_LEVEL = [
        ("Beginner", "Beginner"),
        ("Basic Knowledge", "Basic Knowledge"),
        ("Intermediate", "Intermediate"),
        ("Advanced", "Advanced"),
        ("Other", "Other"),
    ]

    # ---------------- Demo Interest ----------------
    DEMO_INTEREST = [
        ("Yes", "Yes, I want to Attend a Free Demo Session on my Interested Domain"),
        ("Maybe", "Maybe"),
        ("Need more information", "Need more information"),
        ("No", "No"),
        ("Other", "Other"),
    ]

    # ---------------- Demo Mode ----------------
    DEMO_MODE = [
        ("Online", "Online"),
        ("Offline", "Offline"),
        ("Either", "Either is Okay"),
    ]

    # ---------------- Gender ----------------

    GENDER_CHOICES = [
        ("Male", "Male"),
        ("Female", "Female"),
        ("Prefer not to say", "Prefer not to say"),
    ]

    # ===================================================
    # Basic Details
    # ===================================================

    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    mobile = models.CharField(max_length=20)

    gender = models.CharField(
        max_length=30,
        choices=GENDER_CHOICES,
        blank=True,
        null=True
    )

    participation_mode = models.CharField(
        max_length=20,
        choices=PARTICIPATION_MODE
    )

    present_address = models.TextField(blank=True, null=True)

    year_of_study = models.CharField(max_length=50, blank=True, null=True)

    college_name = models.CharField(max_length=200, blank=True, null=True)

    degree = models.CharField(max_length=100, blank=True, null=True)

    department = models.CharField(max_length=100, blank=True, null=True)

    passed_out_year = models.CharField(max_length=10, blank=True, null=True)

    # ===================================================
    # Upskill Domain
    # (Store multiple selections as comma separated text)
    # ===================================================

    interested_domains = models.TextField(
        help_text="Comma separated selected domains"
        , blank=True, null=True
    )

    # ===================================================
    # Technical Skill
    # ===================================================

    technical_skill = models.CharField(
        max_length=30,
        choices=TECHNICAL_LEVEL
        , blank=True, null=True
    )

    technical_skill_other = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    # ===================================================
    # Free Demo Session
    # ===================================================

    demo_interest = models.CharField(
        max_length=40,
        choices=DEMO_INTEREST, blank=True, null=True
    )

    demo_interest_other = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    # ===================================================
    # Optional Demo Preferences
    # ===================================================

    demo_mode = models.CharField(
        max_length=20,
        choices=DEMO_MODE,
        blank=True,
        null=True
    )

    # Morning, Afternoon, Evening, Weekend
    preferred_demo_time = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Comma separated selected time slots"
    )
    workshop = models.ForeignKey(
        "UpcomingWorkshop",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="registrations",
    )
    registration_type = models.CharField(
        max_length=10,
        choices=WORKSHOP_REGISTRATION_TYPE_CHOICES,
        default="free",
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="not_required",
    )

    # ===================================================
    # Consent
    # ===================================================

    consent = models.BooleanField(default=False, blank=True, null=True)

    # ===================================================
    # Additional Details
    # ===================================================

    queries = models.TextField(
        blank=True,
        null=True
    )

    referred_by = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name

class UpcomingWorkshop(models.Model):
    REGISTRATION_TYPE_CHOICES = WORKSHOP_REGISTRATION_TYPE_CHOICES

    title = models.CharField(max_length=200)
    description = models.TextField()

    event_date = models.DateField()
    event_time = models.TimeField(null=True, blank=True)
    location = models.CharField(max_length=200, blank=True)
    registration_type = models.CharField(
        max_length=10,
        choices=REGISTRATION_TYPE_CHOICES,
        default="free",
    )
    registration_info = models.CharField(max_length=200, blank=True)

    image = models.ImageField(upload_to="upcoming_workshops/")
    fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text=("Enter the workshop fee only when " "registration is paid."),
    )

    @property
    def is_paid(self):
        return self.registration_type == "paid" and self.fee > 0

    def __str__(self):
        return self.title

class Certificate(models.Model):
    """
    Stores certificate images that E2E issues to students.
    Each certificate can have a name, course name, and an image (scan/design).
    Upload via Django admin → they appear in the Certificates section.
    """
    CERT_TYPES = (
        ('course',      'Course Completion'),
        ('internship',  'Internship'),
        ('workshop',    'Workshop'),
        ('project',     'Live Project'),
    )

    cert_type   = models.CharField(max_length=20, choices=CERT_TYPES, default='course', verbose_name='Certificate Type')
    course_name = models.CharField(max_length=200, help_text="e.g. 'Python Full Stack Development'")
    image       = models.ImageField(upload_to='certificates/', help_text="Upload certificate image/scan")
    description = models.TextField(blank=True, help_text="Optional tagline shown under the certificate")
    order       = models.PositiveIntegerField(default=0, help_text="Lower number = shown first")
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name        = 'Certificate'
        verbose_name_plural = 'Certificates'

    def __str__(self):
        return f"{self.course_name} ({self.get_cert_type_display()})"

class Internship(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.CharField(max_length=100)
    # Storing syllabus as a JSON list for easy iteration
    syllabus = models.JSONField(help_text="Enter syllabus items as a list")

    # Image Field
    image = models.ImageField(upload_to='internships/', blank=True, null=True)

    def __str__(self):
        return self.title


class InternshipBooking(models.Model):

    PAYMENT_CHOICES = [
        (
            "full",
            "Full Payment",
        ),
        (
            "half",
            "Half Payment",
        ),
    ]

    PAYMENT_STATUS_CHOICES = [
        (
            "pending",
            "Payment Pending",
        ),
        (
            "verified",
            "Payment Verified",
        ),
        (
            "cancelled",
            "Cancelled",
        ),
    ]

    internship = models.ForeignKey(
        Internship,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings",
    )

    internship_name = models.CharField(
        max_length=200,
    )

    full_name = models.CharField(
        max_length=150,
    )

    email = models.EmailField()

    mobile = models.CharField(
        max_length=15,
    )

    education = models.CharField(
        max_length=200,
        blank=True,
    )

    year_passed = models.CharField(
        max_length=10,
        blank=True,
    )

    college_name = models.CharField(
        max_length=200,
        blank=True,
    )

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    payment_type = models.CharField(
        max_length=20,
        choices=PAYMENT_CHOICES,
        default="full",
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="pending",
    )

    message = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "-created_at",
        ]

        verbose_name = "Internship Booking"
        verbose_name_plural = "Internship Bookings"

    def __str__(self):
        return f"{self.full_name} - " f"{self.internship_name}"

class SiteOffer(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='site_offers/', blank=True, null=True)
    link_url = models.CharField(max_length=200, help_text="e.g., /internships/")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class DemoCategory(models.Model):
    name = models.CharField(max_length=150, unique=True)
    demo_link = models.URLField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class DemoRequest(models.Model):

    STATUS_CHOICES = [
        (
            "Pending",
            "Pending",
        ),
        (
            "Completed",
            "Completed",
        ),
    ]

    organization_name = models.CharField(
        max_length=200,
    )

    email = models.EmailField()

    mobile = models.CharField(
        max_length=15,
    )

    # -------------------------------------------------
    # Selected Service
    # -------------------------------------------------

    service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="demo_requests",
    )

    # -------------------------------------------------
    # Exact demo selected by the user
    # -------------------------------------------------

    selected_demo = models.ForeignKey(
        ServiceDemoLink,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="demo_requests",
    )

    # -------------------------------------------------
    # Existing generic DemoCategory
    # Keep this for existing database records and
    # other generic demo-request functionality.
    # -------------------------------------------------

    category = models.ForeignKey(
        DemoCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    custom_requirement = models.TextField(
        blank=True,
        null=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = [
            "-created_at",
        ]

        verbose_name = "Demo Request"
        verbose_name_plural = "Demo Requests"

    def __str__(self):

        if self.selected_demo:
            return f"{self.organization_name} - " f"{self.selected_demo.title}"

        if self.category:
            return f"{self.organization_name} - " f"{self.category.name}"

        return f"{self.organization_name} - " "Custom Request"

class DemoBooking(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField()
    mobile = models.CharField(max_length=15)
    education = models.CharField(max_length=150)
    source = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
