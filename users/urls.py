from django.urls import path
from .views import UserListView, RegisterView, LogoutView, CustomTokenObtainPairView, CookieTokenRefreshView, VerifyEmailView, ResendVerificationView, UpdateEmailView, UserMeView

urlpatterns = [
    path("", UserListView.as_view()),
    path("register/", RegisterView.as_view()),
    path("login/", CustomTokenObtainPairView.as_view()),
    path("logout/", LogoutView.as_view()),
    path("token/refresh/", CookieTokenRefreshView.as_view()),
    path("verify/<uidb64>/<token>/", VerifyEmailView.as_view()),
    path("resend-verification/", ResendVerificationView.as_view()),
    path("update-email/", UpdateEmailView.as_view()),
    path("me/", UserMeView.as_view()),
]
