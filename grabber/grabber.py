# -*- coding: utf-8 -*-

from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
from abc import ABCMeta, abstractmethod
from background_task import background
import re
import random
import logging
import logging.handlers
#~ import socks
#~ import socket
#~ socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", 8888)
#~ socket.socket = socks.socksocket
#~ import pdb;pdb.set_trace()

################
import time
###################
from grabber.carspec import *

__author__ = "Andrey Kashrin <kashirinas@rambler.ru>"
__license__ = "Apache 2.0"

log = logging.getLogger(__name__)


def zip_dict(d1, d2):
    result = {}
    for k in d1:
        if k not in d2:
            result[k] = d1[k]
        else:
            result[k] = (d1[k] or d2[k])
    return result

class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


engine = dotdict({'cylinders': 0, 'displacement': 1, 'fuel': 2,
                  'fuelsystem': 3, 'power': 4, 'torque': 5,
                  'turbo': 6})
performance = dotdict({'speed': 10, 'acceleration': 11})
fuel_consumption = dotdict({'city': 20, 'highway': 21, 'combined': 22})
transmission = dotdict({'drivetype': 30, 'gearboxtype': 31, 'gears': 32})
breaks = dotdict({'front': 40, 'rear': 41})
tires = dotdict({'size': 50})
dimensions = dotdict({'cargovolume': 60, 'clearance': 61, 'dimensions': 62,
                      'height': 63, 'length': 64, 'track': 65,
                      'wheelbase': 66, 'width': 67})
weight = dotdict({'unladen': 70, 'gross': 71})
generic = dotdict({'carbody': 80, 'dragcoef': 81})


SPECS = dotdict({'engine': engine, 'performance': performance,
                 'fuel_consumption': fuel_consumption,
                 'transmission': transmission, 'breaks': breaks,
                 'tires': tires, 'dimensions': dimensions,
                 'weight': weight, 'generic': generic})


class Grabber(metaclass=ABCMeta):
    CAR_SPECS = 1

    def __init__(self, url, mode):
        self.url = url
        self.mode = mode
        self.car_specs = {}
        self.get_brands_callback = None
        self.get_models_callback = None
        self.get_generations_callback = None
        logging.basicConfig(filename='/tmp/grabber.log', level=logging.DEBUG)
        self.UAs = ['Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.1 Safari/603.1.30',
                    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:56.0) Gecko/20100101 Firefox/56.0',
                    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/61.0.3163.79 Chrome/61.0.3163.79 Safari/537.36',
                    'Mozilla',
                    ]

    def make_soup(self, url):
        def get_cached(url):
            if url in self.url_cache:
                return self.url_cache[url]
            else:
                return url
        try:
            self.url = url
            page = urlopen(Request(get_cached(self.url),
                           headers={'User-Agent': random.choice(self.UAs)}))
            self.soup = BeautifulSoup(page, 'html5lib')
        except:
            log.exception("Making soup failed for %s" % url)

    def parse(self):
        log.debug("Enter parse")
        if self.mode == self.CAR_SPECS:
            for ko in SPECS:
                for ki in SPECS[ko]:
                    self.car_specs[SPECS[ko][ki]] = None
            self.url_cache = {
                        'https://www.autoevolution.com/cars': 'https://webcache.googleusercontent.com/search?q=cache:SUdASOkLJ0UJ:https://www.autoevolution.com/cars/+&cd=1&hl=en&ct=clnk&gl=tr&client=ubuntu',
                        'https://www.autoevolution.com/acura/': 'https://webcache.googleusercontent.com/search?q=cache:HCq-XWL1GF4J:https://www.autoevolution.com/acura/+&cd=1&hl=en&ct=clnk&gl=tr&client=ubuntu',
                        'https://www.autoevolution.com/cars/acura-tlx-2015.html': 'https://webcache.googleusercontent.com/search?q=cache:0c5F-zD70yYJ:https://www.autoevolution.com/cars/acura-tlx-2015.html+&cd=1&hl=en&ct=clnk&gl=tr&client=ubuntu'
                         }
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
    def fill_car_specs(self):
        pass

    @abstractmethod
    def remap_spec(self, specs):
        pass

    def make_car(self, generation):
        log.debug("Enter make_car")
        t = TransmissionP(type=self.car_specs[SPECS.transmission.gearboxtype],
                          gears=self.car_specs[SPECS.transmission.gears],
                          drive_type=self.car_specs[SPECS.transmission.drivetype])
        t.save()
        e = EngineP(cylinders=self.car_specs[SPECS.engine.cylinders],
                    generation=generation,
                    displacement=self.car_specs[SPECS.engine.displacement],
                    fuel=self.car_specs[SPECS.engine.fuel],
                    turbo=self.car_specs[SPECS.engine.turbo],
                    fuelsystem=self.car_specs[SPECS.engine.fuelsystem],
                    power=self.car_specs[SPECS.engine.power],
                    torque=self.car_specs[SPECS.engine.torque],
                    speed=self.car_specs[SPECS.performance.speed],
                    acceleration=self.car_specs[SPECS.performance.acceleration])
        e.save()
        cb = BodyP(type=self.car_specs[SPECS.generic.carbody])
        cb.save()
        car = CarP(generation=generation, engine=e,
                 transmission=t, body=cb,
                 breaks_f=self.car_specs[SPECS.breaks.front],
                 breaks_r=self.car_specs[SPECS.breaks.rear],
                 tires=self.car_specs[SPECS.tires.size],
                 fconsumption=self.car_specs[SPECS.fuel_consumption.combined],
                 length=self.car_specs[SPECS.dimensions.length],
                 width=self.car_specs[SPECS.dimensions.width],
                 height=self.car_specs[SPECS.dimensions.height],
                 clearance=self.car_specs[SPECS.dimensions.clearance],
                 cargovolume=self.car_specs[SPECS.dimensions.cargovolume],
                 unladen=self.car_specs[SPECS.weight.unladen])
        car.save()
        return car

    def denote_spec(self, k, v):
        self.car_specs[k] = v

    def get_car_specs(self):
        log.debug("Enter get_car_specs")
        self.make_soup(self.url)
        for brand, url in self.get_brands():
            self.make_soup(url)
            for model, url in self.get_models(brand):
                self.make_soup(url)
                for generation, url in self.get_generations(model):
                    self.make_soup(url)
                    for url in self.get_modifications():
                        self.make_soup(url)
                        self.car_specs = zip_dict(self.car_specs,
                                                  self.fill_car_specs())
                        log.debug(self.car_specs)
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
                g = GenerationP(img=img, year_s=year_s, year_e=year_e,
                                model=model)
                g.save()
                yield g, url
            except:
                log.exception("get_generations failed on block %s" % block)

    def get_models(self, brand):
        log.debug("Enter get_models")
        for block in self.get_model_blocks():
            try:
                name = self.extract_model_name(block)
                url = self.extract_model_models(block)
                img = self.extract_model_img(block)
                m = ModelP(name=name, img=img, brand=brand)
                m.save()
                if self.get_models_callback:
                    self.get_models_callback(block)
                yield m, url
            except:
                log.exception("get_models failed on block %s" % block)

    def get_brands(self):
        log.debug("Enter get_brands")
        for block in self.get_brand_blocks():
            try:
                name = self.extract_brand_name(block)
                url = self.extract_brand_models(block)
                img = self.extract_brand_img(block)
                b = BrandP(name=name, img=img)
                b.save()
                yield b, url
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

    def remap_spec(self, specs):
        result = {}
        for k, v in specs.items():
            if k == 'Cylinders:':
                result[SPECS.engine.cylinders] = v
            elif k == 'Displacement:':
                result[SPECS.engine.displacement] = v
            elif k == 'Max power:':
                result[SPECS.engine.power] = v
            elif k == 'Max torque:':
                result[SPECS.engine.torque] = v
            elif k == 'Fuel delivery:':
                result[SPECS.engine.fuelsystem] = v
            elif k == 'Fuel:':
                result[SPECS.engine.fuel] = v
            elif k == 'Turbo:':
                result[SPECS.engine.turbo] = v
            elif k == 'Top speed:':
                result[SPECS.performance.speed] = v
            elif k == 'Acceleration 0-100 km/h:':
                result[SPECS.performance.acceleration] = v
            elif k == 'Urban consumption:':
                result[SPECS.fuel_consumption.city] = v
            elif k == 'Extra-urban consumption:':
                result[SPECS.fuel_consumption.highway] = v
            elif k == 'Average consumption:':
                result[SPECS.fuel_consumption.combined] = v
            elif k == 'Wheel drive:':
                result[SPECS.transmission.drivetype] = v
            elif k == 'Transmission type:':
                result[SPECS.transmission.gearboxtype] = v
            elif k == 'Gears:':
                result[SPECS.transmission.gears] = v
            #~ elif k == 'Front':
                #~ result[SPECS.breaks.front] = v
            #~ elif k == 'Rear':
                #~ result[SPECS.breaks.rear] = v
            #~ elif k == 'Tire Size':
                #~ result[SPECS.tires.size] = v
            elif k == 'Length:':
                result[SPECS.dimensions.length] = v
            elif k == 'Width:':
                result[SPECS.dimensions.width] = v
            elif k == 'Height:':
                result[SPECS.dimensions.height] = v
            elif k == 'Front track:':
                result[SPECS.dimensions.track] = v
            elif k == 'Wheelbase:':
                result[SPECS.dimensions.wheelbase] = v
            elif k == 'Ground clearance:':
                result[SPECS.dimensions.clearance] = v
            elif k == 'Trunk capacity:':
                result[SPECS.dimensions.cargovolume] = v
            elif k == 'Empty mass:':
                result[SPECS.weight.unladen] = v
            elif k == 'Max. loading capacity:':
                result[SPECS.weight.gross] = v
            elif k == 'Carbody:':
                result[SPECS.generic.carbody] = v
        return result

    def fill_car_specs(self):
        log.debug("Enter fill_car_specs")
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
        specs['Gears:'] = str(gears)
        return self.remap_spec(specs)


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
                result[SPECS.engine.cylinders] = v
            elif k == 'Displacement':
                result[SPECS.engine.displacement] = v
            elif k == 'Power':
                result[SPECS.engine.power] = v
            elif k == 'Torque':
                result[SPECS.engine.torque] = v
            elif k == 'Fuel System':
                result[SPECS.engine.fuelsystem] = v
            elif k == 'Fuel':
                result[SPECS.engine.fuel] = v
            elif k == 'Top Speed':
                result[SPECS.performance.speed] = v
            elif k == 'Acceleration 0-62 Mph (0-100 kph)':
                result[SPECS.performance.acceleration] = v
            elif k == 'City':
                result[SPECS.fuel_consumption.city] = v
            elif k == 'Highway':
                result[SPECS.fuel_consumption.highway] = v
            elif k == 'Combined':
                result[SPECS.fuel_consumption.combined] = v
            elif k == 'Drive Type':
                result[SPECS.transmission.drivetype] = v
            elif k == 'Gearbox':
                mo = re.match(r'(\d)-speed ([^$]+$)', v)
                if mo:
                    result[SPECS.transmission.gears] = mo.group(1)
                    result[SPECS.transmission.gearboxtype] = mo.group(2)
            elif k == 'Front':
                result[SPECS.breaks.front] = v
            elif k == 'Rear':
                result[SPECS.breaks.rear] = v
            elif k == 'Tire Size':
                result[SPECS.tires.size] = v
            elif k == 'Length':
                result[SPECS.dimensions.length] = v
            elif k == 'Width':
                result[SPECS.dimensions.width] = v
            elif k == 'Height':
                result[SPECS.dimensions.height] = v
            elif k == 'Front/rear Track':
                result[SPECS.dimensions.track] = v
            elif k == 'Wheelbase':
                result[SPECS.dimensions.wheelbase] = v
            elif k == 'Ground Clearance':
                result[SPECS.dimensions.clearance] = v
            elif k == 'Cargo Volume':
                result[SPECS.dimensions.cargovolume] = v
            elif k == 'Unladen Weight':
                result[SPECS.weight.unladen] = v
            elif k == 'Gross Weight Limit':
                result[SPECS.weight.gross] = v
        return result

    def fill_car_specs(self):
        log.debug("Enter fill_car_specs")
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

    def models_callback(self, block):
        body = block.find(class_="body")
        self.denote_spec(SPECS.generic.carbody, body.text)


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
