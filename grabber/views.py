from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, ButtonHolder, Submit
from crispy_forms.bootstrap import Field, InlineRadios, TabHolder, Tab
from django import forms
from . import models
from . import grabber


class NameForm(forms.ModelForm):
    class Meta:
        fields = ('url',)
        model = models.Source_site

    def __init__(self, *args, **kwargs):
        super(NameForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
                'url',
                ButtonHolder(
                    Submit('start', 'Start', css_class='btn-primary')
                )
        )


def index(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = NameForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            url=form.cleaned_data['url']
            grabber.grab(url)
            return HttpResponseRedirect('/admin/')

    # if a GET (or any other method) we'll create a blank form
    else:
        sources = models.Source_site.objects.get()
        form = NameForm(instance=sources)

    return render(request, 'index.html', {'form': form})
