from django.db import models


class Region(models.Model):
    name = models.CharField(max_length=15, null=True, blank=True)


class TimePeriod(models.Model):
    period = models.CharField(max_length=12, null=True, blank=True)


class ForOrders(models.Model):
    id = models.IntegerField(primary_key=True, unique=True)


class Courier(models.Model):
    id = models.IntegerField(primary_key=True, unique=True)
    type = models.CharField(max_length=10)
    regions = models.ManyToManyField(Region)
    working_hours = models.ManyToManyField(TimePeriod)
    orders = models.ManyToManyField(ForOrders)


class Order(models.Model):
    id = models.IntegerField(primary_key=True, unique=True)
    weight = models.FloatField()
    region = models.IntegerField()
    delivery_time = models.ManyToManyField(TimePeriod)
    assigned = models.IntegerField(default=-1)
