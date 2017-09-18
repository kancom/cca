from django.db import models

class Country(models.Model):
    name = models.CharField(max_length=50, unique=True)

class Brand(models.Model):
    country = models.ForeignKey(Country, null=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=50, unique=True)

class Model(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)

class Generation(models.Model):
    model = models.ForeignKey(Model, on_delete=models.CASCADE)
    generation = models.IntegerField()
    name = models.CharField(max_length=50)
    year_s = models.IntegerField()
    year_e = models.IntegerField(null=True)

class Bodies(models.Model):
    CAR_BODIES = (
        ('Suv', 'SUV'),
        ('P', 'Pickup'),
        ('S', 'Sedan'),
        ('V', 'Van'),
        ('Cp', 'Coupe'),
        ('W', 'Wagon'),
        ('Cv', 'Convertible'),
        ('Sc', 'Sports Car'),
        ('C', 'Crossover'),
        ('H', 'Hatchback'),
        ('O', 'Other')
    )
    type = models.CharField(max_length=3, default='O', choices=CAR_BODIES)
    model = models.ForeignKey(Model, on_delete=models.CASCADE)

#class Car2Body(models.Model):
#    car = models.ForeignKey(Car, on_delete=models.CASCADE)
#    body = models.ForeignKey(Body, on_delete=models.CASCADE)

class Engines(models.Model):
    name = models.CharField(max_length=50)
    power = models.IntegerField()
    torque = models.IntegerField()
    model = models.ForeignKey(Model, on_delete=models.CASCADE)

class Car(models.Model):
    model = models.ForeignKey(Model, on_delete=models.CASCADE)
    body = models.ManyToManyField(Bodies)
    engine = models.ManyToManyField(Engines)
    last_update = models.DateTimeField(auto_now=True)
