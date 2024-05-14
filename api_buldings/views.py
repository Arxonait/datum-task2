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

    def get_serializer_context(self):
        context = {}
        if "area" in self.request.query_params:
            context["area"] = True
        if "latitude" in self.request.query_params and "longitude" in self.request.query_params:
            longitude = self.request.GET.get('longitude')
            latitude = self.request.GET.get('latitude')
            ref_point = Point(float(longitude), float(latitude), srid=4326)
            context["target_point"] = ref_point
        return context

    def retrieve(self, request, *args, **kwargs):
        queryset = self.get_queryset().filter(pk=kwargs["pk"])
        if len(queryset) != 1:
            raise Http404("Building matching query does not exist")
        feature = self.serializer_class(queryset, context=self.get_serializer_context()).data
        return Response(feature)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        feature_collection = self.serializer_class(queryset, context=self.get_serializer_context(), single=False).data
        return Response(feature_collection)
