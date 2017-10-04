# -*- coding: utf-8 -*-

from urllib.request import urlopen
from bs4 import BeautifulSoup
from abc import ABCMeta, abstractmethod
from background_task import background
import re
import logging
import logging.handlers
#~ import pdb; pdb.set_trace()

################
import time
###################
from grabber.carspec import *

__author__ = "Andrey Kashrin <kashirinas@rambler.ru>"
__license__ = "Apache 2.0"

log = logging.getLogger(__name__)


class Specs(object):
    CYLINDERS = 0
    DISPLACEMENT = 1
    FUEL = 2
    FUELSYSTEM = 3
    POWER = 4
    TORQUE = 5
    ENGINE = [CYLINDERS, DISPLACEMENT, POWER, TORQUE, FUELSYSTEM, FUEL]
    SPEED = 10
    ACCELERATION = 11
    PERFORMANCE = [SPEED, ACCELERATION]
    CITY = 20
    HIGHWAY = 21
    COMBINED = 22
    FUEL_CONSUMPTION = [CITY, HIGHWAY, COMBINED]
    DRIVETYPE = 30
    GEARBOXTYPE = 31
    GEARS = 32
    TRANSMISSION = [DRIVETYPE, GEARS]
    FRONT = 40
    REAR = 41
    BREAKS = [FRONT, REAR]
    SIZE = 50
    TIRES = [SIZE]
    CARGOVOLUME = 60
    CLEARANCE = 61
    DIMENSIONS = 62
    HEIGHT = 63
    LENGTH = 64
    TRACK = 65
    WHEELBASE = 66
    WIDTH = 67
    DIMENSIONS = [LENGTH, WIDTH, HEIGHT, TRACK, WHEELBASE, CLEARANCE,
                  CARGOVOLUME]
    UNLADEN = 70
    GROSS = 71
    WEIGHT = [UNLADEN, GROSS]
    CARBODY = 80
    DRAGCOEF = 81
    GENERIC = [CARBODY, DRAGCOEF]
    SPECS = [ENGINE, PERFORMANCE, FUEL_CONSUMPTION, TRANSMISSION,
             BREAKS, TIRES, DIMENSIONS, WEIGHT, GENERIC]


class Grabber(metaclass=ABCMeta):
    CAR_SPECS = 1

    def __init__(self, url, mode):
        self.url = url
        self.mode = mode
        self.make_soup(self.url)
        self.parsing_result = {}
        self.car_specs = {}
        self.get_brands_callback = None
        self.get_models_callback = None
        self.get_generations_callback = None
        logging.basicConfig(filename='/tmp/grabber.log', level=logging.DEBUG)

    def make_soup(self, url):
        try:
            self.url = url
            page = urlopen(self.url)
            self.soup = BeautifulSoup(page, 'html5lib')
        except:
            log.exception("Making soup failed for %s" % url)

    def parse(self):
        log.debug("Enter parse")
        if self.mode == self.CAR_SPECS:
            self.parsing_result['specs'] = {}
            return self.get_car_specs()

    @abstractmethod
    def extract_brand_name(self, block):
        pass

    @abstractmethod
    def extract_brand_models(self, block):
        pass

    @abstractmethod
    def extract_brand_img(self, block):
        pass

    @abstractmethod
    def get_brand_blocks(self):
        pass

    @abstractmethod
    def extract_model_name(self, block):
        pass

    @abstractmethod
    def extract_model_models(self, block):
        pass

    @abstractmethod
    def extract_model_img(self, block):
        pass

    @abstractmethod
    def get_model_blocks(self):
        pass

    @abstractmethod
    def get_generation_blocks(self):
        pass

    @abstractmethod
    def extract_generation_years(self):
        pass

    @abstractmethod
    def extract_generation_specs(self):
        pass

    @abstractmethod
    def extract_generation_img(self):
        pass

    @abstractmethod
    def get_modification_blocks(self):
        pass

    @abstractmethod
    def extract_modification_url(self):
        pass

    @abstractmethod
    def fill_car_specs(self, generation):
        pass

    @abstractmethod
    def remap_spec(self, specs):
        pass

    @abstractmethod
    def make_car(self):
        pass

    def denote_spec(self, k, v):
        self.car_specs[k] = v

    def get_car_specs(self):
        log.debug("Enter get_car_specs")
        for brand in self.get_brands():
            self.make_soup(brand['url'])
            for model in self.get_models(brand):
                self.make_soup(model['url'])
                for generation in self.get_generations(model):
                    self.make_soup(generation['url'])
                    for url in self.get_modifications():
                        self.make_soup(url)
                        self.car_specs = {**(self.fill_car_specs()),
                                         **self.car_specs}
                        yield self.make_car(generation)
                        ##################################################
                        time.sleep(1000)
                        ##################################################

    def get_modifications(self):
        log.debug("Enter get_modifications")
        for block in self.get_modification_blocks():
            try:
                url = self.extract_modification_url(block)
                yield url
            except:
                log.exception("get_modifications failed on block %s" % block)

    def get_generations(self, model):
        log.debug("Enter get_generations")
        for block in self.get_generation_blocks():
            try:
                year_s, year_e = self.extract_generation_years(block)
                url = self.extract_generation_specs(block)
                img = self.extract_generation_img(block)
                generation = {}
                generation['year_s'] = year_s
                generation['year_e'] = year_e
                generation['url'] = url
                generation['img'] = img
                generation['model'] = model
                yield generation
            except:
                log.exception("get_generations failed on block %s" % block)

    def get_models(self, brand):
        log.debug("Enter get_models")
        for block in self.get_model_blocks():
            try:
                name = self.extract_model_name(block)
                url = self.extract_model_models(block)
                img = self.extract_model_img(block)
                model = {}
                model['name'] = name
                model['url'] = url
                model['img'] = img
                model['brand'] = brand
                if self.get_models_callback:
                    self.get_models_callback(block)
                yield model
            except:
                log.exception("get_models failed on block %s" % block)

    def get_brands(self):
        log.debug("Enter get_brands")
        for block in self.get_brand_blocks():
            try:
                name = self.extract_brand_name(block)
                url = self.extract_brand_models(block)
                img = self.extract_brand_img(block)
                brand = {}
                brand['name'] = name
                brand['url'] = url
                brand['img'] = img
                yield brand
            except:
                log.exception("get_brands failed on block %s" % block)


class Cars_Data_Grabber(Grabber):
    def extract_brand_name(self, block):
        return block.a['title']

    def extract_brand_models(self, block):
        return block.a['href']

    def extract_brand_img(self, block):
        return block.img['src']

    def get_brand_blocks(self):
        brands = self.soup.find('div', class_="models")
        return brands.find_all('div', class_="col-2")

    def extract_model_name(self, block):
        return self.extract_brand_name(block)

    def extract_model_models(self, block):
        return self.extract_brand_models(block)

    def extract_model_img(self, block):
        return self.extract_brand_img(block)

    def get_model_blocks(self):
        models = self.soup.find('section', class_="models")
        return models.find_all('div', class_="col-4")

    def get_generation_blocks(self):
        self.generation_re = re.compile(r'(\d{4})\s+-\s+(\d{4}|present)')
        return self.get_model_blocks()

    def extract_generation_years(self, block):
        result = self.generation_re.search(str(block))
        if result:
            return [result.group(1), result.group(2)]
        return None

    def extract_generation_specs(self, block):
        return self.extract_brand_models(block)

    def extract_generation_img(self, block):
        return self.extract_brand_img(block)

    def get_modification_blocks(self):
        modifications = self.soup.find('section', class_="types")
        modifications = modifications.find('div', class_="col-8")
        return modifications.find_all('div', class_="row")

    def extract_modification_url(self, block):
        return block.a['href']

    def fill_car_specs(self, generation):
        specs = {}
        for block in self.soup.find_all('div', class_='row box'):
            div = block.find('div', class_='col-6')
            while div:
                if re.match(r".*:$", div.text):
                    key = div.text
                else:
                    specs[key] = div.text
                div = div.find_next_sibling('div', class_=re.compile("col\-6"))
        gears = 1
        for i in range(1, 10):
            if ((str(i)+'th gear ratio:' in specs) and
                (specs[str(i)+'th gear ratio:'] != '-') and
                (i > gears)):
                    gears = i
        transmission = {'type': specs['Transmission type:'],
                        'gears': str(gears)}
        engine = {'cylinders': specs['Cylinders:'],
                  'generation': generation,
                  'power': specs['Max power:'],
                  'torque': specs['Max torque:'],
                  'speed': specs['Top speed:'],
                  'acceleration': specs['Acceleration 0-100 km/h:']}
        carbody = {'type': specs['Carbody:']}
        car = {'generation': generation, 'engine': engine,
               'transmission': transmission, 'body': carbody}
        return car


class Autoevolution_Grabber(Grabber):
    def __init__(self, *args):
        super(Autoevolution_Grabber, self).__init__(*args)
        self.get_models_callback = self.models_callback

    def extract_brand_name(self, block):
        return block.a.text

    def extract_brand_models(self, block):
        return block.a['href']

    def extract_brand_img(self, block):
        return block.img['src']

    def get_brand_blocks(self):
        brands = self.soup.find('div', class_="container carlist clearfix")
        return brands.find_all('div', class_="col2width fl bcol-white carman")

    def extract_model_name(self, block):
        return block.a['title']

    def extract_model_models(self, block):
        return self.extract_brand_models(block)

    def extract_model_img(self, block):
        return self.extract_brand_img(block)

    def get_model_blocks(self):
        models = self.soup.find('div', class_="carmodels col23width clearfix")
        return models.find_all('div', class_="col2width bcol-white fl")

    def get_generation_blocks(self):
        self.generation_re = re.compile(r'(\d{4})\s+-\s+(\d{4}|present)', re.I)
        return self.soup.find_all('div', class_="container carmodel clearfix")

    def extract_generation_years(self, block):
        block = block.find('div', class_="col2width fl bcol-white")
        years = block.find(class_='years').text
        result = self.generation_re.search(years)
        if result:
            return [result.group(1), result.group(2)]
        return None

    def extract_generation_specs(self, block):
        block = block.find('div', class_="col2width fl bcol-white")
        return self.extract_brand_models(block)

    def extract_generation_img(self, block):
        return block.find(class_='mpic fr').img['src']

    def get_modification_blocks(self):
        modifications = self.soup.find('div', class_='sbox10')
        return modifications.find_all('li')

    def extract_modification_url(self, block):
        url = block['onclick']
        url = re.sub(r"\S+\('([^']+)'.*", '\g<1>', url)
        return self.url + '#a' + url

    def remap_spec(self, specs):
        result = {}
        for k, v in specs.items():
            if k == 'Cylinders':
                result[Specs.CYLINDERS] = v
            elif k == 'Displacement':
                result[Specs.DISPLACEMENT] = v
            elif k == 'Power':
                result[Specs.POWER] = v
            elif k == 'Torque':
                result[Specs.TORQUE] = v
            elif k == 'Fuel System':
                result[Specs.FUELSYSTEM] = v
            elif k == 'Fuel':
                result[Specs.FUEL] = v
            elif k == 'Top Speed':
                result[Specs.SPEED] = v
            elif k == 'Acceleration 0-62 Mph (0-100 kph)':
                result[Specs.ACCELERATION] = v
            elif k == 'City':
                result[Specs.CITY] = v
            elif k == 'Highway':
                result[Specs.HIGHWAY] = v
            elif k == 'Combined':
                result[Specs.COMBINED] = v
            elif k == 'Drive Type':
                result[Specs.DRIVETYPE] = v
            elif k == 'Gearbox':
                mo = re.match(r'(\d)-speed ([^$]+$)', v)
                if mo:
                    result[Specs.GEARS] = mo.group(1)
                    result[Specs.GEARBOXTYPE] = mo.group(2)
            elif k == 'Front':
                result[Specs.FRONT] = v
            elif k == 'Rear':
                result[Specs.REAR] = v
            elif k == 'Tire Size':
                result[Specs.SIZE] = v
            elif k == 'Length':
                result[Specs.LENGTH] = v
            elif k == 'Width':
                result[Specs.WIDTH] = v
            elif k == 'Height':
                result[Specs.HEIGHT] = v
            elif k == 'Front/rear Track':
                result[Specs.TRACK] = v
            elif k == 'Wheelbase':
                result[Specs.WHEELBASE] = v
            elif k == 'Ground Clearance':
                result[Specs.CLEARANCE] = v
            elif k == 'Cargo Volume':
                result[Specs.CARGOVOLUME] = v
            elif k == 'Unladen Weight':
                result[Specs.UNLADEN] = v
            elif k == 'Gross Weight Limit':
                result[Specs.GROSS] = v
        return result

    def fill_car_specs(self):
        block = self.soup.find(class_='enginedata engine-inline')
        keys = []
        vals = []
        for blk in block.find_all('div', class_='techdata'):
            dl = blk.find(class_=re.compile('table1w clearfix'))
            for i in dl.find_all('dt'):
                keys.append(i.text)
            for i in dl.find_all('dd'):
                vals.append(i.text)
        specs = dict(zip(keys, vals))
        return self.remap_spec(specs)

    def make_car(self, generation):
        breaks_f = {'type': self.car_specs[Specs.FRONT]}
        breaks_r = {'type': self.car_specs[Specs.REAR]}
        transmission = {'type': self.car_specs[Specs.GEARBOXTYPE],
                        'gears': Specs.GEARS,
                        'drive_type': Specs.DRIVETYPE}
        engine = {'cylinders': self.car_specs[Specs.CYLINDERS],
                  'generation': generation,
                  'displacement': self.car_specs[Specs.DISPLACEMENT],
                  'fuel': self.car_specs[Specs.FUEL],
                  'fuelsystem': self.car_specs[Specs.FUELSYSTEM],
                  'power': self.car_specs[Specs.POWER],
                  'torque': self.car_specs[Specs.TORQUE],
                  'speed': self.car_specs[Specs.SPEED],
                  'acceleration': self.car_specs[Specs.ACCELERATION]}
        carbody = {'type': self.car_specs[Specs.CARBODY]}
        car = {'generation': generation, 'engine': engine,
               'transmission': transmission, 'body': carbody,
               'breaks_f': breaks_f, 'breaks_r': breaks_r,
               'tires': self.car_specs[Specs.SIZE]}
        return car

    def models_callback(self, block):
        body = block.find(class_="body")
        self.denote_spec(Specs.CARBODY, body.text)


def grabber_factory(url, mode):
    if "cars-data.com" in url:
        return Cars_Data_Grabber(url, mode)
    elif "autoevolution" in url:
        return Autoevolution_Grabber(url, mode)


@background(schedule=5)
def grab(url):
    grabber = grabber_factory(url, Grabber.CAR_SPECS)
    logging.info('Started for %s' % url)
    for item in grabber.parse():
        logging.debug(item)
        b = BrandP(name=item['generation']['model']['brand']['name'],
                   img=item['generation']['model']['brand']['img'])
        b.save()
        m = ModelP(name=item['generation']['model']['name'],
                   img=item['generation']['model']['img'],
                   brand=b)
        m.save()
        g = GenerationP(img=item['generation']['img'],
                        year_s=item['generation']['year_s'],
                        year_e=item['generation']['year_e'],
                        model=m)
        g.save()
        cb = BodyP(type=item['body']['type'])
        cb.save()
        t = TransmissionP(type=item['transmission']['type'],
                          gears=item['transmission']['gears'])
        t.save()
        e = EngineP(cylinders=item['engine']['cylinders'],
                    power=item['engine']['power'],
                    torque=item['engine']['torque'],
                    speed=item['engine']['speed'],
                    acceleration=item['engine']['acceleration'],
                    generation=g)
        e.save()
        c = CarP(body=cb,
                 engine=e,
                 transmission=t,
                 generation=g)
        c.save()
