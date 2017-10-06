# -*- coding: utf-8 -*-

from abc import ABC
import re, os
from grabber.models import *
from urllib.request import urlretrieve
from django.conf import settings

__author__ = "Andrey Kashrin <kashirinas@rambler.ru>"
__license__ = "Apache 2.0"

FORMAT = "%(asctime)s %(levelname)s - %(name)s: %(message)s"
logging.basicConfig(format=FORMAT, filename='/tmp/grabber.log',
                    level=logging.DEBUG)
log = logging.getLogger(__name__)


class Field(object):
    def __init__(self, clean_proc, *args, **kwargs):
        self.clean_proc = clean_proc
        self.value = None
        self.kwargs = kwargs
        self.args = args

    def set(self, val):
        self.value = self.clean_proc(val, *self.args, **self.kwargs)

    def get(self):
        return self.value

    def __str__(self):
        return "%s" % self.value


re_int = re.compile(r'([+\-]?\d+)')
re_float = re.compile(r'([+\-]?[\d,\.]+)')
re_float_msr = re.compile(r'([\d,\.]+)\s*([A-z/]+)', re.I)


def extract_group(regexp, text, default=None, groups=[1],
                  group_having=None):
    try:
        match = False
        need_default = True
        result = []
        mo_group = []
        re_iter = regexp.finditer(text) if type(text) is str else []
        for mo in re_iter:
            need_default = False
            del mo_group[:]
            for intr_group in groups:
                mo_group.append(mo.group(intr_group))
            if group_having and any(re.match(group_having, moi, re.I) for moi in mo_group):
                return mo_group
        if need_default:
            for g in groups:
                result.append(default)
        else:
            result = mo_group
    except:
        log.exception("extract_group({}, {} of {}, {}, {}, {}) failed".
                      format(str(regexp), text, type(text), default, groups,
                             group_having))
    return result


def extract_int(text, default=None):
    result = extract_group(re_int, text, default)
    return int(result[0]) if result[0] else None


def extract_float(text, default=None):
    result = extract_group(re_float, text, default)
    return float(result[0].replace(',', '.')) if result[0] else None


def extract_int_measure(text, group_having=None):
    return extract_group(re_float_msr, text, groups=[1, 2],
                         group_having=group_having)


def extract_int_and_correct(text, group_having, correcting):
    int = None
    try:
        int, measure = extract_int_measure(text, group_having)
        if int and not re.match(group_having, measure, re.I):
            int = float(int) * correcting
    except:
        log.exception("extract_int_and_correct({}, {}, {}) failed".
                      format(text, group_having, correcting))
    return int


def extract_int_and_correct_rev(text, group_having, correcting):
    fl = None
    try:
        fl, measure = extract_int_measure(text, group_having)
        if fl and not re.match(group_having, measure, re.I):
            fl = correcting / float(fl)
    except:
        log.exception("extract_int_and_correct_rev({}, {}, {}) failed".
                      format(text, group_having, correcting))
    return fl


def extract_name(text):
    return text.strip().title()


def extract_url(url, suffix):
    filename = url.split('/')[-1]
    path = os.path.join(settings.MEDIA_ROOT,
                                  suffix, filename)
    if not os.path.exists(path):
        urlretrieve(url, path)
    #~ log.debug("https://stackoverflow.com/a/10297620/3621883")
    return filename


def extract_dbobject(proxy):
    return proxy.dbobject


def extract_none(*args):
    return None


def strip_spaces(text):
    return re.sub(r"[^0-9R/]", "", text, count=0, flags=re.I)


def contains_word(text, word):
    result = None
    if text:
        if word in text:
            result = True
        else:
            result = False
    return result


def adapt(text, verify_list):
    if not text:
        return None
    text = re.sub(r'\W', '', text)
    text = extract_name(text)
    for k, v in verify_list.items():
        if text in verify_list[k]:
            return k
    raise Exception("Value not found. adapt({}, {})".format(text, verify_list))


class Entity(ABC):
    _clsfields = {}
    _locked = False

    def __setattr__(self, name, value):
        if self._locked and name in self._clsfields:
            raise AttributeError("Direct assignment forbidden")
        self.__dict__[name] = value

    def make_dbobject(self):
        vals = []
        for f in self._clsfields:
            f = getattr(self, f)
            vals.append(f.get())
        self.dbobject = self.dbclass(
                                **dict(zip(self._clsfields, vals)))
        if len(self.dbobject.get_model_fields()) != len(self._clsfields):
            raise AttributeError("Fields count in model {} and proxy {}"
                                 " doesn't match for {}".format(
                                 len(self.dbobject.get_model_fields()),
                                 len(self._clsfields),
                                 self))

    def save(self):
        if self.clean:
            self.clean()
        if not self.dbobject:
            self.make_dbobject()
        self.dbobject.save()

    def init(self, **kwargs):
        for k, v in kwargs.items():
            f = getattr(self, k)
            f.set(v)

    def __init__(self, **kwargs):
        self.dbobject = None
        self._locked = True
        self.clean = None
        self.init(**kwargs)


class BrandP(Entity):
    _clsfields = ['name', 'img', 'country']

    def __init__(self, **kwargs):
        self.name = Field(extract_name)
        self.img = Field(extract_url, 'brands')
        self.country = Field(extract_name)
        self.dbclass = Brands
        super(BrandP, self).__init__(**kwargs)


class ModelP(Entity):
    _clsfields = ['name', 'img', 'brand']

    def __init__(self, **kwargs):
        self.name = Field(extract_name)
        self.img = Field(extract_url, 'models')
        self.brand = Field(extract_dbobject)
        self.dbclass = Models
        super(ModelP, self).__init__(**kwargs)
        self.clean = self.set_name

    def set_name(self):
        brand = self.brand.get()
        if brand.name in self.name.get():
            self.name.set(self.name.get().replace(brand.name, ''))


class GenerationP(Entity):
    _clsfields = ['img', 'model', 'year_s', 'year_e', 'name']

    def __init__(self, **kwargs):
        self.img = Field(extract_url, 'generations')
        self.name = Field(extract_name)
        self.model = Field(extract_dbobject)
        self.year_s = Field(extract_int)
        self.year_e = Field(extract_int)
        self.dbclass = Generations
        super(GenerationP, self).__init__(**kwargs)


class BodyP(Entity):
    _clsfields = ['type']

    verify_list = {
                    'Suv': ['Suv', 'Suvcrossover', 'Suvs'],
                    'Cv': ['Cabriolet', 'Convertibles'],
                    'H': ['Hatchback', 'Hatchbacks'],
                    'S': ['Sedans'],
                    'Cp': ['Coupes'],
                    'W': ['Wagons'],
                    'P': ['Trucks'],
                    'V': ['Vans'],
                  }

    def __init__(self, **kwargs):
        self.type = Field(adapt, self.verify_list)
        self.dbclass = Bodies
        super(BodyP, self).__init__(**kwargs)


class TransmissionP(Entity):
    _clsfields = ['type', 'gears', 'drive_type']

    gb_list = {
                'robot': ['Robot', 'Stronicautomatic'],
                'manual': ['Manual'],
                'semia': ['Semiautomaat', 'Semiautomatic',
                          'Sequentialautomatic'],
                'auto': ['Autmetdubbkoppeling', 'Automaticdct',
                         'Automatic'],
                }

    dt_list = {
                'a': ['Allwheeldrive', 'Frontrear'],
                'f': ['Frontwheeldrive', 'Front'],
                'r': ['Rearwheeldrive', 'Rear'],
              }

    def __init__(self, **kwargs):
        self.type = Field(adapt, self.gb_list)
        self.gears = Field(extract_int)
        self.drive_type = Field(adapt, self.dt_list)
        self.dbclass = Transmissions
        super(TransmissionP, self).__init__(**kwargs)


class EngineP(Entity):
    _clsfields = ['generation', 'power', 'torque', 'speed',
                  'acceleration', 'cylinders', 'displacement', 'fuel',
                  'fuelsystem', 'turbo']

    fuel_list = {
                    'g': ['Gasoline', 'Petrol'],
                    'd': ['Diesel'],
                    'e': ['Electric'],
                }

    fuelsys_list = {
                    'c': ['Carburetor'],
                    'd': ['Turbochargeddirectinjection',
                          'Directinjection',
                          'Directhighpressurefuelinjection'],
                    's': ['Electric'],
                    'p': ['Multipointinjection',
                          'Multipointfuelinjection'],
                    'sp': ['Electric'],
                    'id': ['Indirectinjection'],
                    }

    def __init__(self, **kwargs):
        self.cylinders = Field(extract_int)
        self.generation = Field(extract_dbobject)
        self.displacement = Field(extract_int_and_correct, r'[cс][mм]3', 1)
        self.power = Field(extract_int_and_correct, 'hp', 1.34102)
        self.torque = Field(extract_int_and_correct, r'[nн][mм]', 1)
        self.speed = Field(extract_int_and_correct, r'[kк][mм].?[hч]', 1.609344)
        self.acceleration = Field(extract_float)
        self.fuel = Field(adapt, self.fuel_list)
        self.turbo = Field(contains_word, 'yes')
        self.fuelsystem = Field(adapt, self.fuelsys_list)
        self.dbclass = Engines
        super(EngineP, self).__init__(**kwargs)


class CarP(Entity):
    _clsfields = ['generation', 'body', 'engine', 'transmission',
                  'breaks_f', 'breaks_r', 'tires', 'fconsumption',
                  'length', 'width', 'height', 'clearance',
                  'cargovolume', 'unladen',
                  'last_update']

    verify_list = {
                    'vd': ['Ventilateddiscs'],
                    'd': ['Discs'],
                    'dr': ['Drums'],
                  }

    def __init__(self, **kwargs):
        self.generation = Field(extract_dbobject)
        self.body = Field(extract_dbobject)
        self.engine = Field(extract_dbobject)
        self.transmission = Field(extract_dbobject)
        self.breaks_f = Field(adapt, self.verify_list)
        self.breaks_r = Field(adapt, self.verify_list)
        self.tires = Field(strip_spaces)
        self.last_update = Field(extract_none)
        self.fconsumption = Field(extract_int_and_correct_rev,
                                  r'[lл]/',
                                  235.215)  # because re_float_msr doesn't contain digits
        self.length = Field(extract_int_and_correct, r'[mм][mм]', 25.4)
        self.width = Field(extract_int_and_correct, r'[mм][mм]', 25.4)
        self.height = Field(extract_int_and_correct, r'[mм][mм]', 25.4)
        self.clearance = Field(extract_int_and_correct, r'[mм][mм]', 25.4)
        self.cargovolume = Field(extract_int_and_correct, r'[lл]', 28.3168)
        self.unladen = Field(extract_int_and_correct, r'[kк][gг]', 0.453592)
        self.dbclass = Car
        super(CarP, self).__init__(**kwargs)
