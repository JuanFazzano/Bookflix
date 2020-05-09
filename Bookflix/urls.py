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
    url(r'^admin/', admin.site.urls),
    url(r'^carga_editorial/',views.Vista_Carga_Editorial.as_view()),
    url(r'^carga_genero/',views.Vista_Carga_Genero.as_view()),
    url(r'^carga_autor/',views.Vista_Carga_Autor.as_view()),
    url(r'^iniciar_sesion/',views.Vista_Iniciar_Sesion.as_view()),
    url(r'^registro/',views.Vista_Registro.as_view()),
    url(r'^prueba/id=(?P<id>\w+)/$',views.Prueba.as_view()),
    url(r'^datos_suscriptor/id=(?P<id>\w+)/$',views.Vista_Datos_Usuario.as_view()),
    url(r'^carga_libro',views.Vista_Carga_Libro.as_view()),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
