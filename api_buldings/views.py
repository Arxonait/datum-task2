import django_filters
import geojson
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.http import Http404
from rest_framework import viewsets
from rest_framework.request import Request
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
        context = {
            'request': self.request
        }
        return context

    def retrieve(self, request, *args, **kwargs):
        #instance = self.get_object()
        try:
            instance = self.queryset.get(pk=kwargs["pk"])
        except Exception:
            raise Http404("Building matching query does not exist")
        feature = self.serializer_class(instance, context=self.get_serializer_context()).data
        return Response(feature)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        data = self.filter_after_queryset(request, queryset)

        features = [self.serializer_class(instance, context=self.get_serializer_context()).data
                    for instance in data]
        feature_collection = geojson.FeatureCollection(features)

        return Response(feature_collection)

    def filter_after_queryset(self, request: Request, queryset):
        min_area = int(request.query_params.get("min_area", -1))
        max_area = int(request.query_params.get("max_area", -1))

        result = []
        for instance in queryset:
            result.append(instance)
            area = instance.area
            if min_area != -1 and min_area >= area or max_area != -1 and max_area <= area:
                result.pop()
        return result
