# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User


#ALTER TABLE modelos_perfil DROP PRIMARY KEY, ADD PRIMARY KEY(email_id,nombre_perfil);

# Create your models here.
class Usuario(models.Model):
    auth = models.OneToOneField(User,unique = True)
    clave = models.CharField(max_length = 20, blank = False,null=False)
    email = models.EmailField(primary_key = True,max_length = 254)

class Tarjeta(models.Model):
    fecha_vencimiento = models.DateField(null=False)
    dni_titular = models.CharField(max_length = 8,null=False)
    empresa = models.CharField(max_length = 254,null=False)
    codigo_seguridad = models.CharField(max_length = 3,null=False)
    nro_tarjeta = models.CharField(primary_key = True, max_length = 18)

class Tipo_Suscripcion(models.Model):
    cantidad_maxima_perfiles = models.IntegerField(default = 0,null=False)
    tipo_suscripcion = models.CharField(primary_key = True, max_length = 16)


class Administrador(models.Model):
    email = models.OneToOneField(Usuario,primary_key = True,on_delete=models.CASCADE)

class Suscriptor(models.Model):
    email = models.OneToOneField(Usuario,primary_key = True, on_delete=models.CASCADE)
    nro_tarjeta = models.ForeignKey(Tarjeta, null=False, on_delete=models.CASCADE)
    tipo_suscripcion = models.ForeignKey(Tipo_Suscripcion, null=False, on_delete=models.CASCADE)
    fecha_suscripcion = models.DateField(null=False)
    dni = models.CharField(max_length = 8, blank=False, null=False, unique=True)
    nombre = models.CharField(max_length = 25, blank=False, null=False)
    apellido = models.CharField(max_length = 25, blank=False, null=False)


class Perfil(models.Model):
    class Meta:
        unique_together = (('nombre_perfil','email'),)
    email = models.ForeignKey(Suscriptor, on_delete=models.CASCADE)
    nombre_perfil = models.CharField(max_length = 25)

class Autor (models.Model):
    nombre = models.CharField(primary_key = True,max_length = 25)

class Editorial (models.Model):
    nombre = models.CharField(max_length = 35, primary_key=True)

class Genero (models.Model):
    nombre = models.CharField(max_length = 25, primary_key=True)

class Libro(models.Model):
    titulo = models.CharField(max_length = 255, primary_key=True)
    ISBN = models.CharField(max_length = 13, unique=True, blank=False, null=False)
    foto = models.CharField(max_length = 255, blank=True, null=True)
    descripcion = models.TextField(blank=True)
    autor = models.ForeignKey(Autor,max_length=35,null=False,blank=False, on_delete=models.CASCADE)
    editorial = models.ForeignKey(Editorial, max_length = 35, null = False, blank = False, on_delete=models.CASCADE)
    genero = models.ForeignKey(Genero, max_length = 25, null = False, blank=False, on_delete=models.CASCADE)
    listado_favoritos = models.ManyToManyField(Perfil)

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
    titulo = models.OneToOneField(Libro,primary_key = True, on_delete=models.CASCADE)
    fecha_lanzamiento = models.DateTimeField()
    fecha_vencimiento = models.DateTimeField(null=True)
    archivo_pdf = models.TextField(null = False)

class Libro_Incompleto(models.Model):
    titulo = models.OneToOneField(Libro,primary_key = True, on_delete=models.CASCADE)

class Capitulo(models.Model):
    class Meta:
        unique_together = (('capitulo','titulo'),)
    titulo = models.ForeignKey(Libro_Incompleto, on_delete=models.CASCADE)
    capitulo = models.IntegerField()
    fecha_lanzamiento = models.DateTimeField()
    fecha_vencimiento = models.DateTimeField(null=True)
    archivo_pdf = models.TextField(null = False)

class Novedad(models.Model):
    titulo=models.TextField(null=False)
    foto= models.TextField(null = True)
    audio= models.TextField(null = True)
    video= models.TextField(null = True)
    texto= models.TextField(null = True)

class Trailer(models.Model):
    pass

class Posee_trailer(models.Model):
    trailer = models.OneToOneField(Trailer, on_delete=models.CASCADE)
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE)