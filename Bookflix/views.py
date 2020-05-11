import datetime
from django.views                   import View
from django.core.paginator          import Paginator
from django.contrib.auth.models     import User
from django.shortcuts               import render,redirect
from django.contrib.auth            import authenticate,login
from django.views.decorators.csrf   import csrf_exempt
from django.core.files.storage      import FileSystemStorage
from forms.forms                    import FormularioIniciarSesion,FormularioRegistro
from modelos.models                 import Autor,Genero,Editorial,Suscriptor,Tarjeta,Tipo_Suscripcion,Libro,Perfil

class Vista_Registro(View):
    def __init__(self,*args,**kwargs):
        self.contexto = dict()
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
        self.contexto['formulario'] = FormularioRegistro()
        return render(request,'registro.html',self.contexto)

    @csrf_exempt
    def post(self,request):
        formulario=FormularioRegistro(request.POST)
        if formulario.is_valid():
            print('Contrasena ',type(formulario.cleaned_data['Contrasena']))
            print('DNI ',type(formulario.cleaned_data['DNI']))
            print('email',type(formulario.cleaned_data['Email']))
            print('Fecha',type(formulario.cleaned_data['Fecha_de_vencimiento']))

            #self.__cargar_usuario_suscriptor(formulario)
            return redirect('/iniciar_sesion/')
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
        datos_tarjeta = (Tarjeta.objects.filter(nro_tarjeta = datos_suscriptor['nro_tarjeta_id'])).values()[0]
        email_usuario = (Usuario.objects.values('email').filter(auth_id = id))[0]['email']
        perfiles = Perfil.objects.values('nombre_perfil').filter(auth_id = id)
        contexto={
                'nombre': datos_suscriptor['nombre'],
                'apellido': datos_suscriptor['apellido'],
                'email': datos_suscriptor['email_id'],
                'dni': datos_suscriptor['dni'],
                'fecha_suscripcion': datos_suscriptor['fecha_suscripcion'],
                'tipo_suscripcion': datos_suscriptor['tipo_suscripcion_id'],
                'numero_tarjeta': datos_suscriptor['nro_tarjeta_id'],
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
