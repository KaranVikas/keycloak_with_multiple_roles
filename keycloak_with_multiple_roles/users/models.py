import random
import string
import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

class TimestampModel(models.Model):
  """ Abstract model with created_at and updated_at fields """
  created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
  updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

  class Meta:
    abstract = True

#     Utility funcitons
def generate_family_code():
  """Generate unique 5-character family code (e.g., 'A8K9Z')"""
  while True:
    code = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
    # Check if code exists using a late import to avoid circular dependency
    from keycloak_with_multiple_roles.users.models import Parent
    if not Parent.objects.filter(family_code=code).exists():
      return code


def generate_student_code():
  """Generate unique 8-character student code (e.g., 'STU12345')"""
  while True:
    code = "STU" + "".join(random.choices(string.digits, k=5))
    from keycloak_with_multiple_roles.users.models import Student
    if not Student.objects.filter(student_code=code).exists():
      return code

class User(AbstractUser):
  """
  Custom User model for KC_multiroles.
  Support multiple user types: parent, student, Admin
  """
  USER_TYPE_CHOICES = (
      ('parent',  _('Parent')),
      ('student', _('Student')),
      ('admin', _('Admin')),
  )

  uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
  email = models.EmailField(_('email address'), unique=True)
  user_type = models.CharField(_("User Type"), max_length=10, choices=USER_TYPE_CHOICES, null=True, blank=True)

  name = models.CharField(_("Name of User"), max_length=255, null=True, blank=True)
  first_name = None
  last_name  = None

  class Meta:
    verbose_name = _("User")
    verbose_name_plural = _("Users")
    ordering = ['-data_joined']

  def get_absolute_url(self) -> str:
      """ Get URL for user's detail view."""

      return reverse("users:detail", kwargs={"username": self.username})

  def __str__(self):
    return self.email or self.username

class Parent(TimestampModel):
  """
    Parent Model: onetoone relationship with User
    A parent can have multiple students linked via family code.
  """


  uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
  # one to one relationship with user

  parent_link = models.OneToOneField(
    User,
    on_delete= models.CASCADE,
    related_name='parent_profile',
    primary_key=True
  )

  # unique family code for parent
  family_code = models.CharField(
    _("Family code"),
    max_length=10,
    unique=True,
    default=generate_family_code,
    editable=False,
    help_text=_("Unique family code for parent.")
                                 )

  user = models.OneToOneField(
    User,
    on_delete=models.CASCADE,
    related_name='parent',
    primary_key=True
  )

  family_code = models.CharField(_(
    "Family Code"),
    max_length=10,
    unique=True,
    default=generate_family_code,
    editable=False,
    help_text="Unique family code for parent."
  )
  phone_number = models.CharField(_("Phone Number"), max_length=15, blank=True)
  address = models.TextField(_("Address"), blank=True)

  created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
  updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

  class Meta:
    verbose_name = _("Parent")
    verbose_name_plural = _("Parents")
    ordering = ["-created_at"]
    indexes = [
      models.Index(fields=['family_code']),
    ]

  def __str__(self):
    return f"Parent: {self.user.link.email} ({self.family_code})"

  def get_all_students(self):
    """
      Get all students linked to this parent via family_code
    Returns:
      Queryset: All students with matching parent_family code
    """
    return Student.objects.filter(parent_family_code=self.family_code)

  def get_student_count(self):
    """ Get total number of students linked to parents """
    return self.get_all_students().count()

  def check_valid_student(self, student_user_id):
    """
      check if a student belong to this parent

     Args:
       student_user_id: User ID of the student to check.

      Returns:
        bool: True if student belongs to this parent, False otherwise.
    """
    return self.get_all_students().filter(student_link__id=student_user_id).exists()

class StudentManager(models.Manager):
  """ Custom manager for student model """

  def get_or_none(self, **kwargs):
    """ Safely get a student without raising exception. """
    try:
      return self.get(**kwargs)
    except Student.DoesNotExist:
      return None

  def get_by_user_id(self, user_id):
    """ Get student by user ID """
    try:
      return self.get(student_link__id=user_id)
    except Student.DoesNotExist:
      return None

  def get_by_student_code(self, student_code):
    """ Get student by student code """
    try:
      return self.get(student_code=student_code)
    except Student.DoesNotExist:
      return None

  def unlinked_students(self):
    """ Get all studnets without parent links """
    return self.filter(
      model.Q(parent_family_code__isnull=True) | models.Q(parent_family_code='')
    )

  def linked_students(self):
    """ Get all students with parent links"""
    return self.exclude(
      models.Q(parent_family_code__isnull=True) | models.Q(parent_family_code='')
    )

class Student(TimestampModel):
  """
      Student model - One-to-One relationship with User.
      Students are linked to parents via parent_family_code.
      """

  uuid = models.UUIDField(
    default=uuid.uuid4,
    editable=False,
    unique=True,
  )

  student_link = models.OneToOneField(
    User,
    on_delete=models.CASCADE,
    related_name='student_profile',
    primary_key=True
  )

  parent_family_code = models.CharField(
    _("Parent Family Code"),
    max_length=10,
    blank=True,
    null=True,
    help_text="Unique family code for parent"
  )

  #Auto-generated student code
  student_code = models.CharField()
  _("student Code"),
  max_length=10,
  unique=True,
  default=generate_student_code,
  editable=False,
  help_text=_("Auto-generated student code")

  #grade and class information
  grade = models.CharField(
    _("Grade"),
    max_length=20,
    blank=True,
    help_text=_("Student's current grade level")
  )

  class_name = models.CharField(
    _("Class Name"),
    max_length=20,
    blank=True,
    help_text=_("Student's current class")
  )

  objects = StudentManager()

  class Meta:
    verbose_name = _("Student")
    verbose_name_plural = _("Students")
    ordering = ['created_at']
    indexes = [
      models.Index(fields=['parent_family_code']),
      models.Index(fields=['student_code']),
      models.Index(fields=['grade']),
      models.Index(fields=['class_name'])
    ]

  def __str__(self):
    return f"Student: {self.student_link.email} ({self.student_code})"

  def get_parent(self):
    """
        Get the parent for this student via family code.

        Returns:
          Parent: Parent object or None if not found.
    """
    if not self.parent_family_code:
      return None

    try:
      return Parent.objects.get(family_code=self.parent_family_code)
    except Parent.DoesNotExist:
      return None

  def is_linked_to_parent(self):
    """ Check if student is linked to a parent"""
    return bool(self.parent_family_code and self.get_parent())

  def link_to_parent(self, family_code):
    """
      Link this student to a parent using family code.

      Args:
        family_code: The parent's family code.

      Returns:
        bool: true if successful, False if family code invalid
    """

    try:
      parent = Parent.objects.get(family_code=family_code)
      self.parent_family_code = family_code
      self.save(update_fields=['parent_family_code', 'updated_at'])
      return True
    except Parent.DoesNotExist:
      return False

  def unlink_from_parent(self):
    """ Remove parent link from this student"""
    self.parent_family_code = None
    self.save(update_fields=['parent_family_code','updated_at'])

