from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import User, EmailVerificationToken, PasswordResetToken
import uuid


class RegisterView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('events:feed')
        return render(request, 'accounts/register.html')

    def post(self, request):
        email = request.POST.get('email', '').strip().lower()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')

        errors = {}
        if not email:
            errors['email'] = 'Email is required.'
        elif User.objects.filter(email=email).exists():
            errors['email'] = 'An account with this email already exists.'
        if not username:
            errors['username'] = 'Username is required.'
        elif len(username) < 3:
            errors['username'] = 'Username must be at least 3 characters.'
        elif User.objects.filter(username=username).exists():
            errors['username'] = 'This username is taken.'
        if len(password) < 8:
            errors['password'] = 'Password must be at least 8 characters.'
        if password != password2:
            errors['password2'] = 'Passwords do not match.'

        if errors:
            return render(request, 'accounts/register.html', {'errors': errors, 'email': email, 'username': username})

        user = User.objects.create_user(username=username, email=email, password=password)
        token = EmailVerificationToken.objects.create(user=user)
        # In production: send email. For dev, auto-verify.
        user.is_email_verified = True
        user.save()
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(request, f'Welcome to KIPAS, {username}! 🎉')
        return redirect('events:feed')


class LoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('maps:map')
        return render(request, 'accounts/login.html', {'next': request.GET.get('next', '')})

    def post(self, request):
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        next_url = request.POST.get('next', '')

        user = authenticate(request, username=email, password=password)
        if user:
            if user.is_deactivated:
                return render(request, 'accounts/login.html', {'error': 'Your account has been deactivated.'})
            login(request, user)
            return redirect(next_url or 'maps:map')
        return render(request, 'accounts/login.html', {'error': 'Invalid email or password.', 'email': email, 'next': next_url})


class LogoutView(LoginRequiredMixin, View):
    def post(self, request):
        logout(request)
        return redirect('/')


class VerifyEmailView(View):
    def get(self, request, token):
        try:
            vtoken = EmailVerificationToken.objects.get(token=token)
            vtoken.user.is_email_verified = True
            vtoken.user.save()
            vtoken.delete()
            messages.success(request, 'Email verified! You can now log in.')
        except EmailVerificationToken.DoesNotExist:
            messages.error(request, 'Invalid or expired verification link.')
        return redirect('accounts:login')


class PasswordResetView(View):
    def get(self, request):
        return render(request, 'accounts/password_reset.html')

    def post(self, request):
        email = request.POST.get('email', '').strip().lower()
        try:
            user = User.objects.get(email=email)
            PasswordResetToken.objects.filter(user=user).delete()
            token = PasswordResetToken.objects.create(user=user)
            # In production: send email with reset link
        except User.DoesNotExist:
            pass  # Don't reveal if email exists
        return render(request, 'accounts/password_reset.html', {'sent': True})


class PasswordResetConfirmView(View):
    def get(self, request, token):
        try:
            reset_token = PasswordResetToken.objects.get(token=token, is_used=False)
            return render(request, 'accounts/password_reset_confirm.html', {'token': token})
        except PasswordResetToken.DoesNotExist:
            messages.error(request, 'Invalid or expired reset link.')
            return redirect('accounts:password_reset')

    def post(self, request, token):
        try:
            reset_token = PasswordResetToken.objects.get(token=token, is_used=False)
            password = request.POST.get('password', '')
            password2 = request.POST.get('password2', '')
            if len(password) < 8:
                return render(request, 'accounts/password_reset_confirm.html', {'token': token, 'error': 'Password must be at least 8 characters.'})
            if password != password2:
                return render(request, 'accounts/password_reset_confirm.html', {'token': token, 'error': 'Passwords do not match.'})
            reset_token.user.set_password(password)
            reset_token.user.save()
            reset_token.is_used = True
            reset_token.save()
            messages.success(request, 'Password reset successful! Please log in.')
            return redirect('accounts:login')
        except PasswordResetToken.DoesNotExist:
            return redirect('accounts:password_reset')
