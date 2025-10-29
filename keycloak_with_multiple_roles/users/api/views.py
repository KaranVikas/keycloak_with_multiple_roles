from re import search

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth import login, authenticate, logout


from keycloak_with_multiple_roles.users.models import User, Parent, Student
from .serializers import (
  UserSerializer,
  UserCreateSerializer, ParentSerializer, StudentLinkToParentSerializer, StudentSerializer
)

# Pagination
class StandardResultSetPagination(PageNumberPagination):
  page_size = 10
  page_size_query_param = 'page-size'
  max_page_size = 100

class LoginView(APIView):
  """
    Minimal login view for local authentication
    Replace with keycloak authentication

    POST /api/auth/login
    Body: {username: "user@example.com", password: ""}

  """
  permission_classes = [AllowAny]

  def post(self, request):
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
      return Response({
        "error":"Username and password are required"
    }, status= status.HTTP_400_BAD_REQUEST)

    # Authenticate user
    user = User.objects.filter(username= username, password=password)

    if user is None:
      return Response({
        "error":"Invalid username or password"
      }, status= status.HTTP_401_UNAUTHORIZED)

    #Login user (creates session)
    login(request, user)

    # get or create token for API access
    token, created = Token.objects.get_or_create(user=user)

    # Get user profiles based on user_type
    profile_data = None
    if user.user_type == 'parent':
      try:
        parent = Parent.objects.get(parent_link=user)
        profile_data = {
          "family_code": parent.family_code,
          "student_count": parent.get_student_count(),
        }
      except Parent.DoesNotExist:
        pass
    elif user.user_type == 'student':
      try:
        student = Student.objects.get(student_link=user)
        profile_data = {
          "student_code": student.student_code,
          "is_linked": student.is_linked_to_parent(),
        }
      except Student.DoesNotExist:
        pass

    return Response({
      'message': 'Login successful',
      'token': token.key,
      'user': {
        'id': user.id,
        'email': user.email,
        'username': user.username,
        'user_type': user.user_type,
      },
      "profile": profile_data
    },status= status.HTTP_200_OK)

class LogoutView(APIView):
  """
  Logout view - invalidates token and session

  POST /api/auth/logout
  """

  permission_classes = [IsAuthenticated]

  def post(self, request):
    # Delete token
    try:
      request.user.auth_token.delete()
    except:
      pass

    logout(request)

    return Response(
      {"message": "Logout successful"},
      status=status.HTTP_200_OK
    )

class MeView(APIView):
  """
  Get current authenticated user's information

  GET /api/auth/me
  """

  permission_classes = [IsAuthenticated]

  def get(self, request):
    user = request.user
    user_data = UserSerializer(user).data

    # Add profile information based on user_type

    if user.user_type == 'parent':
      try:
        parent = Parent.objects.get(parent_link=user)
        user_data['profile'] = ParentSerializer(parent).data
      except Parent.DoesNotExist:
        user_data['profile'] = None
    elif user.user_type == 'student':
      try:
        student = Student.objects.get(student_link=user)
        user_data['profile'] = StudentSerializer(student).data
      except Student.DoesNotExist:
        user_data['profile'] = None

    return Response(user_data, status=status.HTTP_200_OK)

class UserViewSet(viewsets.ModelViewSet):
  """
  User viewset with full CRUD operations
  """
  queryset = User.objects.all()
  serializer_class = UserSerializer
  permission_classes = [IsAuthenticated]
  pagination_class = StandardResultSetPagination

