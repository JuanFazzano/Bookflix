import datetime
from django import forms
from django.contrib.auth.models import User
from modelos.models import Autor,Genero,Editorial,Libro,Suscriptor


def clean_campo(clase,atributo,longitud):
    campo = clase.cleaned_data[atributo] #Si no es un numero, esto levanta excepcion.
    if campo.isdigit(): #verifica si un string tiene unicamente digitos
        if len(campo) != longitud:
            raise forms.ValidationError("Deben ingresarse {} digitos en el campo {}".format(str(longitud),atributo))
    else:
        raise forms.ValidationError(" En {} solo debe ingresarse digitos numericos".format(atributo))
    return clase.cleaned_data[atributo]

class FormularioRegistro(forms.Form):

    tipo_suscripcion=[
    ('regular','Regular(2 perfiles maximo)'),
    ('premium','Premium(4 perfiles maximo)')

    ]
    DNI = forms.CharField(max_length = 8)
    Nombre = forms.CharField(max_length = 25)
    Apellido =forms.CharField(max_length = 25)
    Email = forms.EmailField(max_length = 254)
    Contrasena = forms.CharField(widget=forms.PasswordInput,max_length = 20)
    Numero_de_tarjeta = forms.CharField(max_length = 16)
    Fecha_de_vencimiento = forms.DateField(widget = forms.SelectDateWidget(years = [x for x in range(1990,2051)]))
    DNI_titular = forms.CharField(max_length = 8)
    Empresa= forms.CharField(max_length = 7)
    Codigo_de_seguridad = forms.CharField(max_length = 3)
    Suscripcion=forms.CharField(widget=forms.Select(choices=tipo_suscripcion))

    def __init__(self,*args,**kwargs):
        super(FormularioRegistro,self).__init__(*args,**kwargs)

    def clean_Email(self):
        email = self.cleaned_data['Email']
        if (User.objects.values('username').filter(username = email).exists()):
            raise forms.ValidationError('El Email ya esta registrado en el sistema')
        return email

    def clean_DNI(self):
        campo = clean_campo(self,'DNI',8)
        if (Suscriptor.objects.values('dni').filter(dni = campo).exists()):
            raise forms.ValidationError('El DNI ya esta registrado en el sistema')
        return campo

    def clean_DNI_titular(self):
        return clean_campo(self,'DNI_titular',8)

    def clean_Codigo_de_seguridad(self):
        return clean_campo(self,'Codigo_de_seguridad',3)

    def clean_Numero_de_tarjeta(self):
        return clean_campo(self,'Numero_de_tarjeta',16)

    def clean_Fecha_de_vencimiento(self):
        fecha_vencimiento = (self.cleaned_data['Fecha_de_vencimiento'])
        fecha_hoy = ((datetime.datetime.now()).date())
        vencida = (fecha_hoy >= fecha_vencimiento)
        if vencida:
            raise forms.ValidationError('Tarjeta vencida')
        return self.cleaned_data['Fecha_de_vencimiento']

class FormularioIniciarSesion(forms.Form):
    email = forms.EmailField(max_length=254)
    clave = forms.CharField(widget=forms.PasswordInput)
