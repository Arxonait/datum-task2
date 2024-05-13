from django.contrib.gis.db.models.functions import Distance, Area
import django_filters
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import Area as AreaMeasure

from api_buldings.models import Building


class BuildingFilter(django_filters.FilterSet):
    max_distance = django_filters.NumberFilter(method='filter_max_distance')
    min_area = django_filters.NumberFilter(method='filter_min_area')
    max_area = django_filters.NumberFilter(method='filter_max_area')

    class Meta:
        model = Building
        fields = ['max_distance', 'min_area', 'max_area']

    def filter_max_distance(self, queryset, name, value):
        longitude = self.request.GET.get('longitude')
        latitude = self.request.GET.get('latitude')

        if longitude and latitude and value:
            ref_point = Point(float(longitude), float(latitude), srid=4326)
            queryset = self.queryset.annotate(distance=Distance('geom', ref_point))
            queryset = queryset.filter(distance__lt=int(value))
        return queryset

    def filter_min_area(self, queryset, name, value):
        if value:
            queryset = queryset.annotate(area=Area('geom'))
            value_as_area = AreaMeasure(sq_m=int(value))
            queryset = queryset.filter(area__gte=value_as_area)
        return queryset

    def filter_max_area(self, queryset, name, value):
        if value:
            queryset = queryset.annotate(area=Area('geom'))
            value_as_area = AreaMeasure(sq_m=int(value))
            queryset = queryset.filter(area__lte=value_as_area)
        return queryset
