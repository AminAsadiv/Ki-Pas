from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

User = get_user_model()


class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        email = data.get('email', '').lower().strip()
        username = data.get('username', '').strip()
        password = data.get('password', '')

        errors = {}
        if not email:
            errors['email'] = 'Email is required'
        elif User.objects.filter(email=email).exists():
            errors['email'] = 'Email already in use'
        if not username:
            errors['username'] = 'Username is required'
        elif User.objects.filter(username=username).exists():
            errors['username'] = 'Username already taken'
        try:
            validate_password(password)
        except ValidationError as e:
            errors['password'] = list(e.messages)

        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(
            email=email, username=username, password=password
        )
        return Response({'id': str(user.id), 'email': user.email, 'username': user.username}, status=status.HTTP_201_CREATED)


class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        profile = getattr(user, 'profile', None)
        return Response({
            'id': str(user.id),
            'email': user.email,
            'username': user.username,
            'is_staff': user.is_staff,
            'profile': {
                'full_name': profile.full_name if profile else '',
                'avatar': request.build_absolute_uri(profile.avatar.url) if profile and profile.avatar else None,
                'level': profile.level if profile else 1,
                'xp': profile.xp if profile else 0,
            } if profile else None,
        })


class ChangePasswordAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        old = request.data.get('old_password', '')
        new = request.data.get('new_password', '')
        if not user.check_password(old):
            return Response({'old_password': 'Incorrect password'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            validate_password(new, user)
        except ValidationError as e:
            return Response({'new_password': list(e.messages)}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new)
        user.save()
        return Response({'detail': 'Password changed successfully'})
