import datetime
from django import forms

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

    def clean_campo(self,atributo,longitud):
        campo = self.cleaned_data[atributo] #Si no es un numero, esto levanta excepcion.
        if campo.isdigit(): #verifica si un string tiene unicamente digitos
            if len(campo) != longitud:
                raise forms.ValidationError("Deben ingresarse {} digitos en el campo {}".format(str(longitud),atributo))
        else:
            raise forms.ValidationError(" {} Debe ingresarse un campo numerico".format(atributo))
        return self.cleaned_data[atributo]

    def clean_DNI(self):
        return self.clean_campo('DNI',8)

    def clean_DNI_titular(self):
        return self.clean_campo('DNI_titular',8)

    def clean_Codigo_de_seguridad(self):
        return self.clean_campo('Codigo_de_seguridad',3)

    def clean_Numero_de_tarjeta(self):
        return self.clean_campo('Numero_de_tarjeta',16)

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

class FormularioAtributosLibro(forms.Form):
    nombre = forms.CharField(max_length = 25)




