# venues/models.py
from django.contrib.gis.db import models

class Venue(models.Model):
    name = models.CharField(max_length=255, unique=True)
    location = models.PointField(srid=4326)

    class Meta:
        verbose_name = "Площадка"
        verbose_name_plural = "Площадки"
        ordering = ["name"]

    def __str__(self):
        return self.name