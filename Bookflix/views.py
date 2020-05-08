import datetime
from django.views import View
from django.contrib.auth.models import User
from django.shortcuts import render,redirect
from django.contrib.auth import authenticate,login
from django.views.decorators.csrf import csrf_exempt
from forms.forms import FormularioAtributosLibro,FormularioIniciarSesion,FormularioRegistro
from modelos.models import Autor,Genero,Editorial,Usuario,Suscriptor,Administrador,Tarjeta,Tipo_Suscripcion

class Vista_Carga_Atributo(View):
    def __init__(self,clase_model,clase_formulario,*args,**kwargs):
        self.__clase_model = clase_model
        self.__clase_formulario = clase_formulario #Se recibe la clase que se va a instanciar. Ejemplo FormularioAtributoLibro, FormularioAutor
        self.__formulario = clase_formulario() #Creo una instancia de un formulario
        super(Vista_Carga_Atributo,self).__init__(*args,**kwargs)

    def get_contexto(self):
        pass

    def cargar_atributo(self):
        pass

    def __renderizar_formulario(self):
        self.__formulario = self.__clase_formulario()
        self.contexto['formulario'] = self.__formulario

    def get(self,request):
        print(request.session.keys())
        print(request.session.values())
        self.__renderizar_formulario()
        return render(request,'cargar_atributo_libro.html',self.contexto)

    @csrf_exempt
    def post(self,request):
        self.__formulario = self.__clase_formulario(request.POST)
        if self.__formulario.is_valid():
            self.cargar_atributo(self.__formulario)
        self.__renderizar_formulario()
        return render(request,'cargar_atributo_libro.html',self.contexto)


    def cargar_atributo(self,formulario=None):
        "clase puede ser la clase Editorial o Autor. formulario es None x defecto por si este metodo es sobreescrito"
        atributo_nombre = self.__formulario.cleaned_data['nombre'].lower()
        existe_clase = list(self.__clase_model.objects.filter(nombre = atributo_nombre)) != []
        caso = ''
        tipo = self.contexto['error']
        if not existe_clase:
            #Si no existe, la agrega.
            editorial = self.__clase_model(nombre=atributo_nombre)
            editorial.save()
            tipo = 'Registrado exitosamente'
        self.contexto['caso'] = tipo

class Vista_Carga_Editorial(Vista_Carga_Atributo):
    def __init__(self,*args,**kwargs):
        self.__caso = ''
        self.contexto = {'nombre':'Editorial','caso': self.__caso,'error':'Ya existe la editorial'}
        super(Vista_Carga_Editorial,self).__init__(Editorial,FormularioAtributosLibro,*args,**kwargs)

class Vista_Carga_Genero(Vista_Carga_Atributo):
    def __init__(self,*args,**kwargs):
        self.__caso = ''
        self.contexto = {'nombre':'Genero','caso': self.__caso,'error':'Ya existe el genero'}
        super(Vista_Carga_Genero,self).__init__(Genero,FormularioAtributosLibro,*args,**kwargs)

class Vista_Carga_Autor(Vista_Carga_Atributo):
    def __init__(self,*args,**kwargs):
        self.contexto = {'nombre':'Autor','caso':'','error':'Ya existe el autor'}
        super(Vista_Carga_Autor,self).__init__(Autor,FormularioAtributosLibro,*args,**kwargs)

class Vista_Registro(View):
    def __init__(self,*args,**kwargs):
        self.contexto = dict()
        super(Vista_Registro,self).__init__(*args,**kwargs)

    def __actualizar_contexto(self,formulario):
        self.contexto['formulario'] =  formulario
        self.contexto['caso'] = ''

    def __existe_tarjeta(self,numero_tarjeta):
        """
            Retorna False si la tarjeta no existe
        """
        try:
            #Si levanta excepcion, no existe la tarjeta, entonces hay que cargarla
            Tarjeta.objects.get(nro_tarjeta = numero_tarjeta)
            return True
        except:
            return False

    def __cargar_tarjeta(self,formulario):
        "Este metodo carga la tarjeta en caso de no existir"
        if not self.__existe_tarjeta(formulario.cleaned_data['Numero_de_tarjeta']):
            #Como no existe la tarjeta, la cargamos en la Base de datos
            empresa= formulario.cleaned_data['Empresa']
            DNI_titular=  formulario.cleaned_data['DNI_titular']
            numero_tarjeta=  formulario.cleaned_data['Numero_de_tarjeta']
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
        
        #Cargamos al usuario trayendonos la pk de User
        usuario= Usuario(clave=contrasena,email=email,auth_id=(User.objects.values('id').get(username=email))['id'])
        usuario.save()
        
        #Cargamos al suscriptor
        suscriptor=Suscriptor(email_id=email,
                              fecha_suscripcion=datetime.datetime.now().date(),
                              dni=dni,
                              nombre=nombre ,
                              nro_tarjeta_id=numero_tarjeta,
                              apellido=apellido,
                              tipo_suscripcion_id=suscripcion
                              )
        suscriptor.save()

    def __verificarCampos(self,email,dni):
        """
            Retorna un string con un error, si hubo, y el tipo
        """
        error=''
        if ((Suscriptor.objects.filter(email_id = email)).exists()):
            error = 'El email ya existe en el sistema'
        elif ((Suscriptor.objects.filter(dni = dni)).exists() ):
            error = 'El DNI ya se encuentra cargado en el sistema'
        return error

    def cargar_atributos_usuario(self,formulario):
        """
            Este metodo delega las verificaciones y la carga.
        """
        email = formulario.cleaned_data['Email']
        dni = formulario.cleaned_data['DNI']
        error = self.__verificarCampos(email,dni)
        if error == '':
            #Si no hubo error
            self.__cargar_usuario_suscriptor(formulario)
        return error

    def get(self,request):
        self.__actualizar_contexto(FormularioRegistro())
        return render(request,'registro.html',self.contexto)

    @csrf_exempt
    def post(self,request):
        error = ''
        formulario=FormularioRegistro(request.POST)
        if formulario.is_valid():
            error = self.cargar_atributos_usuario(formulario)
            if error == '': #Error es vacio si algun dato no estaba duplicado en la BD
                return redirect('/iniciar_sesion/')
        
        self.__actualizar_contexto(formulario)
        self.contexto['caso'] = error
        
        return render(request,'registro.html',self.contexto)

class Vista_Iniciar_Sesion(View):
    def __init__(self,*args,**kwargs):
        self.__vista_html = 'iniciar_sesion.html'
        self.__contexto = {'formulario': None,'caso':''} #en caso se guarda el mensaje que se va a mostrar en el html
        super(Vista_Iniciar_Sesion,self).__init__(*args,**kwargs)

    def __contextualizar_formulario(self):
        self.__contexto['formulario'] = FormularioIniciarSesion()

    def __crear_usuario(self,email,clave):
        user = User.objects.create_user(username = email, password=clave )
        user.save()

    def __es_suscriptor(self,email):
        try:
            (Administrador.objects.get(email_id = email))
            return False
        except:
            return True

    def get(self,request):
        self.__contextualizar_formulario()
        return render(request,self.__vista_html,self.__contexto)

    @csrf_exempt
    def post(self,request):
        self.formulario = FormularioIniciarSesion(request.POST)
        if self.formulario.is_valid():
            email = self.formulario.cleaned_data['email']
            clave = self.formulario.cleaned_data['clave']
            usuario = authenticate(username=email,password=clave)
            if usuario is not None: #El usuario se autentica
                id_usuario_logueado = (User.objects.values('id').get(username=email))['id']
                url = str(id_usuario_logueado)+'/'
                if self.__es_suscriptor(email):
                    print('Es Suscriptor')
                    #return redirect('/prefiles/id='+url)
                else:
                    print ('Es administrador')
                    #return redirect('/administrador/id='+url)
                return redirect('/prueba/id='+url)
            else:
                self.__contexto['caso'] = 'Los datos ingresados no son validos'
        self.__contextualizar_formulario()
        return render(request,self.__vista_html,self.__contexto)

class Vista_Datos_Usuario (View):
    def get(self,request,id=None,*args, **kwargs):
        datos_usuario = (Usuario.objects.filter(auth_id=id)).values()[0]
        email = datos_usuario['email']        
        datos_suscriptor = Suscriptor.objects.filter(email_id=email).values()[0]
        datos_tarjeta = (Tarjeta.objects.filter(nro_tarjeta = datos_suscriptor['nro_tarjeta_id'])).values()[0]
        print(datos_tarjeta)
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
        }
        return render(request,'datos_usuario.html',contexto)

class Prueba(View):
    def get(self,request,id=None):
        
        email = (Usuario.objects.values('email').get(auth_id = id))['email']
        return render(request,'n.html',{'usuario':email})

