from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Course, Service, Career, Internship


class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = "weekly"

    def items(self):
        return [
            "home",
            "about",
            "courses",
            "allcourse",
            "services",
            "placement",
            "reviews",
            "contact",
            "careers",
            "team",
            "workshops",
            "certificates",
            "internship_list",
        ]

    def location(self, item):
        return reverse(item)


class CourseSitemap(Sitemap):
    priority = 0.9
    changefreq = "weekly"

    def items(self):
        return Course.objects.all()

    def location(self, obj):
        return reverse("course_detail", args=[obj.id])


class ServiceSitemap(Sitemap):
    priority = 0.9
    changefreq = "weekly"

    def items(self):
        return Service.objects.all()

    def location(self, obj):
        return reverse("service_detail", args=[obj.pk])


class CareerSitemap(Sitemap):
    priority = 0.8
    changefreq = "weekly"

    def items(self):
        return Career.objects.filter(is_active=True)

    def location(self, obj):
        return reverse("career_detail", args=[obj.pk])


class InternshipSitemap(Sitemap):
    priority = 0.9
    changefreq = "weekly"

    def items(self):
        return Internship.objects.all()

    def location(self, obj):
        return reverse("internship_detail", args=[obj.pk])


sitemaps = {
    "static": StaticViewSitemap,
    "courses": CourseSitemap,
    "services": ServiceSitemap,
    "careers": CareerSitemap,
    "internships": InternshipSitemap,
}