import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE","Bookflix.settings")
django.setup()

if __name__ == '__main__':

    from django.contrib.auth.models import User
    from modelos.models import Autor,Genero,Editorial,Suscriptor,Tarjeta,Tipo_Suscripcion,Libro,Perfil

    #-------------------- Guarda en la tabla auth_user ---------------------#
    usuario_marcos = User.objects.create_user(username=unicode('marcos123@gmail.com'),password=unicode('123'))
    usuario_cristian = User.objects.create_user(username=unicode('cristian123@gmail.com'),password=unicode('123'))
    usuario_juan = User.objects.create_user(username=unicode('juan123@gmail.com'),password=unicode('123'))

    usuario_marcos.save()
    usuario_cristian.save()
    usuario_juan.save()
    #---------------------------------------------------------------------#

    #---------------Guardamos los tipos de suscripcion--------------------#
    suscripcion_regular = Tipo_Suscripcion(
                            cantidad_maxima_perfiles = 2,
                            tipo_suscripcion = unicode('Regular')
                          )
    suscripcion_premium = Tipo_Suscripcion(
                            cantidad_maxima_perfiles = 4,
                            tipo_suscripcion = unicode('Premium')
                         )
    suscripcion_regular.save()
    suscripcion_premium.save()


    id_suscripcion_regular = Tipo_Suscripcion.objects.values('id').filter(tipo_suscripcion = 'Regular')[0]['id']
    id_suscripcion_premium = Tipo_Suscripcion.objects.values('id').filter(tipo_suscripcion ='Premium')[0]['id']
    #---------------------------------------------------------------------#

    #--------------Guardamos las tarjeta----------------------------------#
    tarjeta_1 = Tarjeta(
                    nro_tarjeta = unicode('3456789876543212'),
                    fecha_vencimiento = '2025-12-06',
                    dni_titular = unicode('12345678'),
                    empresa = unicode('apple'),
                    codigo_seguridad = '123'
                )

    tarjeta_2 = Tarjeta(
                    nro_tarjeta = unicode('2222222222222222'),
                    fecha_vencimiento = '2025-10-06',
                    dni_titular = unicode('87654321'),
                    empresa = unicode('microsoft'),
                    codigo_seguridad = unicode('234')
                )
    tarjeta_1.save()
    tarjeta_2.save()

    id_tarjeta1 = Tarjeta.objects.values('id').filter(nro_tarjeta = '3456789876543212')[0]['id']
    id_tarjeta2 = Tarjeta.objects.values('id').filter(nro_tarjeta = '2222222222222222')[0]['id']
    #---------------------------------------------------------------------#

    #-------------- Guarda en la tabla suscriptor ------------------------#
    id_usuario_marcos = User.objects.values('id').filter(username = 'marcos123@gmail.com')[0]['id']
    id_usuario_cristian = User.objects.values('id').filter(username = 'cristian123@gmail.com')[0]['id']
    id_usuario_juan = User.objects.values('id').filter(username = 'juan123@gmail.com')[0]['id']

    suscriptor_marcos = Suscriptor(
                            auth_id = id_usuario_marcos,
                            fecha_suscripcion = '2020-05-10',
                            dni = unicode('42395304'),
                            nombre = unicode('Marcos'),
                            apellido = unicode('Azcona'),
                            nro_tarjeta_id = id_tarjeta1,
                            tipo_suscripcion_id = id_suscripcion_regular,
                        )

    suscriptor_juan = Suscriptor(
                            auth_id = id_usuario_juan,
                            fecha_suscripcion = '2020-04-09',
                            dni = unicode('11111111'),
                            nombre = unicode('Juan Manuel'),
                            apellido = unicode('Fazzano'),
                            nro_tarjeta_id = id_tarjeta2,
                            tipo_suscripcion_id = id_suscripcion_premium,
                        )
    suscriptor_cristian = Suscriptor(
                            auth_id = id_usuario_cristian,
                            fecha_suscripcion = '2020-04-09',
                            dni = unicode('22222222'),
                            nombre = unicode('Cristian Gabriel'),
                            apellido = unicode('Alvarez'),
                            nro_tarjeta_id = id_tarjeta2,
                            tipo_suscripcion_id = id_suscripcion_premium,
                        )
    suscriptor_marcos.save()
    suscriptor_juan.save()
    suscriptor_cristian.save()

    #--------------------GUARDA EN LA TABLA Perfil------------------------------------#
    perfil_marcos = Perfil(
                        nombre_perfil=unicode('MarcosAzcona'),
                        auth_id = id_usuario_marcos
                    )
    perfil_cristian = Perfil(
                        nombre_perfil=unicode('CristianAlvarez'),
                        auth_id = id_usuario_cristian
                    )
    perfil_juan = Perfil(
                        nombre_perfil=unicode('JuanFazzano'),
                        auth_id = id_usuario_juan
                    )
    perfil_juan.save()
    perfil_marcos.save()
    perfil_cristian.save()
    #---------------------------------------------------------------------------------#

    #--------------------GUARDA EN LA TABLA AUTOR------------------------------------#
    autor_dardo=Autor(nombre=unicode('Dardo'))
    autor_pepe=Autor(nombre=unicode('Pepe'))
    autor_pepe.save()
    autor_dardo.save()

    id_dardo = Autor.objects.values('id').filter(nombre = 'Dardo')[0]['id']
    id_pepe = Autor.objects.values('id').filter(nombre = 'Pepe')[0]['id']


    #--------------------------GUARDA EN LA TABLA EDITORIAL--------------------------------#
    editorial_dunken=Editorial(nombre=unicode('dunken'))
    editorial_casita=Editorial(nombre=unicode('casita'))
    editorial_dunken.save()
    editorial_casita.save()

    id_dunken = Editorial.objects.values('id').filter(nombre = 'dunken')[0]['id']
    id_casita = Editorial.objects.values('id').filter(nombre = 'casita')[0]['id']



    #----------------------------GUARDA EN LA TABLA GENERO-----------------------------------------#
    genero_terror=Genero(nombre=unicode('terror'))
    genero_fantasia=Genero(nombre=unicode('fantasia'))
    genero_terror.save()
    genero_fantasia.save()
    id_terror = Genero.objects.values('id').filter(nombre = 'terror')[0]['id']
    id_fantasia = Genero.objects.values('id').filter(nombre = 'fantasia')[0]['id']


    #----------------------------GUARDA EN LA TABLA LIBRO-----------------------------------------#
    libro_harry=Libro(foto=unicode('portada1.jpeg'),titulo=unicode('harry'),ISBN=unicode('1111111111'),descripcion=unicode('una gran mago'),autor_id=id_dardo,editorial_id=id_dunken,genero_id=id_fantasia)
    libro_anabelle=Libro(foto=unicode('portada3.jpeg'),titulo=unicode('anabelle'),ISBN=unicode('2222222222222'),descripcion=unicode('la munieca maldita'),autor_id=id_pepe,editorial_id=id_casita,genero_id=id_terror)
    libro_harry.save()
    libro_anabelle.save()
