from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .auth_utils import validate_password_match, remove_password2_from_data


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration with password confirmation"""
    password2 = serializers.CharField(write_only=True, required=False)
    confirmed_password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'confirmed_password']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def validate(self, attrs):
        """Validates registration data"""
        password = attrs['password']
        password2 = attrs.get('password2') or attrs.get('confirmed_password')
        
        if not password2:
            raise serializers.ValidationError("Password confirmation is required.")
        
        validate_password_match(password, password2)
        return attrs
    
    def create(self, validated_data):
        """Creates new user"""
        validated_data.pop('password2', None)
        validated_data.pop('confirmed_password', None)
        user = User.objects.create_user(**validated_data)
        return user


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user data"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']