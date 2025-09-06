from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration with password confirmation"""
    password2 = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def _validate_password_match(self, password, password2):
        """Validates that passwords match"""
        if password != password2:
            raise serializers.ValidationError("Passwörter stimmen nicht überein.")
    
    def validate(self, attrs):
        """Validates registration data"""
        password = attrs['password']
        password2 = attrs['password2']
        self._validate_password_match(password, password2)
        return attrs
    
    def _remove_password2_from_data(self, validated_data):
        """Removes password2 from validated data"""
        validated_data.pop('password2')
        return validated_data
    
    def create(self, validated_data):
        """Creates new user"""
        validated_data = self._remove_password2_from_data(validated_data)
        user = User.objects.create_user(**validated_data)
        return user


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user data"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']