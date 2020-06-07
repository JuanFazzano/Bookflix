import datetime
from django.contrib.auth.models     import User
from django.views                   import View
from django.core.paginator          import Paginator
from django.views.decorators.csrf   import csrf_exempt
from django.http                    import HttpResponse
from django.shortcuts               import render,redirect
from django.contrib.auth            import authenticate,login, logout
from django.core.files.storage      import FileSystemStorage
from django.http                    import HttpResponseRedirect
from forms.forms                    import FormularioIniciarSesion,FormularioRegistro,FormularioModificarDatosPersonales,FormularioCargaLibro
from modelos.models                 import Libro_Completo,Autor,Genero,Editorial,Suscriptor,Tarjeta,Tipo_Suscripcion,Trailer,Libro,Perfil,Novedad

def listado_libros_activos(request,limit=None):
    libros = Libro_Completo.objects.exclude(fecha_vencimiento = None)
    libros = Libro_Completo.objects.filter(fecha_vencimiento__gte = datetime.datetime.now())
    if limit is not None:
        libros = libros[:limit]
    #tuplas = Trailer.objects.filter(id = 3)
    return paginar(request,libros,10)

def cerrar_sesion(request):
    #Cierra la sesion del usuario, y lo redireccion al /
    logout(request)
    return HttpResponseRedirect('/')

class Estrategia:
    def __init__(self,estado,formulario_nuevo,valores_iniciales):
        #Estado es un boolean que indica si cambio o no
        self.estado = estado
        self.formulario = formulario_nuevo
        self.valores_iniciales = valores_iniciales

class Estrategia_Email(Estrategia):
    def validar(self):
        if self.estado:
            #Como cambio, actualizamos la BD
            auth_usuario = User.objects.get(username = self.valores_iniciales['Email'])
            auth_usuario.username = str(self.formulario.cleaned_data['Email'])
            auth_usuario.save()

class Estrategia_Numero_de_tarjeta(Estrategia):
    def __init__(self,auth_id,formulario_nuevo,estado=None,valores_iniciales=None):
        self.auth_id = auth_id
        super(Estrategia_Numero_de_tarjeta,self).__init__(estado,formulario_nuevo,valores_iniciales)

    def __cargar_tarjeta(self):
        "Este metodo carga la tarjeta en caso de no existir"
        #if not Tarjeta.objects.filter(nro_tarjeta = numero_tarjeta).exists():
        #Como no existe la tarjeta, la cargamos en la Base de datos
        empresa= self.formulario.cleaned_data['Empresa']
        numero_tarjeta = self.formulario.cleaned_data['Numero_de_tarjeta']
        DNI_titular=self.formulario.cleaned_data['DNI_titular']
        fecha_de_vencimiento= self.formulario.cleaned_data['Fecha_de_vencimiento']
        Codigo_de_seguridad= self.formulario.cleaned_data['Codigo_de_seguridad']
        tarjeta = Tarjeta(nro_tarjeta = numero_tarjeta,
                          codigo_seguridad = Codigo_de_seguridad,
                          empresa = empresa,
                          fecha_vencimiento = fecha_de_vencimiento,
                          dni_titular = DNI_titular
                          )
        tarjeta.save()

    def cargar_tarjeta(self):
        "Este metodo carga la tarjeta en caso de no existir"
        numero_tarjeta = self.formulario.cleaned_data['Numero_de_tarjeta']

        #Como no existe la tarjeta, la cargamos en la Base de datos
        empresa= self.formulario.cleaned_data['Empresa']
        DNI_titular=self.formulario.cleaned_data['DNI_titular']
        fecha_de_vencimiento= self.formulario.cleaned_data['Fecha_de_vencimiento']
        Codigo_de_seguridad= self.formulario.cleaned_data['Codigo_de_seguridad']
        tarjeta = Tarjeta(nro_tarjeta = numero_tarjeta,
                          codigo_seguridad = Codigo_de_seguridad,
                          empresa = empresa,
                          fecha_vencimiento = fecha_de_vencimiento,
                          dni_titular = DNI_titular
                          )
        tarjeta.save()

    def validar(self):
        if self.estado:
            self.cargar_tarjeta()
            suscriptor = Suscriptor.objects.get(auth_id = self.auth_id)
            id_tarjeta = (Tarjeta.objects.values('id').filter(nro_tarjeta = self.formulario.cleaned_data['Numero_de_tarjeta'])[0])['id']
            suscriptor.nro_tarjeta_id = id_tarjeta
            suscriptor.save()
        tarjeta=Tarjeta.objects.get(nro_tarjeta = self.formulario.cleaned_data['Numero_de_tarjeta'])
        tarjeta.codigo_seguridad = self.formulario.cleaned_data['Codigo_de_seguridad']
        tarjeta.fecha_vencimiento = self.formulario.cleaned_data['Fecha_de_vencimiento']
        tarjeta.empresa = self.formulario.cleaned_data['Empresa']
        tarjeta.save()

class Vista_Registro(View):
    def __init__(self,*args,**kwargs):
        self.contexto = dict()
        self.url = '/iniciar_sesion/'
        super(Vista_Registro,self).__init__(*args,**kwargs)

    def __cargar_tarjeta(self,formulario):
        "Este metodo carga la tarjeta en caso de no existir"
        numero_tarjeta=  formulario.cleaned_data['Numero_de_tarjeta']
        if not Tarjeta.objects.filter(nro_tarjeta = numero_tarjeta).exists():
            #Como no existe la tarjeta, la cargamos en la Base de datos
            empresa= formulario.cleaned_data['Empresa']
            DNI_titular=  formulario.cleaned_data['DNI_titular']
            fecha_de_vencimiento= formulario.cleaned_data['Fecha_de_vencimiento']
            Codigo_de_seguridad= formulario.cleaned_data['Codigo_de_seguridad']
            tarjeta = Tarjeta(nro_tarjeta = numero_tarjeta,
                              codigo_seguridad = Codigo_de_seguridad,
                              empresa = empresa,
                              fecha_vencimiento = fecha_de_vencimiento,
                              dni_titular = DNI_titular
                              )
            tarjeta.save()

    def __cargar_usuario_suscriptor(self,formulario):
        """
            Carga los datos del suscriptor en la tabla modelos_suscriptor, modelos_usuario y auth_user
        """
        email = formulario.cleaned_data['Email']
        dni_titular = formulario.cleaned_data['DNI_titular']
        numero_tarjeta = formulario.cleaned_data['Numero_de_tarjeta']
        contrasena = formulario.cleaned_data['Contrasena']
        apellido = formulario.cleaned_data['Apellido']
        nombre = formulario.cleaned_data['Nombre']
        suscripcion = formulario.cleaned_data['Suscripcion']

        #el auth_id que se pasa por parámetro no se usa. Pusimos 0 para que no se rompa. TODO sacarlo y poser el parámetro como opcional
        estrategia_numero_de_tarjeta = Estrategia_Numero_de_tarjeta(auth_id = 0,formulario_nuevo = formulario)
        estrategia_numero_de_tarjeta.cargar_tarjeta()

        #Cargamos el modelos User de auth_user
        model_usuario = User.objects.create_user(username = email, password=contrasena ) #Se guarda en la tabla auth_user
        model_usuario.save()

        #Tomamos las Claves foraneas
        auth_id = User.objects.values('id').get(username=email)['id']
        id_tarjeta = Tarjeta.objects.values('id').get(dni_titular = dni_titular)['id']
        id_suscripcion = Tipo_Suscripcion.objects.values('id').get(tipo_suscripcion = suscripcion)['id']


        #Cargamos al suscriptor
        suscriptor=Suscriptor(auth_id=auth_id,
                              fecha_suscripcion=datetime.datetime.now().date(),
                              nombre=nombre ,
                              nro_tarjeta_id=id_tarjeta,
                              apellido=apellido,
                              tipo_suscripcion_id=id_suscripcion
                              )
        suscriptor.save()

        #nombre_perfil = nombre_apellido
        nombre_perfil = nombre+(apellido.capitalize())
        perfil_usuario = Perfil(nombre_perfil = nombre_perfil,auth_id = auth_id)
        perfil_usuario.save()

    def get(self,request):
        formulario = FormularioRegistro()
        self.contexto['formulario'] = formulario
        return render(request,'registro.html',self.contexto)

    @csrf_exempt
    def post(self,request):
        formulario = FormularioRegistro(request.POST)
        if formulario.is_valid():
            self.__cargar_usuario_suscriptor(formulario)
            return redirect('/')
        self.contexto['formulario'] =  formulario
        return render(request,'registro.html',self.contexto)

class Vista_Iniciar_Sesion(View):
    def __init__(self,*args,**kwargs):
        self.__vista_html = 'iniciar_sesion.html'
        self.__contexto = {'formulario': None} #en caso se guarda el mensaje que se va a mostrar en el html
        super(Vista_Iniciar_Sesion,self).__init__(*args,**kwargs)

    def __contextualizar_formulario(self,caso = None):
        self.__contexto['caso'] = caso or ''
        self.__contexto['formulario'] = FormularioIniciarSesion()

    def get(self,request):
        self.__contextualizar_formulario()
        return render(request,self.__vista_html,self.__contexto)

    @csrf_exempt
    def post(self,request):
        error = ''
        self.formulario = FormularioIniciarSesion(request.POST)
        if self.formulario.is_valid():
            email = self.formulario.cleaned_data['email']
            clave = self.formulario.cleaned_data['clave']
            usuario = authenticate(username=email,password=clave)
            if usuario is not None: #El usuario se autentica
                login(request,usuario)
                id_usuario_logueado = (User.objects.values('id').get(username=email))['id']
                url = str(id_usuario_logueado)+'/'
                if not usuario.is_staff:
                    return redirect('/listado_perfiles/')
                else:
                    return redirect('/home_admin/')
            else:
               error = 'Los datos ingresados no son validos'
        self.__contextualizar_formulario(error or '')
        return render(request,self.__vista_html,self.__contexto)

class Vista_Datos_Usuario(View):
    def get(self,request,*args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/iniciar_sesion/')
        id = request.session['_auth_user_id']
        datos_suscriptor = (Suscriptor.objects.filter(auth_id=id)).values()[0]
        datos_tarjeta = Tarjeta.objects.filter(id = datos_suscriptor['nro_tarjeta_id']).values()[0]
        email_usuario = (User.objects.values('username').filter(id = id)[0])['username']
        perfiles = Perfil.objects.values('nombre_perfil').filter(auth_id = id)
        suscripcion = (Tipo_Suscripcion.objects.filter(id = datos_suscriptor['tipo_suscripcion_id']).values()[0])['tipo_suscripcion']
        contexto={
                'nombre': datos_suscriptor['nombre'],
                'apellido': datos_suscriptor['apellido'],
                'email': email_usuario,
                'fecha_suscripcion': datos_suscriptor['fecha_suscripcion'],
                'tipo_suscripcion': suscripcion,
                'numero_tarjeta': datos_tarjeta['nro_tarjeta'],
                'fecha_vencimiento': datos_tarjeta['fecha_vencimiento'],
                'dni_titular': datos_tarjeta['dni_titular'],
                'empresa': datos_tarjeta['empresa'],
                'perfiles': [str(clave['nombre_perfil']) for clave in list(perfiles)]

        }
        return render(request,'datos_usuario.html',contexto)

class Vista_Visitante(View):
    def get(self,request):
        if request.user.is_authenticated:
            if request.user.is_staff:
                return redirect('/home_admin/')
            return redirect('/listado_perfiles/')
        return render(request,'visitante.html',{'objeto_pagina': listado_libros_activos(request,6)})

class Home_Admin(View):
    def get(self,request):
        if not request.user.is_authenticated:
            return redirect('/iniciar_sesion/')
        return render(request,'home_admin.html',{})

class Vista_Modificar_Datos_Personales(View):
    def __init__(self,*args,**kwargs):
        self.contexto = dict()
        super(Vista_Modificar_Datos_Personales,self).__init__(*args,**kwargs)

    def __valores_iniciales(self,id):
        """
            Setea los valores iniciales del formulario
        """
        email_usuario = (User.objects.values('username').filter(id = id)[0])['username']
        datos_suscriptor = (Suscriptor.objects.filter(auth_id = id).values())[0]
        datos_tarjeta = Tarjeta.objects.filter(id = datos_suscriptor['nro_tarjeta_id']).values()[0]
        suscripcion = (Tipo_Suscripcion.objects.filter(id = datos_suscriptor['tipo_suscripcion_id']).values()[0])['tipo_suscripcion']
        valores_por_defecto = {
                'Email': email_usuario,
                'Nombre': datos_suscriptor['nombre'],
                'Apellido': datos_suscriptor['apellido'],
                'Numero_de_tarjeta': datos_tarjeta['nro_tarjeta'],
                'Fecha_de_vencimiento': datos_tarjeta['fecha_vencimiento'],
                'DNI_titular': datos_tarjeta['dni_titular'],
                'Empresa': datos_tarjeta['empresa'],
                'Codigo_de_seguridad': datos_tarjeta['codigo_seguridad'],
                'Suscripcion': suscripcion
        }
        return valores_por_defecto

    def __cambiar_datos_usuario(self,formulario,id):
        nombre = formulario.cleaned_data['Nombre']
        apellido = formulario.cleaned_data['Apellido']

        #Aplicamos el patron de estrategia. get_datos_cambiados es un diccionario donde para cada campo importante guarda un boolean si cambio o no con respecto a su valor inicial
        estrategia_email = Estrategia_Email(formulario.get_datos_cambiados()['Email'],formulario,self.__valores_iniciales(id))
        estrategia_numero_de_tarjeta = Estrategia_Numero_de_tarjeta(auth_id = id, estado = formulario.get_datos_cambiados()['Numero_de_tarjeta'],formulario_nuevo = formulario,valores_iniciales = self.__valores_iniciales(id))

        estrategia_email.validar()
        estrategia_numero_de_tarjeta.validar()

        suscriptor = Suscriptor.objects.get(auth_id = id)
        suscriptor.nombre = nombre
        suscriptor.apellido = apellido
        suscriptor.save()

    def get(self,request):
        if not request.user.is_authenticated:
            return redirect('/iniciar_sesion/')
        formulario = FormularioModificarDatosPersonales(initial = self.__valores_iniciales(request.session['_auth_user_id']))
        self.contexto['formulario'] = formulario
        return render(request,'modificar_datos_personales.html',self.contexto)

    def post(self,request):
        formulario = FormularioModificarDatosPersonales(initial = self.__valores_iniciales(request.session['_auth_user_id']), data = request.POST)
        if formulario.is_valid():
            self.__cambiar_datos_usuario(formulario,request.session['_auth_user_id'])
        self.contexto['formulario'] = formulario
        return render(request,'modificar_datos_personales.html',self.contexto)

def paginar(request,tuplas,cantidad_maxima_paginado=1):
    "Pagina la pagina para los listados o detalle (el detalle necesita pagina por las fk)"
    paginador = Paginator(tuplas, cantidad_maxima_paginado)
    numero_de_pagina = request.GET.get('page')
    pagina = paginador.get_page(numero_de_pagina)  # Me devuelve el objeto de la pagina actualizamos
    return pagina

class Vista_Detalle(View):
    def __init__(self,*args, **kwargs):
        self.contexto = {'modelo': self.modelo_string}

    def get(self,request,id = None):
        if not request.user.is_authenticated:
            return redirect('/iniciar_sesion/')
        try:
            #Se pagina porque si en la tabla las fk son ids, es porque el paginador asocia el id con la fila que le corresponde
            tuplas = self.modelo.objects.filter(id = id)
            self.contexto ['id'] = id #El id se usa para pasar entre las vistas, porque se usa en el "detalle.html"
            self.contexto['objeto_pagina'] = paginar(request, tuplas)
            self.cargar_diccionario(id)
            return render(request,self.url,self.contexto)
        except:
            return redirect('/')
    def cargar_diccionario(self,id):
        "Hook que sobreescriben los hijos"
        "Este mensaje carga el contexto con lo que requiera un detalle especifico"
        pass

class Vista_Listado(View):
    def get(self,request):
        contexto = dict()
        if not request.user.is_authenticated:
            return redirect('/iniciar_sesion/')
        tuplas = self.modelo.objects.all()
        contexto = {'objeto_pagina': paginar(request,tuplas,10),'modelo': self.modelo_string}
        #EL contexto_extra existe ya que hay tablas que tienen ids de las claves foraneas. En este dic se setean los valores de esos ids foraneos
        return render(request,self.url,contexto)

class Vista_Listado_Libro(Vista_Listado):
    def __init__(self,*args,**kwargs):
        self.url = 'listado_libro.html'
        self.modelo = Libro
        self.modelo_string = 'libro'
        super(Vista_Listado_Libro,self).__init__(*args,**kwargs)

class Vista_Listado_Novedad(Vista_Listado):
    def __init__(self,*args,**kwargs):
        self.url = 'listado_novedad.html'
        self.modelo = Novedad
        self.modelo_string = 'novedad'
        super(Vista_Listado_Novedad,self).__init__(*args,**kwargs)

class Vista_Detalle_Novedad(Vista_Detalle):
    def __init__(self,*args,**kwargs):
        self.url = 'detalle_novedad.html'
        self.modelo = Novedad
        self.modelo_string = 'novedad'
        super(Vista_Detalle_Novedad,self).__init__(*args,**kwargs)

class Vista_Listado_Genero(Vista_Listado):
    def __init__(self,*args,**kwargs):
        self.url = 'listado_genero.html'
        self.modelo = Genero
        self.modelo_string = 'genero'
        super(Vista_Listado_Genero,self).__init__(*args,**kwargs)

class Vista_Listado_Autor(Vista_Listado):
    def __init__(self,*args,**kwargs):
        self.url = 'listado_autor.html'
        self.modelo = Autor
        self.modelo_string = 'autor'
        super(Vista_Listado_Autor,self).__init__(*args,**kwargs)

class Vista_Listado_Editorial(Vista_Listado):
    def __init__(self,*args,**kwargs):
        self.url = 'listado_editorial.html'
        self.modelo = Editorial
        self.modelo_string = 'editorial'
        super(Vista_Listado_Editorial,self).__init__(*args,**kwargs)

class Vista_Listado_Perfiles(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('/iniciar_sesion/')
        return render(request,'listado_perfiles.html',{'perfiles': self.__obtener_perfiles(request.session['_auth_user_id'])})

    def __obtener_perfiles(self,id):
        lista_nombre_perfiles=list()
        lista_perfiles=Perfil.objects.values('nombre_perfil','id').filter(auth_id = id)
        return [diccionario for diccionario in lista_perfiles]

class Vista_Detalle_Trailer(Vista_Detalle):
    def __init__(self,*args,**kwargs):
            self.url = 'detalle_trailer.html'
            self.modelo = Trailer
            self.modelo_string = 'trailer'
            super(Vista_Detalle_Trailer,self).__init__(*args,**kwargs)

class Vista_Listado_Trailer(Vista_Listado):
    def __init__(self,*args,**kwargs):
        self.url = 'listado_trailer.html'
        self.modelo = Trailer
        self.modelo_string = 'trailer'
        super(Vista_Listado_Trailer,self).__init__(*args,**kwargs)

class Vista_Formulario_Libro_Completo(View):
    def get(self,request,id=None):
        return render(request,'formulario_libro_completo.html',{'formulario': FormularioCargaLibro()})

    def __guardar_libro_completo(self,formulario,id):
        "----Guarda el archivo en la carpeta static--------"
        archivo_pdf = formulario.cleaned_data['pdf']
        fs = FileSystemStorage()
        fs.save(archivo_pdf.name, archivo_pdf)
        "-------------------------------------------------"
        libro_completo = Libro_Completo(libro_id = id,
                                        fecha_lanzamiento = formulario.cleaned_data['fecha_de_lanzamiento'],
                                        archivo_pdf = archivo_pdf
                                        )
        fecha_vencimiento =  formulario.cleaned_data['fecha_de_vencimiento']
        if fecha_vencimiento is not None: #Si lleno la fecha de vencimiento
            libro_completo.fecha_vencimiento = fecha_vencimiento
        libro_completo.save()

        # Seteamos que el libro ahora se encuentra completo
        libro = Libro.objects.get(id=id)
        libro.esta_completo = True
        libro.save()

        ##TODO: si tiene capitulos, borrarlos.

    def post(self,request,id=None):
        formulario = FormularioCargaLibro(request.POST,request.FILES)
        if formulario.is_valid():
            self.__guardar_libro_completo(formulario,id)
            return redirect('/listado_libro/')
        return render(request,'formulario_libro_completo.html',{'formulario': formulario})

class Vista_Detalle_libro(Vista_Detalle):
    def __init__(self,*args,**kwargs):
        self.modelo_string = 'libro'
        self.url = 'detalle_libro.html'
        self.modelo = Libro
        super(Vista_Detalle_libro, self).__init__(*args, **kwargs)


    def cargar_diccionario (self, id):

        trailers = Trailer.objects.filter(libro_asociado_id = id).values('titulo','id')
        self.contexto ['trailers'] = trailers