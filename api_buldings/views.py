import django_filters
from django.contrib.gis.db.models.functions import Distance, Area
from django.contrib.gis.geos import Point
from django.http import Http404
from rest_framework import viewsets
from rest_framework.response import Response

from api_buldings.filters import BuildingFilter
from api_buldings.models import Building
from api_buldings.serializers import BuildingSerializer


class BuildingViewSet(viewsets.ModelViewSet):
    queryset = Building.objects.all()
    serializer_class: BuildingSerializer = BuildingSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = BuildingFilter

    def get_queryset(self):
        queryset = self.queryset

        if "area" in self.request.query_params:
            queryset = queryset.annotate(area=Area('geom'))

        if "latitude" in self.request.query_params and "longitude" in self.request.query_params:
            longitude = self.request.GET.get('longitude')
            latitude = self.request.GET.get('latitude')
            ref_point = Point(float(longitude), float(latitude), srid=4326)
            queryset = queryset.annotate(distance=Distance('geom', ref_point))

        return queryset

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_queryset().get(pk=kwargs["pk"])
        except Exception:
            raise Http404("Building matching query does not exist")
        feature = self.serializer_class(instance, context=self.get_serializer_context()).data
        return Response(feature)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        feature_collection = self.serializer_class(queryset, context=self.get_serializer_context()).data
        return Response(feature_collection)
