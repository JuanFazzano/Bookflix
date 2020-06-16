import datetime
from django import forms
from django.contrib.auth.models import User
from modelos.models import *
from django.db.models import Max

def clean_campo(clase,atributo,longitud):
    campo = clase.cleaned_data[atributo] #Si no es un numero, esto levanta excepcion.
    if campo.isdigit(): #verifica si un string tiene unicamente digitos
        if len(campo) != longitud:
            raise forms.ValidationError("Deben ingresarse {} digitos en el campo {}".format(str(longitud),atributo))
    else:
        raise forms.ValidationError(" En {} solo debe ingresarse digitos numericos".format(atributo))
    return clase.cleaned_data[atributo]

class DateInput(forms.DateInput):
    input_type = 'date'

class FormularioModificarAtributos(forms.Form):
    "Este formulario permite modificar autor,genero,editorial"

    #show_hidden_initial permite mostrar el valor inicial/home/marcos/Escritorio/Bookflix/Bookflix
    nombre = forms.CharField(max_length=30,show_hidden_initial = True)

    def __init__(self,modelo,nombre_modelo,*args,**kwargs):
        self.modelo = modelo
        self.nombre_modelo = nombre_modelo
        super(FormularioModificarAtributos,self).__init__(*args,**kwargs)

    def __cambio(self,valor_inicial,valor_nuevo):
        return valor_inicial != valor_nuevo

    def clean_nombre(self):
        field_nombre = self.visible_fields()[0] #Me devuelve una instancia del CharField --> campo nombre
        valor_nombre_inicial = field_nombre.initial
        valor_nombre_actual = self.cleaned_data['nombre']
        if self.__cambio(valor_nombre_inicial,valor_nombre_actual):
            if (self.modelo.objects.filter(nombre = valor_nombre_actual).exists()):
                raise forms.ValidationError('Ya existe {} '.format(self.nombre_modelo))
        return valor_nombre_actual

class FormularioCargaAtributos(forms.Form):
    "Este formulario permite cargar autor,genero,editorial"
    nombre = forms.CharField(max_length = 30)

    def __init__(self,modelo,nombre_modelo,*args,**kwargs):
        self.modelo = modelo
        self.nombre_modelo = nombre_modelo
        super(FormularioCargaAtributos,self).__init__(*args,**kwargs)

    def clean_nombre(self):
        "Acá se hace la validación del nombre"
        if self.modelo.objects.filter(nombre = self.cleaned_data['nombre']).exists():
            raise forms.ValidationError('Ya existe {} {}'.format(self.nombre_modelo,self.cleaned_data['nombre']))
        return self.cleaned_data['nombre']

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
    DNI = forms.CharField(max_length = 8)
    Numero_de_tarjeta = forms.CharField(max_length = 16)
    Fecha_de_vencimiento = forms.DateField(widget = forms.SelectDateWidget(years = [x for x in range(1990,2051)]))
    Empresa= forms.CharField(max_length = 254)
    Codigo_de_seguridad = forms.CharField(max_length = 3)
    Suscripcion=forms.CharField(widget=forms.Select(choices=tipo_suscripcion))

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

class FormularioCambiarContraseña(forms.Form):
    def __init__(self,id_usuario, *args, **kwargs):
        self.id = id_usuario
        super(FormularioCambiarContraseña,self).__init__(*args,**kwargs)

    Contraseña_actual = forms.CharField(widget=forms.PasswordInput, max_length=20)
    Contraseña_nueva = forms.CharField(widget=forms.PasswordInput, max_length=20)

    def clean_Contraseña_actual(self):
        if not User.objects.get(id=self.id).check_password(self.cleaned_data['Contraseña_actual']):
            raise forms.ValidationError('Contraseña actual incorrecta')
        else:
            return self.cleaned_data['Contraseña_actual']

class FormularioModificarDatosPersonales(forms.Form):
    def __init__(self,*args,**kwargs):
        self.datos_cambiados = {'Email': False, 'DNI': False, 'Numero_de_tarjeta': False}
        super(FormularioModificarDatosPersonales,self).__init__(*args,**kwargs)

    Email = forms.EmailField(max_length = 254,show_hidden_initial=True)
    Nombre = forms.CharField(max_length = 25,show_hidden_initial=True)
    Apellido =forms.CharField(max_length = 25,show_hidden_initial=True)
    DNI = forms.CharField(max_length = 8, show_hidden_initial=True)
    Numero_de_tarjeta = forms.CharField(max_length = 16,show_hidden_initial=True)
    Fecha_de_vencimiento = forms.DateField(widget = forms.SelectDateWidget(years = [x for x in range(1990,2051)]),show_hidden_initial=True)
    Empresa= forms.CharField(show_hidden_initial=True)
    Codigo_de_seguridad = forms.CharField(max_length = 3,show_hidden_initial=True)
    Suscripcion=forms.CharField(disabled = True,show_hidden_initial=True)


    def get_datos_cambiados(self):
        return self.datos_cambiados

    def __cambio(self,valor_inicial,valor_nuevo):
        return valor_inicial != valor_nuevo

    def clean_Fecha_de_vencimiento(self):
        field_fecha_vencimiento = self.visible_fields()[5]
        valor_fecha_inicial = field_fecha_vencimiento.initial
        valor_fecha_actual = self.cleaned_data['Fecha_de_vencimiento']
        if valor_fecha_actual < datetime.date.today():
            raise forms.ValidationError('La fecha de vencimiento no puede ser inferior a la fecha del dia de hoy')
        if (self.__cambio(valor_fecha_inicial,valor_fecha_actual) and (valor_fecha_actual < valor_fecha_inicial)):
            raise forms.ValidationError('La fecha de vencimiento no puede ser inferior a la ya ingresada')
        return valor_fecha_actual

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

    def clean_DNI(self):
        field_DNI = self.visible_fields()[3] #Me devuelve una instancia del CharField --> campo DNI
        valor_dni_inicial = field_DNI.initial
        valor_dni_actual = self.cleaned_data['DNI']
        clean_campo(self,'DNI',8)
        if (self.__cambio(valor_dni_inicial,valor_dni_actual)):
            if (Suscriptor.objects.values('dni').filter(dni = valor_dni_actual).exists()):
               raise forms.ValidationError('El DNI ya esta registrado en el sistema')
            self.datos_cambiados['DNI'] = True
        else:
            self.datos_cambiados['DNI'] = False

        return valor_dni_actual

    def clean_Codigo_de_seguridad(self):
        return clean_campo(self,'Codigo_de_seguridad',3)

    def clean_Numero_de_tarjeta(self):
        return clean_campo(self,'Numero_de_tarjeta',16)

class FormularioCargaFechas(forms.Form):

    def __init__(self,lanzamiento,vencimiento,*args,**kwargs):
        super(FormularioCargaFechas, self).__init__(*args, **kwargs)
        self.fecha_vencimiento_inicial=vencimiento
        self.fecha_lanzamiento_inicial = lanzamiento
        self.fields['fecha_de_lanzamiento'] =forms.DateField(widget=forms.DateInput(attrs={'type':'date','value': lanzamiento}))
        self.fields['fecha_de_vencimiento'] =forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'value': vencimiento}))
    '''fecha_de_lanzamiento = forms.DateField(widget = forms.SelectDateWidget(years = [x for x in range(1990,2051)]),show_hidden_initial=True)
    fecha_de_vencimiento = forms.DateField(widget = forms.SelectDateWidget(years = [x for x in range(1990,2051)]),show_hidden_initial=True,required=False)
    '''
    def clean_fecha_de_lanzamiento(self):
        print('la fecha incial mandada es: ', self.fecha_lanzamiento_inicial)
        fecha_de_lanzamiento1 = self.cleaned_data['fecha_de_lanzamiento']
        if( self.fecha_lanzamiento_inicial != fecha_de_lanzamiento1):
            if(fecha_de_lanzamiento1 < datetime.date.today()):
                print('tire alto error')
                raise forms.ValidationError('La fecha de lanzamiento no puede ser anterior a la fecha de hoy')
            return fecha_de_lanzamiento1
        return  self.fecha_lanzamiento_inicial

    def clean_fecha_de_vencimiento(self):
        fecha_de_vencimiento1 =None
        print(self.cleaned_data)
        if 'fecha_de_lanzamiento' in self.cleaned_data.keys():
            fecha_de_lanzamiento1= self.cleaned_data['fecha_de_lanzamiento']
            fecha_de_vencimiento1= self.cleaned_data['fecha_de_vencimiento']
            if((fecha_de_vencimiento1 is not None)and(fecha_de_lanzamiento1 > fecha_de_vencimiento1)):
                raise forms.ValidationError('La fecha de lanzamiento no puede ser posterior a la fecha de vencimiento')
        return fecha_de_vencimiento1

class FormularioCargaLibro(forms.Form):
    fecha_de_lanzamiento = forms.DateField(widget=forms.DateInput(attrs={'type':'date','value':datetime.date.today()}))
    fecha_de_vencimiento = forms.DateField(widget=DateInput,required=False)
    pdf = forms.FileField(required=True)

    def clean_fecha_de_lanzamiento(self):
        fecha_de_lanzamiento1 = self.cleaned_data['fecha_de_lanzamiento']
        if(fecha_de_lanzamiento1 < datetime.date.today()):
            raise forms.ValidationError('La fecha de lanzamiento no puede ser anterior a la fecha de hoy')
        return fecha_de_lanzamiento1

    def clean_fecha_de_vencimiento(self):
        fecha_de_vencimiento1 =None
        print(self.cleaned_data)
        if 'fecha_de_lanzamiento' in self.cleaned_data.keys():
            fecha_de_lanzamiento1= self.cleaned_data['fecha_de_lanzamiento']
            fecha_de_vencimiento1= self.cleaned_data['fecha_de_vencimiento']
            if((fecha_de_vencimiento1 is not None)and(fecha_de_lanzamiento1 > fecha_de_vencimiento1)):
                raise forms.ValidationError('La fecha de lanzamiento no puede ser posterior a la fecha de vencimiento')
        return fecha_de_vencimiento1

class FormularioNovedad(forms.Form):
    titulo = forms.CharField(max_length = 255,show_hidden_initial = True)
    descripcion = forms.CharField(widget=forms.Textarea,required=False, show_hidden_initial = True)
    foto = forms.FileField(required=False, show_hidden_initial = True)

    def clean_titulo(self):
        pass

class FormularioCargaNovedad(FormularioNovedad):
    limpiar_foto = forms.BooleanField(required=False,widget=forms.CheckboxInput)

    def clean_titulo(self):
        print('ENTRE')
        if Novedad.objects.filter(titulo = self.cleaned_data['titulo']).exists():
            raise forms.ValidationError('Ya exista la novedad con ese titulo')
        return self.cleaned_data['titulo']

    def clean_limpiar_foto(self):
        if self.cleaned_data['limpiar_foto']:
            #Si pide limpiar la foto, en el diccionario guardo None para que en la BD ponga none en el campo foto
            self.cleaned_data['foto'] = None
        return self.cleaned_data['limpiar_foto']

class FormularioModificarNovedad(FormularioNovedad):
    def __cambio(self,valor_inicial,valor_nuevo):
        return valor_inicial != valor_nuevo

    def clean_titulo(self):
        field_titulo = self.visible_fields()[0]  # Me devuelve una instancia del Charfield --> campo titulo
        valor_titulo_inicial = field_titulo.initial
        valor_titulo_actual = self.cleaned_data['titulo']
        print(Novedad.objects.filter(titulo = valor_titulo_actual).exists())
        if self.__cambio(valor_titulo_inicial, valor_titulo_actual):
            if (Novedad.objects.filter(titulo = valor_titulo_actual).exists()):
                print('HOLA entre aca papa ')
                raise forms.ValidationError('El titulo ya esta registrado en el sistema')
        return valor_titulo_actual

class FormularioCargaDeMetadatosLibro(forms.Form):
    def __init__(self,*args,**kwargs):
        super(FormularioCargaDeMetadatosLibro, self).__init__(*args, **kwargs)
        self.fields['autor']=forms.CharField(widget=forms.Select(choices= self.obtener_objetos(Autor)),required=True)
        self.fields['editorial']=forms.CharField(widget=forms.Select(choices= self.obtener_objetos(Editorial)),required=True)
        self.fields['genero']=forms.CharField(widget=forms.Select(choices= self.obtener_objetos(Genero)),required=True)


    def obtener_objetos(self,modelo):
        print('entre')
        todos_los_objetos = modelo.objects.all()
        print(todos_los_objetos)
        lista_a_retornar = list()
        for i in range(0, len(todos_los_objetos)):
            lista_a_retornar.append(((todos_los_objetos[i]).id, (todos_los_objetos[i]).nombre))
            print(lista_a_retornar)
        return lista_a_retornar

    titulo= forms.CharField(max_length=40,required=True,show_hidden_initial = True)
    ISBN = forms.CharField(max_length=13,required=True,show_hidden_initial = True)
    imagen =forms.FileField(required=False,show_hidden_initial = True)
    descripcion= forms.CharField(widget=forms.Textarea, required=False,show_hidden_initial = True)

    def clean_titulo(self):
        titulo = self.cleaned_data['titulo']
        if Libro.objects.filter(titulo=titulo).exists():
            raise forms.ValidationError('El titulo ya se encuentra registrado')
        return titulo

    def clean_ISBN(self):
        isbn = self.cleaned_data['ISBN']
        if isbn.isdigit(): #verifica si un string tiene unicamente digitos
            if Libro.objects.filter(ISBN = isbn).exists():
                raise forms.ValidationError("El ISBN ya se encuentra registrado en el sistema")
            if (len(isbn) not in (10,13)):
                raise forms.ValidationError("Deben ingresarse 10 o 13 dígitos")
        else:
            raise forms.ValidationError(" En ISBN solo debe ingresarse digitos numericos")
        return isbn

class Formulario_modificar_metadatos_libro(FormularioCargaDeMetadatosLibro):
    def clean_limpiar_foto(self):
        if self.cleaned_data['limpiar_foto']:
            self.cleaned_data['foto'] = None
        return self.cleaned_data['limpiar_foto']

    def __cambio(self,valor_inicial,valor_nuevo):
        return valor_inicial != valor_nuevo

    def clean_titulo(self):
        field_titulo = self.visible_fields()[0]  # Me devuelve una instancia del Charfield --> campo titulo
        valor_titulo_inicial = field_titulo.initial
        valor_titulo_actual = self.cleaned_data['titulo']
        if self.__cambio(valor_titulo_inicial, valor_titulo_actual):
            if (Libro.objects.filter(titulo = valor_titulo_actual).exists()):
                print('HOLA entre aca papa ')
                self.fields['titulo'].label = 'titulo anteriror'
                raise forms.ValidationError('El titulo ya esta registrado en el sistema')
        return valor_titulo_actual

    def clean_ISBN(self):
        field_ISBN = self.visible_fields()[1]  # Me devuelve una instancia del Charfield --> campo titulo
        valor_ISBN_inicial = field_ISBN.initial
        valor_ISBN_actual = self.cleaned_data['ISBN']
        if self.__cambio(valor_ISBN_inicial, valor_ISBN_actual):
            if (Libro.objects.filter(ISBN = valor_ISBN_actual).exists()):
                print('HOLA entre aca papa ')
                raise forms.ValidationError('El ISBN ya esta registrado en el sistema')
        return valor_ISBN_actual

class FormularioTrailer(forms.Form):
    def obtener_libros(self):
        libros = Libro.objects.all()
        lista_libros = list()
        for i in range(0, len(libros)):
            # Arega una tupla (id_libro, titulo_libro)
            lista_libros.append(((libros[i]).id, (libros[i]).titulo))
        lista_libros.insert(0, (None, ''))
        return lista_libros

    def __init__(self,*args,**kwargs):
        super(FormularioTrailer, self).__init__(*args,**kwargs)
        self.fields['libro']=forms.CharField(widget=forms.Select(choices= self.obtener_libros()),required = False)



    titulo = forms.CharField(max_length=255,show_hidden_initial = True)
    descripcion = forms.CharField(widget = forms.Textarea,show_hidden_initial = True)
    pdf = forms.FileField(required = False,show_hidden_initial = True)
    video = forms.FileField(required = False,show_hidden_initial = True)

    def clean_titulo(self):
        pass

class FormularioCargaTrailer(FormularioTrailer):
    limpiar_pdf = forms.BooleanField(required=False,widget=forms.CheckboxInput)
    limpiar_video = forms.BooleanField(required=False,widget=forms.CheckboxInput)

    def clean_titulo(self):
        if Trailer.objects.filter(titulo = self.cleaned_data['titulo']).exists():
            raise forms.ValidationError('El titulo ya existe')
        return self.cleaned_data['titulo']

    def clean_limpiar_checkbox(self,atributo,campo_bd):
        if self.cleaned_data[atributo]:
            #Si pide limpiar la foto, en el diccionario guardo None para que en la BD ponga none en el campo foto
            self.cleaned_data[campo_bd] = None
        return self.cleaned_data[atributo]

    def clean_limpiar_pdf(self):
        self.clean_limpiar_checkbox('limpiar_pdf','pdf')
        return self.cleaned_data['limpiar_pdf']

    def clean_limpiar_video(self):
        self.clean_limpiar_checkbox('limpiar_video','video')
        return self.cleaned_data['limpiar_video']

class FormularioModificarTrailer(FormularioTrailer):
    def __cambio(self, valor_inicial, valor_nuevo):
        return valor_inicial != valor_nuevo

    def clean_titulo(self):
        field_titulo = self.visible_fields()[0]  # Me devuelve una instancia del Charfield --> campo titulo
        valor_titulo_inicial = field_titulo.initial
        valor_titulo_actual = self.cleaned_data['titulo']
        print(valor_titulo_actual,valor_titulo_inicial)
        print(self.__cambio(valor_titulo_inicial,valor_titulo_actual))
        if self.__cambio(valor_titulo_inicial, valor_titulo_actual):
            if (Trailer.objects.filter(titulo=valor_titulo_actual).exists()):
                raise forms.ValidationError('El titulo ya esta en el sistema')
        return valor_titulo_actual

class FormularioCapitulo(forms.Form):
    def __init__(self,id = None,*args,**kwargs):
        super(FormularioCapitulo,self).__init__(*args,**kwargs)
        self.id_libro = id
        self.fields['numero_capitulo'] = forms.IntegerField()
        self.fields['archivo_pdf'] = forms.FileField()
        self.fields['fecha_de_lanzamiento'] =  forms.DateField(widget=forms.DateInput(attrs={'type':'date','value':datetime.date.today()}))
        self.fields['fecha_de_vencimiento'] = forms.DateField(widget=DateInput,required=False)
        self.fields['ultimo_capitulo'] = forms.BooleanField(required=False,widget=forms.CheckboxInput)


    def clean_fecha_de_lanzamiento(self):
        fecha_de_lanzamiento1 = self.cleaned_data['fecha_de_lanzamiento']
        if(fecha_de_lanzamiento1 < datetime.date.today()):
            raise forms.ValidationError('La fecha de lanzamiento no puede ser anterior a la fecha de hoy')
        return fecha_de_lanzamiento1

    def clean_fecha_de_vencimiento(self):
        fecha_de_vencimiento1 =None
        if 'fecha_de_lanzamiento' in self.cleaned_data.keys():
            fecha_de_lanzamiento1= self.cleaned_data['fecha_de_lanzamiento']
            fecha_de_vencimiento1= self.cleaned_data['fecha_de_vencimiento']
            if((fecha_de_vencimiento1 is not None)and(fecha_de_lanzamiento1 > fecha_de_vencimiento1)):
                raise forms.ValidationError('La fecha de vencimiento no puede ser inferior a la fecha de lanzamiento')
        return fecha_de_vencimiento1

    def clean_numero_capitulo(self):
        "Checkea que no exista el capítulo para el mismo libro"
        capitulos_libro = Capitulo.objects.filter(titulo_id = Libro_Incompleto.objects.get(libro_id=self.id_libro).id).values('capitulo')
        existe_capitulo = capitulos_libro.filter(capitulo = self.cleaned_data['numero_capitulo']).exists()
        if existe_capitulo:
            raise forms.ValidationError('Ya existe el capitulo para ese libro')
        return self.cleaned_data['numero_capitulo']
#
#
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
