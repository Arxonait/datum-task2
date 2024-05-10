from django.contrib.gis.db.models.functions import Distance
import django_filters
from django.contrib.gis.geos import Point

from api_buldings.models import Building


class BuildingFilter(django_filters.FilterSet):
    max_distance = django_filters.NumberFilter(method='filter_max_distance')

    class Meta:
        model = Building
        fields = ['max_distance']

    def filter_max_distance(self, queryset, name, value):
        longitude = self.request.GET.get('longitude')
        latitude = self.request.GET.get('latitude')

        if longitude and latitude and value:
            ref_point = Point(float(longitude), float(latitude), srid=4326)
            queryset = queryset.annotate(distance=Distance('geom', ref_point))
            queryset = queryset.filter(distance__lt=int(value))
            #queryset = queryset.annotate(distance=Distance('geom', ref_point))
        return queryset

    @classmethod
    def get_name_data_for_max_distance(cls):
        return {"max_distance", "longitude", "latitude"}
