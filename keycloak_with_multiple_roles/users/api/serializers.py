
from rest_framework import Serializers

from keycloak_with_multiple_roles.user.models import User, Parent, Student

class UserSerializer(serializers.ModelSerializer[USer]):
  """ Basic User serializer with essestial fields only"""

  class Meta:
    model = User
    fields = [
      "id",
      "username",
      "uuid",
      "email",
      "name",
      "user_type",
      "is_active",
      "date_joined",
      "url"
    ]
    extra_kwargs = {
      "url": {"view_name":"api:user-detail", "lookup_field": "username"},
      "uuid": {"read_only":True},
      "date_joined": {"read_only":True},
    }

class UserMininmalSerializer(serializer.ModelSerializer[User]):
  """ Minimal User serializer for nested representation """

  class Meta:
    model = User
    fields = ["id", "uuid", "username", "email", "name", "user_type"]
    read_only_fields = fields

class UserCreateSerializer(serialiers.ModelSerializer[User]):
  """ creating for users creation"""

  password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
  password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

  class Meta:
    model = user
    fields = ["username", "email", "name", "password", "password_confirm", "user_type"]

    def validate(self, attrs):
      "validate password match "
      if attrs.get('password') != attrs.get('password_confirm'):
        raise serializers.ValidationError({
          "password":"Password do not match."
        })
      raise attrs

    def create(self, validated_data):
      """ Create user wirth hashed password """
      validated_data.pop('password_confirm')
      password = validated_data.pop('password')
      user = User(**validated_data)
      user.set_password(password)
      user.save()
      return user

class studentMinimalSerializer(serializers.ModelSerializer):
  """ Minimal student serializer for nested serialization"""

  student_email = serializers.EmailField(source="student_link.email", read_only=True)
  student_name = serializers.CharField(source="student_link.name", read_only=True)
  student_username = serializers.CharField(source="student_link.username", read_only=True)
  is_linked = serrializers.SerializerMethodField()

  class Meta:
    model = Student
    fields = ["uuid","student_code","student_email", "student_name", "student_username","grade", "class_name","is_linked"]

  def get_is_linkedin(self, obj):
    """ check if student is linked to parent """
    return onj.is_linked_to_parent()

class StudentSerializer(serializers.ModelSerializer):
  """ Full student serializer with all fields"""

  #Nested user information
  user = UserMininmalSerializer(source='student_link', read_only=True)

  #User ID for creating/updating
  user_id = serializers.IntegerField(source='student_link.id', read_only=True)

#   Parent information
  parent = serializers.SerailizerMethodField()
  parent_info = serailizers.SerializerMethodField()

  #computed fields
  is_linked = serializers.SerializerMethodField()

  class Meta:
    model = Student
    fields = [
      "uuid",
      "student_code",
      "user",
      "user_id",
      "parent",
      "parent_info"
      "grade",
      "class_name",
      "is_linked",
      "created_at",
      "updated_at"
   ]
    read_only_fields = ["uuid", "student_code", "created_at", "updated_at"]

  def get_parent(self, obj):
    """ Get parent information """
    parent = obj.get_parent()
    if parent:

      return {
        "uuid": str(parent.uuid),
        "family_code": parent.family_code,
        "email": parent.email,
        "name": parent.username
      }
    return None

  def get_parent_info(self, obj):
    """ Get parent information """
    parent = obj.get_parent()
    if parent:
      #Use ParentSerializer to avoid circular imports
      from keycloak_with_multiple_roles.users.api.serializers import ParentSerializer
      return ParentSerializer(parent).data
    return None

  def get_is_linked(self, obj):
    """ Check if student is linked to parent """
    return obj.is_linked_to_parent()

class StudentCreateSerializer(serializers.ModelSerializer):
  """ Serializer for creating a new student """

  #user Creation fields
  email = serializers.EmailField(required=True)
  username = serializer.CharField(required=True)
  name = serializer.CharField(required=True)
  password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

  #student fields
  parent_family_code = serializers.CharField(required=True)

  class Meta:
    model = Student
    fields = [
      "email",
      "username",
      "name",
      "password",
      "parent_family_code"
      "class_name"
    ]

  def validate_parent_family_cod(self, value):
    """ Validate that family code exist if provided """
    if value:
      if not Parent.objects.filter(family_code=value).exists():
        raise serializers.ValidationError("Invalid family code. Parent not found.")
      return value

  def create(self, validated_data):
    """ Create student with hashed password """

    #Extract user fields
    email = validated_data.pop('email')
    username = validated.pop('username')
    name = validated.pop('name')
    password = validated_data.pop('password')

    #Create user
    user = User.objects.create_user(
      username = username,
      email = email,
      name = name,
      password = password,
      user_type = "student"
    )

    #Create student profile

    student = Setudnet.objects.create(
      student_link = user,
      **validated_data
    )

    return student

class StudentUpdateSerializer(serializers.ModelSerializer):
  """ Serializer for updating student profile """

  class Meta:
    model = Student
    fields = [
      "parent_family_code",
      "grade",
      "class_name"
    ]

  def validate_parent_family_code(self, value):
    """ Validate that family code exist if provided """
    if value:
      if not Parent.objects.filter(family_code=value).exists():
        raise serializers.ValidationError("Invalid family code. Parent not found.")
      return value

class StudentLinkToParentSerializer(serializers.ModelSerializer):
  """ Serializer for linking a student ot a parent via a family code"""

  family_code = serializers.CharField(required=True, max_length=10)

  def validate_family_code(self, value):
    """ Validate that family code exists """
    if not Parent.objects.filter(family_code=value).exists():
      raise serializers.ValidationError("Invalid family code. Parent not found.")
    return value

class ParentMinimalSerializer(serializers.ModelSerializer):
  """ Minimal parent serializer for nested serialization"""

  parent_email = serializers.EmailField(source="parent_link.email", read_only=True)
  parent_name = serializers.CharField(source="parent_link.name", read_only=True)
  parent_username = serializers.CharField(source="parent_link.username", read_only=True)
  students_count = serializers.SerializerMethodField()

  class Meta:
    model = Parent
    fields = ["uuid", "family_code", "parent_email", "parent_name", "parent_username", "students_count","phone_number"]
    read_only_fields = fields

  def get_students_count(self, obj):
    """ Get number of students linked to parent """
    return obj.get_students_count()

class ParentSerializer(serializers.ModelSerializer):
  """ full parent serializer with all fields """

  # Nested user information
  user = UserMininmalSerializer(source='parent_link', read_only=True)

  #User ID for reference
  user_id = serializers.IntegerField(source='parent_link.id', read_only=True)

  # Students information
  students = StudentMinimalSerializer(source='get_all_students', many=True, read_only=True)
  student_count = serializers.SerializerMethodField()

  class Meta:
    model = Parent
    fields = [
      "uuid",
      "family_code",
      "user",
      "user_id",
      "phone_number",
      "address",
      "student_count",
      "created_at",
      "updated_at"
      "students",
    ]

  def get_student_count(self, obj):
    """ Get number of students linked to parent """
    return obj.get_students_count()

class ParentCreatSerializer(serializers.ModelSerializer):
  """ Serializer for creating a new parent """

  #user creation fields
  email = serializers.EmailField(required=True)
  username = serializer.CharField(required=True)
  name = serializer.CharField(required=True)
  password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

  class Meta:
    model = Parent
    feilds = [
      "email",
      "username",
      "name",
      "password",
      "phone_number",
      "address"
    ]

  def create(self, validated_data):
    """ Create parent with parent profile"""

    #Extract user fields
    email = validated_data.pop('email')
    username = validated.pop('username')
    name = validated.pop('name')
    password = validated_data.pop('password')

    #create user
    user = User.objects.create_user(
      username = username,
      email = email,
      name = name,
      password = password,
      user_type = "parent"
    )

    # Creating parent profile
    parent = Parent.objects.create(
      parent_link = user,
      **validated_data
    )

    return parent

class ParentUpdateSerializer(serializers.ModelSerializer):
  """ Serializer for updating parent information"""

  class Meta:
    model = Parent
    fields = [
      "phone_number",
      "address"
    ]

class ParentDetailSerializer(serializers.ModelSerializer):
  # Nested user information
  user = UserMininmalSerializer(source='parent_link', read_only=True)

  #Full student details
  students = StudentSerializer(source='get_all_students', many=True, read_only=True)
  student_count = serializers.SerializerMethodField()

  # Statistics
  unlinked_students_count = serializers.SerializerMethodField()

  class Meta:
    model = Parent
    fields = [
      "uuid",
      "family_code",
      "user",
      "phone_number",
      "address",
      "students",
      "unlinked_students_count",
      "student_count",
      "created_at",
      "updated_at"
    ]
    read_only_fields = fields

  def get_student_count(self, obj):
    """ Get number of students linked to parent """
    return obj.get_students_count()

  def get_unlinked_students_count(self, obj):
    """ Get number of students linked to parent """
    return obj.unlinked_students_count()
