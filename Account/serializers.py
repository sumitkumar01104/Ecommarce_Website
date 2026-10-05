from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Profile


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=6
    )

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'password'
        ]

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Email already registered."
            )
        return value

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            password=validated_data['password']
        )


class ProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = Profile
        fields = [
            'id',
            'first_name',
            'last_name',
            'email',
            'profile_image',
        ]
        read_only_fields = [
            'id',
            'email',
        ]
class VerifiedTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        profile = getattr(self.user, 'profile', None)
        if profile and not profile.is_email_verified:
            raise PermissionDenied("Please verify your email before logging in.")
        return data