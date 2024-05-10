import geojson
from django.contrib.gis.geos import Polygon
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request

from api_buldings.filters import BuildingFilter
from api_buldings.models import Building
from api_buldings.validators import ValidatorFeatureFormat, ValidatorPolygon, ValidatorWKTPolygonFormat, \
    ValidatorPropertiesBuildings


class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = ("id", "address", "geom", "area", "distance_to_target_point")
        id_field = "id"
        geo_field = "geom"

    def to_internal_value(self, data):
        if data.get("address") or data.get("geom"):
            internal_value = super().to_internal_value(data)
        elif data.get("type") == "Feature":
            internal_value = self.validate_feature(data)
        else:
            raise ValidationError({"detail": "wrong format"})
        return internal_value

    def validate_geom(self, value):
        try:
            wkt_coordinates = ValidatorWKTPolygonFormat(geom=value)
            ValidatorPolygon(coordinates=wkt_coordinates.geom)
        except Exception as e:
            raise ValidationError(e.errors())
        return value

    def validate_feature(self, data: dict):
        internal_value = {}
        try:
            validate_data = ValidatorFeatureFormat(**data)
        except Exception as e:
            raise ValidationError({"detail": e.errors()})

        if validate_data.geometry.type.lower() != "polygon":
            raise ValidationError({"detail": ["geometry type must be polygon"]})

        try:
            polygon = ValidatorPolygon(**validate_data.geometry.model_dump())
        except Exception as e:
            raise ValidationError({"detail": e.errors()})

        internal_value["geom"] = Polygon(polygon.coordinates)

        valid_properties = ValidatorPropertiesBuildings(**validate_data.properties)
        if not valid_properties.address and self.context.get("request").method == "PUT":
            raise ValidationError({"detail": ["address is required"]})

        internal_value["address"] = data["properties"].get("address")
        return internal_value

    def get_fields(self):
        fields = super(BuildingSerializer, self).get_fields()
        request: Request = self.context.get("request")
        if request is None:
            fields.pop("area")
            fields.pop("distance_to_target_point")
            return fields

        if "area" not in request.query_params:
            fields.pop("area")
        if (not BuildingFilter.get_name_data_for_max_distance().issubset(set(request.query_params.keys())) or
                request.method != "GET"):
            fields.pop("distance_to_target_point")
        return fields

    def to_representation(self, instance):
        target_fields = self.get_fields()

        properties = {}
        for target_field in target_fields:
            if target_field not in (self.Meta.id_field, self.Meta.geo_field):
                try:
                    value = instance.__getattribute__(target_field)
                    properties[target_field] = value
                except AttributeError as e:
                    print(f"LOG --- serializers buildings --- {e.args[0]}")

        cords = geojson.Polygon(instance.geom.coords[0])

        result = geojson.Feature(id=instance.pk, geometry=cords, properties=properties)
        return result
