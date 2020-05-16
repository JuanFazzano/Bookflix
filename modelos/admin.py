# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from Bookflix import views
from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from .models import Genero,Autor,Editorial,Libro,Suscriptor,Novedad
from django.shortcuts import redirect
from django.urls import reverse



class NovedadAdmin(admin.ModelAdmin):
    list_display=('titulo',)
    list_per_page = 2
    view_only=True
    #https://stackoverflow.com/questions/1339845/redirect-on-admin-save/1340106
    def response_add(self, request, obj, post_url_continue=None):
        return redirect('/listado_novedades/')
    
    def response_change(self, request, obj, post_url_continue=None):
        return redirect('/listado_novedades/')


admin.site.site_header = 'Panel de Administracion Bookflix'

#Saca los modelos que no queremos que se interactúen
admin.site.unregister(Group)


#Registra que modelos se pueden interactuar
#admin.site.register(Libro,LibroAdmin)
admin.site.register(Novedad,NovedadAdmin)
admin.site.register(Libro)
admin.site.register(Genero)
admin.site.register(Editorial)
admin.site.register(Autor)
admin.site.register(Suscriptor)
