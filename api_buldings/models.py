from django.contrib.gis.db import models
from osgeo import ogr
from pyproj import Transformer

crs_from = "epsg:4326"
crs_to = "epsg:32633"
transformer = Transformer.from_crs(crs_from, crs_to, always_xy=True)


# Create your models here.
class Building(models.Model):
    objects = models.Manager()

    address = models.CharField(max_length=255)
    geom = models.PolygonField()

    def __str__(self):
        return f"Buildings: pk={self.pk} address={self.address}"

    @property
    def area(self):
        """Площадь в квадратных метрах"""
        coords_degrees = self.geom.coords[0]
        coords_meters = [transformer.transform(lon, lat) for lon, lat in coords_degrees]
        ring = ogr.Geometry(ogr.wkbLinearRing)
        for x, y in coords_meters:
            ring.AddPoint(x, y)

        poly = ogr.Geometry(ogr.wkbPolygon)
        poly.AddGeometry(ring)

        area = poly.GetArea()
        return round(area, 4)

    @property
    def distance_to_target_point(self):
        distance = self.distance
        return float(distance.m)
