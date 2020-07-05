# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.contrib import admin
from django.shortcuts import redirect
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from .models import Genero,Autor,Editorial,Libro,Suscriptor,Novedad,Trailer,Calificacion

class NovedadAdmin(admin.ModelAdmin):
    list_display=('titulo',)
    list_per_page = 10
    view_only=True
    #https://stackoverflow.com/questions/1339845/redirect-on-admin-save/1340106
    def response_add(self, request, obj, post_url_continue=None):
        return redirect('/listado_novedad/')

    def response_change(self, request, obj, post_url_continue=None):
        return redirect('/listado_novedad/')

    def response_delete(self, request, obj, post_url_continue=None):
        return redirect('/listado_novedad/')

class GeneroAdmin(admin.ModelAdmin):
    list_per_page = 10
    view_only=True
    #https://stackoverflow.com/questions/1339845/redirect-on-admin-save/1340106
    def response_add(self, request, obj, post_url_continue=None):
        return redirect('/listado_genero/')

    def response_change(self, request, obj, post_url_continue=None):
        return redirect('/listado_genero/')

class AutorAdmin(admin.ModelAdmin):
    list_per_page = 10
    view_only=True
    #https://stackoverflow.com/questions/1339845/redirect-on-admin-save/1340106
    def response_add(self, request, obj, post_url_continue=None):
        return redirect('/listado_autor/')

    def response_change(self, request, obj, post_url_continue=None):
        return redirect('/listado_autor/')

class EditorialAdmin(admin.ModelAdmin):
    list_per_page = 10
    view_only=True
    #https://stackoverflow.com/questions/1339845/redirect-on-admin-save/1340106
    def response_add(self, request, obj, post_url_continue=None):
        return redirect('/listado_editorial/')

    def response_change(self, request, obj, post_url_continue=None):
        return redirect('/listado_editorial/')

class LibroAdmin(admin.ModelAdmin):
    list_per_page = 10
    view_only = True
    #https://stackoverflow.com/questions/1339845/redirect-on-admin-save/1340106
    def response_add(self, request, obj, post_url_continue=None):
        return redirect('/listado_libro/')

    def response_change(self, request, obj, post_url_continue=None):
        return redirect('/listado_libro/')

    def response_delete(self, request, obj, post_url_continue=None):
        return redirect('/listado_libro/')

    def get_form(self, request, obj=None, **kwargs):
        #Deshabilita los botones de agregar y modificar de los campos many to many genero, autor y editorial
        form = super(LibroAdmin, self).get_form(request, obj, **kwargs)
   #     form.base_fields['titulo'].widget.attrs['placeholder'] = 'Hola'
        form.base_fields['autor'].widget.can_add_related = False
        form.base_fields['autor'].widget.can_change_related = False
        form.base_fields['editorial'].widget.can_add_related = False
        form.base_fields['editorial'].widget.can_change_related = False
        form.base_fields['genero'].widget.can_add_related = False
        form.base_fields['genero'].widget.can_change_related = False
        self.exclude = ('esta_completo',) #Saca el checkbox
        return form


class EditorialAdmin(admin.ModelAdmin):
    list_per_page = 2
    view_only=True
    #https://stackoverflow.com/questions/1339845/redirect-on-admin-save/1340106
    def response_add(self, request, obj, post_url_continue=None):
        return redirect('/listado_editorial/')

    def response_change(self, request, obj, post_url_continue=None):
        return redirect('/listado_editorial/')

class TrailerAdmin(admin.ModelAdmin):
    view_only     = True
    list_per_page = 10
    #https://stackoverflow.com/questions/1339845/redirect-on-admin-save/1340106
    def response_add(self, request, obj, post_url_continue=None):
        return redirect('/listado_trailer/')

    def response_change(self, request, obj, post_url_continue=None):
        return redirect('/listado_trailer/')

    def response_delete(self, request, obj, post_url_continue=None):
        return redirect('/listado_trailer/')

    def get_form(self, request, obj=None, **kwargs):
        #Deshabilita los botones de agregar y modificar de los campos many to many genero, autor y editorial
        form = super(TrailerAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['libro_asociado'].widget.can_add_related = False
        form.base_fields['libro_asociado'].widget.can_change_related = False
        return form

class CalificacionAdmin(admin.ModelAdmin):
    id_libro = None
    def delete_view(self, request, object_id, extra_context=None):
        self.id_libro = Calificacion.objects.get(id=object_id).libro_id
        return super(CalificacionAdmin, self).delete_view(request, object_id, extra_context)

    def response_delete(self, request, obj_display, obj_id):
        return redirect('/detalle_libro/id='+str(self.id_libro))

admin.site.site_header = 'Panel de Administracion Bookflix'

#Saca los modelos que no queremos que se interactúen
admin.site.unregister(Group)


#Registra que modelos se pueden interactuar
#admin.site.register(Libro,LibroAdmin)
admin.site.register(Calificacion,CalificacionAdmin)
admin.site.register(Novedad,NovedadAdmin)
admin.site.register(Libro,LibroAdmin)
admin.site.register(Genero,GeneroAdmin)
admin.site.register(Editorial,EditorialAdmin)
admin.site.register(Autor,AutorAdmin)
admin.site.register(Trailer,TrailerAdmin)
