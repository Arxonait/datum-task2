import json
import re

import geojson
from django.contrib.gis.geos import Polygon
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request

from api_buldings.filters import BuildingFilter
from api_buldings.models import Building


class ValidatePolygon:
    def __init__(self, coordinates: list):
        self.coordinates = coordinates

    def is_valid(self):
        for coord in self.coordinates:
            if len(coord) != 2:
                raise ValidationError(["not complete coords"])

        if self.coordinates[0] != self.coordinates[-1]:
            raise ValidationError(["polygon not closed"])


def validate_parse_wkt_polygon_format(value):
    if not isinstance(value, str):
        raise ValidationError(["geom must be str"])

    pattern = r"POLYGON \(\(([0-9,. ]+)\)\)"
    if not re.match(pattern, value):
        raise ValidationError([f"geom must be format: POLYGON ((... ..., ... ...))"])

    coords_str = re.search(pattern, value).group(1).split(",")
    coords = []
    for coord in coords_str:
        coord = coord.lstrip()
        coord = coord.rstrip()
        coord = coord.split(" ")
        try:
            coord = list(map(float, coord))
        except:
            raise ValidationError(["coordinates must be float"])
        coords.append(coord)

    return value, coords


def validate_feature_format(feature: dict):
    if not (feature.get("type") and feature.get("geometry") and isinstance(feature.get("properties"), dict)):
        raise ValidationError(["feature format required keys type, geometry, properties"])
    if not (isinstance(feature.get("geometry"), dict) and isinstance(feature.get("properties"), dict)):
        raise ValidationError(["geometry, properties must be dict"])
    if not (feature["geometry"].get("type") and feature["geometry"].get("coordinates")):
        raise ValidationError(["geometry required keys type, coordinates"])
    if not isinstance(feature["geometry"].get("coordinates"), list):
        raise ValidationError(["coordinates must be list"])
    if not isinstance(feature["geometry"].get("type"), str):
        raise ValidationError(["geometry type must be str"])
    return feature


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
        _, coordinates = validate_parse_wkt_polygon_format(value)
        validate_polygon = ValidatePolygon(coordinates)
        validate_polygon.is_valid()
        return value

    def validate_feature(self, data: dict):
        #todo
        internal_value = {}
        try:
            validate_feature_format(data)
        except ValidationError as e:
            raise ValidationError({"detail": e.detail})

        if data["geometry"]["type"].lower() != "polygon":
            raise ValidationError({"detail": ["geometry type must be polygon"]})

        validate_polygon = ValidatePolygon(data["geometry"]["coordinates"])
        try:
            validate_polygon.is_valid()
        except ValidationError as e:
            raise ValidationError({"detail": e.detail})

        internal_value["geom"] = Polygon(validate_polygon.coordinates)

        if not data["properties"].get("address") and self.context.get("request").method == "PUT":
            raise ValidationError({"detail": ["address is required"]})

        if isinstance(data["properties"].get("address"), str):
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
                request.method == "POST"):
            fields.pop("distance_to_target_point")
        return fields

    def to_representation(self, instance):
        target_fields = self.get_fields()

        properties = {}
        for target_field in target_fields:
            if target_field not in (self.Meta.id_field, self.Meta.geo_field):
                value = instance.__getattribute__(target_field)
                properties[target_field] = value

        cords = geojson.Polygon(instance.geom.coords[0])

        result = geojson.Feature(id=instance.pk, geometry=cords, properties=properties)
        return result
