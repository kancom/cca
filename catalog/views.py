from django.shortcuts import render, get_object_or_404
from grabber.models import *
from django.views.generic import ListView

#~ def people(request):
    
    #~ table = CatalogTable(Car.objects.all())
    #~ RequestConfig(request).configure(table)
    #~ return render(request, 'catalog.html', {'table': table})


class ListCatalog(ListView):
    model = Models
    #~ context_object_name = 'object_list'
    queryset = Models.objects.all()
    template_name = "catalog.html"

    def get_queryset(self):
        self.stage = 'brand'
        obj = Brands
        if self.kwargs['gen']:
            self.stage = 'modif'
            obj = get_object_or_404(Generations, id=self.kwargs['gen'])
            return Car.objects.filter(generation = obj)
        elif self.kwargs['model']:
            self.stage = 'gen'
            obj = get_object_or_404(Models, id=self.kwargs['model'])
            return Generations.objects.filter(model = obj)
        elif self.kwargs['brand']:
            self.stage = 'model'
            obj = get_object_or_404(Brands, id=self.kwargs['brand'])
            return Models.objects.filter(brand = obj)
        return Brands.objects.all()

    def get_context_data(self, **kwargs):
        context = super(ListCatalog, self).get_context_data(**kwargs)
        context['stage'] = self.stage
        context['kwargs'] = self.kwargs
        return context
