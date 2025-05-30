from rest_framework import serializers
from .models import AppSettings, ActivityLog, SystemHealth


class AppSettingsSerializer(serializers.ModelSerializer):
    typed_value = serializers.SerializerMethodField()

    class Meta:
        model = AppSettings
        fields = '__all__'

    def get_typed_value(self, obj):
        return obj.get_typed_value()

    def validate_value(self, value):
        data_type = self.initial_data.get('data_type')

        if data_type == 'INTEGER':
            try:
                int(value)
            except ValueError:
                raise serializers.ValidationError("Butun son kiriting")
        elif data_type == 'FLOAT':
            try:
                float(value)
            except ValueError:
                raise serializers.ValidationError("Haqiqiy son kiriting")
        elif data_type == 'JSON':
            try:
                import json
                json.loads(value)
            except json.JSONDecodeError:
                raise serializers.ValidationError("To'g'ri JSON format kiriting")

        return value


class ActivityLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        model = ActivityLog
        fields = '__all__'


class SystemHealthSerializer(serializers.ModelSerializer):
    component_display = serializers.CharField(source='get_component_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = SystemHealth
        fields = '__all__'
