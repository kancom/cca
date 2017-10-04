import django_tables2 as tables
from grabber.models import Car
from django.utils.html import format_html


class ImageColumn(tables.FileColumn):
    def render(self, value):
        return format_html('<img src="{}" />', value.name)


class CatalogTable(tables.Table):
    pic = ImageColumn(accessor='generation.img')
    brand = tables.Column(accessor='generation.model.brand.name', verbose_name='Brand')
    model = tables.Column(accessor='generation.model.name')
    generation = tables.Column(accessor='generation.name')
    body = tables.Column(accessor='body.type')
    power = tables.Column(accessor='engine.power')
    torque = tables.Column(accessor='engine.torque')


    class Meta:
        model = Car
        fields = ('pic', 'brand', 'model', 'generation', 'body', 'power', 'torque')
        attrs = {'class': 'paleblue'}
