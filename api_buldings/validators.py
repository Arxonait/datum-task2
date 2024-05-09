import re
from typing import Annotated

import pydantic
from pydantic import AfterValidator

PATTERN_POLYGON = r"POLYGON \(\(([0-9,. ]+)\)\)"


class ValidatorFeatureGeometry(pydantic.BaseModel):
    type: str
    coordinates: list[list[float]]


class ValidatorFeatureFormat(pydantic.BaseModel):
    type: str
    geometry: ValidatorFeatureGeometry
    properties: dict | None


def check_close_polygon(v: list[list[float]]):
    assert v[0] == v[-1], "polygon not closed"
    return v


def check_only_x_y(v: list[list[float]]):
    for coord in v:
        assert len(coord) == 2, "not complete coord"
    return v


class ValidatorPolygon(pydantic.BaseModel):
    coordinates: Annotated[list[list[float]], AfterValidator(check_close_polygon), AfterValidator(check_only_x_y)]


class ValidatorWKTPolygonFormat(pydantic.BaseModel):
    geom: str | list = pydantic.Field(pattern=PATTERN_POLYGON)

    @pydantic.field_validator("geom", mode="after")
    @classmethod
    def geom_convert_str_to_list(cls, v: str):
        coords_str = re.search(PATTERN_POLYGON, v).group(1).split(",")
        coords = []
        for coord in coords_str:
            coord = coord.lstrip()
            coord = coord.rstrip()
            coord = coord.split(" ")
            try:
                coord = list(map(float, coord))
            except:
                assert False, "coordinates must be float"
            coords.append(coord)
        return coords


class ValidatorPropertiesBuildings(pydantic.BaseModel):
    address: str = pydantic.Field(max_length=255, default=None)
