from django.contrib.gis.db import models


# Create your models here.
class Building(models.Model):
    objects = models.Manager()

    address = models.CharField(max_length=255)
    geom = models.PolygonField(srid=4326, geography=True)

    def __str__(self):
        return f"Buildings: pk={self.pk} address={self.address}"
