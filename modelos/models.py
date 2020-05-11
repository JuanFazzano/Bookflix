# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User

class Tarjeta(models.Model):
    nro_tarjeta = models.CharField(unique = True, max_length = 16)
    fecha_vencimiento = models.DateField(null=False)
    dni_titular = models.CharField(max_length = 8,null=False)
    empresa = models.CharField(max_length = 254,null=False)
    codigo_seguridad = models.CharField(max_length = 3,null=False)

class Tipo_Suscripcion(models.Model):
    cantidad_maxima_perfiles = models.IntegerField(default = 0,null=False)
    tipo_suscripcion = models.CharField(unique = True, max_length = 16)

class Suscriptor(models.Model):
    class Meta:
        verbose_name = 'Suscriptor'
        verbose_name_plural = 'Suscriptores'

    auth = models.OneToOneField(User,primary_key = True, on_delete = models.CASCADE)
    nro_tarjeta = models.ForeignKey(Tarjeta, null=False, on_delete=models.CASCADE)
    tipo_suscripcion = models.ForeignKey(Tipo_Suscripcion, null=False, on_delete=models.CASCADE)
    fecha_suscripcion = models.DateField(null=False)
    dni = models.CharField(max_length = 8, blank=False, null=False, unique=True)
    nombre = models.CharField(max_length = 25, blank=False, null=False)
    apellido = models.CharField(max_length = 25, blank=False, null=False)

class Autor (models.Model):
    class Meta:
        verbose_name = 'Autor'
        verbose_name_plural = 'Autores'
    nombre = models.CharField(unique = True,max_length = 25)

    def __str__(self):
        return self.nombre

class Editorial (models.Model):
    class Meta:
        verbose_name = 'Editorial'
        verbose_name_plural = 'Editoriales'
    nombre = models.CharField(max_length = 35, unique=True)

    def __str__(self):
        return self.nombre

class Genero (models.Model):
    class Meta:
        verbose_name = 'Genero'
        verbose_name_plural = 'Generos'
    nombre = models.CharField(max_length = 25, unique=True)

    def __str__(self):
        return self.nombre

class Libro(models.Model):
    class Meta:
        verbose_name = 'Libro'
        verbose_name_plural = 'Libros'

    titulo = models.CharField(max_length = 255, unique=True)
    ISBN = models.CharField(max_length = 13,unique=True)
    foto = models.FileField(blank=True, null=True)
    descripcion = models.TextField(blank=True,null=True)
    autor = models.ForeignKey(Autor,max_length=35,null=False, on_delete=models.CASCADE)
    editorial = models.ForeignKey(Editorial, max_length = 35, null = False, on_delete=models.CASCADE)
    genero = models.ForeignKey(Genero, max_length = 25, null = False, on_delete=models.CASCADE)

    def __str__(self):
        return self.titulo

class Perfil(models.Model):
    class Meta:
        unique_together = (('nombre_perfil','auth'),)
    auth = models.ForeignKey(Suscriptor, on_delete=models.CASCADE)
    nombre_perfil = models.CharField(max_length = 25)
    listado_favoritos = models.ManyToManyField(Libro)


class Calificacion(models.Model):
    class Meta:
        unique_together = (('libro','perfil'),)
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE)
    perfil =models.ForeignKey(Perfil, on_delete=models.CASCADE)
    valoracion=models.IntegerField(default=0,null=False)

class Comentario(models.Model):
    class Meta:
        unique_together = (('fecha_hora','calificacion'),)
    calificacion = models.ForeignKey(Calificacion, on_delete=models.CASCADE)
    fecha_hora = models.DateTimeField()
    texto = models.TextField(blank = False, null = False)

class Lee_libro(models.Model):
    class Meta:
        unique_together = (('libro','perfil'),)
    perfil=models.ForeignKey(Perfil, on_delete=models.CASCADE)
    libro=models.ForeignKey(Libro, on_delete=models.CASCADE)
    terminado=models.NullBooleanField(null=True)

class Libro_Completo(models.Model):
    libro = models.OneToOneField(Libro,primary_key = True, on_delete=models.CASCADE)
    fecha_lanzamiento = models.DateTimeField()
    fecha_vencimiento = models.DateTimeField(null=True)
    archivo_pdf = models.FileField(null = False)

class Libro_Incompleto(models.Model):
    libro = models.OneToOneField(Libro,primary_key = True, on_delete=models.CASCADE)

class Capitulo(models.Model):
    class Meta:
        unique_together = (('capitulo','titulo'),)
    titulo = models.ForeignKey(Libro_Incompleto, on_delete=models.CASCADE)
    capitulo = models.IntegerField()
    fecha_lanzamiento = models.DateTimeField()
    fecha_vencimiento = models.DateTimeField(null=True)
    archivo_pdf = models.FileField(null = False)

class Novedad(models.Model):
    titulo=models.CharField(unique = True, max_length=255)
    foto= models.FileField(null = True)
    link = models.TextField(null = True)

class Trailer(models.Model):
    pass

class Posee_trailer(models.Model):
    trailer = models.OneToOneField(Trailer, on_delete=models.CASCADE)
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE)
