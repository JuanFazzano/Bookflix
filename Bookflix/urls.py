"""Bookflix URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from Bookflix import views
from django.conf.urls import url
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    url(r'^$', views.Vista_Visitante.as_view()),
    url(r'^admin/', admin.site.urls),
    url(r'^home_admin/',views.Home_Admin.as_view()),
    url(r'^iniciar_sesion/',views.Vista_Iniciar_Sesion.as_view()),
    url(r'^datos_suscriptor/',views.Vista_Datos_Usuario.as_view()),
    url(r'^crear_perfil/',views.Vista_Crear_Perfil.as_view()),
    url(r'^eliminar_perfil/id=(?P<id>\w+)/$', views.Vista_Eliminar_Perfil.as_view()),
    url(r'^eleccion_perfil/id=(?P<id>\w+)/$',views.eleccion_perfil),
    url(r'^registro/',views.Vista_Registro.as_view()),
    url(r'^modificar_datos_personales/',views.Vista_Modificar_Datos_Personales.as_view()),
    url(r'^cambiar_tipo_suscripcion/', views.cambiar_tipo_suscripcion, name="cambiar_suscripcion"),
    url(r'^detalle_novedad/id=(?P<id>\w+)/$',views.Vista_Detalle_Novedad.as_view()),
    url(r'^detalle_trailer/id=(?P<id>\w+)/$', views.Vista_Detalle_Trailer.as_view()),
    url(r'^listado_novedad/',views.Vista_Listado_Novedad.as_view()),
    url(r'^listado_trailer/',views.Vista_Listado_Trailer.as_view()),
    url(r'^listado_genero/',views.Vista_Listado_Genero.as_view()),
    url(r'^listado_editorial/',views.Vista_Listado_Editorial.as_view()),
    url(r'^listado_capitulo/id=(?P<id>\w+)/$',views.Vista_Listado_Capitulo.as_view()),
    url(r'^listado_autor/',views.Vista_Listado_Autor.as_view()),
    url(r'^listado_libro/',views.Vista_Listado_Libro.as_view()),
    url(r'^listado_perfiles/',views.Vista_Listado_Perfiles.as_view()),
    url(r'^carga_libro_completo/id=(?P<id>\w+)/$', views.Vista_Formulario_Libro_Completo.as_view()),
    url(r'^detalle_libro/id=(?P<id>\w+)/$',views.Vista_Detalle_libro.as_view()),
    url(r'^cargar_genero',views.Vista_Formulario_Genero.as_view()),
    url(r'^cargar_autor', views.Vista_Formulario_Autor.as_view()),
    url(r'^cargar_editorial', views.Vista_Formulario_Editorial.as_view()),
    url(r'^cargar_novedad', views.Vista_Formulario_Novedad.as_view()),
    url(r'^cargar_metadatos_libro', views.Vista_Carga_Metadatos_Libro.as_view()),
    url(r'^cargar_trailer', views.Vista_Formulario_Trailer.as_view()),
    url(r'^cargar_capitulo/id=(?P<id>\w+)/$', views.Vista_Alta_Capitulo.as_view()),
    url(r'^modificar_genero/id=(?P<id>\w+)/$', views.Vista_Formulario_Modificar_Genero.as_view()),
    url(r'^modificar_autor/id=(?P<id>\w+)/$', views.Vista_Formulario_Modificar_Autor.as_view()),
    url(r'^modificar_editorial/id=(?P<id>\w+)/$', views.Vista_Formulario_Modificar_Editorial.as_view()),
    url(r'^modificar_novedad/id=(?P<id>\w+)/$', views.Vista_Modificar_Novedad.as_view()),
    url(r'^modificar_libro/id=(?P<id>\w+)/$', views.Vista_Modificar_Metadatos_Libro.as_view()),
    url(r'^modificar_trailer/id=(?P<id>\w+)/$', views.Vista_Formulario_Modificar_Trailer.as_view()),
    url(r'^modificar_fechas_libro/id=(?P<id>\w+)/$',views.Vista_modificar_fechas_libro.as_view()),
    url(r'^logout/',views.cerrar_sesion,name="logout"),
    url(r'^marcar_como_terminado/id=(?P<id>\w+)/$', views.marcar_como_terminado, name="marcar_como_terminado"),
    url(r'^lectura_completo/id=(?P<id>\w+)/$',views.Vista_Lectura_Libro_Completo.as_view()),
    url(r'^lectura_capitulo/id=(?P<id>\w+)/$', views.Vista_Lectura_Capitulo.as_view()),
    url(r'^cambiar_contrasena/', views.Cambiar_Contraseña.as_view()),
    url(r'^historial/pagina=(?P<pagina>\w+)/$',views.Vista_Historial.as_view()),
    url(r'^buscar/', views.Buscar.as_view())

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
