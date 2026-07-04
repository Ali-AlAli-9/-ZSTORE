from .models import User
from rest_framework import generics
from .serializers import UserSerializer, StaffUserSerializer
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.views import APIView
from .throttles import LoginThrottle, RegisterThrottle, EmailThrottle
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from ecommerce.email_utils import send_email
from django.conf import settings
from django.template.loader import render_to_string
from .tokens import email_verification_token
from django.core.validators import validate_email as django_validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password as django_validate_password
import logging

logger = logging.getLogger(__name__)


class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    throttle_classes = [RegisterThrottle]

    def get_serializer_class(self):
        return UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            password = serializer.validated_data["password"]
            try:
                django_validate_password(password)
            except ValidationError as e:
                return Response({"password": e.messages}, status=status.HTTP_400_BAD_REQUEST)
            user = User.objects.create_user(
                username=serializer.validated_data["username"],
                email=serializer.validated_data.get("email", ""),
                password=serializer.validated_data["password"],
            )

            refresh = RefreshToken.for_user(user)

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = email_verification_token.make_token(user)
            verify_url = f"{settings.FRONTEND_URL}/verify/{uid}/{token}/"
            subject = "Verify your email - ZSTORE"
            message = render_to_string("email/verify_email.html", {"verify_url": verify_url, "user": user})
            if user.email:
                try:
                    send_email(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
                except Exception as e:
                    logger.error(f"Failed to send verification email to {user.email}: {e}")

            response = Response(
                {
                    "user": UserSerializer(user).data,
                    "access": str(refresh.access_token),
                },
                status=status.HTTP_201_CREATED,
            )
            response.set_cookie(
                key="refresh_token",
                value=str(refresh),
                httponly=True,
                samesite="Lax",
                max_age=7 * 24 * 3600,
                path="/users/",
            )
            return response
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token") or request.data.get("refresh")
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token_user_id = token.payload.get("user_id")
                if token_user_id != request.user.id:
                    return Response(
                        {"error": "This token does not belong to you"},
                        status=status.HTTP_403_FORBIDDEN,
                    )
                token.blacklist()
            except TokenError:
                pass

        response = Response({"message": "logged out"})
        response.delete_cookie("refresh_token", path="/users/")
        return response


class CustomTokenObtainPairView(TokenObtainPairView):
    throttle_classes = [LoginThrottle]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200 and "refresh" in response.data:
            refresh_token = response.data.pop("refresh")
            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                httponly=True,
                samesite="Lax",
                max_age=7 * 24 * 3600,
                path="/users/",
            )
        return response


class CookieTokenRefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")
        if not refresh_token:
            return Response({"error": "Refresh token not found"}, status=401)

        serializer = TokenRefreshSerializer(data={"refresh": refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response({"error": "Invalid or expired refresh token"}, status=401)

        data = serializer.validated_data
        response = Response({"access": data["access"]}, status=200)

        if "refresh" in data:
            response.set_cookie(
                key="refresh_token",
                value=data["refresh"],
                httponly=True,
                samesite="Lax",
                max_age=7 * 24 * 3600,
                path="/users/",
            )

        return response


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"error": "Invalid link"}, status=400)

        if email_verification_token.check_token(user, token):
            if user.is_email_verified:
                return Response({"message": "Already verified"})
            user.is_email_verified = True
            user.save()
            return Response({"message": "Email verified successfully"})
        return Response({"error": "Invalid or expired link"}, status=400)


class ResendVerificationView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [EmailThrottle]

    def post(self, request):
        user = request.user
        if user.is_email_verified:
            return Response({"message": "Already verified"}, status=400)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = email_verification_token.make_token(user)
        verify_url = f"{settings.FRONTEND_URL}/verify/{uid}/{token}/"
        subject = "Verify your email - ZSTORE"
        message = render_to_string("email/verify_email.html", {"verify_url": verify_url, "user": user})
        try:
            send_email(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
        except Exception as e:
            logger.error(f"Failed to resend verification email to {user.email}: {e}")
        return Response({"message": "Verification email sent"})


class UpdateEmailView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [EmailThrottle]

    def post(self, request):
        email = request.data.get("email", "").strip()
        if not email:
            return Response({"error": "Email is required"}, status=400)
        try:
            django_validate_email(email)
        except ValidationError:
            return Response({"error": "Invalid email format"}, status=400)
        if User.objects.filter(email=email).exclude(id=request.user.id).exists():
            return Response({"error": "Email already in use"}, status=400)

        request.user.email = email
        request.user.is_email_verified = False
        request.user.save()

        uid = urlsafe_base64_encode(force_bytes(request.user.pk))
        token = email_verification_token.make_token(request.user)
        verify_url = f"{settings.FRONTEND_URL}/verify/{uid}/{token}/"
        subject = "Verify your email - ZSTORE"
        message = render_to_string("email/verify_email.html", {"verify_url": verify_url, "user": request.user})
        try:
            send_email(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
        except Exception as e:
            logger.error(f"Failed to send verification email to {email}: {e}")

        return Response({"message": "Verification email sent to " + email})


class UserMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.is_staff:
            serializer = StaffUserSerializer(request.user)
        else:
            serializer = UserSerializer(request.user)
        return Response(serializer.data)
