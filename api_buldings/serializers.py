import json

from django.contrib.gis.geos import GEOSGeometry, Polygon
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request

from api_buldings.models import Building


class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = ("id", "address", "geom")
        id_field = "id"
        geo_field = "geom"

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
                raise ValidationError(["Coordinates out of range: longitude must be between -180 and 180, latitude must be between -90 and 90"])
        return polygon

    def parse_feature(self, data: dict):
        internal_value = {}
        if not (isinstance(data["type"], str) and isinstance(data["geometry"], dict)
                and isinstance(data["properties"], dict)):
            raise ValidationError({"detail": "wrong feature format"})

        internal_value["geom"] = json.dumps(data['geometry'])

        internal_value.update(data["properties"])
        return internal_value

    def get_fields(self):
        fields = super(BuildingSerializer, self).get_fields()
        request: Request = self.context.get("request")
        return fields

    def to_representation(self, instance):
        if isinstance(instance, list):
            feature_collection = {
                "type": "FeatureCollection",
                "features": [self.to_representation_single(obj) for obj in instance]
            }
            return feature_collection
        else:
            return self.to_representation_single(instance)

    def to_representation_single(self, instance):
        target_fields = self.get_fields()

        properties = {}
        for target_field in target_fields:
            if target_field not in (self.Meta.id_field, self.Meta.geo_field):
                try:
                    value = instance.__getattribute__(target_field)
                    properties[target_field] = value
                except:
                    continue

        result = {
            "type": "Feature",
            "geometry": json.loads(instance.geom.json),
            "id": instance.pk,
            "properties": properties
        }
        return result
