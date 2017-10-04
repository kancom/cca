# -*- coding: utf-8 -*-

from abc import ABC
import re
from grabber.models import *

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
re_int_msr = re.compile(r'([\d,\.]+)\s*([A-z/]+)', re.I)


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
    return extract_group(re_int_msr, text, groups=[1, 2],
                         group_having=group_having)


def extract_int_and_correct(text, group_having, correcting):
    int = None
    try:
        int, measure = extract_int_measure(text, group_having)
        if int and not re.match(group_having, measure):
            int = float(int) * correcting
    except:
        log.exception("extract_int_and_correct({}, {}, {}) failed".
                      format(text, group_having, correcting))
    return int


def extract_name(text):
    return text.strip().title()


def extract_url(text):
    log.debug("https://stackoverflow.com/a/10297620/3621883")
    return text


def extract_dbobject(proxy):
    return proxy.dbobject


def extract_none(*args):
    return None


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
        self.img = Field(extract_url)
        self.country = Field(extract_name)
        self.dbclass = Brands
        super(BrandP, self).__init__(**kwargs)


class ModelP(Entity):
    _clsfields = ['name', 'img', 'brand']

    def __init__(self, **kwargs):
        self.name = Field(extract_name)
        self.img = Field(extract_url)
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
        self.img = Field(extract_url)
        self.name = Field(extract_name)
        self.model = Field(extract_dbobject)
        self.year_s = Field(extract_int)
        self.year_e = Field(extract_int)
        self.dbclass = Generations
        super(GenerationP, self).__init__(**kwargs)


class BodyP(Entity):
    _clsfields = ['type']

    def extract_body(self, text):
        text = re.sub(r'\W', '', text)
        text = extract_name(text)
        if text in ['Suv', 'Suvcrossover', 'Suvs']:
            return 'Suv'
        elif text in ['Cabriolet', 'Convertibles']:
            return 'Cv'
        elif text in ['Hatchback', 'Hatchbacks']:
            return 'H'
        elif text in ['Sedans']:
            return 'S'
        elif text in ['Coupes']:
            return 'Cp'
        elif text in ['Wagons']:
            return 'W'
        elif text in ['Trucks']:
            return 'P'
        elif text in ['Vans']:
            return 'V'
        else:
            raise Exception("Unsupported car body: %s" % text)

    def __init__(self, **kwargs):
        self.type = Field(self.extract_body)
        self.dbclass = Bodies
        super(BodyP, self).__init__(**kwargs)


class TransmissionP(Entity):
    _clsfields = ['type', 'gears', 'drive_type']

    def extract_gearbox(self, text):
        text = re.sub(r'\W', '', text)
        text = extract_name(text)
        if text in ['Robot', 'Stronicautomatic']:
            return 'robot'
        elif text in ['Manual']:
            return 'manual'
        elif text in ['Semiautomaat', 'Semiautomatic',
                      'Sequentialautomatic']:
            return 'semia'
        elif text in ['Autmetdubbkoppeling', 'Automaticdct', 'Automatic']:
            return 'auto'
        else:
            raise Exception("Unsupported transmission: %s" % text)

    def extract_drivetype(self, text):
        text = re.sub(r'\W', '', text)
        text = extract_name(text)
        if text in ['Allwheeldrive']:
            return 'a'
        elif text in ['Frontwheeldrive']:
            return 'f'
        elif text in ['Rearwheeldrive']:
            return 'r'
        else:
            raise Exception("Unsupported transmission: %s" % text)

    def __init__(self, **kwargs):
        self.type = Field(self.extract_gearbox)
        self.gears = Field(extract_int)
        self.drive_type = Field(self.extract_drivetype)
        self.dbclass = Transmissions
        super(TransmissionP, self).__init__(**kwargs)


class EngineP(Entity):
    _clsfields = ['generation', 'power', 'torque', 'speed',
                  'acceleration', 'cylinders', 'displacement', 'fuel',
                  'fuelsystem', ]

    def extract_fuel(self, text):
        ext = re.sub(r'\W', '', text)
        text = extract_name(text)
        if text in ['Gasoline', 'Petrol']:
            return 'g'
        elif text in ['Diesel']:
            return 'd'
        elif text in ['Electric']:
            return 'e'
        else:
            raise Exception("Unsupported fuel: %s" % text)

    def extract_fuelsystem(self, text):
        ext = re.sub(r'\W', '', text)
        text = extract_name(text)
        if text in ['Carburetor']:
            return 'c'
        elif text in ['Turbochargeddirectinjection', 'Directinjection',
                      'Directhighpressurefuelinjection']:
            return 'd'
        elif text in ['Electric']:
            return 's'
        elif text in ['Multipointinjection', 'Multipointfuelinjection',]:
            return 'p'
        elif text in ['Electric']:
            return 'sp'
        elif text in ['Indirectinjection']:
            return 'id'
        else:
            raise Exception("Unsupported fuelsystem: %s" % text)

    def __init__(self, **kwargs):
        self.cylinders = Field(extract_int)
        self.generation = Field(extract_dbobject)
        self.displacement = Field(extract_int_and_correct, r'[cс][mм]3', 1)
        self.power = Field(extract_int_and_correct, 'hp', 1.34102)
        self.torque = Field(extract_int_and_correct, r'[nн][mм]', 1)
        self.speed = Field(extract_int_and_correct, r'[kк][mм].?[hч]', 1.609344)
        self.acceleration = Field(extract_float)
        self.fuel = Field(self.extract_fuel)
        self.fuelsystem = Field(self.extract_fuelsystem)
        self.dbclass = Engines
        super(EngineP, self).__init__(**kwargs)

class BreakP(Entity):
    _clsfields = ['type']

    def extract_breaktype(self, text):
        text = re.sub(r'\W', '', text)
        text = extract_name(text)
        if text in ['Ventilateddiscs']:
            return 'vd'
        elif text in ['Discs']:
            return 'd'
        elif text in ['Drums']:
            return 'dr'
        else:
            raise Exception("Unsupported transmission: %s" % text)

    def __init__(self, **kwargs):
        self.type = Field(self.extract_breaktype)
        super(BreakP, self).__init__(**kwargs)


class CarP(Entity):
    _clsfields = ['generation', 'body', 'engine', 'transmission',
                  'breaks_f', 'breaks_r',
                  'last_update']

    def __init__(self, **kwargs):
        self.generation = Field(extract_dbobject)
        self.body = Field(extract_dbobject)
        self.engine = Field(extract_dbobject)
        self.transmission = Field(extract_dbobject)
        self.breaks_f = Field(extract_dbobject)
        self.breaks_r = Field(extract_dbobject)
        self.tires = Field(strip_spaces)
        self.last_update = Field(extract_none)
        self.dbclass = Car
        super(CarP, self).__init__(**kwargs)
