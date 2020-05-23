# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.contrib import admin
from django.shortcuts import redirect
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from .models import Genero,Autor,Editorial,Libro,Suscriptor,Novedad

class NovedadAdmin(admin.ModelAdmin):
    list_display=('titulo',)
    list_per_page = 10
    view_only=True
    #https://stackoverflow.com/questions/1339845/redirect-on-admin-save/1340106
    def response_add(self, request, obj, post_url_continue=None):
        return redirect('/listado_novedades/')

    def response_change(self, request, obj, post_url_continue=None):
        return redirect('/listado_novedades/')

    def response_delete(self, request, obj, post_url_continue=None):
        return redirect('/listado_novedades/')


class GeneroAdmin(admin.ModelAdmin):
    list_per_page = 10
    view_only=True
    #https://stackoverflow.com/questions/1339845/redirect-on-admin-save/1340106
    def response_add(self, request, obj, post_url_continue=None):
        return redirect('/listado_generos/')

    def response_change(self, request, obj, post_url_continue=None):
        return redirect('/listado_generos/')

class AutorAdmin(admin.ModelAdmin):
    list_per_page = 10
    view_only=True
    #https://stackoverflow.com/questions/1339845/redirect-on-admin-save/1340106
    def response_add(self, request, obj, post_url_continue=None):
        return redirect('/listado_autores/')

    def response_change(self, request, obj, post_url_continue=None):
        return redirect('/listado_autores/')

class EditorialAdmin(admin.ModelAdmin):
    list_per_page = 10
    view_only=True
    #https://stackoverflow.com/questions/1339845/redirect-on-admin-save/1340106
    def response_add(self, request, obj, post_url_continue=None):
        return redirect('/listado_editoriales/')

    def response_change(self, request, obj, post_url_continue=None):
        return redirect('/listado_editoriales/')

class LibroAdmin(admin.ModelAdmin):
    list_per_page = 10
    view_only=True
    #https://stackoverflow.com/questions/1339845/redirect-on-admin-save/1340106
    def response_add(self, request, obj, post_url_continue=None):
        return redirect('/listado_libros/')

    def response_change(self, request, obj, post_url_continue=None):
        return redirect('/listado_libros/')

    def get_form(self, request, obj=None, **kwargs):
        #Deshabilita los botones de agregar y modificar de los campos many to many genero, autor y editorial
        form = super(LibroAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['autor'].widget.can_add_related = False
        form.base_fields['autor'].widget.can_change_related = False

        form.base_fields['editorial'].widget.can_add_related = False
        form.base_fields['editorial'].widget.can_change_related = False
        form.base_fields['genero'].widget.can_add_related = False
        form.base_fields['genero'].widget.can_change_related = False
        return form


class EditorialAdmin(admin.ModelAdmin):
    list_per_page = 2
    view_only=True
    #https://stackoverflow.com/questions/1339845/redirect-on-admin-save/1340106
    def response_add(self, request, obj, post_url_continue=None):
        return redirect('/listado_editoriales/')

    def response_change(self, request, obj, post_url_continue=None):
        return redirect('/listado_editoriales/')


admin.site.site_header = 'Panel de Administracion Bookflix'

#Saca los modelos que no queremos que se interactúen
admin.site.unregister(Group)


#Registra que modelos se pueden interactuar
#admin.site.register(Libro,LibroAdmin)
admin.site.register(Novedad,NovedadAdmin)
admin.site.register(Libro,LibroAdmin)
admin.site.register(Genero,GeneroAdmin)
admin.site.register(Editorial,EditorialAdmin)
admin.site.register(Autor,AutorAdmin)
