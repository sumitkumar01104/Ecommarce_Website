from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme, urlencode
from django.views.decorators.http import require_POST
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Profile
from .serializers import ProfileSerializer, VerifiedTokenObtainPairSerializer
from Cart.utils import merge_session_cart_into_user_cart


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


def normalize_email(value):
    return (value or '').strip().lower()


def _login_redirect(request):
    """Back to the login page, keeping ?next= if there was one."""
    next_url = request.POST.get('next', '')
    if next_url:
        return redirect(f"{reverse('login')}?{urlencode({'next': next_url})}")
    return redirect('login')


# ─────────────────────────────────────────────────────────────
# REST API Views
# ─────────────────────────────────────────────────────────────

class VerifiedTokenObtainPairView(TokenObtainPairView):
    serializer_class = VerifiedTokenObtainPairSerializer


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return get_object_or_404(Profile, user=self.request.user)


class RegisterView(APIView):
    permission_classes = []

    def post(self, request):
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        email = normalize_email(request.data.get('email'))
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {"error": "Email and Password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(email__iexact=email).exists():
            return Response(
                {"error": "Email already exists"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            validate_password(password)
        except ValidationError as e:
            return Response(
                {"error": list(e.messages)},
                status=status.HTTP_400_BAD_REQUEST
            )

        User.objects.create_user(
            username=email,
            first_name=first_name or '',
            last_name=last_name or '',
            email=email,
            password=password
        )

        return Response(
            {
                "message": (
                    "Registration successful. "
                    "Please check your email and verify your account."
                )
            },
            status=status.HTTP_201_CREATED
        )


class LoginView(APIView):
    permission_classes = []

    def post(self, request):
        email = normalize_email(request.data.get('email'))
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {"error": "Email and Password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(
            username=email,
            password=password
        )

        if not user:
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        profile = getattr(user, 'profile', None)

        if not profile or not profile.is_email_verified:
            return Response(
                {
                    "error": (
                        "Please verify your email before logging in."
                    )
                },
                status=status.HTTP_403_FORBIDDEN
            )

        tokens = get_tokens_for_user(user)

        return Response(
            {
                "message": "Login successful",
                "tokens": tokens
            },
            status=status.HTTP_200_OK
        )

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response(
                {"error": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token = RefreshToken(refresh_token)

            if str(token["user_id"]) != str(request.user.id):
                return Response(
                    {"error": "This refresh token does not belong to you."},
                    status=status.HTTP_403_FORBIDDEN
                )

            token.blacklist()

            return Response(
                {"message": "Logout successful."},
                status=status.HTTP_200_OK
            )

        except TokenError:
            return Response(
                {"error": "Invalid or expired refresh token."},
                status=status.HTTP_400_BAD_REQUEST
            )

# ─────────────────────────────────────────────────────────────
# Template-Based Views
# ─────────────────────────────────────────────────────────────

def register_page(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = normalize_email(request.POST.get('email'))
        password = request.POST.get('password')

        if not email or not password:
            messages.error(request, 'Email and password are required.')
            return redirect('register')

        if User.objects.filter(email__iexact=email).exists():
            messages.error(
                request,
                'Email already registered.'
            )
            return redirect('register')

        try:
            validate_password(password)
        except ValidationError as e:
            for msg in e.messages:
                messages.error(request, msg)
            return redirect('register')

        User.objects.create_user(
            username=email,
            first_name=first_name or '',
            last_name=last_name or '',
            email=email,
            password=password
        )

        messages.success(
            request,
            'Account created! Please check your email and verify your account.'
        )

        return redirect('login')

    return render(
        request,
        'accounts/register.html'
    )


def login_page(request):
    if request.method == 'POST':
        email = normalize_email(request.POST.get('email'))
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=email,
            password=password
        )

        if user:
            profile = getattr(user, 'profile', None)

            if not profile or not profile.is_email_verified:
                messages.error(
                    request,
                    'Please verify your email before logging in. '
                    'Check your inbox for the activation link.'
                )
                return _login_redirect(request)

            # login() changes the session key, so remember the guest one first
            old_session_key = request.session.session_key

            login(request, user)

            merge_session_cart_into_user_cart(
                request,
                user,
                old_session_key
            )

            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)

            return redirect('index')

        messages.error(
            request,
            'Invalid email or password.'
        )
        return _login_redirect(request)

    return render(
        request,
        'accounts/login.html'
    )


@require_POST
def logout_page(request):
    logout(request)
    return redirect('login')