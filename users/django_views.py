from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView, UpdateView
from django.views import View

from .forms import CustomUserCreationForm, UserProfileForm
from .models import User


class RegisterView(CreateView):
    """User registration view"""

    model = User
    form_class = CustomUserCreationForm
    template_name = "users/register.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.save()
        login(self.request, user)
        messages.success(
            self.request,
            "Welcome to CharityNepal! Your account has been created successfully.",
        )
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Join CharityNepal"
        return context


class LoginView(View):
    """User login view"""

    template_name = "users/login.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("home")
        return render(request, self.template_name, {"title": "Sign In"})

    def post(self, request):
        email = request.POST.get("email")
        password = request.POST.get("password")

        if email and password:
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name}!")
                next_url = request.GET.get("next", "home")
                return redirect(next_url)
            else:
                messages.error(request, "Invalid email or password.")
        else:
            messages.error(request, "Please provide both email and password.")

        return render(request, self.template_name, {"title": "Sign In", "email": email})


class LogoutView(View):
    """User logout view"""

    def get(self, request):
        logout(request)
        messages.success(request, "You have been logged out successfully.")
        return redirect("home")


class ProfileView(LoginRequiredMixin, TemplateView):
    """User profile view"""

    template_name = "users/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "My Profile"
        return context


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """Edit user profile"""

    model = User
    form_class = UserProfileForm
    template_name = "users/profile_edit.html"
    success_url = reverse_lazy("users:profile")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Your profile has been updated successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Profile"
        return context


class PasswordChangeView(LoginRequiredMixin, auth_views.PasswordChangeView):
    """Change password view"""

    template_name = "users/password_change.html"
    success_url = reverse_lazy("users:profile")

    def form_valid(self, form):
        messages.success(self.request, "Your password has been changed successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Change Password"
        return context


class PasswordResetView(auth_views.PasswordResetView):
    """Password reset request view"""

    template_name = "users/password_reset.html"
    email_template_name = "users/password_reset_email.html"
    success_url = reverse_lazy("users:password_reset_done")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Reset Password"
        return context


class PasswordResetDoneView(auth_views.PasswordResetDoneView):
    """Password reset done view"""

    template_name = "users/password_reset_done.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Password Reset Sent"
        return context


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    """Password reset confirm view"""

    template_name = "users/password_reset_confirm.html"
    success_url = reverse_lazy("users:password_reset_complete")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Set New Password"
        return context


class PasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    """Password reset complete view"""

    template_name = "users/password_reset_complete.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Password Reset Complete"
        return context
