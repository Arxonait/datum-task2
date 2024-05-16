import json

from django.contrib.gis.db.models.functions import Distance, Area
from django.contrib.gis.geos import GEOSGeometry, Polygon
from django.db.models import QuerySet
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from api_buldings.models import Building


class BuildingSerializer(serializers.ModelSerializer):
    area = serializers.SerializerMethodField()
    distance = serializers.SerializerMethodField()

    class Meta:
        model = Building
        fields = ("id", "address", "geom", "area", "distance")

    def __init__(self, *args, single=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.single = single

    def to_internal_value(self, data):
        if data.get("address") or data.get("geom"):
            internal_value = data
        elif data.get("type") == "Feature":
            internal_value = self.parse_feature(data)
        else:
            raise ValidationError({"detail": "wrong format"})
        internal_value = super().to_internal_value(internal_value)
        return internal_value

    def validate_geom(self, value):
        try:
            polygon = GEOSGeometry(value)
        except Exception as e:
            raise ValidationError([str(e)])

        if not isinstance(polygon, Polygon):
            raise ValidationError(["geom must be a Polygon"])

        if not polygon.valid:
            raise ValidationError([f"geom is not a valid polygon: {polygon.valid_reason}"])

        for coord in polygon.coords[0]:
            if not (-180.0 <= coord[0] <= 180.0 and -90.0 <= coord[1] <= 90.0):
                raise ValidationError([
                    "Coordinates out of range: longitude must be between -180 and 180, latitude must be between -90 and 90"])
        return polygon

    def get_area(self, obj):
        area = getattr(obj, 'area', None)
        if area is None:
            return None
        return area.sq_m

    def get_distance(self, obj):
        distance = getattr(obj, 'distance', None)
        if distance is None:
            return None
        return distance.m

    def parse_feature(self, data: dict):
        internal_value = {}
        if not (isinstance(data["type"], str) and isinstance(data["geometry"], dict)
                and isinstance(data["properties"], dict)):
            raise ValidationError({"detail": "wrong feature format"})

        internal_value["geom"] = json.dumps(data['geometry'])

        internal_value.update(data["properties"])
        return internal_value

    def change_queryset_serializers_context(self, queryset):
        context = self.context
        if "area" in context:
            queryset = queryset.annotate(area=Area('geom'))

        if "target_point" in context:
            ref_point = context.get("target_point")
            queryset = queryset.annotate(distance=Distance('geom', ref_point))
        return queryset

    def to_representation(self, queryset: QuerySet):
        if not isinstance(queryset, QuerySet) and self.single:
            return self.to_representation_single(queryset)

        instances = self.change_queryset_serializers_context(queryset)
        if not self.single:
            feature_collection = {
                "type": "FeatureCollection",
                "features": [self.to_representation_single(obj) for obj in instances]
            }
            return feature_collection
        else:
            instance = instances[0]
            return self.to_representation_single(instance)

    def to_representation_single(self, instance):
        serialize_data = super().to_representation(instance)

        proprieties = {}
        for atr in serialize_data:
            if atr not in ["id", "geom"] and serialize_data[atr] is not None:
                proprieties[atr] = serialize_data[atr]

        result = {
            "type": "Feature",
            "geometry": json.loads(instance.geom.json),
            "id": instance.pk,
            "properties": proprieties
        }
        return result
