from rest_framework import serializers
from ..models import Quiz


class QuizSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source='created_by.username')
    
    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description', 'created_at', 'updated_at', 'video_url', 'created_by']
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'id']


class QuizDetailSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source='created_by.username')
    
    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description', 'created_at', 'updated_at', 'video_url', 'questions', 'created_by']
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'id']


class CreateQuizSerializer(serializers.ModelSerializer):
    url = serializers.URLField(write_only=True)
    
    class Meta:
        model = Quiz
        fields = ['url']
    
    def create(self, validated_data):
        url = validated_data.pop('url')
        
        title = f"Quiz für Video: {url}"
        description = f"Ein automatisch generiertes Quiz basierend auf dem Video: {url}"
        
        validated_data.update({
            'title': title,
            'description': description,
            'video_url': url,
            'created_by': self.context['request'].user
        })
        
        return super().create(validated_data)
    
    def to_representation(self, instance):
        return QuizDetailSerializer(instance, context=self.context).data
