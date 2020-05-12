import datetime
from django.views                   import View
from django.core.paginator          import Paginator
from django.contrib.auth.models     import User
from django.shortcuts               import render,redirect
from django.contrib.auth            import authenticate,login
from django.views.decorators.csrf   import csrf_exempt
from django.core.files.storage      import FileSystemStorage
from forms.forms                    import FormularioIniciarSesion,FormularioRegistro,FormularioModificarDatosPersonales
from modelos.models                 import Autor,Genero,Editorial,Suscriptor,Tarjeta,Tipo_Suscripcion,Libro,Perfil

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
        dni = formulario.cleaned_data['DNI']
        numero_tarjeta = formulario.cleaned_data['Numero_de_tarjeta']
        contrasena = formulario.cleaned_data['Contrasena']
        apellido = formulario.cleaned_data['Apellido']
        nombre = formulario.cleaned_data['Nombre']
        suscripcion = formulario.cleaned_data['Suscripcion']

        self.__cargar_tarjeta(formulario)

        #Cargamos el modelos User de auth_user
        model_usuario = User.objects.create_user(username = email, password=contrasena ) #Se guarda en la tabla auth_user
        model_usuario.save()

        #Tomamos las Claves foraneas
        auth_id = User.objects.values('id').get(username=email)['id']
        id_tarjeta = Tarjeta.objects.values('id').get(nro_tarjeta = numero_tarjeta)['id']
        id_suscripcion = Tipo_Suscripcion.objects.values('id').get(tipo_suscripcion = suscripcion)['id']


        #Cargamos al suscriptor
        suscriptor=Suscriptor(auth_id=auth_id,
                              fecha_suscripcion=datetime.datetime.now().date(),
                              dni=dni,
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
            print(type(self.formulario.cleaned_data['clave']))
            email = self.formulario.cleaned_data['email']
            clave = self.formulario.cleaned_data['clave']
            usuario = authenticate(username=email,password=clave)
            if usuario is not None: #El usuario se autentica
                print('Entre')
                id_usuario_logueado = (User.objects.values('id').get(username=email))['id']
                url = str(id_usuario_logueado)+'/'
                if not usuario.is_staff:
                    return redirect('/prueba/id='+url)
                else:
                    login(request,usuario) #Carga la sesion del administrador
                    return redirect('/admin/')
            else:
               error = 'Los datos ingresados no son validos'
        self.__contextualizar_formulario(error or '')
        return render(request,self.__vista_html,self.__contexto)

class Vista_Datos_Usuario (View):
    def get(self,request,id=None,*args, **kwargs):
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
                'dni_titular': datos_tarjeta['dni_titular'],
                'empresa': datos_tarjeta['empresa'],
                'perfiles': [str(clave['nombre_perfil']) for clave in list(perfiles)]

        }
        return render(request,'datos_usuario.html',contexto)


    @csrf_exempt
    def post(self,request,id=None):
        email = (Usuario.objects.values('email').get(auth_id = id))['email']
        formulario = PruebaFormulario(request.POST)
        if formulario.is_valid():
            pass
        return render(request,'n.html',{'usuario':email,'formulario':PruebaFormulario()})

class Vista_Home(View):
    def get(self,request):
        return render(request,'home.html',{})

    def post(self,request):
        pass

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
                'DNI': datos_suscriptor['dni'],
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
        print(formulario.get_datos_cambiados())
        nombre = formulario.cleaned_data['Nombre']
        apellido = formulario.cleaned_data['Apellido']

        #Aplicamos la estrategia. get_datos_cambiados es un diccionario donde para cada campo importante guarda un boolean si cambio o no con respecto a su valor inicial
        estrategia_email = Estrategia_Email(formulario.get_datos_cambiados()['Email'],formulario,self.__valores_iniciales(id))
        estrategia_dni = Estrategia_DNI(formulario.get_datos_cambiados()['DNI'],formulario,self.__valores_iniciales(id))
        estrategia_numero_de_tarjeta = Estrategia_Numero_de_tarjeta(formulario.get_datos_cambiados()['Numero_de_tarjeta'],formulario,self.__valores_iniciales(id))

        estrategia_email.validar()
        estrategia_dni.validar()
        estrategia_numero_de_tarjeta.validar()

        suscriptor = Suscriptor.objects.get(auth_id = id)
        suscriptor.nombre = nombre
        suscriptor.apellido = apellido

        suscriptor.save()

    def get(self,request,id = None):
        formulario = FormularioModificarDatosPersonales(initial = self.__valores_iniciales(id))
        self.contexto['formulario'] = formulario
        return render(request,'modificar_datos_personales.html',self.contexto)

    def post(self,request,id = None):
        formulario = FormularioModificarDatosPersonales(initial = self.__valores_iniciales(id), data = request.POST)
        if formulario.is_valid():
            #print(formulario.cleaned_data)
            self.__cambiar_datos_usuario(formulario,id)
            pass
        self.contexto['formulario'] = formulario
        return render(request,'modificar_datos_personales.html',self.contexto)

class Estrategia:
    def __init__(self,estado,formulario_nuevo,valores_iniciales,*args,**kwargs):
        #Estado es un boolean que indica si cambio o no
        self.estado = estado
        self.formulario = formulario_nuevo
        self.valores_iniciales = valores_iniciales
        self.auth_id = 1


class Estrategia_Email(Estrategia):
    def validar(self):
        if self.estado:
            print('entre')
            #Como cambio, actualizamos la BD
            print(self.valores_iniciales)
            auth_usuario = User.objects.get(username = self.valores_iniciales['Email'])
            auth_usuario.username = str(self.formulario.cleaned_data['Email'])
            auth_usuario.save()
            print('guarde')

class Estrategia_DNI(Estrategia):
    def validar(self):
        if self.estado:
            #cambio
            suscriptor = Suscriptor.objects.get(dni = self.valores_iniciales['DNI'])
            print('HOLA DNI')
            suscriptor.dni = self.formulario.cleaned_data['DNI']
            suscriptor.save()

#TODO arreglar el super para mandar el id del usuario logueado que esta por parametro
class Estrategia_Numero_de_tarjeta(Estrategia):
#    def __init__(self,auth_id,estado,formulario_nuevo,valores_iniciales):
#        self.auth_id = 1
#        super(Estrategia_Numero_de_tarjeta,self).__init__(estado,formulario_nuevo,valores_iniciales,*args,**kwargs)

    def __cargar_tarjeta(self):
        "Este metodo carga la tarjeta en caso de no existir"
        numero_tarjeta=  self.formulario.cleaned_data['Numero_de_tarjeta']
        if not Tarjeta.objects.filter(nro_tarjeta = numero_tarjeta).exists():
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
            self.__cargar_tarjeta()
            suscriptor = Suscriptor.objects.get(auth_id = self.auth_id)
            id_tarjeta = (Tarjeta.objects.values('id').filter(nro_tarjeta = self.formulario.cleaned_data['Numero_de_tarjeta'])[0])['id']
            suscriptor.nro_tarjeta_id = id_tarjeta
            suscriptor.save()
        else:
            tarjeta=Tarjeta.objects.get(nro_tarjeta = self.valores_iniciales['Numero_de_tarjeta'])
            tarjeta.dni_titular=self.formulario.cleaned_data['DNI_titular']
            tarjeta.codigo_seguridad = self.formulario.cleaned_data['Codigo_de_seguridad']
            tarjeta.fecha_de_vencimiento = self.formulario.cleaned_data['Fecha_de_vencimiento']
            tarjeta.empresa = self.formulario.cleaned_data['Empresa']
            tarjeta.save()
