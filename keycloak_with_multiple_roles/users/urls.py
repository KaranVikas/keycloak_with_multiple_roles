from django.urls import path
from keycloak_with_multiple_roles.users.api.views import (
  UserViewSet,
  LoginView,
  LogoutView,
  MeView,
)
app_name = "users"

# authentication endpoints
auth_patterns = [
  path("auth/login", LoginView.as_view(), name="login"),
  path("auth/logout", LogoutView.as_view(), name="logout"),
  path("auth/me", MeView.as_view(), name="me"),
]


urlpatterns = [
  *auth_patterns
  # user_patterns
]
