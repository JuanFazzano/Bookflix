import datetime
from django import forms
from django.contrib.auth.models import User
from modelos.models import Suscriptor,Tarjeta,Tipo_Suscripcion

def clean_campo(clase,atributo,longitud):
    campo = clase.cleaned_data[atributo] #Si no es un numero, esto levanta excepcion.
    if campo.isdigit(): #verifica si un string tiene unicamente digitos
        if len(campo) != longitud:
            raise forms.ValidationError("Deben ingresarse {} digitos en el campo {}".format(str(longitud),atributo))
    else:
        raise forms.ValidationError(" En {} solo debe ingresarse digitos numericos".format(atributo))
    return clase.cleaned_data[atributo]

class FormularioRegistro(forms.Form):
    def __init__(self,*args,**kwargs):
        super(FormularioRegistro,self).__init__(*args,**kwargs)

    tipo_suscripcion=[
        ('regular','Regular(2 perfiles maximo)'),
        ('premium','Premium(4 perfiles maximo)')
    ]

    Nombre = forms.CharField(max_length = 25)
    Apellido =forms.CharField(max_length = 25)
    Email = forms.EmailField(max_length = 254)
    Contrasena = forms.CharField(widget=forms.PasswordInput,max_length = 20)
    Numero_de_tarjeta = forms.CharField(max_length = 16)
    Fecha_de_vencimiento = forms.DateField(widget = forms.SelectDateWidget(years = [x for x in range(1990,2051)]))
    DNI_titular = forms.CharField(max_length = 8)
    Empresa= forms.CharField(max_length = 254)
    Codigo_de_seguridad = forms.CharField(max_length = 3)
    Suscripcion=forms.CharField(widget=forms.Select(choices=tipo_suscripcion))

    def clean_Email(self):
        email = self.cleaned_data['Email']
        if (User.objects.values('username').filter(username = email).exists()):
            raise forms.ValidationError('El Email ya esta registrado en el sistema')
        return email

    def clean_DNI_titular(self):
        campo = clean_campo(self,'DNI_titular',8)
        if (Tarjeta.objects.values('dni_titular').filter(dni_titular = campo).exists()):
            raise forms.ValidationError('El DNI ya esta registrado en el sistema')
        return campo

    def clean_Codigo_de_seguridad(self):
        return clean_campo(self,'Codigo_de_seguridad',3)


#    def clean_Numero_de_tarjeta(self):
#        campo=clean_campo(self,'Numero_de_tarjeta',16)
#        if Tarjeta.objects.filter(nro_tarjeta = campo).exists():
#            raise forms.ValidationError('El numero de tarjeta ya se encuentra registrado en el sistema')
#        return campo

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

class FormularioModificarDatosPersonales(forms.Form):
    def __init__(self,*args,**kwargs):
        self.datos_cambiados = {'Email': False, 'DNI': False, 'Numero_de_tarjeta': False}
        super(FormularioModificarDatosPersonales,self).__init__(*args,**kwargs)


    Email = forms.EmailField(max_length = 254,show_hidden_initial=True)
    Nombre = forms.CharField(max_length = 25,show_hidden_initial=True)
    Apellido =forms.CharField(max_length = 25,show_hidden_initial=True)
    Numero_de_tarjeta = forms.CharField(disabled = True,max_length = 16,show_hidden_initial=True)
    Fecha_de_vencimiento = forms.DateField(disabled = True,widget = forms.SelectDateWidget(years = [x for x in range(1990,2051)]),show_hidden_initial=True)
    DNI_titular = forms.CharField(disabled = True,show_hidden_initial=True)
    Empresa= forms.CharField(disabled = True,show_hidden_initial=True)
    Codigo_de_seguridad = forms.CharField(disabled = True,show_hidden_initial=True)
    Suscripcion=forms.CharField(disabled = True,show_hidden_initial=True)


    def get_datos_cambiados(self):
        return self.datos_cambiados

    def __cambio(self,valor_inicial,valor_nuevo):
        return valor_inicial != valor_nuevo

    def clean_Email(self):
        field_email = self.visible_fields()[0] #Me devuelve una instancia del EmailField --> campo Email
        valor_email_inicial = field_email.initial
        valor_email_actual = self.cleaned_data['Email']
        if  self.__cambio(valor_email_inicial,valor_email_actual):
            if (User.objects.values('username').filter(username = valor_email_actual).exists()):
                raise forms.ValidationError('El Email ya esta registrado en el sistema')
            self.datos_cambiados['Email'] = True
        else:
            self.datos_cambiados['Email'] = False
        return valor_email_actual

class FormularioCargaLibro(forms.Form):
    pdf = forms.FileField(required=False)
    fecha_de_lanzamiento = forms.DateField(widget = forms.SelectDateWidget(years = [x for x in range(1990,2051)]))
    fecha_de_vencimiento = forms.DateField(widget = forms.SelectDateWidget(years = [x for x in range(1990,2051)]))

#    def clean_DNI_titular(self):
#        field_DNI_titular = self.visible_fields()[5] #Me devuelve una instancia del CharField --> campo DNI
#        valor_dni_inicial = field_DNI_titular.initial
#        valor_dni_actual = self.cleaned_data['DNI_titular']
#        clean_campo(self,'DNI_titular',8)
#        if (Tarjeta.objects.values('dni_titular').filter(dni_titular = valor_dni_actual).exists()):
#            raise forms.ValidationError('El DNI ya esta registrado en el sistema')
#
#        if self.__cambio(valor_dni_inicial,valor_dni_actual):
#            self.datos_cambiados['DNI'] = True
#        else:
#            self.datos_cambiados['DNI'] = False
#        return valor_dni_actual

#    def clean_Codigo_de_seguridad(self):
#        return clean_campo(self,'Codigo_de_seguridad',3)

#    def clean_Numero_de_tarjeta(self):
#        field_Numero_de_tarjeta = self.visible_fields()[4] #Me devuelve una instancia del CharField --> campo Numero_de_tarjeta
#        valor_numero_inicial=field_Numero_de_tarjeta.initial
#        valor_Numero_actual=self.cleaned_data['Numero_de_tarjeta']
#        if self.__cambio(valor_numero_inicial,valor_Numero_actual):
#            clean_campo(self,'Numero_de_tarjeta',16)
#            self.datos_cambiados['Numero_de_tarjeta'] = True
#        else:
#            self.datos_cambiados['Numero_de_tarjeta'] = False
#        return valor_Numero_actual

#    def clean_Fecha_de_vencimiento(self):
#        fecha_vencimiento = (self.cleaned_data['Fecha_de_vencimiento'])
#        fecha_hoy = ((datetime.datetime.now()).date())
#        vencida = (fecha_hoy >= fecha_vencimiento)
#        if vencida:
#            raise forms.ValidationError('Tarjeta vencida')
#        return self.cleaned_data['Fecha_de_vencimiento']
