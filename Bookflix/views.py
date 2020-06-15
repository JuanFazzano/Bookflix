import datetime
import itertools
from django.contrib.auth.models     import User
from django.views                   import View
from django.core.paginator          import Paginator
from django.views.decorators.csrf   import csrf_exempt
from django.http                    import HttpResponse,FileResponse
from django.shortcuts               import render,redirect
from django.contrib.auth            import authenticate,login, logout
from django.core.files.storage      import FileSystemStorage
from django.http                    import HttpResponseRedirect
from forms.forms                    import *
from modelos.models                 import Libro_Incompleto,Libro_Completo,Autor,Genero,Editorial,Suscriptor,Tarjeta,Tipo_Suscripcion,Trailer,Libro,Perfil,Novedad
from django.db.models import Q
#def dar_de_baja_libros():
#    Da de baja los libros que están vencidos
#    libros = Libro_Completo.objects.exclude(fecha_vencimiento=None)
#    libros = libros.filter(fecha_vencimiento__lte=datetime.datetime.now())
#    for libro in libros:
#        libro_baja= Libro.objects.get(id = libro.libro_id)
#        libro_baja.esta_activo = False
#        libro_baja.save()

def listado_libros_activos(request,limit=None):
    "limit es un parametro que define cuantas tuplas se van a tomar"
    #TODO ver listado de libros activos si está incompleto por capitulos
    #libros = Libro_Completo.objects.exclude(fecha_vencimiento = None)
    #print('Esto es lo que devolvio' ,(Libro.objects.all().select_related('libro').all().values()))

    #capitulos = Capitulo.objects.exclude(fecha_vencimiento = None)
    '''Q(fecha_lanzamiento__lte = datetime.datetime.now()) &
    ()'''

    "Filtra los capitulos no vencidos (los que no tienen fecha_vencimiento o la fecha de vencimiento no es la de hoy)"
    capitulos_activos =  Capitulo.objects.filter(
                                                    Q(fecha_lanzamiento__lte = datetime.datetime.now()) &
                                                    (
                                                    Q(fecha_lanzamiento__lte = datetime.datetime.now(),fecha_vencimiento = None) |
                                                    Q(fecha_lanzamiento__lte = datetime.datetime.now(),fecha_vencimiento__gt = datetime.datetime.now())
                                                    )
                                                )

    "Filtramos los libros_incompletos que esté entre los libros de capitulos activos"
    libros_incompletos_activos = Libro_Incompleto.objects.filter(id__in = capitulos_activos.values('titulo_id'))
    #Recordemos que la coma es and
    '''
        Filtra los LIBROS cuya fecha_vencimiento sea menor a la actual O la fecha de vencimiento no es None y está completo (con ult cap cargado )
        o el libro que esté entre los incompletos_activos
    '''
    libros_activos = Libro.objects.filter(          Q(id__in = libros_incompletos_activos.values('libro_id')) |
                                                    Q(esta_completo=True,fecha_lanzamiento__lte= datetime.datetime.now(),fecha_vencimiento__gt = datetime.datetime.now()) |
                                                    Q(esta_completo=True,fecha_lanzamiento__lte= datetime.datetime.now(),fecha_vencimiento = None)
                                        ).distinct()
    if limit is not None:
        libros_activos = libros_activos[:limit]
    return paginar(request,libros_activos,10)

def listado_libros_activos_1(limit=None):
    "limit es un parametro que define cuantas tuplas se van a tomar"
    #TODO ver listado de libros activos si está incompleto por capitulos
    #libros = Libro_Completo.objects.exclude(fecha_vencimiento = None)
    #print('Esto es lo que devolvio' ,(Libro.objects.all().select_related('libro').all().values()))

    #capitulos = Capitulo.objects.exclude(fecha_vencimiento = None)
    '''Q(fecha_lanzamiento__lte = datetime.datetime.now()) &
    ()'''

    "Filtra los capitulos no vencidos (los que no tienen fecha_vencimiento o la fecha de vencimiento no es la de hoy)"
    capitulos_activos =  Capitulo.objects.filter(
                                                    Q(fecha_lanzamiento__lte = datetime.datetime.now()) &
                                                    (
                                                    Q(fecha_lanzamiento__lte = datetime.datetime.now(),fecha_vencimiento = None) |
                                                    Q(fecha_lanzamiento__lte = datetime.datetime.now(),fecha_vencimiento__gt = datetime.datetime.now())
                                                    )
                                                )

    "Filtramos los libros_incompletos que esté entre los libros de capitulos activos"
    libros_incompletos_activos = Libro_Incompleto.objects.filter(id__in = capitulos_activos.values('titulo_id'))
    #Recordemos que la coma es and
    '''
        Filtra los LIBROS cuya fecha_vencimiento sea menor a la actual O la fecha de vencimiento no es None y está completo (con ult cap cargado )
        o el libro que esté entre los incompletos_activos
    '''
    libros_activos = Libro.objects.filter(          Q(id__in = libros_incompletos_activos.values('libro_id')) |
                                                    Q(esta_completo=True,fecha_lanzamiento__lte= datetime.datetime.now(),fecha_vencimiento__gt = datetime.datetime.now()) |
                                                    Q(esta_completo=True,fecha_lanzamiento__lte= datetime.datetime.now(),fecha_vencimiento = None)
                                        ).distinct()

    return libros_activos


def cerrar_sesion(request):
    #Cierra la sesion del usuarios, y lo redireccion al /
    logout(request)
    return HttpResponseRedirect('/')

class Vista_Registro(View):
    def __init__(self,*args,**kwargs):
        self.contexto = dict()
        self.url = '/iniciar_sesion/'
        super(Vista_Registro,self).__init__(*args,**kwargs)

    def cargar_tarjeta(self,formulario):
        "Este metodo carga la tarjeta en caso de no existir"
        numero_tarjeta=  formulario.cleaned_data['Numero_de_tarjeta']
        empresa= formulario.cleaned_data['Empresa']
        fecha_de_vencimiento= formulario.cleaned_data['Fecha_de_vencimiento']
        Codigo_de_seguridad= formulario.cleaned_data['Codigo_de_seguridad']
        tarjeta = Tarjeta(nro_tarjeta = numero_tarjeta,
                          codigo_seguridad = Codigo_de_seguridad,
                          empresa = empresa,
                          fecha_vencimiento = fecha_de_vencimiento,
                          )
        tarjeta.save()
        #return Tarjeta.objects.values('id')
        return tarjeta.id

    def __cargar_usuario_suscriptor(self,formulario):
        """
            Carga los datos del suscriptor en la tabla modelos_suscriptor, modelos_usuario y auth_user
        """
        email = formulario.cleaned_data['Email']
        dni =   formulario.cleaned_data['DNI']
        numero_tarjeta = formulario.cleaned_data['Numero_de_tarjeta']
        contrasena = formulario.cleaned_data['Contrasena']
        apellido = formulario.cleaned_data['Apellido']
        nombre = formulario.cleaned_data['Nombre']
        suscripcion = formulario.cleaned_data['Suscripcion']

        id_tarjeta = self.cargar_tarjeta(formulario)

        #Cargamos el modelos User de auth_user
        model_usuario = User.objects.create_user(username = email, password=contrasena ) #Se guarda en la tabla auth_user
        model_usuario.save()

        #Tomamos las Claves foraneas
        auth_id = User.objects.values('id').get(username=email)['id']
        id_suscripcion = Tipo_Suscripcion.objects.values('id').get(tipo_suscripcion = suscripcion)['id']


        #Cargamos al suscriptor
        suscriptor=Suscriptor(auth_id=auth_id,
                              fecha_suscripcion=datetime.datetime.now().date(),
                              nombre=nombre ,
                              nro_tarjeta_id=id_tarjeta,
                              apellido=apellido,
                              tipo_suscripcion_id=id_suscripcion,
                              dni=dni
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
                'dni': datos_suscriptor['dni'],
                'fecha_suscripcion': datos_suscriptor['fecha_suscripcion'],
                'tipo_suscripcion': suscripcion,
                'numero_tarjeta': datos_tarjeta['nro_tarjeta'],
                'fecha_vencimiento': datos_tarjeta['fecha_vencimiento'],
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

class Buscar:
    def __init__(self,request = None):
        self.request = request

    def tuplas(self):
        if not all(map(lambda x: x == '', self.request.GET.values())):
            if(self.request.user.is_staff):
                listado_de_libros=Libro.objects.all()
            else:
                listado_de_libros= listado_libros_activos_1()
            decorado = Listado_decorado(listado_de_libros)
            decoradorGenero = DecoradorGenero(decorado,self.request.GET['genero'])
            decoradorAutor = DecoradorAutor(decoradorGenero,self.request.GET['autor'])
            decoradorEditorial = DecoradorEditorial(decoradorAutor,self.request.GET['editorial'])
            decoradorTitulo = DecoradorTitulo(decoradorEditorial,self.request.GET['titulo'])
            return decoradorTitulo.buscar_libro()
        return ()

def listado_libros_buscados(request):
    contexto = {}
    if not all(map(lambda x: x == '', request.GET.values())):
        buscar = Buscar(request)
        tuplas = buscar.tuplas()
        print('Las tuplas ', tuplas)
        if tuplas:
            print('entre al if')
            contexto['objeto_pagina'] = paginar(request, tuplas, 10)
            contexto['modelo'] = 'libro'
    return contexto

class Home_Admin(View):
    def get(self,request):
        contexto = listado_libros_buscados(request)
        if contexto != {}:
            return render(request, 'listado_libro.html', contexto)
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
                'DNI': datos_suscriptor['dni'],
                'Numero_de_tarjeta': datos_tarjeta['nro_tarjeta'],
                'Fecha_de_vencimiento': datos_tarjeta['fecha_vencimiento'],
                'Empresa': datos_tarjeta['empresa'],
                'Codigo_de_seguridad': datos_tarjeta['codigo_seguridad'],
                'Suscripcion': suscripcion
        }
        return valores_por_defecto

    def __cambiar_datos_usuario(self,formulario,id):
        print('Entre')
        nombre = formulario.cleaned_data['Nombre']
        apellido = formulario.cleaned_data['Apellido']

        suscriptor = Suscriptor.objects.get(auth_id = id)
        suscriptor.nombre = nombre
        suscriptor.apellido = apellido

        if formulario.get_datos_cambiados()['Email']:
            #Cambio el email
            auth_usuario = User.objects.get(username = self.__valores_iniciales(id)['Email'])
            auth_usuario.username = str(formulario.cleaned_data['Email'])
            auth_usuario.save()

        if formulario.get_datos_cambiados()['DNI']:
            #Cambio el DNI
            suscriptor.dni = formulario.cleaned_data['DNI']
        suscriptor.save()

        print('ID tarjeta ',suscriptor.nro_tarjeta_id)
        tarjeta = Tarjeta.objects.get(id = suscriptor.nro_tarjeta_id)
        print('La tarjeta {}'.format(tarjeta))
        tarjeta.empresa = formulario.cleaned_data['Empresa']
        tarjeta.nro_tarjeta = formulario.cleaned_data['Numero_de_tarjeta']
        tarjeta.codigo_seguridad = formulario.cleaned_data['Codigo_de_seguridad']
        tarjeta.fecha_vencimiento = formulario.cleaned_data['Fecha_de_vencimiento']
        tarjeta.save()

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
            return redirect('/datos_suscriptor/')
        self.contexto['errores'] = formulario.errors
        self.contexto['formulario'] = FormularioModificarDatosPersonales(initial = self.__valores_iniciales(request.session['_auth_user_id']))
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
    def __init__(self, *args, **kwargs):
        self.contexto = {}

    def get(self,request):
        contexto = listado_libros_buscados(request)
        if contexto != {}:
            return render(request, 'listado_libro.html', contexto)
        if not request.user.is_authenticated:
            return redirect('/iniciar_sesion/')
        tuplas = self.modelo.objects.all()
        #self.contexto = {'objeto_pagina': paginar(request,tuplas,10),'modelo': self.modelo_string}
        self.contexto['objeto_pagina']=paginar(request,tuplas,10)
        self.contexto['modelo']=self.modelo_string
        #EL contexto_extra existe ya que hay tablas que tienen ids de las claves foraneas. En este dic se setean los valores de esos ids foraneos
        return render(request,self.url,self.contexto)

class Vista_Listado_Libro(Vista_Listado):
    def __init__(self,*args,**kwargs):
        self.url = 'listado_libro.html'
        self.modelo = Libro
        self.modelo_string = 'libro'
        super(Vista_Listado_Libro,self).__init__(*args,**kwargs)
        #TODO agregar fecha de vencimiento (Checkear si está por capitulos o completo)


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
        #lista_nombre_perfiles=list()
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
        self.modelo  = Trailer
        self.modelo_string = 'trailer'
        super(Vista_Listado_Trailer,self).__init__(*args,**kwargs)

class Vista_Formulario_Libro_Completo(View):
    def get(self,request,id=None):
        return render(request,'formulario_libro_completo.html',{'formulario': FormularioCargaLibro()})

    def __guardar_libro_completo(self,formulario,id):
        """
        :param formulario:
        :param id: es el id del libro
        :return:
        """
        "----Guarda el archivo en la carpeta static--------"

        archivo_pdf = formulario.cleaned_data['pdf']
        fs = FileSystemStorage()
        fs.save(archivo_pdf.name, archivo_pdf)
        "-------------------------------------------------"
        "Lo cargamos como libro incomplto"
        libro_completo = Libro_Completo(libro_id = id,archivo_pdf = archivo_pdf)
        libro_completo.save()

        "Actualizamos su metadata"
        libro = Libro.objects.get(id=id)
        libro.fecha_lanzamiento = formulario.cleaned_data['fecha_de_lanzamiento']
        libro.fecha_vencimiento = formulario.cleaned_data['fecha_de_vencimiento']
        libro.esta_completo = True
        libro.save()

        "Borramos los capitulos del libro"
        try:
            libro_incompleto = Libro_Incompleto.objects.get(libro_id = id)

            "Borramos los capitulos del libro"
            Capitulo.objects.filter(titulo_id = libro_incompleto.id).delete()

            "Borramos la instancia de libro incompleto"
            libro_incompleto.delete()
        except:
            "No estaba cargado como libro incompleto"
            pass

    def post(self,request,id=None):
        formulario = FormularioCargaLibro(request.POST,request.FILES)
        if formulario.is_valid():
            self.__guardar_libro_completo(formulario,id)
            return redirect('/listado_libro/')
        return render(request,'formulario_libro_completo.html',{'formulario': formulario})

class Vista_Formulario_Atributo(View):
    "Clase abstracta para la carga de autor,genero y editorial"
    def get(self,request):
        return render(request,'carga_atributos_libro.html',self.contexto)

    @csrf_exempt
    def post(self,request):
        formulario = FormularioCargaAtributos(data = request.POST,modelo = self.modelo,nombre_modelo = self.nombre_modelo)
        if formulario.is_valid():
            #Cargamos en la BD
            modelo = self.modelo(nombre = formulario.cleaned_data['nombre'])
            modelo.save()
            return redirect(self.url_redirect)
        self.contexto['formulario'] = formulario
        return render(request,'carga_atributos_libro.html',self.contexto)

class Vista_Formulario_Genero(Vista_Formulario_Atributo):
    def __init__(self):
        self.modelo = Genero
        self.nombre_modelo = 'genero'
        self.url_redirect = '/listado_genero/'
        self.contexto = {'formulario': FormularioCargaAtributos(Genero,'genero'),'modelo':'genero'}

class Vista_Formulario_Autor(Vista_Formulario_Atributo):
    def __init__(self):
        self.modelo = Autor
        self.nombre_modelo = 'autor'
        self.url_redirect = '/listado_autor/'
        self.contexto = {'formulario': FormularioCargaAtributos(Autor,'autor'),'modelo':'autor'}

class Vista_Formulario_Editorial(Vista_Formulario_Atributo):
    def __init__(self):
        self.modelo = Editorial
        self.nombre_modelo = 'editorial'
        self.url_redirect = '/listado_editorial/'
        self.contexto = {'formulario': FormularioCargaAtributos(Editorial,'editorial'),'modelo':'editorial'}

class Vista_Formulario_Novedad(View):
    def get(self,request):
        return render(request,'carga_novedad.html',{'formulario': FormularioCargaNovedad()})

    def post(self,request):
        formulario = FormularioCargaNovedad(request.POST,request.FILES)
        if formulario.is_valid():

            imagen = formulario.cleaned_data['foto']
            if imagen is not None:
                fs = FileSystemStorage()
                fs.save(imagen.name, imagen)
            novedad = Novedad(
                titulo = formulario.cleaned_data['titulo'],
                descripcion = formulario.cleaned_data['descripcion'],
                foto = imagen
                )
            novedad.save()
            return redirect('/listado_novedad/')
        return render(request,'carga_novedad.html',{'formulario': formulario})

class Vista_Formulario_Trailer(View):
    def __init__(self):
        self.contexto = {'modelo':'trailer'}

    def __carga_archivo(self,campo_archivo):
        archivo = campo_archivo
        if archivo is not None:
            fs = FileSystemStorage()
            fs.save(archivo.name, archivo)

    def get(self,request):
        self.contexto['formulario'] =  FormularioCargaTrailer()
        return render(request,'carga_atributos_libro.html',self.contexto)

    def post(self,request):
        formulario = FormularioCargaTrailer(request.POST,request.FILES)
        if formulario.is_valid():
            self.__carga_archivo(formulario.cleaned_data['pdf'])
            self.__carga_archivo(formulario.cleaned_data['video'])
            trailer = Trailer(
                titulo = formulario.cleaned_data['titulo'],
                descripcion = formulario.cleaned_data['descripcion'],
                pdf = formulario.cleaned_data['pdf'],
                video = formulario.cleaned_data['video'],
                libro_asociado_id = formulario.cleaned_data['libro']
            )
            trailer.save()
            return redirect('/listado_trailer/')
        self.contexto['errores'] = formulario.errors
        self.contexto['formulario'] = FormularioCargaTrailer()
        return render(request,'carga_atributos_libro.html',self.contexto)

class Vista_Modificar_Novedad(View):
    def __get_valores_inicials(self,id):
        novedad = Novedad.objects.get(id = id)
        return {
            'titulo': novedad.titulo,
            'descripcion': novedad.descripcion if (novedad.descripcion is not None) else '',
            'foto': novedad.foto if (novedad.foto is not None) else ''
        }

    def get(self,request, id = None):
        print(self.__get_valores_inicials(id)['foto'])
        return render(request,'carga_novedad.html',{'formulario': FormularioModificarNovedad(initial = self.__get_valores_inicials(id))})

    def post(self,request, id = None):
        formulario = FormularioModificarNovedad(request.POST,request.FILES,initial = self.__get_valores_inicials(id))
        if formulario.is_valid():

            imagen = formulario.cleaned_data['foto']
            print('Imagen ',imagen)
            if imagen:
                fs = FileSystemStorage()
                fs.save(imagen.name, imagen)
            novedad = Novedad.objects.get(id = id)
            novedad.titulo = formulario.cleaned_data['titulo']
            novedad.descripcion = formulario.cleaned_data['descripcion']
            novedad.foto = formulario.cleaned_data['foto'] if (imagen) else None
            novedad.save()
            return redirect('/listado_novedad/')

        return render(request,'carga_novedad.html',{'formulario':FormularioModificarNovedad(initial=self.__get_valores_inicials(id)),'errores':formulario.errors})

class Vista_Formulario_Modificar_Atributo(View):
    def __init__(self):
        self.nombre = None
        self.contexto = {'formulario': None, 'modelo':self.nombre_modelo}

    def __get_iniciales(self,id):
        "Devuelve los valores iniciales"
        self.nombre = self.modelo.objects.get(id = id).nombre
        return {'nombre': self.nombre}

    def get(self,request,id = None):
        self.contexto['formulario'] = FormularioModificarAtributos(initial = self.__get_iniciales(id),modelo = self.modelo,nombre_modelo = self.nombre_modelo)
        return render(request,'carga_atributos_libro.html',self.contexto)

    def post(self,request,id = None):
        formulario = FormularioModificarAtributos(data = request.POST,initial = self.__get_iniciales(id),modelo = self.modelo,nombre_modelo = self.nombre_modelo)
        if formulario.is_valid():
            modelo = self.modelo.objects.get(id = id)
            modelo.nombre = formulario.cleaned_data['nombre']
            modelo.save()
            return redirect(self.url_redirect)
        self.contexto['errores'] = formulario.errors
        self.contexto['formulario'] = FormularioModificarAtributos(initial = self.__get_iniciales(id),modelo = self.modelo,nombre_modelo = self.nombre_modelo)
        return render(request,'carga_atributos_libro.html',self.contexto)

class Vista_Formulario_Modificar_Genero(Vista_Formulario_Modificar_Atributo):
    def __init__(self):
        self.modelo = Genero
        self.nombre_modelo = 'genero'
        self.url_redirect = '/listado_genero/'
        super(Vista_Formulario_Modificar_Genero,self).__init__()

class Vista_Formulario_Modificar_Autor(Vista_Formulario_Modificar_Atributo):
    def __init__(self):
        self.modelo = Autor
        self.nombre_modelo = 'autor'
        self.url_redirect = '/listado_autor/'
        super(Vista_Formulario_Modificar_Autor,self).__init__()

class Vista_Formulario_Modificar_Editorial(Vista_Formulario_Modificar_Atributo):
    def __init__(self):
        self.modelo = Editorial
        self.nombre_modelo = 'editorial'
        self.url_redirect = '/listado_editorial/'
        super(Vista_Formulario_Modificar_Editorial,self).__init__()

class Vista_Formulario_Modificar_Trailer(View):
    def __init__(self):
        self.contexto = {'modelo':'trailer'}

    def __get_valores_iniciales(self,id):
        trailer = Trailer.objects.get(id = id)
        return{
            'titulo': trailer.titulo,
            'descripcion': trailer.descripcion,
            'pdf': trailer.pdf if (trailer.pdf is not None) else None,
            'video': trailer.video if (trailer.video is not None) else None,
            'libro': trailer.libro_asociado_id if (trailer.libro_asociado is not None) else ''
        }

    def get(self,request,id = None):
        self.contexto['formulario'] = FormularioModificarTrailer(initial=self.__get_valores_iniciales(id))
        return render(request,'carga_atributos_libro.html',self.contexto)

    def post(self,request,id = None):
        formulario = FormularioModificarTrailer(request.POST,request.FILES,initial=self.__get_valores_iniciales(id))
        if formulario.is_valid():
            trailer = Trailer.objects.get(id = id)
            trailer.titulo = formulario.cleaned_data['titulo']
            trailer.descripcion =  formulario.cleaned_data['descripcion']
            trailer.pdf =  None if (not formulario.cleaned_data['pdf']) else formulario.cleaned_data['pdf']
            trailer.video =  None if (not formulario.cleaned_data['video']) else formulario.cleaned_data['video']
            trailer.libro_asociado_id =  formulario.cleaned_data['libro']
            trailer.save()
            return redirect('/listado_trailer/')
        self.contexto['errores'] = formulario.errors
        self.contexto['formulario'] = FormularioModificarTrailer(initial = self.__get_valores_iniciales(id))
        return render(request,'carga_atributos_libro.html',self.contexto)

class Vista_Detalle_libro(Vista_Detalle):
    def __init__(self,*args,**kwargs):
        self.modelo_string = 'libro'
        self.url = 'detalle_libro.html'
        self.modelo = Libro
        super(Vista_Detalle_libro, self).__init__(*args, **kwargs)


    def cargar_diccionario (self, id):
        trailers = Trailer.objects.filter(libro_asociado_id = id).values('titulo','id')
        libro = Libro.objects.filter(id = id)[0]
        if libro.esta_completo:
            #libro_completo =  Libro_Completo.objects.values().filter(libro_id = libro.id)
            libro_completo =  Libro_Completo.objects.get(libro_id = libro.id)
            print('VALORES COMPLETO ',libro_completo)
            self.contexto['completo'] = libro_completo
        self.contexto ['trailers'] = trailers
        decoradorGenero = DecoradorGenero(libro,libro.genero_id)
        decoradorAutor = DecoradorAutor(decoradorGenero,libro.autor_id)
        decoradorEditorial = DecoradorEditorial(decoradorAutor,libro.editorial_id)
        self.contexto ['libros_similares'] = decoradorEditorial.buscar_similares()

class Vista_Carga_Metadatos_Libro(View):
    def __init__(self, *args, **kwargs):
        self.contexto = dict()
        self.url = '/listado_libro/'
        super(Vista_Carga_Metadatos_Libro, self).__init__(*args, **kwargs)

    def __cargar_metadatos_libro(self,formulario):
        archivo_imagen = formulario.cleaned_data['imagen']
        if archivo_imagen is not None:
            "----Guarda el archivo en la carpeta static--------"
            fs = FileSystemStorage()
            fs.save(archivo_imagen.name, archivo_imagen)
        titulo = formulario.cleaned_data['titulo']
        isbn = formulario.cleaned_data['ISBN']
        descripcion = formulario.cleaned_data['descripcion']
        autor = formulario.cleaned_data['autor']
        editorial = formulario.cleaned_data['editorial']
        genero = formulario.cleaned_data['genero']
        nuevo_libro = Libro(titulo=titulo, ISBN = isbn ,foto= archivo_imagen, descripcion= descripcion , autor_id = autor ,editorial_id= editorial, genero_id = genero  )
        nuevo_libro.save()

    def get(self, request):
        formulario = FormularioCargaDeMetadatosLibro()
        self.contexto['formulario'] = formulario
        self.contexto['modelo'] = 'libro'
        return render(request, 'carga_atributos_libro.html', self.contexto)

    @csrf_exempt
    def post(self, request):
        formulario = FormularioCargaDeMetadatosLibro(request.POST, request.FILES)
        if formulario.is_valid():
            print(formulario.cleaned_data)
            self.__cargar_metadatos_libro(formulario)
            return redirect(self.url)
        self.contexto['formulario'] = formulario
        self.contexto['modelo'] = 'libro'
        return render(request, 'carga_atributos_libro.html', self.contexto)

class Vista_Modificar_Metadatos_Libro(View):
    def __get_valores_inicials(self,id):
        libro = Libro.objects.get(id = id)
        return {
            'titulo': libro.titulo,
            'ISBN' : libro.ISBN,
            'descripcion': libro.descripcion if (libro.descripcion is not None) else '',
            'imagen': libro.foto if (libro.foto is not None) else '',
            'autor': libro.autor_id,
            'genero':libro.genero_id,
            'editorial' : libro.editorial_id,
        }

    def get(self,request, id = None):
        return render(request,'carga_atributos_libro.html',{'formulario': Formulario_modificar_metadatos_libro(initial = self.__get_valores_inicials(id)),'modelo':'libro'})

    def post(self,request, id = None):
        formulario = Formulario_modificar_metadatos_libro(request.POST,request.FILES,initial = self.__get_valores_inicials(id))
        if formulario.is_valid():
            imagen = formulario.cleaned_data['imagen']
            print('Imagen ',imagen)
            if imagen:
                fs = FileSystemStorage()
                fs.save(imagen.name, imagen)
            libro = Libro.objects.get(id = id)
            libro.titulo = formulario.cleaned_data['titulo']
            libro.ISBN= formulario.cleaned_data['ISBN']
            libro.descripcion = formulario.cleaned_data['descripcion']
            libro.foto = formulario.cleaned_data['imagen'] if (imagen) else None
            libro.autor_id= formulario.cleaned_data['autor']
            libro.genero_id= formulario.cleaned_data['genero']
            libro.editorial_id= formulario.cleaned_data['editorial']
            libro.save()
            return redirect('/listado_libro/')
        formulario.initial["titulo"]= 'hola'
        return render(request,'carga_atributos_libro.html',{'formulario':formulario,'modelo':'libro'})

class Vista_modificar_fechas_libro(View):
    def __init__(self, *args, **kwargs):
        self.esta_completo = None
        super(Vista_modificar_fechas_libro, self).__init__(*args, **kwargs)

    def __get_valores_inicials(self, id):
        libro = Libro.objects.get(id=id)
        return {
            'fecha_de_lanzamiento': libro.fecha_lanzamiento.date(),
            'fecha_de_vencimiento': libro.fecha_vencimiento if libro.fecha_vencimiento is None else libro.fecha_vencimiento.date(),
        }
    def cambiar_fechas(self,id,formulario):
        "Cambia las fechas del libro (el boton se habilita cuando esté completo o tenga el último capitulo cargado"
        libro = Libro.objects.get(id=id)
        libro.fecha_lanzamiento = formulario.cleaned_data['fecha_de_lanzamiento']
        libro.fecha_vencimiento = formulario.cleaned_data['fecha_de_vencimiento']
        libro.save()

    def get(self, request, id=None):
        #TODO hacer que la fecha de vencimiento sea opcional. Actualmentee
        esta_completo = Libro.objects.get(id=id).esta_completo
        valores_fechas=self.__get_valores_inicials(id)
        return render(request, 'carga_atributos_libro.html', {'formulario': FormularioCargaFechas(valores_fechas['fecha_de_lanzamiento'],valores_fechas['fecha_de_vencimiento']),'modelo':'libro'})


    def post(self, request, id=None):
        valores_fechas=self.__get_valores_inicials(id)
        formulario = FormularioCargaFechas(data = request.POST,lanzamiento=valores_fechas['fecha_de_lanzamiento'],vencimiento = valores_fechas['fecha_de_vencimiento'], initial=self.__get_valores_inicials(id))
        if formulario.is_valid():
            self.cambiar_fechas(id,formulario)
            return redirect('/listado_libro/')
        return render(request, 'carga_atributos_libro.html',{'formulario': FormularioCargaFechas(valores_fechas['fecha_de_lanzamiento'],valores_fechas['fecha_de_vencimiento']),'errores': formulario.errors,'modelo':'libro'})


class Vista_Alta_Capitulo(View):
    def __init__(self):
        self.contexto = {'modelo': 'libro'}

    def get_capitulo_mas_grande(self,id):
        "id:int que representa el titulo_id (id del Libro)"
        "Devuelve el capítulo más grande cargado"
        capitulos = Capitulo.objects.filter(titulo_id = Libro_Incompleto.objects.get(libro_id=id).id)
        capitulo_maximo = 1 #Por defecto sugiere el 1
        if capitulos: #Si hay capitulos
            capitulo_maximo = (capitulos.order_by('-capitulo').values('capitulo')).first() #Ordena de mayor a menor
            capitulo_maximo = capitulo_maximo['capitulo'] + 1
        return capitulo_maximo

    def cargar_incompleto(self,id):
        "Carga el libro incompleto en caso de que sea la primera carga"
        try:
            incompleto = Libro_Incompleto(libro_id = id)
            incompleto.save()
        except:
            pass


    def cambiamos_fechas_capitulos(self,id,fecha_lanzamiento,fecha_vencimiento):
        "Cambia las fechas de los capitulos del libro para mantener la consistencia"
        try:
            capitulos = Capitulo.objects.filter(titulo_id = id)
            for capitulo in capitulos:
                capitulo.fecha_lanzamiento = fecha_lanzamiento
                capitulo.fecha_vencimiento = fecha_vencimiento
                capitulo.save()

        except:
            return None

    def get(self,request,id = None):
        self.cargar_incompleto(id)
        self.contexto['formulario'] = FormularioCapitulo(id = id,initial={'numero_capitulo':self.get_capitulo_mas_grande(id)})
        return render(request,'carga_atributos_libro.html',self.contexto)

    def post(self,request,id = None):
        formulario = FormularioCapitulo(data = request.POST,files = request.FILES,id = id)
        if formulario.is_valid():
            #Si es valido el formulario, cargo el capitulo
            incompleto = Libro_Incompleto.objects.get(libro_id=id)
            print('ID incompleto ',incompleto.id)
            capitulo = Capitulo(
                capitulo=formulario.cleaned_data['numero_capitulo'],
                archivo_pdf=formulario.cleaned_data['archivo_pdf'],
                titulo_id=incompleto.id,
            )
            capitulo.fecha_lanzamiento = formulario.cleaned_data['fecha_de_lanzamiento']
            capitulo.fecha_vencimiento = formulario.cleaned_data['fecha_de_vencimiento']
            if formulario.cleaned_data['ultimo_capitulo']:
                #Si no es el ultimo capitulo, le cargo la fecha
                libro = Libro.objects.get(id=id)
                libro.fecha_lanzamiento = formulario.cleaned_data['fecha_de_lanzamiento']
                libro.fecha_vencimiento = formulario.cleaned_data['fecha_de_vencimiento']
                libro.save()
                incompleto.esta_completo = True
                incompleto.save()
                print(self.cambiamos_fechas_capitulos(incompleto.id,formulario.cleaned_data['fecha_de_lanzamiento'], formulario.cleaned_data['fecha_de_vencimiento']))

            capitulo.save()
            return redirect('/listado_libro/')
        self.contexto['formulario'] = formulario
        return render(request,'carga_atributos_libro.html',self.contexto)

class Vista_Lectura_Libro(View):
    def get(self,request):
        #return render(request,'prueba.html',{'pdf': 'parte2grupo52.pdf'})
        return FileResponse(open('static/parte2grupo52.pdf', 'rb'), content_type='application/pdf')


class Listado_decorado:
    def __init__(self,listado):
        self.listado = listado

    def buscar_libro(self):
        return self.listado

class Decorador:
    def __init__(self,decorado,campo):
        self.campo = campo
        self.decorado = decorado
        self.libros_del_decorado=None

    def buscar_similares(self):
        lista = list()
        lista.append(self.libros())
        lista.append(self.decorado.buscar_similares())
        lista_a_retornar=list()
        for lista_de_libros in lista:
            if lista_de_libros is not None: #Puede ser None por el archivo base
                for i in range(0,len(lista_de_libros)):
                    #Se saca el repetido
                    if lista_de_libros[i] not in lista_a_retornar:
                        lista_a_retornar.append(lista_de_libros[i])
        return lista_a_retornar


    def buscar_libro(self):
        '''
            libros: param
            input_busqueda: Dictionary {'titulo': '','genero': '',}
        '''

        self.libros_del_decorado = self.decorado.buscar_libro()
        if (self.campo == ''):
            return self.libros_del_decorado
        return self.template()

#decorado = Listado_decorado(listado_de_libros)
#decoradorGenero = DecoradorGenero(decorado,self.request.GET['genero'])
#decoradorAutor = DecoradorAutor(decoradorGenero,self.request.GET['autor'])
#decoradorEditorial = DecoradorEditorial(decoradorAutor,self.request.GET['editorial'])
#decoradorTitulo = DecoradorTitulo(decoradorEditorial,self.request.GET['titulo'])
#decoradorTitulo.buscar_libro()

class DecoradorTitulo(Decorador):
    def template(self):
        titulos = Libro.objects.filter(titulo__icontains = self.campo).values('titulo')
        return self.libros_del_decorado.filter(titulo__in = titulos)

class DecoradorGenero(Decorador):
    def template(self):
        generos = Genero.objects.filter(nombre__icontains = self.campo).values('id')
        return self.libros_del_decorado.filter(genero_id__in = generos)

    def libros(self):
        return Libro.objects.filter(genero_id = self.campo)


class DecoradorAutor(Decorador):
    def template(self):
        autores = Autor.objects.filter(nombre__icontains = self.campo).values('id')
        return self.libros_del_decorado.filter(autor_id__in = autores)


    def libros(self):
        return Libro.objects.filter(autor_id = self.campo)

class DecoradorEditorial(Decorador):
    def template(self):
        editoriales = Editorial.objects.filter(nombre__icontains = self.campo).values('id')
        return self.libros_del_decorado.filter(editorial_id__in = editoriales)

    def libros(self):
        return Libro.objects.filter(editorial_id = self.campo)
