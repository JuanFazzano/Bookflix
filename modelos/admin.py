# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group
from .models import Genero,Autor,Editorial,Libro,Suscriptor,Novedad
from django.core.exceptions import ValidationError


admin.site.site_header = 'Panel de Administracion'

#Saca los modelos que no queremos que se interactúen
admin.site.unregister(Group)


#Registra que modelos se pueden interactuar
#admin.site.register(Libro,LibroAdmin)
admin.site.register(Novedad)
admin.site.register(Libro)
admin.site.register(Genero)
admin.site.register(Editorial)
admin.site.register(Autor)
admin.site.register(Suscriptor)
