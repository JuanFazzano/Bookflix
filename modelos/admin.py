# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib import admin
from django.contrib.auth.models import Group

from .models import Genero,Autor,Editorial,Libro,Suscriptor,Novedad


#class LibroAdmin(admin.ModelAdmin):
    #exclude = ('titulo',) Para excluir elementos que no queremos que se completen

#Pone el nombre del header
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
