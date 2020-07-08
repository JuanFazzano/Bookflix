# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import Max
from django import template
import datetime
from django.db.models import Avg, Count, Min, Sum

#register = template.Library()

class Tarjeta(models.Model):
    nro_tarjeta = models.CharField(max_length = 16)
    fecha_vencimiento = models.DateField(null=False)
    #dni_titular = models.CharField(unique = True, max_length = 8,null=False)
    empresa = models.CharField(max_length = 254,null=False)
    codigo_seguridad = models.CharField(max_length = 3,null=False)

class Tipo_Suscripcion(models.Model):
    cantidad_maxima_perfiles = models.IntegerField(default = 0,null=False)
    tipo_suscripcion = models.CharField(unique = True, max_length = 16)

    def tiene_maximo_permitido(self,cantidad_perfiles):
        return cantidad_perfiles == self.cantidad_maxima_perfiles

class Suscriptor(models.Model):
    class Meta:
        verbose_name = 'Suscriptor'
        verbose_name_plural = 'Suscriptores'
    auth = models.OneToOneField(User,primary_key = True, on_delete = models.CASCADE)
    nro_tarjeta = models.OneToOneField(Tarjeta, null=False, on_delete=models.CASCADE)
    tipo_suscripcion = models.ForeignKey(Tipo_Suscripcion, null=False, on_delete=models.CASCADE)
    fecha_suscripcion = models.DateField(null=False)
    nombre = models.CharField(max_length = 25, blank=False, null=False)
    apellido = models.CharField(max_length = 25, blank=False, null=False)
    dni = models.CharField(unique = True, max_length = 8, null=False)

    def tiene_maximo_permitido(self):
        return self.suscripcion().tiene_maximo_permitido(self.cantidad_perfiles())

    def suscripcion(self):
        return Tipo_Suscripcion.objects.get(id=self.tipo_suscripcion_id)

    def perfiles(self):
        return Perfil.objects.filter(auth_id=self.auth_id)

    def cantidad_perfiles(self):
        return len(self.perfiles())

    def es_regular(self):
        return self.tipo_suscripcion.tipo_suscripcion == "regular"

class Autor (models.Model):
    class Meta:
        verbose_name = 'Autor'
        verbose_name_plural = 'Autores'
    nombre = models.CharField(unique = True,max_length = 25)

    def clean(self):
        if Autor.objects.filter(nombre = self.nombre).exists():
            raise ValidationError('El autor ya se encuentra registrado en el sistema')

    def __str__(self):
        return self.nombre

class Editorial (models.Model):
    class Meta:
        verbose_name = 'Editorial'
        verbose_name_plural = 'Editoriales'
    nombre = models.CharField(max_length = 35, unique=True)

    def clean(self):
        if Editorial.objects.filter(nombre = self.nombre).exists():
            raise ValidationError('La editorial ya se encuentra registrado en el sistema')

    def __str__(self):
        return self.nombre

class Genero (models.Model):
    class Meta:
        verbose_name = 'Genero'
        verbose_name_plural = 'Generos'
    nombre = models.CharField(max_length = 25, unique=True)

    def clean(self):
        if Genero.objects.filter(nombre = self.nombre).exists():
            raise ValidationError('El género ya se encuentra registrado en el sistema')

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
    esta_completo= models.BooleanField(default=0)
    fecha_lanzamiento = models.DateTimeField(null = True)
    fecha_vencimiento = models.DateTimeField(null = True)
    #esta_activo = models.BooleanField(default=1)

    def __str__(self):
        return self.titulo

    def clean(self):
        isbn = self.ISBN
        if Libro.objects.filter(titulo = self.titulo).exists():
                print('Entre')
                raise ValidationError('El titulo ya se encuentra registrado')

        if isbn.isdigit(): #verifica si un string tiene unicamente digitos
            if Libro.objects.filter(ISBN = self.ISBN).exists():
                raise ValidationError("El ISBN ya se encuentra registrado en el sistema")
            if (len(isbn) not in (10,13)):
                raise ValidationError("Deben ingresarse 10 o 13 dígitos")
        else:
            raise ValidationError(" En ISBN solo debe ingresarse digitos numericos")

    def buscar_similares(self):
        pass

    def esta_vencido(self):
        if self.fecha_vencimiento is not None:
           return self.fecha_vencimiento.date() <= datetime.datetime.today().date()
        return False

    def esta_lanzado(self):
        if self.fecha_lanzamiento is not None:
           return self.fecha_lanzamiento.date() <= datetime.datetime.today().date()
        return False

    def esta_activo(self):
        return self.esta_lanzado() and not self.esta_vencido()

    def trailers(self):
        return Trailer.objects.filter(libro_asociado_id=self.id)

    def tiene_capitulos(self):
        "Devuelve de un libro si tiene capítulos"
        try:
            "Intenta ver si está como libro completo"
            return Libro_Incompleto.objects.get(libro_id=self.id)
        except:
            return False

    def lectores(self):
        return Lee_libro.objects.filter(libro_id=self.id)

    def lectores_que_terminaron(self):
        return self.lectores().filter(terminado=True)

    def cantidad_lectores_que_terminaron(self):
        return self.lectores_que_terminaron().count()

    def cantidad_lectores_totales(self):
        return self.lectores().count()

    def promedio_puntaje(self):
        calificaciones = self.reseñas()
        print('Promedio ',calificaciones.aggregate(total=Avg('valoracion')) )
        #try:
        #    return calificaciones.aggregate(total=Sum('valoracion')) / calificaciones.count()
        #except:
            #return 0
        return calificaciones.aggregate(total=Avg('valoracion'))

    def reseñas(self):
        return Calificacion.objects.filter(libro_id=self.id).order_by('-fecha_calificacion')

class Perfil(models.Model):
    class Meta:
        unique_together = (('nombre_perfil','auth'),)
    auth = models.ForeignKey(Suscriptor, on_delete=models.CASCADE)
    nombre_perfil = models.CharField(max_length = 25)
    foto = models.FileField(blank=True, null=True)
    listado_favoritos = models.ManyToManyField(Libro)

class Calificacion(models.Model):
    class Meta:
        unique_together = (('libro', 'perfil'),)
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE)
    perfil = models.ForeignKey(Perfil,null=True,blank=True,on_delete=models.SET_NULL)
    valoracion=models.IntegerField(default=0,null=False)
    fecha_calificacion = models.DateTimeField(null=False)

    def perfil_califico(self):
        "Devuelve el perfil que hizo la calificacion"
        return Perfil.objects.get(id = self.perfil_id)

    def comentario(self):
        return Comentario.objects.get(calificacion_id = self.id)

class Comentario(models.Model):
        #class Meta:
    #    unique_together = (('fecha_hora','calificacion'),)
    calificacion = models.ForeignKey(Calificacion,unique = True,on_delete=models.CASCADE)
    texto = models.TextField(blank = False, null = False)
    spoiler = models.BooleanField(default=0)
    spoiler_admin = models.BooleanField(default=0)

class Lee_libro(models.Model):
    class Meta:
        unique_together = (('libro','perfil'),)
    perfil=models.ForeignKey(Perfil,null=True,blank=True,on_delete=models.SET_NULL)
    libro=models.ForeignKey(Libro, on_delete=models.CASCADE)
    terminado=models.NullBooleanField(null=True)
    ultimo_acceso= models.DateTimeField(null = True)

class Libro_Completo(models.Model):
    libro = models.OneToOneField(Libro,default=None, on_delete=models.CASCADE)
    archivo_pdf = models.FileField(null = False)

class Libro_Incompleto(models.Model):
    libro = models.OneToOneField(Libro,unique = True, on_delete=models.CASCADE)
    esta_completo=models.BooleanField(default = 0,null = True)

    def capitulos(self):
        return Capitulo.objects.filter(titulo_id = self.id)

    def numero_maximo_capitulo(self):
        numero_maximo=Capitulo.objects.filter(titulo=self.id).aggregate(Max('capitulo'))
        return numero_maximo['capitulo__max']
        # devuelve {'capitulo__max':599 }

class Capitulo(models.Model):
    class Meta:
        unique_together = (('capitulo','titulo'),)
    titulo = models.ForeignKey(Libro_Incompleto, on_delete=models.CASCADE)
    capitulo = models.IntegerField()
    fecha_lanzamiento = models.DateTimeField()
    fecha_vencimiento = models.DateTimeField(null=True)
    archivo_pdf = models.FileField(null = False)
    ultimo = models.BooleanField(default=0, null=True)

    def esta_vencido(self):
        if self.fecha_vencimiento is not None:
           return self.fecha_vencimiento.date() <= datetime.datetime.today().date()
        return False

    def esta_lanzado(self):
        if self.fecha_lanzamiento is not None:
           return self.fecha_lanzamiento.date() <= datetime.datetime.today().date()
        return False

class Lee_Capitulo(models.Model):
    class Meta:
        unique_together = (('capitulo','perfil'),)
    perfil=models.ForeignKey(Perfil,null=True,blank=True,on_delete=models.SET_NULL)
    capitulo=models.ForeignKey(Capitulo, on_delete=models.CASCADE)
    ultimo_acceso= models.DateTimeField(null = True)

class Novedad(models.Model):
    class Meta:
        verbose_name = 'Novedad'
        verbose_name_plural = 'Novedades'
        ordering = ['titulo']

    titulo=models.CharField(unique = True, max_length=255)
    descripcion = models.TextField(blank = True,null = True)
    foto = models.ImageField(blank = True,null = True)

    def __str__(self):
        return self.titulo

    def clean(self):
        if Novedad.objects.filter(titulo = self.titulo).exists():
            raise ValidationError('El titulo ya se encuentra registrado en el sistema')

class Trailer(models.Model):
    class Meta:
        verbose_name        = 'Trailer'
        verbose_name_plural = 'Trailers'
    titulo          = models.CharField(unique = True, max_length=255, default = None)
    descripcion     = models.TextField(null = False)
    libro_asociado  = models.ForeignKey(Libro,null = True, blank = True,on_delete = models.SET_NULL)
    pdf             = models.FileField(null = True, blank = True)
    video           = models.FileField(null = True, blank = True)

    def clean(self):
        if self.titulo is None:
            raise ValidationError('el campo titulo es obligatorio')
        print(self.descripcion,'descripcionnnn')
        if self.descripcion == '':
            raise ValidationError('el campo descripcion es obligatorio')

    def __str__(self):
        return self.titulo

