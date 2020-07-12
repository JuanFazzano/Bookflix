import datetime
import itertools
from django.contrib.auth.models import User
from django.views import View
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, FileResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponseRedirect
from forms.forms import *
from modelos.models import Libro_Incompleto, Libro_Completo, Autor, Genero, Editorial, Suscriptor, Tarjeta, \
    Tipo_Suscripcion, Trailer, Libro, Perfil, Novedad, Calificacion
from django.db.models import Q


def listado_libros_activos():
    "Filtra los capitulos no vencidos (los que no tienen fecha_vencimiento o la fecha de vencimiento no es la de hoy)"
    capitulos_activos = Capitulo.objects.filter(
        Q(fecha_lanzamiento__lte=datetime.datetime.now()) &
        (
                Q(fecha_lanzamiento__lte=datetime.datetime.now(), fecha_vencimiento=None) |
                Q(fecha_lanzamiento__lte=datetime.datetime.now(), fecha_vencimiento__gt=datetime.datetime.now())
        )
    )

    "Filtramos los libros_incompletos que esté entre los libros de capitulos activos"
    libros_incompletos_activos = Libro_Incompleto.objects.filter(id__in=capitulos_activos.values('titulo_id'))

    '''
        Filtra los LIBROS cuya fecha_vencimiento sea menor a la actual O la fecha de vencimiento no es None y está completo (con ult cap cargado )
        o el libro que esté entre los incompletos_activos
    '''
    libros_activos = Libro.objects.filter(Q(id__in=libros_incompletos_activos.values('libro_id')) |
                                          Q(esta_completo=True, fecha_lanzamiento__lte=datetime.datetime.now(),
                                            fecha_vencimiento__gt=datetime.datetime.now()) |
                                          Q(esta_completo=True, fecha_lanzamiento__lte=datetime.datetime.now(),
                                            fecha_vencimiento=None)
                                          ).distinct()

    return libros_activos


def cerrar_sesion(request):
    # Cierra la sesion del usuarios, y lo redireccion al /
    logout(request)
    return HttpResponseRedirect('/')


def eleccion_perfil(request, id=None):
    id_usuario_logueado = request.session['_auth_user_id']
    perfil = Perfil.objects.get(auth_id=id_usuario_logueado, id=id)
    request.session['perfil'] = perfil.id
    request.session['nombre_perfil'] = perfil.nombre_perfil
    return redirect('/listado_libro/')


class Vista_Resenar_libro(View):
    def __init__(self):
        self.contexto = dict()

    def get(self, request, id=None):
        self.contexto['formulario'] = FormularioReseña()
        self.contexto['libro'] = Libro.objects.get(id=id)
        return render(request, 'reseñar_libro.html', self.contexto)

    def post(self, request, id=None):
        formulario = FormularioReseña(data=request.POST)
        if formulario.is_valid():
            calificacion = Calificacion(
                valoracion=formulario.cleaned_data['puntuacion'],
                libro_id=id,
                perfil_id=request.session['perfil'],
                fecha_calificacion=datetime.datetime.now()
            )
            calificacion.save()
            "Vemos si tiene comentario y lo guardamos en su correspondiente tabla"
            comentario = formulario.cleaned_data['comentario']
            if comentario != '':
                print(calificacion)
                comentario = Comentario(
                    texto=comentario,
                    spoiler=formulario.cleaned_data['spoiler'],
                    calificacion_id=calificacion.id
                )
                comentario.save()
            calificacion.save()
            return redirect('/detalle_libro/id=' + id)
        self.contexto['formulario'] = formulario
        return render(request, 'reseñar_libro.html', self.contexto)


class Vista_Modificar_Resena_libro(View):
    def __init__(self):
        self.contexto = dict()

    def __valores_iniciales(self, id):
        calificacion = Calificacion.objects.get(id=id)
        valores_iniciales = dict()
        self.contexto['calificacion'] = calificacion
        valores_iniciales['puntuacion'] = calificacion.valoracion
        try:
            comentario = Comentario.objects.get(calificacion_id=calificacion.id)
            valores_iniciales['comentario'] = comentario.texto
            valores_iniciales['spoiler'] = comentario.spoiler
        except:
            valores_iniciales['comentario'] = ''
            valores_iniciales['spoiler'] = False
        return valores_iniciales

    def get(self, request, id):
        self.contexto['formulario'] = FormularioReseña(initial=self.__valores_iniciales(id),
                                                       comentario=Comentario.objects.get(calificacion_id=id))
        return render(request, 'reseñar_libro.html', self.contexto)

    def post(self, request, id):
        formulario = FormularioReseña(data=request.POST, initial=self.__valores_iniciales(id),
                                      comentario=Comentario.objects.get(calificacion_id=id))
        if formulario.is_valid():
            calificacion = Calificacion.objects.get(id=id)
            calificacion.valoracion = formulario.cleaned_data['puntuacion']
            calificacion.save()
            try:
                "Se guarda el comentario si existe para esa calificacion"
                comentario = Comentario.objects.get(calificacion_id=calificacion.id)
                comentario.texto = formulario.cleaned_data['comentario']
                comentario.spoiler = formulario.cleaned_data['spoiler']
            except:
                "Si no existe, se crea"
                comentario = Comentario(
                    calificacion_id=calificacion.id,
                    texto=formulario.cleaned_data['comentario'],
                    spoiler=formulario.cleaned_data['spoiler']
                )
            comentario.save()
            return redirect('/detalle_libro/id=' + str(calificacion.libro_id))
        self.contexto['errores'] = formulario.errors
        self.contexto['formulario'] = FormularioReseña(initial=self.__valores_iniciales(id))
        return render(request, 'reseñar_libro.html', self.contexto)


class Vista_Registro(View):
    def __init__(self, *args, **kwargs):
        self.contexto = dict()
        self.url = '/iniciar_sesion/'
        super(Vista_Registro, self).__init__(*args, **kwargs)

    def cargar_tarjeta(self, formulario):
        "Este metodo carga la tarjeta en caso de no existir"
        numero_tarjeta = formulario.cleaned_data['Numero_de_tarjeta']
        empresa = formulario.cleaned_data['Empresa']
        fecha_de_vencimiento = formulario.cleaned_data['Fecha_de_vencimiento']
        Codigo_de_seguridad = formulario.cleaned_data['Codigo_de_seguridad']
        tarjeta = Tarjeta(nro_tarjeta=numero_tarjeta,
                          codigo_seguridad=Codigo_de_seguridad,
                          empresa=empresa,
                          fecha_vencimiento=fecha_de_vencimiento,
                          )
        tarjeta.save()
        # return Tarjeta.objects.values('id')
        return tarjeta.id

    def __cargar_usuario_suscriptor(self, formulario):
        """
            Carga los datos del suscriptor en la tabla modelos_suscriptor, modelos_usuario y auth_user
        """
        email = formulario.cleaned_data['Email']
        dni = formulario.cleaned_data['DNI']
        numero_tarjeta = formulario.cleaned_data['Numero_de_tarjeta']
        contrasena = formulario.cleaned_data['Contrasena']
        apellido = formulario.cleaned_data['Apellido']
        nombre = formulario.cleaned_data['Nombre']
        suscripcion = formulario.cleaned_data['Suscripcion']

        id_tarjeta = self.cargar_tarjeta(formulario)

        # Cargamos el modelos User de auth_user
        model_usuario = User.objects.create_user(username=email, password=contrasena)  # Se guarda en la tabla auth_user
        model_usuario.save()

        # Tomamos las Claves foraneas
        auth_id = User.objects.values('id').get(username=email)['id']
        id_suscripcion = Tipo_Suscripcion.objects.values('id').get(tipo_suscripcion=suscripcion)['id']

        # Cargamos al suscriptor
        suscriptor = Suscriptor(auth_id=auth_id,
                                fecha_suscripcion=datetime.datetime.now().date(),
                                nombre=nombre,
                                nro_tarjeta_id=id_tarjeta,
                                apellido=apellido,
                                tipo_suscripcion_id=id_suscripcion,
                                dni=dni
                                )
        suscriptor.save()

        # nombre_perfil = nombre_apellido
        nombre_perfil = nombre + (apellido.capitalize())
        perfil_usuario = Perfil(nombre_perfil=nombre_perfil, auth_id=auth_id)
        perfil_usuario.save()

    def get(self, request):
        formulario = FormularioRegistro()
        self.contexto['formulario'] = formulario
        return render(request, 'registro.html', self.contexto)

    @csrf_exempt
    def post(self, request):
        formulario = FormularioRegistro(request.POST)
        if formulario.is_valid():
            self.__cargar_usuario_suscriptor(formulario)
            return redirect('/')
        self.contexto['formulario'] = formulario
        return render(request, 'registro.html', self.contexto)


class Vista_Crear_Perfil(View):
    def __init__(self):
        self.contexto = dict()

    def get(self, request):
        self.contexto['formulario'] = FormularioCrearPerfil()
        return render(request, 'crear_perfil.html', self.contexto)

    def post(self, request):
        formulario = FormularioCrearPerfil(data=request.POST, files=request.FILES,
                                           id_suscriptor=request.session['_auth_user_id'])
        if formulario.is_valid():
            nombre_perfil = formulario.cleaned_data['nombre']
            imagen = formulario.cleaned_data['foto']
            if imagen is not None:
                fs = FileSystemStorage()
                fs.save(imagen.name, imagen)

            "Creamos el perfil"
            perfil = Perfil(
                auth_id=request.session['_auth_user_id'],
                nombre_perfil=nombre_perfil,
                foto=imagen
            )
            perfil.save()

            return redirect('/')

        self.contexto['formulario'] = formulario
        return render(request, 'crear_perfil.html', self.contexto)


class Vista_Eliminar(View):
    def eliminar_tupla(self, id):
        self.modelo.objects.get(id=id).delete()

    def get(self, request, id=None):
        self.eliminar_tupla(id)
        self.cerrar_sesion(request)
        return redirect(self.ruta_redireccion)

    def cerrar_sesion(self, request):
        "Hook"
        pass


class Vista_Eliminar_Perfil(Vista_Eliminar):
    def __init__(self):
        self.modelo = Perfil
        self.ruta_redireccion = '/'

    def cerrar_sesion(self, request):
        request.session['perfil'] = None
        request.session['nombre_perfil'] = None


class Vista_Eliminar_Resena(Vista_Eliminar):
    def __init__(self):
        self.ruta_redireccion = None

    def eliminar_tupla(self, id):
        calificacion = Calificacion.objects.get(id=id)
        self.ruta_redireccion = '/detalle_libro/id=' + str(calificacion.libro_id)
        try:
            comentario = Comentario.objects.get(calificacinon_id=calificacion.id)
            comentario.delete()
        except:
            pass
        calificacion.delete()


class Vista_Iniciar_Sesion(View):
    def __init__(self, *args, **kwargs):
        self.__vista_html = 'iniciar_sesion.html'
        self.__contexto = {'formulario': None}  # en caso se guarda el mensaje que se va a mostrar en el html
        super(Vista_Iniciar_Sesion, self).__init__(*args, **kwargs)

    def __contextualizar_formulario(self, caso=None):
        self.__contexto['caso'] = caso or ''
        self.__contexto['formulario'] = FormularioIniciarSesion()

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('/')
        self.__contextualizar_formulario()
        return render(request, self.__vista_html, self.__contexto)

    @csrf_exempt
    def post(self, request):
        error = ''
        self.formulario = FormularioIniciarSesion(request.POST)
        if self.formulario.is_valid():
            email = self.formulario.cleaned_data['email']
            clave = self.formulario.cleaned_data['clave']
            usuario = authenticate(username=email, password=clave)
            if usuario is not None:  # El usuario se autentica
                login(request, usuario)
                id_usuario_logueado = (User.objects.values('id').get(username=email))['id']
                if not usuario.is_staff:
                    "Se guarda el perfil"
                    # request.session['perfil'] = Perfil.objects.get(auth_id = id_usuario_logueado).id
                    # request.session['nombre_perfil'] = Perfil.objects.get(auth_id = id_usuario_logueado).nombre_perfil
                    return redirect('/listado_perfiles/')
                else:
                    return redirect('/home_admin/')
            else:
                error = 'Los datos ingresados no son validos'
        self.__contextualizar_formulario(error or '')
        return render(request, self.__vista_html, self.__contexto)


class Vista_Datos_Usuario(View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/iniciar_sesion/')
        id = request.session['_auth_user_id']
        datos_suscriptor = (Suscriptor.objects.filter(auth_id=id)).values()[0]
        datos_tarjeta = Tarjeta.objects.filter(id=datos_suscriptor['nro_tarjeta_id']).values()[0]
        perfiles = Perfil.objects.values('nombre_perfil').filter(auth_id=id)
        suscriptor = Suscriptor.objects.get(auth_id=request.session['_auth_user_id'])
        contexto = {
            'suscriptor': suscriptor,
            'numero_tarjeta': datos_tarjeta['nro_tarjeta'],
            'fecha_vencimiento': datos_tarjeta['fecha_vencimiento'],
            'empresa': datos_tarjeta['empresa'],
            'perfiles': [str(clave['nombre_perfil']) for clave in list(perfiles)]
        }

        return render(request, 'datos_usuario.html', contexto)


def eliminar_suscripcion(request):
    User.objects.get(id=request.session['_auth_user_id']).delete()
    return cerrar_sesion(request)


class Vista_Visitante(View):
    def get(self, request):
        if request.user.is_authenticated:
            if request.user.is_staff:
                return redirect('/home_admin/')
            return redirect('/listado_perfiles/')
        return render(request, 'visitante.html', {'objeto_pagina': paginar(request, listado_libros_activos(), 6)})


class Buscar(View):

    def get(self, request):
        contexto = {}
        paginado = None
        if not all(map(lambda x: x == '', self.request.GET.values())):
            if (self.request.user.is_staff):
                listado_de_libros = Libro.objects.all()
            else:
                listado_de_libros = listado_libros_activos()
            decorado = Listado_decorado(listado_de_libros)
            decoradorGenero = DecoradorGenero(decorado, self.request.GET['genero'])
            decoradorAutor = DecoradorAutor(decoradorGenero, self.request.GET['autor'])
            decoradorEditorial = DecoradorEditorial(decoradorAutor, self.request.GET['editorial'])
            decoradorTitulo = DecoradorTitulo(decoradorEditorial, self.request.GET['titulo'])
            paginado = paginar(request, decoradorTitulo.buscar_libro(), 10)
        contexto['objeto_pagina'] = paginado
        contexto['modelo'] = 'libro'
        return render(request, 'listado_libro.html', contexto)


def listado_libros_buscados(request):
    "Se usa por el buscar para deolver el contexto de los libros buscados"
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
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('/iniciar_sesion/')
        return render(request, 'home_admin.html', {})


class Cambiar_Contraseña(View):
    def __init__(self, *args, **kwargs):
        self.contexto = dict()

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('/iniciar_sesion/')
        self.contexto['formulario'] = FormularioCambiarContraseña(request.session['_auth_user_id'])
        return render(request, 'cambiar_contrasena.html', self.contexto)

    def post(self, request):
        formulario = FormularioCambiarContraseña(id_usuario=request.session['_auth_user_id'], data=request.POST)
        if formulario.is_valid():
            self.__cambiar_contraseña(formulario, request.session['_auth_user_id'])
            return redirect('/iniciar_sesion/')
        self.contexto['errores'] = formulario.errors
        self.contexto['formulario'] = FormularioCambiarContraseña(id_usuario=request.session['_auth_user_id'])
        return render(request, 'cambiar_contrasena.html', self.contexto)

    def __cambiar_contraseña(self, formulario, id):
        contraseña = formulario.cleaned_data['Contraseña_nueva']
        user = User.objects.get(id=id)
        user.set_password(contraseña)
        user.save()


class Vista_Modificar_Datos_Personales(View):
    def __init__(self, *args, **kwargs):
        self.contexto = dict()
        super(Vista_Modificar_Datos_Personales, self).__init__(*args, **kwargs)

    def __valores_iniciales(self, id):
        """
            Setea los valores iniciales del formulario
        """
        email_usuario = (User.objects.values('username').filter(id=id)[0])['username']
        datos_suscriptor = (Suscriptor.objects.filter(auth_id=id).values())[0]
        datos_tarjeta = Tarjeta.objects.filter(id=datos_suscriptor['nro_tarjeta_id']).values()[0]
        suscripcion = (Tipo_Suscripcion.objects.filter(id=datos_suscriptor['tipo_suscripcion_id']).values()[0])[
            'tipo_suscripcion']
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

    def __cambiar_datos_usuario(self, formulario, id):
        print('Entre')
        nombre = formulario.cleaned_data['Nombre']
        apellido = formulario.cleaned_data['Apellido']

        suscriptor = Suscriptor.objects.get(auth_id=id)
        suscriptor.nombre = nombre
        suscriptor.apellido = apellido

        if formulario.get_datos_cambiados()['Email']:
            # Cambio el email
            auth_usuario = User.objects.get(username=self.__valores_iniciales(id)['Email'])
            auth_usuario.username = str(formulario.cleaned_data['Email'])
            auth_usuario.save()

        if formulario.get_datos_cambiados()['DNI']:
            # Cambio el DNI
            suscriptor.dni = formulario.cleaned_data['DNI']
        suscriptor.save()

        print('ID tarjeta ', suscriptor.nro_tarjeta_id)
        tarjeta = Tarjeta.objects.get(id=suscriptor.nro_tarjeta_id)
        print('La tarjeta {}'.format(tarjeta))
        tarjeta.empresa = formulario.cleaned_data['Empresa']
        tarjeta.nro_tarjeta = formulario.cleaned_data['Numero_de_tarjeta']
        tarjeta.codigo_seguridad = formulario.cleaned_data['Codigo_de_seguridad']
        tarjeta.fecha_vencimiento = formulario.cleaned_data['Fecha_de_vencimiento']
        tarjeta.save()

    def get(self, request):  # import itertools

        if not request.user.is_authenticated:
            return redirect('/iniciar_sesion/')
        formulario = FormularioModificarDatosPersonales(
            initial=self.__valores_iniciales(request.session['_auth_user_id']))
        self.contexto['formulario'] = formulario
        return render(request, 'modificar_datos_personales.html', self.contexto)

    def post(self, request):
        formulario = FormularioModificarDatosPersonales(
            initial=self.__valores_iniciales(request.session['_auth_user_id']), data=request.POST)
        if formulario.is_valid():
            self.__cambiar_datos_usuario(formulario, request.session['_auth_user_id'])
            return redirect('/datos_suscriptor/')
        self.contexto['errores'] = formulario.errors
        self.contexto['formulario'] = FormularioModificarDatosPersonales(
            initial=self.__valores_iniciales(request.session['_auth_user_id']))
        return render(request, 'modificar_datos_personales.html', self.contexto)


def paginar(request, tuplas, cantidad_maxima_paginado=1):
    "Pagina la pagina para los listados o detalle (el detalle necesita pagina por las fk)"
    paginador = Paginator(tuplas, cantidad_maxima_paginado)
    numero_de_pagina = request.GET.get('page')
    pagina = paginador.get_page(numero_de_pagina)  # Me devuelve el objeto de la pagina actualizamos
    return pagina


class Vista_Detalle(View):
    def __init__(self, *args, **kwargs):
        self.request = None
        self.contexto['modelo'] = self.modelo_string

    def get(self, request, id=None):
        self.request = request
        if not request.user.is_authenticated:
            return redirect('/iniciar_sesion/')
        try:
            # Se pagina porque si en la tabla las fk son ids, es porque el paginador asocia el id con la fila que le corresponde
            tuplas = self.modelo.objects.filter(id=id)
            self.contexto['id'] = id  # El id se usa para pasar entre las vistas, porque se usa en el "detalle.html"
            self.contexto['objeto_pagina'] = paginar(request, tuplas)
            self.cargar_diccionario(id)
            try:
                self.verificar_estado_para_terminar(id, request.session['perfil'])
            except:
                pass
            return render(request, self.url, self.contexto)
        except:
            return redirect('/')

    def cargar_diccionario(self, id, id_perfil=None):
        "Hook que sobreescriben los hijos"
        "Este mensaje carga el contexto con lo que requiera un detalle especifico"
        pass

    def verificar_estado_para_terminar(self, id_libro, id_perfil):
        pass


class Vista_Listado(View):
    def __init__(self, *args, **kwargs):
        self.contexto = {}

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('/iniciar_sesion/')
        tuplas = self.retornar_tuplas(request)
        # self.contexto = {'objeto_pagina': paginar(request,tuplas,10),'modelo': self.modelo_string}
        self.contexto['objeto_pagina'] = paginar(request, tuplas, 10)
        self.contexto['modelo'] = self.modelo_string
        # EL contexto_extra existe ya que hay tablas que tienen ids de las claves foraneas. En este dic se setean los valores de esos ids foraneos
        return render(request, self.url, self.contexto)

    def retornar_tuplas(self, request):
        "Este mensaje se puede aprovechar para carrgas cosas extras en el contxto"
        return self.modelo.objects.all()


class Vista_Listado_Favoritos(Vista_Listado):
    def __init__(self, *args, **kwargs):
        self.url = 'listado_de_favoritos.html'
        self.modelo = Libro
        self.modelo_string = 'favoritos'
        super(Vista_Listado_Favoritos, self).__init__(*args, **kwargs)

    def retornar_tuplas(self, request):
        perfil = Perfil.objects.get(id=request.session['perfil'])
        libros_activos = listado_libros_activos()
        print("abababababba")
        listado_de_favoritos_activos = perfil.listado_favoritos.filter(id__in=libros_activos.values('id'))
        return listado_de_favoritos_activos

class Vista_Listado_Libro(Vista_Listado):
    def __init__(self, *args, **kwargs):
        self.url = 'listado_libro.html'
        self.modelo = Libro
        self.modelo_string = 'libro'
        super(Vista_Listado_Libro, self).__init__(*args, **kwargs)

    def retornar_tuplas(self, request):
        if request.user.is_staff:
            return super(Vista_Listado_Libro, self).retornar_tuplas(request)
        return listado_libros_activos()


def eliminar_libro_completo(request, id):
    for lectura_libro in Lee_libro.objects.filter(libro_id=id):
        # lectura_libro.terminado=False
        # lectura_libro.save()
        lectura_libro.delete()

    Libro_Completo.objects.get(libro_id=id).delete()
    libro = Libro.objects.get(id=id)
    libro.esta_completo = False
    libro.fecha_lanzamiento = None
    libro.fecha_vencimiento = None
    libro.save()

    return redirect('/listado_libro/')


class Vista_Listado_Novedad(Vista_Listado):
    def __init__(self, *args, **kwargs):
        self.url = 'listado_novedad.html'
        self.modelo = Novedad
        self.modelo_string = 'novedad'
        super(Vista_Listado_Novedad, self).__init__(*args, **kwargs)


class Vista_Detalle_Novedad(Vista_Detalle):
    def __init__(self, *args, **kwargs):
        self.contexto = dict()
        self.url = 'detalle_novedad.html'
        self.modelo = Novedad
        self.modelo_string = 'novedad'
        super(Vista_Detalle_Novedad, self).__init__(*args, **kwargs)


class Vista_Listado_Genero(Vista_Listado):
    def __init__(self, *args, **kwargs):
        self.url = 'listado_genero.html'
        self.modelo = Genero
        self.modelo_string = 'genero'
        super(Vista_Listado_Genero, self).__init__(*args, **kwargs)


class Vista_Listado_Autor(Vista_Listado):
    def __init__(self, *args, **kwargs):
        self.url = 'listado_autor.html'
        self.modelo = Autor
        self.modelo_string = 'autor'
        super(Vista_Listado_Autor, self).__init__(*args, **kwargs)


class Vista_Listado_Editorial(Vista_Listado):
    def __init__(self, *args, **kwargs):
        self.url = 'listado_editorial.html'
        self.modelo = Editorial
        self.modelo_string = 'editorial'
        super(Vista_Listado_Editorial, self).__init__(*args, **kwargs)


class Vista_Listado_Perfiles(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('/iniciar_sesion/')
        suscriptor = Suscriptor.objects.get(auth_id=request.session['_auth_user_id'])
        return render(request, 'listado_perfiles.html', {'suscriptor': suscriptor})


class Vista_Detalle_Trailer(Vista_Detalle):
    def __init__(self, *args, **kwargs):
        self.contexto = dict()
        self.url = 'detalle_trailer.html'
        self.modelo = Trailer
        self.modelo_string = 'trailer'
        super(Vista_Detalle_Trailer, self).__init__(*args, **kwargs)


class Vista_Listado_Trailer(Vista_Listado):
    def __init__(self, *args, **kwargs):
        self.url = 'listado_trailer.html'
        self.modelo = Trailer
        self.modelo_string = 'trailer'
        super(Vista_Listado_Trailer, self).__init__(*args, **kwargs)


class Vista_Listado_Capitulo(Vista_Listado):
    def __init__(self, *args, **kwargs):
        self.id_libro = None
        self.url = 'listado_capitulo.html'
        self.modelo = Capitulo
        self.modelo_string = 'capitulo'
        super(Vista_Listado_Capitulo, self).__init__(*args, **kwargs)

    def get(self, request, id):
        self.id_libro = id
        self.contexto['libro'] = Libro.objects.get(id=(Libro_Incompleto.objects.get(libro_id=self.id_libro).libro_id))
        return super(Vista_Listado_Capitulo, self).get(request)

    def retornar_tuplas(self, es_staff):
        id_libro_incompleto = Libro_Incompleto.objects.get(libro_id=self.id_libro).id
        return Capitulo.objects.filter(titulo_id=id_libro_incompleto).order_by('capitulo')


class Vista_Formulario_Libro_Completo(View):
    def get(self, request, id=None):
        return render(request, 'formulario_libro_completo.html', {'formulario': FormularioCargaLibro()})

    def __guardar_libro_completo(self, formulario, id):
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
        libro_completo = Libro_Completo(libro_id=id, archivo_pdf=archivo_pdf)
        libro_completo.save()

        "Actualizamos su metadata"
        libro = Libro.objects.get(id=id)
        libro.fecha_lanzamiento = formulario.cleaned_data['fecha_de_lanzamiento']
        libro.fecha_vencimiento = formulario.cleaned_data['fecha_de_vencimiento']
        libro.esta_completo = True
        libro.save()

        "Borramos los capitulos del libro"
        try:
            libro_incompleto = Libro_Incompleto.objects.get(libro_id=id)

            "Borramos los capitulos del libro"
            Capitulo.objects.filter(titulo_id=libro_incompleto.id).delete()

            "Borramos la instancia de libro incompleto"
            libro_incompleto.delete()

            libros_leidos = Lee_libro.objects.filter(libro_id=libro.id)
            for libro_leido in libros_leidos:
                libros_leidos.delete()
        except:
            "No estaba cargado como libro incompleto"
            pass

    def post(self, request, id=None):
        formulario = FormularioCargaLibro(request.POST, request.FILES)
        if formulario.is_valid():
            self.__guardar_libro_completo(formulario, id)
            return redirect('/listado_libro/')
        return render(request, 'formulario_libro_completo.html', {'formulario': formulario})


class Vista_Formulario_Atributo(View):
    "Clase abstracta para la carga de autor,genero y editorial"

    def get(self, request):
        return render(request, 'carga_atributos_libro.html', self.contexto)

    @csrf_exempt
    def post(self, request):
        formulario = FormularioCargaAtributos(data=request.POST, modelo=self.modelo, nombre_modelo=self.nombre_modelo)
        if formulario.is_valid():
            # Cargamos en la BD
            modelo = self.modelo(nombre=formulario.cleaned_data['nombre'])
            modelo.save()
            return redirect(self.url_redirect)
        self.contexto['formulario'] = formulario
        return render(request, 'carga_atributos_libro.html', self.contexto)


class Vista_Formulario_Genero(Vista_Formulario_Atributo):
    def __init__(self):
        self.modelo = Genero
        self.nombre_modelo = 'genero'
        self.url_redirect = '/listado_genero/'
        self.contexto = {'formulario': FormularioCargaAtributos(Genero, 'genero'), 'modelo': 'genero'}


class Vista_Formulario_Autor(Vista_Formulario_Atributo):
    def __init__(self):
        self.modelo = Autor
        self.nombre_modelo = 'autor'
        self.url_redirect = '/listado_autor/'
        self.contexto = {'formulario': FormularioCargaAtributos(Autor, 'autor'), 'modelo': 'autor'}


class Vista_Formulario_Editorial(Vista_Formulario_Atributo):
    def __init__(self):
        self.modelo = Editorial
        self.nombre_modelo = 'editorial'
        self.url_redirect = '/listado_editorial/'
        self.contexto = {'formulario': FormularioCargaAtributos(Editorial, 'editorial'), 'modelo': 'editorial'}


class Vista_Formulario_Novedad(View):
    def get(self, request):
        return render(request, 'carga_novedad.html', {'formulario': FormularioCargaNovedad()})

    def post(self, request):
        formulario = FormularioCargaNovedad(request.POST, request.FILES)
        if formulario.is_valid():

            imagen = formulario.cleaned_data['foto']
            if imagen is not None:
                fs = FileSystemStorage()
                fs.save(imagen.name, imagen)
            novedad = Novedad(
                titulo=formulario.cleaned_data['titulo'],
                descripcion=formulario.cleaned_data['descripcion'],
                foto=imagen
            )
            novedad.save()
            return redirect('/listado_novedad/')
        return render(request, 'carga_novedad.html', {'formulario': formulario})



class Vista_Formulario_Trailer(View):
    def __init__(self):
        self.contexto = {'modelo': 'trailer'}

    def __carga_archivo(self, campo_archivo):
        archivo = campo_archivo
        if archivo is not None:
            fs = FileSystemStorage()
            fs.save(archivo.name, archivo)

    def get(self, request):
        self.contexto['formulario'] = FormularioCargaTrailer()
        return render(request, 'carga_atributos_libro.html', self.contexto)

    def post(self, request):
        formulario = FormularioCargaTrailer(request.POST, request.FILES)
        if formulario.is_valid():
            self.__carga_archivo(formulario.cleaned_data['pdf'])
            self.__carga_archivo(formulario.cleaned_data['video'])
            trailer = Trailer(
                titulo=formulario.cleaned_data['titulo'],
                descripcion=formulario.cleaned_data['descripcion'],
                pdf=formulario.cleaned_data['pdf'],
                video=formulario.cleaned_data['video'],
                libro_asociado_id=formulario.cleaned_data['libro']
            )
            trailer.save()
            return redirect('/listado_trailer/')
        self.contexto['errores'] = formulario.errors
        self.contexto['formulario'] = FormularioCargaTrailer()
        return render(request, 'carga_atributos_libro.html', self.contexto)


class Vista_Modificar_Novedad(View):
    def __get_valores_inicials(self, id):
        novedad = Novedad.objects.get(id=id)
        return {
            'titulo': novedad.titulo,
            'descripcion': novedad.descripcion if (novedad.descripcion is not None) else '',
            'foto': novedad.foto if (novedad.foto is not None) else ''
        }

    def get(self, request, id=None):
        print(self.__get_valores_inicials(id)['foto'])
        return render(request, 'carga_novedad.html',
                      {'formulario': FormularioModificarNovedad(initial=self.__get_valores_inicials(id))})

    def post(self, request, id=None):
        formulario = FormularioModificarNovedad(request.POST, request.FILES, initial=self.__get_valores_inicials(id))
        if formulario.is_valid():

            imagen = formulario.cleaned_data['foto']
            print('Imagen ', imagen)
            if imagen:
                fs = FileSystemStorage()
                fs.save(imagen.name, imagen)
            novedad = Novedad.objects.get(id=id)
            novedad.titulo = formulario.cleaned_data['titulo']
            novedad.descripcion = formulario.cleaned_data['descripcion']
            novedad.foto = formulario.cleaned_data['foto'] if (imagen) else None
            novedad.save()
            return redirect('/listado_novedad/')

        return render(request, 'carga_novedad.html',
                      {'formulario': FormularioModificarNovedad(initial=self.__get_valores_inicials(id)),
                       'errores': formulario.errors})


class Vista_Formulario_Modificar_Atributo(View):
    def __init__(self):
        self.nombre = None
        self.contexto = {'formulario': None, 'modelo': self.nombre_modelo}

    def __get_iniciales(self, id):
        "Devuelve los valores iniciales"
        self.nombre = self.modelo.objects.get(id=id).nombre
        return {'nombre': self.nombre}

    def get(self, request, id=None):
        self.contexto['formulario'] = FormularioModificarAtributos(initial=self.__get_iniciales(id), modelo=self.modelo,
                                                                   nombre_modelo=self.nombre_modelo)
        return render(request, 'carga_atributos_libro.html', self.contexto)

    def post(self, request, id=None):
        formulario = FormularioModificarAtributos(data=request.POST, initial=self.__get_iniciales(id),
                                                  modelo=self.modelo, nombre_modelo=self.nombre_modelo)
        if formulario.is_valid():
            modelo = self.modelo.objects.get(id=id)
            modelo.nombre = formulario.cleaned_data['nombre']
            modelo.save()
            return redirect(self.url_redirect)
        self.contexto['errores'] = formulario.errors
        self.contexto['formulario'] = FormularioModificarAtributos(initial=self.__get_iniciales(id), modelo=self.modelo,
                                                                   nombre_modelo=self.nombre_modelo)
        return render(request, 'carga_atributos_libro.html', self.contexto)


class Vista_Formulario_Modificar_Genero(Vista_Formulario_Modificar_Atributo):
    def __init__(self):
        self.modelo = Genero
        self.nombre_modelo = 'genero'
        self.url_redirect = '/listado_genero/'
        super(Vista_Formulario_Modificar_Genero, self).__init__()


class Vista_Formulario_Modificar_Autor(Vista_Formulario_Modificar_Atributo):
    def __init__(self):
        self.modelo = Autor
        self.nombre_modelo = 'autor'
        self.url_redirect = '/listado_autor/'
        super(Vista_Formulario_Modificar_Autor, self).__init__()


class Vista_Formulario_Modificar_Editorial(Vista_Formulario_Modificar_Atributo):
    def __init__(self):
        self.modelo = Editorial
        self.nombre_modelo = 'editorial'
        self.url_redirect = '/listado_editorial/'
        super(Vista_Formulario_Modificar_Editorial, self).__init__()


class Vista_Formulario_Modificar_Trailer(View):
    def __init__(self):
        self.contexto = {'modelo': 'trailer'}

    def __get_valores_iniciales(self, id):
        trailer = Trailer.objects.get(id=id)
        return {
            'titulo': trailer.titulo,
            'descripcion': trailer.descripcion,
            'pdf': trailer.pdf if (trailer.pdf is not None) else None,
            'video': trailer.video if (trailer.video is not None) else None,
            'libro': trailer.libro_asociado_id if (trailer.libro_asociado is not None) else ''
        }

    def get(self, request, id=None):
        self.contexto['formulario'] = FormularioModificarTrailer(initial=self.__get_valores_iniciales(id))
        return render(request, 'carga_atributos_libro.html', self.contexto)

    def post(self, request, id=None):
        formulario = FormularioModificarTrailer(request.POST, request.FILES, initial=self.__get_valores_iniciales(id))
        if formulario.is_valid():
            trailer = Trailer.objects.get(id=id)
            trailer.titulo = formulario.cleaned_data['titulo']
            trailer.descripcion = formulario.cleaned_data['descripcion']
            trailer.pdf = None if (not formulario.cleaned_data['pdf']) else formulario.cleaned_data['pdf']
            trailer.video = None if (not formulario.cleaned_data['video']) else formulario.cleaned_data['video']
            trailer.libro_asociado_id = formulario.cleaned_data['libro']
            trailer.save()
            return redirect('/listado_trailer/')
        self.contexto['errores'] = formulario.errors
        self.contexto['formulario'] = FormularioModificarTrailer(initial=self.__get_valores_iniciales(id))
        return render(request, 'carga_atributos_libro.html', self.contexto)


def marcar_como_terminado(request, id=None):
    id_perfil = request.session['perfil']
    libro = Libro.objects.get(id=id)
    relacion_lee_libro = Lee_libro.objects.get(perfil_id=id_perfil, libro_id=id)
    relacion_lee_libro.terminado = True
    relacion_lee_libro.save()
    path = '/detalle_libro/id=' + id
    return redirect(path)


def cambiar_tipo_suscripcion(request):
    id_usuario = request.session['_auth_user_id']
    usuario = Suscriptor.objects.get(auth_id=id_usuario)

    if usuario.tipo_suscripcion.tipo_suscripcion == 'premium':
        usuario.tipo_suscripcion = Tipo_Suscripcion.objects.get(tipo_suscripcion='regular')
    else:
        usuario.tipo_suscripcion = Tipo_Suscripcion.objects.get(tipo_suscripcion='premium')
    usuario.save()

    return redirect('/datos_suscriptor/')


class Agregar_a_favoritos(View):
    def __init__(self, *args, **kwargs):
        self.path = None
        super(Agregar_a_favoritos, self).__init__(*args, **kwargs)

    def get(self, request, id):
        id_perfil = request.session['perfil']
        perfil = Perfil.objects.get(id=id_perfil)
        libro = Libro.objects.get(id=id)
        self.cambiar_favorito(perfil, libro)
        return redirect(self.path)

    def cambiar_favorito(self, perfil=None, libro=None):
        self.path = '/detalle_libro/id=' + str(libro.id)
        perfil.listado_favoritos.add(libro)
        perfil.save()


class Quitar_de_favoritos(Agregar_a_favoritos):
    def cambiar_favorito(self, perfil=None, libro=None):
        self.path = '/detalle_libro/id=' + str(libro.id)
        perfil.listado_favoritos.remove(libro)


class Quitar_de_favoritos_desde_listado(Quitar_de_favoritos):
    def cambiar_favorito(self, perfil=None, libro=None):
        super(Quitar_de_favoritos_desde_listado, self).cambiar_favorito(perfil, libro)
        self.path = '/listado_de_favoritos/'


def marcar_comentario_spoiler(request, id_comentario=None, id_libro=None):
    comentario = Comentario.objects.get(id=id_comentario)
    comentario.spoiler = True
    if request.user.is_staff:
        comentario.spoiler_admin = True
    comentario.save()
    return redirect('/detalle_libro/id=' + id_libro)


def desmarcar_comentario_spoiler(request, id_comentario=None, id_libro=None):
    comentario = Comentario.objects.get(id=id_comentario)
    comentario.spoiler = False
    comentario.spoiler_admin = False
    comentario.save()
    return redirect('/detalle_libro/id=' + id_libro)


class Vista_Detalle_libro(Vista_Detalle):
    def __init__(self, *args, **kwargs):
        self.contexto = dict()
        self.contexto['formulario_reseña'] = FormularioReseña()
        self.modelo_string = 'libro'
        self.url = 'detalle_libro.html'
        self.modelo = Libro
        super(Vista_Detalle_libro, self).__init__(*args, **kwargs)

    def cargar_diccionario_1(self, id):  # TODO eliminar este mensaje antes de la demo
        trailers = Trailer.objects.filter(libro_asociado_id=id).values('titulo', 'id')
        libro = Libro.objects.filter(id=id)[0]
        if libro.esta_completo:
            # libro_completo =  Libro_Completo.objects.values().filter(libro_id = libro.id)
            libro_completo = Libro_Completo.objects.get(libro_id=libro.id)
            print('VALORES COMPLETO ', libro_completo)
            self.contexto['completo'] = libro_completo
        self.contexto['trailers'] = trailers
        decoradorGenero = DecoradorGenero(libro, libro.genero_id)
        decoradorAutor = DecoradorAutor(decoradorGenero, libro.autor_id)
        decoradorEditorial = DecoradorEditorial(decoradorAutor, libro.editorial_id)
        listado_de_libros_similares = decoradorEditorial.buscar_similares()
        listado_de_libros_similares = list(filter(lambda libro2: libro2.id != int(id),
                                                  listado_de_libros_similares))  # saca el libro de donde estoy parado.
        self.contexto['libros_similares'] = listado_de_libros_similares

    def cargar_diccionario(self, id):
        trailers = Trailer.objects.filter(libro_asociado_id=id)
        libro = Libro.objects.filter(id=id)[0]

        "Si esta completo o si fue cargado por capitulos y tiene fecha de lanzamiento"
        # if libro.esta_completo or libro.fecha_lanzamiento is not None:
        # libro_completo = Libro_Completo.objects.get(libro_id=libro.id)
        # self.contexto['completo'] = libro_completo

        "Este fragmento de codigo carga, para el libro actual, si el perfil lo termino"
        try:
            "Si esta en la tabla lee_libro, carga el estado de terminado"
            self.contexto['terminado'] = Lee_libro.objects.get(libro_id=libro.id,
                                                               perfil_id=(self.request.session['perfil'])).terminado
        except:
            "Si no esta, lo setea en false"
            self.contexto['terminado'] = False
        print('QUE ONDA ', self.contexto['terminado'])

        "Este fragmento de codigo carga para ese libro si el perfil logueado ya lo resenio"

        "Devuelve las resenias del libro"
        resenas_libro = libro.reseñas()
        try:
            "Se rompe si sos admin"
            resena_perfil = resenas_libro.filter(perfil_id=(self.request.session['perfil']))
            self.contexto['fue_resenado'] = resena_perfil.exists()

            "Si resenio, este fragmento carga la resenia y ademas carga todas las calificaciones"
            if self.contexto['fue_resenado']:
                self.contexto['resena_perfil'] = list(resena_perfil)[0]
                "Saco la resenia del perfil, ya que va a estar al principio"
                resenas_libro = resenas_libro.exclude(perfil_id=(self.request.session['perfil']))
            else:
                self.contexto['resena_perfil'] = None
            id_perfil = self.request.session['perfil']
            self.contexto['lo_tengo_como_favorito'] = Libro.objects.filter(id=id, perfil__id=id_perfil).exists()

        except:
            pass
        self.contexto['resenas'] = paginar(self.request, resenas_libro, 4)  # Paginarlas
        self.contexto['trailers'] = paginar(self.request, trailers, 10)

        "Cargamos los libros similares"
        decoradorGenero = DecoradorGenero(libro, libro.genero_id)
        decoradorAutor = DecoradorAutor(decoradorGenero, libro.autor_id)
        decoradorEditorial = DecoradorEditorial(decoradorAutor, libro.editorial_id)
        listado_de_libros_similares = set(list(itertools.chain.from_iterable(decoradorEditorial.buscar_similares())))
        listado_de_libros_similares = list(filter(lambda libro2: libro2.id != int(id),
                                                  listado_de_libros_similares))  # saca el libro de donde estoy parado.
        self.contexto['libros_similares'] = listado_de_libros_similares

    def verificar_estado_para_terminar(self, id_libro, id_perfil):
        self.contexto['error'] = None
        libro = Libro.objects.get(id=id_libro)
        if (libro.fecha_lanzamiento):  # en este caso el libro esta completo por capitulos o con un solo archivo
            print('entre')
            perfil_leyo_libro = Lee_libro.objects.filter(perfil_id=id_perfil, libro_id=id_libro)
            if (perfil_leyo_libro.exists()):
                if (not perfil_leyo_libro.values()[0]['terminado']):
                    if (not libro.esta_completo):  # si el libro tiene un solo archivo
                        libro_incompleto = Libro_Incompleto.objects.get(libro_id=id_libro)
                        capitulos_del_libro = Capitulo.objects.filter(titulo_id=libro_incompleto.id)
                        if (not capitulos_del_libro.count() == Lee_Capitulo.objects.filter(perfil_id=id_perfil,
                                                                                           capitulo_id__in=capitulos_del_libro.values(
                                                                                                   'id')).count()):
                            self.contexto['error'] = 'Primero debe leer todos los capítulos'
                    return
                else:
                    self.contexto['error'] = 'Usted ya termino el libro'

            else:
                self.contexto['error'] = 'Primero debe leer el libro'
        else:
            self.contexto['error'] = 'El libro no esta completo todavia'


class Vista_Carga_Metadatos_Libro(View):
    def __init__(self, *args, **kwargs):
        self.contexto = dict()
        self.url = '/listado_libro/'
        super(Vista_Carga_Metadatos_Libro, self).__init__(*args, **kwargs)

    def __cargar_metadatos_libro(self, formulario):
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
        nuevo_libro = Libro(titulo=titulo, ISBN=isbn, foto=archivo_imagen, descripcion=descripcion, autor_id=autor,
                            editorial_id=editorial, genero_id=genero)
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
    def __get_valores_inicials(self, id):
        libro = Libro.objects.get(id=id)
        return {
            'titulo': libro.titulo,
            'ISBN': libro.ISBN,
            'descripcion': libro.descripcion if (libro.descripcion is not None) else '',
            'imagen': libro.foto if (libro.foto is not None) else '',
            'autor': libro.autor_id,
            'genero': libro.genero_id,
            'editorial': libro.editorial_id,
        }

    def get(self, request, id=None):
        return render(request, 'carga_atributos_libro.html',
                      {'formulario': Formulario_modificar_metadatos_libro(initial=self.__get_valores_inicials(id)),
                       'modelo': 'libro'})

    def post(self, request, id=None):
        formulario = Formulario_modificar_metadatos_libro(request.POST, request.FILES,
                                                          initial=self.__get_valores_inicials(id))
        if formulario.is_valid():
            imagen = formulario.cleaned_data['imagen']
            print('Imagen ', imagen)
            if imagen:
                fs = FileSystemStorage()
                fs.save(imagen.name, imagen)
            libro = Libro.objects.get(id=id)
            libro.titulo = formulario.cleaned_data['titulo']
            libro.ISBN = formulario.cleaned_data['ISBN']
            libro.descripcion = formulario.cleaned_data['descripcion']
            libro.foto = formulario.cleaned_data['imagen'] if (imagen) else None
            libro.autor_id = formulario.cleaned_data['autor']
            libro.genero_id = formulario.cleaned_data['genero']
            libro.editorial_id = formulario.cleaned_data['editorial']
            libro.save()
            return redirect('/listado_libro/')
        return render(request, 'carga_atributos_libro.html',
                      {'formulario': Formulario_modificar_metadatos_libro(initial=self.__get_valores_inicials(id)),
                       'modelo': 'libro', 'errores': formulario.errors})


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

    def cambiamos_fechas_capitulos(self, id, fecha_lanzamiento, fecha_vencimiento):
        "Cambia las fechas de los capitulos del libro para mantener la consistencia"
        try:
            capitulos = Capitulo.objects.filter(titulo_id=id)
            for capitulo in capitulos:
                capitulo.fecha_lanzamiento = fecha_lanzamiento
                capitulo.fecha_vencimiento = fecha_vencimiento
                capitulo.save()

        except:
            return None

    def cambiar_fechas(self, id, formulario):
        "Cambia las fechas del libro (el boton se habilita cuando esté completo o tenga el último capitulo cargado"
        libro = Libro.objects.get(id=id)
        fecha_lanzamiento = formulario.cleaned_data['fecha_de_lanzamiento']
        fecha_vencimiento = formulario.cleaned_data['fecha_de_vencimiento']
        libro.fecha_lanzamiento = fecha_lanzamiento
        libro.fecha_vencimiento = fecha_vencimiento
        libro.save()
        try:
            self.cambiamos_fechas_capitulos((Libro_Incompleto.objects.get(libro_id=id).id), fecha_lanzamiento,
                                            fecha_vencimiento)

        except:
            pass

    def get(self, request, id=None):
        # TODO hacer que la fecha de vencimiento sea opcional. Actualmentee
        esta_completo = Libro.objects.get(id=id).esta_completo
        valores_fechas = self.__get_valores_inicials(id)
        return render(request, 'carga_atributos_libro.html', {
            'formulario': FormularioCargaFechas(valores_fechas['fecha_de_lanzamiento'],
                                                valores_fechas['fecha_de_vencimiento']), 'modelo': 'libro'})

    def post(self, request, id=None):
        valores_fechas = self.__get_valores_inicials(id)
        formulario = FormularioCargaFechas(data=request.POST, lanzamiento=valores_fechas['fecha_de_lanzamiento'],
                                           vencimiento=valores_fechas['fecha_de_vencimiento'],
                                           initial=self.__get_valores_inicials(id))
        if formulario.is_valid():
            self.cambiar_fechas(id, formulario)
            return redirect('/listado_libro/')
        return render(request, 'carga_atributos_libro.html', {
            'formulario': FormularioCargaFechas(valores_fechas['fecha_de_lanzamiento'],
                                                valores_fechas['fecha_de_vencimiento']), 'errores': formulario.errors,
            'modelo': 'libro'})


class Vista_Alta_Capitulo(View):
    def __init__(self):
        self.contexto = {'modelo': 'libro'}

    def get_capitulo_mas_grande(self, id):
        "id:int que representa el titulo_id (id del Libro)"
        "Devuelve el capítulo más grande cargado"
        capitulos = Capitulo.objects.filter(titulo_id=Libro_Incompleto.objects.get(libro_id=id).id)
        capitulo_maximo = 1  # Por defecto sugiere el 1
        if capitulos:  # Si hay capitulos
            capitulo_maximo = (capitulos.order_by('-capitulo').values('capitulo')).first()  # Ordena de mayor a menor
            capitulo_maximo = capitulo_maximo['capitulo'] + 1
        return capitulo_maximo

    def cargar_incompleto(self, id):
        "Carga el libro incompleto en caso de que sea la primera carga"
        try:
            incompleto = Libro_Incompleto(libro_id=id)
            incompleto.save()
        except:
            pass

    def cambiamos_fechas_capitulos(self, id, fecha_lanzamiento, fecha_vencimiento):
        "Cambia las fechas de los capitulos del libro para mantener la consistencia"
        try:
            capitulos = Capitulo.objects.filter(titulo_id=id)
            for capitulo in capitulos:
                capitulo.fecha_lanzamiento = fecha_lanzamiento
                capitulo.fecha_vencimiento = fecha_vencimiento
                capitulo.save()

        except:
            return None

    def get(self, request, id=None):
        self.cargar_incompleto(id)
        self.contexto['formulario'] = FormularioCapitulo(id=id,
                                                         initial={'numero_capitulo': self.get_capitulo_mas_grande(id)})
        self.contexto['libro_asociado'] = Libro.objects.get(id=id)
        return render(request, 'carga_atributos_libro.html', self.contexto)

    def post(self, request, id=None):
        formulario = FormularioCapitulo(data=request.POST, files=request.FILES, id=id)
        if formulario.is_valid():
            # Si es valido el formulario, cargo el capitulo
            incompleto = Libro_Incompleto.objects.get(libro_id=id)
            capitulo = Capitulo(
                capitulo=formulario.cleaned_data['numero_capitulo'],
                archivo_pdf=formulario.cleaned_data['archivo_pdf'],
                titulo_id=incompleto.id,
            )
            capitulo.fecha_lanzamiento = formulario.cleaned_data['fecha_de_lanzamiento']
            capitulo.fecha_vencimiento = formulario.cleaned_data['fecha_de_vencimiento']
            if formulario.cleaned_data['ultimo_capitulo']:
                "Si no es el ultimo capitulo, le cargo la fecha"
                libro = Libro.objects.get(id=id)
                libro.fecha_lanzamiento = formulario.cleaned_data['fecha_de_lanzamiento']
                libro.fecha_vencimiento = formulario.cleaned_data['fecha_de_vencimiento']
                capitulo.ultimo = True
                libro.save()
                incompleto.esta_completo = True
                incompleto.save()
            capitulo.save()
            try:
                "Siempre que agregue un capitulo, si se leyo el libro y alguien lo termino, lo pone en curso"
                for libro_leido in Lee_libro.objects.filter(libro_id=incompleto.libro_id):
                    libro_leido.terminado = False
                    libro_leido.save()
            except:
                pass

            return redirect('/listado_libro/')
        self.contexto['formulario'] = formulario
        return render(request, 'carga_atributos_libro.html', self.contexto)


class Vista_Modificar_Capitulo(View):
    def get(self, request, id=None):
        capitulo = Capitulo.objects.get(id=id)
        libro_incompleto_asociado = Libro_Incompleto.objects.get(id=capitulo.titulo_id)
        contexto = {'formulario': Formulario_Modificar_Capitulo(capitulo, libro_incompleto_asociado)}
        contexto['libro_asociado'] = Libro.objects.get(id=libro_incompleto_asociado.libro_id)
        return render(request, 'carga_atributos_libro.html', contexto)

    def sacar_libro_como_completo(self, libro_incompleto):
        libro_incompleto.esta_completo = False
        libro_incompleto.save()
        libro = Libro.objects.get(id=libro_incompleto.libro_id)
        libro.fecha_lanzamiento = None
        libro.fecha_vencimiento = None
        libro.save()

    def cambiamos_fechas_capitulos(self, id, fecha_lanzamiento, fecha_vencimiento):
        "Cambia las fechas de los capitulos del libro para mantener la consistencia"
        try:
            capitulos = Capitulo.objects.filter(titulo_id=id)
            for capitulo in capitulos:
                capitulo.fecha_lanzamiento = fecha_lanzamiento
                capitulo.fecha_vencimiento = fecha_vencimiento
                capitulo.save()

        except:
            return None

    def registrar_libro_como_completo(self, libro_incompleto, formulario):
        libro_incompleto.esta_completo = True
        libro_incompleto.save()
        libro = Libro.objects.get(id=libro_incompleto.libro_id)
        libro.fecha_lanzamiento = formulario.cleaned_data['fecha_de_lanzamiento']
        libro.fecha_vencimiento = formulario.cleaned_data['fecha_de_vencimiento']
        libro.save()
        self.cambiamos_fechas_capitulos(libro_incompleto.id, formulario.cleaned_data['fecha_de_lanzamiento'],
                                        formulario.cleaned_data['fecha_de_vencimiento'])

    def modificacion_del_capitulo(self, request, capitulo, libro_incompleto_asociado, formulario):
        if (capitulo.ultimo):
            "Si es el ultimo y en el formulario desmarcaste el checkbox Ultimo Capitulo, lo eliminar como libro_incompleto"
            if (not formulario.cleaned_data['ultimo_capitulo']):
                self.sacar_libro_como_completo(libro_incompleto_asociado)
                capitulo.ultimo = False
        else:
            "Si no es el ultimo capitulo, y el libro no tiene marcado un ultimo capitulo"
            if (not libro_incompleto_asociado.esta_completo):
                "Si en el formulario marcaste el ultimo capitulo"
                if (formulario.cleaned_data['ultimo_capitulo']):
                    self.registrar_libro_como_completo(libro_incompleto_asociado, formulario)
                    capitulo.ultimo = True
                capitulo.fecha_vencimiento = formulario.cleaned_data['fecha_de_vencimiento']
                capitulo.fecha_lanzamiento = formulario.cleaned_data['fecha_de_lanzamiento']
        capitulo.capitulo = formulario.cleaned_data['numero_capitulo']
        if (formulario.cleaned_data['archivo_pdf'] is not None and formulario.cleaned_data[
            'archivo_pdf'] != capitulo.archivo_pdf):
            "Si se modifica el archivo"
            capitulo.archivo_pdf = formulario.cleaned_data['archivo_pdf']
            libro_leido = Lee_libro.objects.get(libro_id=libro_incompleto_asociado.libro_id)
            for perfil in Perfil.objects.all():
                capitulo_leido = Lee_Capitulo.objects.filter(capitulo_id=capitulo.id, perfil_id=perfil.id)
                if capitulo_leido.exists():
                    "Si el perfil leyo el capitulo, lo sacamos de sus capitulos leidos"
                    capitulo_leido.delete()
                    # if Lee_libro.objects.filter(perfil_id = perfil.id,libro_id = libro_leido.id).exists():
                    "Si no existe tupla que cumpla que el perfil leyo un capitulo perteneciente al libro asociado, es decir, se modifica el unico capitulo leido por el perfil"
                    if not Lee_Capitulo.objects.filter(perfil_id=perfil.id,
                                                       capitulo_id__in=libro_incompleto_asociado.capitulos().values(
                                                               'id')).exists():
                        libro_leido.delete()
                    else:
                        "Si exsite tupla, solo marca en false"
                        libro_leido.terminado = False
                        libro_leido.save()
        capitulo.save()

    def post(self, request, id=None):
        capitulo = Capitulo.objects.get(id=id)
        libro_incompleto_asociado = Libro_Incompleto.objects.get(id=capitulo.titulo_id)
        formulario = Formulario_Modificar_Capitulo(data=request.POST, files=request.FILES, capitulo=capitulo,
                                                   libro_asociado=libro_incompleto_asociado)
        if formulario.is_valid():
            self.modificacion_del_capitulo(request, capitulo, libro_incompleto_asociado, formulario)
            path = ('/listado_capitulo/id=' + str(libro_incompleto_asociado.libro_id))
            return redirect(path)
        contexto = {'errores': formulario.errors}
        contexto['libro_asociado'] = Libro.objects.get(id=libro_incompleto_asociado.libro_id)
        contexto['formulario'] = Formulario_Modificar_Capitulo(capitulo, libro_incompleto_asociado)
        return render(request, 'carga_atributos_libro.html', contexto)


class Vista_Lectura_Libro(View):  # TODO validar que el libro este activo
    def __init__(self, *args, **kwargs):
        self.contexto = {}
        self.id = None  # El id puede ser el id del libro o el id_capitulo

    def get(self, request, id=None):
        self.id = id
        if self.esta_vencido():
            return redirect(self.url_redirect())

        if not request.user.is_authenticated:
            return redirect('/iniciar_sesion/')
        self.marcar_como_leido(id_perfil=request.session['perfil'])
        return render(request, 'lectura_pdf.html', self.contexto)

    def esta_vencido(self):
        return Libro.objects.get(id=self.id).esta_vencido()

    def url_redirect(self):
        return '/listado_libro/'

    def marcar_existente(self):
        "Hook"
        pass

    def marcar_nuevo(self):
        "Hook"
        pass

    def actualizar_contexto(self):
        "Hook"
        pass

    def marcar_como_leido(self, id_perfil):
        try:
            self.marcar_nuevo(id_perfil)
        except:
            self.marcar_existente(id_perfil)

        self.actualizar_contexto()


class Vista_Lectura_Capitulo(Vista_Lectura_Libro):
    def __init__(self, *args, **kwargs):
        super(Vista_Lectura_Capitulo, self).__init__(*args, **kwargs)

    def url_redirect(self):
        # 3return '/listado_capitulo/id='+str(Libro.objects.get(id = Libro_Incompleto.objects.get(id =Capitulo.objects.get(id=self.id).titulo_id).libro_id))
        return '/listado_capitulo/id=' + str(
            Libro_Incompleto.objects.get(id=Capitulo.objects.get(id=self.id).titulo_id).libro_id)

    def esta_vencido(self):
        return Capitulo.objects.get(id=self.id).esta_vencido()

    def marcar_existente(self, id_perfil):
        capitulo_leido = Lee_Capitulo.objects.get(perfil_id=id_perfil, capitulo_id=self.id)
        capitulo_leido.ultimo_acceso = datetime.datetime.now()
        capitulo_leido.save()

        "Lo guardo en la tabla Lee_libro"
        id_libro_incompleto = Capitulo.objects.get(id=capitulo_leido.capitulo_id).titulo_id
        libro_id = Libro_Incompleto.objects.get(id=id_libro_incompleto).libro_id
        libro_leido = Lee_libro.objects.get(libro_id=libro_id, perfil_id=id_perfil)
        print(libro_leido)
        libro_leido.ultimo_acceso = datetime.datetime.now()
        libro_leido.save()

    def marcar_nuevo(self, id_perfil):
        capitulo_leido = Lee_Capitulo(
            capitulo_id=self.id,
            perfil_id=id_perfil,
            ultimo_acceso=datetime.datetime.now()
        )
        capitulo_leido.save()

        "Lo guardo en la tabla Lee_Libro"
        id_libro_incompleto = Capitulo.objects.get(id=capitulo_leido.capitulo_id).titulo_id
        libro_id = Libro_Incompleto.objects.get(id=id_libro_incompleto).libro_id
        libro_leido = Lee_libro(
            terminado=False,
            ultimo_acceso=datetime.datetime.now(),
            perfil_id=id_perfil,
            libro_id=libro_id
        )
        libro_leido.save()

    def actualizar_contexto(self):
        self.contexto = {'pdf': Capitulo.objects.get(id=self.id).archivo_pdf}


class Vista_Lectura_Libro_Completo(Vista_Lectura_Libro):
    def __init__(self, *args, **kwargs):
        super(Vista_Lectura_Libro_Completo, self).__init__(*args, **kwargs)

    def marcar_existente(self, id_perfil):
        libro_leido = Lee_libro.objects.get(perfil_id=id_perfil, libro_id=self.id)
        libro_leido.ultimo_acceso = datetime.datetime.now()
        libro_leido.save()

    def marcar_nuevo(self, id_perfil):
        libro_leido = Lee_libro(
            libro_id=self.id,
            perfil_id=id_perfil,
            terminado=False,
            ultimo_acceso=datetime.datetime.now()
        )
        libro_leido.save()

    def actualizar_contexto(self):
        self.contexto = {'pdf': Libro_Completo.objects.get(libro_id=self.id).archivo_pdf}


class Vista_Historial(View):

    def __init__(self):
        self.pagina = None

    def get(self, request, pagina=None):
        self.pagina = int(pagina)
        return render(request, 'historial.html', self.obtener_libros_leidos(request.session['perfil'], request))

    def obtener_capitulos_de_libro(self, request, libro, perfil):
        libro_actual = Libro.objects.get(id=libro.libro_id)
        if (not libro_actual.esta_completo):
            try:
                libro_incompleto = Libro_Incompleto.objects.get(libro_id=libro.libro_id)
                capitulos_del_libro = Capitulo.objects.filter(titulo_id=libro_incompleto.id)
                capitulos_leidos = Lee_Capitulo.objects.filter(perfil_id=perfil,
                                                               capitulo_id__in=capitulos_del_libro.values(
                                                                   'id')).order_by('-ultimo_acceso')
                return paginar(request, capitulos_leidos, capitulos_leidos.count())
            except:
                return None
        return None

    def obtener_libro(self, libro):
        return Libro.objects.get(id=libro.libro_id)

    def obtener_libros_leidos(self, id_perfil, request):
        id_autoincremental = 0
        contexto = {'libros': []}
        for libro in (Lee_libro.objects.filter(perfil_id=id_perfil).order_by('-ultimo_acceso')):
            libro1 = Libro.objects.get(id=libro.libro_id)
            contexto['libros'].append({
                'libro': libro1,
                'lee_libro': Lee_libro.objects.get(libro_id=libro1.id, perfil_id=id_perfil),
                'capitulos': self.obtener_capitulos_de_libro(request, libro, id_perfil)
            })

        cantidad_libro = 3

        cantidad_libros_leidos = Lee_libro.objects.filter(perfil_id=id_perfil).count()
        paginas = (cantidad_libros_leidos // cantidad_libro) + 1 if (cantidad_libros_leidos % cantidad_libro) > 0 else (
                    cantidad_libros_leidos // cantidad_libro)

        contexto['es_pagina_inicial'] = True if (self.pagina == 1) else False
        contexto['tiene_siguiente'] = self.pagina < paginas
        contexto['libros'] = contexto['libros'][
                             ((self.pagina - 1) * cantidad_libro):((self.pagina - 1) * cantidad_libro + cantidad_libro)]
        contexto['numero_pagina'] = self.pagina
        contexto['nombre_perfil'] = Perfil.objects.get(id=id_perfil).nombre_perfil
        return contexto


class Vista_Reporte_Libros(View):
    def get(self, request, pagina=None):
        ''' Nos queda con todos los libros ordenados segun el orden de cual fue más leido '''
        # libros = Lee_libro.objects.values('libro_id').all().annotate(lectores_totales=Count(libro_id)).order_by('lectores_totales')
        libros = Libro.objects.all()
        libros = sorted(libros, key=lambda libro: libro.cantidad_lectores_totales(), reverse=True)
        contexto = {}
        contexto['libros'] = paginar(request, libros, 10)
        return render(request, 'reporte_libros.html', contexto)


class Vista_Reporte_Suscriptores(View):
    def get(self, request, pagina=None):
        contexto = {}
        error = ''
        try:
            fecha_inicio = request.GET['fecha_inicio']
            fecha_fin = request.GET['fecha_fin']
            if fecha_inicio != '':
                if fecha_fin == '':
                    "Si no puso una fecha de fin, tomamos por defecto la actual"
                    fecha_fin = datetime.datetime.now().date()

                if fecha_inicio > fecha_fin:
                    error = 'La fecha límite no puede ser inferior a la fecha de inicio'

                if error == '':
                    "Si no hubo error, agregamos al contexto los suscriptores"
                    suscriptores = Suscriptor.objects.filter(
                        fecha_suscripcion__range=(fecha_inicio, fecha_fin)).order_by('-fecha_suscripcion')
                    contexto['suscriptores'] = paginar(request, suscriptores, 10)
                else:
                    contexto['suscriptores'] = None
                contexto['error'] = error
                contexto['fecha_inicio'] = fecha_inicio
                contexto['fecha_fin'] = str(fecha_fin)

        except:
            pass
        return render(request, 'reporte_suscriptores.html', contexto)


class Listado_decorado:
    def __init__(self, listado):
        self.listado = listado

    def buscar_libro(self):
        return self.listado


class Decorador:
    def __init__(self, decorado, campo):
        self.campo = campo
        self.decorado = decorado
        self.libros_del_decorado = None

    def buscar_similares_1(self):  # TODO eliminar este mensaje antes de la demo
        lista = list()
        lista.append(self.libros())
        lista.append(self.decorado.buscar_similares())

        lista_a_retornar = list()

        for lista_de_libros in lista:
            if lista_de_libros is not None:  # Puede ser None por el archivo base
                for i in range(0, len(lista_de_libros)):
                    # Se saca el repetido
                    if lista_de_libros[i] not in lista_a_retornar:
                        lista_a_retornar.append(lista_de_libros[i])

        return lista_a_retornar

    def buscar_similares(self):
        lista = list()
        lista.append(self.libros())
        try:
            lista.append(list(itertools.chain.from_iterable(self.decorado.buscar_similares())))
        except:
            pass
        return lista

    '''def buscar_similares_1(self):
        lista = list()
        lista.append(self.libros())
        lista.append(self.decorado.buscar_similares())
        print('La lista',lista)
        try:
            lista_flattCollected = list(itertools.chain.from_iterable(lista))
            return lista_flattCollected
        except:
            return lista'''

    def buscar_libro(self):
        '''
            libros: param
            input_busqueda: Dictionary {'titulo': '','genero': '',}
        '''

        self.libros_del_decorado = self.decorado.buscar_libro()
        if (self.campo == ''):
            return self.libros_del_decorado
        return self.template()


class DecoradorTitulo(Decorador):
    def template(self):
        titulos = Libro.objects.filter(titulo__icontains=self.campo).values('titulo')
        return self.libros_del_decorado.filter(titulo__in=titulos)

    def libros(self):
        return listado_libros_activos().filter(titulo__icontains=self.campo)  # por si lo pide mariano


class DecoradorGenero(Decorador):
    def template(self):
        generos = Genero.objects.filter(nombre__icontains=self.campo).values('id')
        return self.libros_del_decorado.filter(genero_id__in=generos)

    def libros(self):
        return listado_libros_activos().filter(genero_id=self.campo)


class DecoradorAutor(Decorador):
    def template(self):
        autores = Autor.objects.filter(nombre__icontains=self.campo).values('id')
        return self.libros_del_decorado.filter(autor_id__in=autores)

    def libros(self):
        return listado_libros_activos().filter(autor_id=self.campo)


class DecoradorEditorial(Decorador):
    def template(self):
        editoriales = Editorial.objects.filter(nombre__icontains=self.campo).values('id')
        return self.libros_del_decorado.filter(editorial_id__in=editoriales)

    def libros(self):
        return listado_libros_activos().filter(editorial_id=self.campo)
