# -*- coding: utf-8 -*-

from django.db import models
from django.db import IntegrityError
import logging
import logging.handlers
import django


__author__ = "Andrey Kashrin <kashirinas@rambler.ru>"
__license__ = "Apache 2.0"

FORMAT = "%(asctime)s %(levelname)s - %(name)s: %(message)s"
logging.basicConfig(format=FORMAT, filename='/tmp/grabber.log',
                    level=logging.DEBUG)
log = logging.getLogger(__name__)


class mBase(models.Model):
    class Meta:
        abstract = True

    def get_unique_fields(self):
        list1 = []
        list2 = []
        try:
            for f in self.get_model_fields():
                if f._unique:
                    list1.append(f)
            for t in self._meta.unique_together:
                for f in t:
                    list2.append(self._meta.get_field(f))
        except:
            log.exception("self: {}\nmodel_fields: {}\nunique_together: {}".
                          format(self,
                                 self.get_model_fields(),
                                 self._meta.unique_together))
        return list1 + list2

    def get_model_fields(self, withid=False):
        result = []
        for f in self._meta.get_fields():
            if not f.auto_created:
                result.append(f)
        if withid:
            result.append(self._meta.get_field('id'))
        return result

    def check_related_saved(self,  fields):
        result = True
        for f in fields:
            if f.is_relation:
                rel_obj = getattr(self, f.name)
                result = result and rel_obj and rel_obj.pk
                if not rel_obj.pk:
                    raise IntegrityError("Related object is not saved")
        return result

    def find_same(self, uniq_flds):
        query = self._meta.model.objects.all()
        for f in uniq_flds:
            val = getattr(self, f.name)
            query_cond = {f.name: val}
            query = query.filter(**query_cond)
        return query

    def save(self, *args, **kwargs):
        ufl = self.get_unique_fields()
        result = False
        if self.check_related_saved(ufl):
            same = self.find_same(ufl)
            fu = False
            if same:
                same = same[0]
                flds = self.get_model_fields(withid=True)
                for f in flds:
                    old_f_val = getattr(same, f.name)
                    new_f_val = getattr(self, f.name)
                    if (not new_f_val and old_f_val) or \
                       (new_f_val and old_f_val and isinstance(old_f_val,
                           django.db.models.fields.files.FieldFile)):
                        setattr(self, f.name, old_f_val)
                kwargs['force_update'] = True
            super(mBase, self).save(*args, **kwargs)
            result = True
        return result


class Countries(mBase):
    name = models.CharField(max_length=50, unique=True)


class Brands(mBase):
    country = models.ForeignKey(Countries, null=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=50, unique=True)
    img = models.FileField(upload_to='brands/')

    def __str__(self):
        return "%s" % self.name


class Models(mBase):
    brand = models.ForeignKey(Brands, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    img = models.FileField(upload_to='models/')

    class Meta:
        unique_together = (("brand", "name"),)

    def __str__(self):
        return "%s" % self.name

    def clean(self):
        self.name = self.name.title()
        if self.brand.name in self.name:
            self.name = self.name.replace(self.brand.name, '').strip()


class Generations(mBase):
    model = models.ForeignKey(Models, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, null=True)
    year_s = models.IntegerField()
    year_e = models.IntegerField(null=True)
    img = models.FileField(upload_to='generations/')

    class Meta:
        unique_together = ("model", "year_s")

    def __str__(self):
        return "{}-{}".format(self.year_s, self.year_e)


class Bodies(mBase):
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
    type = models.CharField(max_length=3,
                            default='O',
                            choices=CAR_BODIES,
                            unique=True
                            )


class Transmissions(mBase):
    TRANSMISSION_TYPE = (
        ('Automatic', (
                        ('robot', 'Robot'),
                        ('auto', 'Auto'),
                        ('vari', 'Variator'),
                      ),),
        ('Manual', (
                        ('manual', 'Manual'),
                        ('semia', 'Semi-automatic'),
                   )),
    )
    DRIVE_TYPE = (
        ('a', 'All Wheel'),
        ('f', 'Front Wheel'),
        ('r', 'Rear Wheel'),
    )
    type = models.CharField(max_length=10, choices=TRANSMISSION_TYPE)
    drive_type = models.CharField(max_length=1, choices=DRIVE_TYPE, null=True)
    gears = models.IntegerField()

    def __str__(self):
        return "Transmission: {}, {}".format(self.type, self.gears)


class Engines(mBase):
    FUEL = (
        ('g', 'Gasoline'),
        ('d', 'Diesel'),
        ('e', 'Electricity'),
    )
    FUELSYSTEM = (
        ('c', 'Carburetor'),
        ('Injection', (
                ('sp', 'Single-point/Throttle body'),
                ('p', 'Port/Multi-point'),
                ('s', 'Sequential'),
                ('d', 'Direct'),
                ('id', 'Indirect injection'),
            ),),
    )
    cylinders = models.IntegerField()
    power = models.IntegerField(help_text='hp')
    torque = models.IntegerField(help_text='Nm')
    speed = models.IntegerField(null=True, help_text='kmh')
    displacement = models.IntegerField(help_text='cm3')
    fuel = models.CharField(max_length=1, choices=FUEL)
    fuelsystem = models.CharField(max_length=2, choices=FUELSYSTEM)
    turbo = models.NullBooleanField()
    acceleration = models.DecimalField(max_digits=4, decimal_places=2,
                                       null=True, help_text='m/s')
    generation = models.ForeignKey(Generations, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("power", "generation")

    def __str__(self):
        return "Engine: {}c, {}hp, {}N/m".format(self.cylinders,
                                                 self.power, self.torque)


class Car(mBase):
    BREAK_TYPE = (
        ('vd', 'Ventilated Discs'),
        ('d', 'Disc'),
        ('dr', 'Drums'),
    )
    generation = models.ForeignKey(Generations, on_delete=models.CASCADE)
    body = models.ForeignKey(Bodies, on_delete=models.CASCADE)
    engine = models.ForeignKey(Engines, on_delete=models.CASCADE)
    transmission = models.ForeignKey(Transmissions,
                                     on_delete=models.CASCADE)
    breaks_f = models.CharField(max_length=2, choices=BREAK_TYPE)
    breaks_r = models.CharField(max_length=2, choices=BREAK_TYPE)
    tires = models.CharField(max_length=15, null=True, help_text='175/70SR16')
    fconsumption = models.DecimalField(max_digits=4, decimal_places=1,
                                       null=True, help_text='l/100Km')
    length = models.IntegerField(help_text='mm')
    width = models.IntegerField(help_text='mm')
    height = models.IntegerField(help_text='mm')
    clearance = models.IntegerField(help_text='mm')
    cargovolume = models.IntegerField(help_text='litres')
    unladen = models.IntegerField(help_text='kg')
    last_update = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("generation", "engine", "body")

    def __str__(self):
        return "{} {} {}\n".format(self.generation, self.engine,
                                   self.transmission)


class Source_site(models.Model):
    SOURCE_TYPE = (
        ('S', 'Specs'),
        ('A', 'Ads')
    )
    url = models.CharField(max_length=255)
    type = models.CharField(max_length=1, choices=SOURCE_TYPE)
