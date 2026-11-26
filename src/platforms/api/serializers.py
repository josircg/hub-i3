from django_countries.serializers import CountryFieldMixin
from rest_framework import serializers

from platforms.models import GeographicExtend, Platform


class GeographicExtendSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeographicExtend
        fields = '__all__'


class PlatformSerializer(CountryFieldMixin, serializers.ModelSerializer):
    class Meta:
        model = Platform
        fields = '__all__'
