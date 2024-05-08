import geojson
from rest_framework import serializers
from rest_framework.request import Request

from api_buldings.filters import BuildingFilter
from api_buldings.models import Building


class BuildingSerializer(serializers.ModelSerializer):

    class Meta:
        model = Building
        fields = ("id", "address", "geom", "area", "distance_to_target_point")
        id_field = "id"
        geo_field = "geom"

    def get_fields(self):
        fields = super(BuildingSerializer, self).get_fields()
        request: Request = self.context.get("request")
        if request is None:
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
