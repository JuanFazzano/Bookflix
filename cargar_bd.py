import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE","Bookflix.settings")
django.setup()

if __name__ == '__main__':

    from django.contrib.auth.models import User
    from modelos.models import Autor,Genero,Editorial,Suscriptor,Tarjeta,Tipo_Suscripcion,Libro,Perfil

    #-------------------- Guarda en la tabla auth_user ---------------------#
    usuario_marcos = User.objects.create_user(username= 'marcos123@gmail.com',password='123')
    usuario_cristian = User.objects.create_user(username='cristian123@gmail.com',password='123')
    usuario_juan = User.objects.create_user(username='juan123@gmail.com',password='123')

    usuario_marcos.save()
    usuario_cristian.save()
    usuario_juan.save()
    #---------------------------------------------------------------------#

    #---------------Guardamos los tipos de suscripcion--------------------#
    suscripcion_regular = Tipo_Suscripcion(
                            cantidad_maxima_perfiles = 2,
                            tipo_suscripcion = 'Regular'
                          )
    suscripcion_premium = Tipo_Suscripcion(
                            cantidad_maxima_perfiles = 4,
                            tipo_suscripcion = 'Premium'
                         )
    suscripcion_regular.save()
    suscripcion_premium.save()


    id_suscripcion_regular = Tipo_Suscripcion.objects.values('id').filter(tipo_suscripcion = 'Regular')[0]['id']
    id_suscripcion_premium = Tipo_Suscripcion.objects.values('id').filter(tipo_suscripcion ='Premium')[0]['id']
    #---------------------------------------------------------------------#

    #--------------Guardamos las tarjeta----------------------------------#
    tarjeta_1 = Tarjeta(
                    nro_tarjeta = '3456789876543212',
                    fecha_vencimiento = '2025-12-06',
                    dni_titular = '12345678',
                    empresa = 'apple',
                    codigo_seguridad = '123'
                )

    tarjeta_2 = Tarjeta(
                    nro_tarjeta = '2222222222222222',
                    fecha_vencimiento = '2025-10-06',
                    dni_titular = '87654321',
                    empresa = 'microsoft',
                    codigo_seguridad = '234'
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
                            dni = '42395304',
                            nombre = 'Marcos',
                            apellido = 'Azcona',
                            nro_tarjeta_id = id_tarjeta1,
                            tipo_suscripcion_id = id_suscripcion_regular,
                        )

    suscriptor_juan = Suscriptor(
                            auth_id = id_usuario_juan,
                            fecha_suscripcion = '2020-04-09',
                            dni = '11111111',
                            nombre = 'Juan Manuel',
                            apellido = 'Fazzano',
                            nro_tarjeta_id = id_tarjeta2,
                            tipo_suscripcion_id = id_suscripcion_premium,
                        )
    suscriptor_cristian = Suscriptor(
                            auth_id = id_usuario_cristian,
                            fecha_suscripcion = '2020-04-09',
                            dni = '22222222',
                            nombre = 'Cristian Gabriel',
                            apellido = 'Alvarez',
                            nro_tarjeta_id = id_tarjeta2,
                            tipo_suscripcion_id = id_suscripcion_premium,
                        )
    suscriptor_marcos.save()
    suscriptor_juan.save()
    suscriptor_cristian.save()

    #--------------------GUARDA EN LA TABLA Perfil------------------------------------#
    perfil_marcos = Perfil(
                        nombre_perfil='MarcosAzcona',
                        auth_id = id_usuario_marcos
                    )
    perfil_cristian = Perfil(
                        nombre_perfil=unicode'CristianAlvarez',
                        auth_id = id_usuario_cristian
                    )
    perfil_juan = Perfil(
                        nombre_perfil=unicode'JuanFazzano',
                        auth_id = id_usuario_juan
                    )
    perfil_juan.save()
    perfil_marcos.save()
    perfil_cristian.save()
    #---------------------------------------------------------------------------------#

    #--------------------GUARDA EN LA TABLA AUTOR------------------------------------#
    autor_dardo=Autor(nombre='Dardo')
    autor_pepe=Autor(nombre='Pepe')
    autor_pepe.save()
    autor_dardo.save()

    id_dardo = Autor.objects.values('id').filter(nombre = 'Dardo')[0]['id']
    id_pepe = Autor.objects.values('id').filter(nombre = 'Pepe')[0]['id']


    #--------------------------GUARDA EN LA TABLA EDITORIAL--------------------------------#
    editorial_dunken=Editorial(nombre='dunken')
    editorial_casita=Editorial(nombre='casita')
    editorial_dunken.save()
    editorial_casita.save()

    id_dunken = Editorial.objects.values('id').filter(nombre = 'dunken')[0]['id']
    id_casita = Editorial.objects.values('id').filter(nombre = 'casita')[0]['id']



    #----------------------------GUARDA EN LA TABLA GENERO-----------------------------------------#
    genero_terror=Genero(nombre='terror')
    genero_fantasia=Genero(nombre='fantasia')
    genero_terror.save()
    genero_fantasia.save()
    id_terror = Genero.objects.values('id').filter(nombre = 'terror')[0]['id']
    id_fantasia = Genero.objects.values('id').filter(nombre = 'fantasia')[0]['id']


    #----------------------------GUARDA EN LA TABLA LIBRO-----------------------------------------#
    libro_harry=Libro(foto='portada1.jpeg',titulo='harry',ISBN='1111111111',descripcion='una gran mago',autor_id=id_dardo,editorial_id=id_dunken,genero_id=id_fantasia)
    libro_anabelle=Libro(foto='portada3.jpeg',titulo='anabelle',ISBN='2222222222222',descripcion='la munieca maldita',autor_id=id_pepe,editorial_id=id_casita,genero_id=id_terror)
    libro_harry.save()
    libro_anabelle.save()
