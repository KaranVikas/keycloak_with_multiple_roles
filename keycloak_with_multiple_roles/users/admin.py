from allauth.account.decorators import secure_admin_login
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.utils.translation import gettext_lazy as _

from .forms import UserAdminChangeForm, UserAdminCreationForm
from .models import User, Parent, Student

if settings.DJANGO_ADMIN_FORCE_ALLAUTH:
  admin.autodiscover()
  admin.site.login = secure_admin_login(admin.site.login)  # type: ignore[method-assign]


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
  form = UserAdminChangeForm
  add_form = UserAdminCreationForm
  fieldsets = (
    (None, {"fields": ("username", "password")}),
    (_("Personal info"), {"fields": ("name", "email", "user_type")}),
    (_("Payment"), {"fields": ("is_paid", "customer_id")}),
    (
      _("Permissions"),
      {
        "fields": (
          "is_active",
          "is_staff",
          "is_superuser",
          "groups",
          "user_permissions",
        ),
      },
    ),
    (_("Important dates"), {"fields": ("last_login", "date_joined")}),
  )
  list_display = ["email", "username", "name", "user_type", "is_paid", "is_superuser"]
  list_filter = ["user_type", "is_paid", "is_staff", "is_superuser", "is_active"]
  search_fields = ["name", "email", "username"]
  ordering = ["-date_joined"]


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
  list_display = [
    "parent_link",
    "family_code",
    "phone_number",
    "country",
    "get_students_count",
    "created_at"
  ]
  list_filter = ["country", "account_emails", "marketing", "student_updates", "created_at"]
  search_fields = ["parent_link__email", "parent_link__username", "family_code", "phone_number"]
  readonly_fields = ["uuid", "family_code", "created_at", "updated_at"]

  fieldsets = (
    (_("User Link"), {"fields": ("parent_link", "uuid", "family_code")}),
    (_("Contact Information"), {"fields": ("phone_number", "address", "country", "state")}),
    (_("Email Preferences"), {"fields": ("account_emails", "marketing", "student_updates")}),
    (_("Timestamps"), {"fields": ("created_at", "updated_at")}),
  )

  def get_students_count(self, obj):
    return obj.get_students_count()

  get_students_count.short_description = _("Students Count")


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
  list_display = [
    "student_link",
    "student_code",
    "grade",
    "class_name",
    "parent_family_code",
    "is_linked",
    "created_at"
  ]
  list_filter = ["grade", "class_name", "created_at"]
  search_fields = [
    "student_link__email",
    "student_link__username",
    "student_code",
    "parent_family_code"
  ]
  readonly_fields = ["uuid", "student_code", "qr_code", "created_at", "updated_at"]

  fieldsets = (
    (_("User Link"), {"fields": ("student_link", "uuid", "student_code")}),
    (_("Parent Link"), {"fields": ("parent_family_code",)}),
    (_("Academic Information"), {"fields": ("grade", "class_name")}),
    (_("Media"), {"fields": ("avatar_image", "qr_code")}),
    (_("Timestamps"), {"fields": ("created_at", "updated_at")}),
  )

  def is_linked(self, obj):
    return obj.is_linked_to_parent()

  is_linked.boolean = True
  is_linked.short_description = _("Linked to Parent")

