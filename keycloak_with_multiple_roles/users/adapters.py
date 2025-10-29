"""
Adapters for django-allauth to customize authentication behavior.
"""
from typing import Any

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.http import HttpRequest


class AccountAdapter(DefaultAccountAdapter):
  """
  Custom account adapter for django-allauth.

  This adapter customizes the behavior of django-allauth for local accounts.
  """

  def is_open_for_signup(self, request: HttpRequest) -> bool:
    """
    Check if new user registration is allowed.

    Returns the value from Django settings.
    """
    return getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True)


class SocialAccountAdapter(DefaultSocialAccountAdapter):
  """
  Custom social account adapter for django-allauth.

  This adapter customizes the behavior of django-allauth for social accounts.
  """

  def is_open_for_signup(self, request: HttpRequest, sociallogin: Any) -> bool:
    """
    Check if new user registration via social accounts is allowed.

    Returns the value from Django settings.
    """
    return getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True)
