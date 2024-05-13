import json

from django.contrib.gis.geos import GEOSGeometry
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

        if polygon.geom_type != "Polygon":
            raise ValidationError(["geom must be Polygon"])

        if polygon.srid != 4326:
            raise ValidationError(["geom must be srid:4326"])

        for coord in polygon.coords[0]:
            if not (isinstance(coord[0], float) and isinstance(coord[1], float)):
                raise ValidationError(["longitude, latitude must be float"])
            if not (-180. < coord[0] < 180. and -90. < coord[1] < 90.):
                raise ValidationError(["wrong range longitude, latitude"])

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
            "geometry": instance.geom.geojson,
            "id": instance.pk,
            "properties": properties
        }
        return result
