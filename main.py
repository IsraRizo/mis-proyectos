from flask import Flask, render_template, request, redirect, url_for, session, flash
import db
from models import Usuario, Categoria, Proveedor, Productos, Factura, Pedido, RegistrationForm, Contabilidad
from PIL import Image  # Libreria para edición de imagenes en Python
import json
from flask_login import LoginManager, login_user, login_required, logout_user  # Para trabajar con sesiones
from werkzeug.security import generate_password_hash  # Genera claves encriptada
from flask_wtf.csrf import CSRFProtect  # Protege al servidor cuando el usuario no ha sido auteticado
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
from pandas import DataFrame
from sqlalchemy import desc
import calendar

app = Flask(__name__)
csrf = CSRFProtect()  # Habilitamos la protección CSRF de forma global en la aplicación Flask
app.secret_key = 'MI_PROYECTO'  # Mantiene los datos seguros
login_manager_app = LoginManager(app)  # Permite que la aplicación y Flask_Login funcionen juntos


@app.route("/")
def home():
    if session == {}:  # Si no hay ningún usuario logueado
        session['admin'] = None

    productos = db.session.query(Productos).all()
    categorias_sin_eliminar = []
    prod_escasos = []
    for producto in productos:  # Compruebo si los stocks de los productos están por debajo del 90%
        if producto.stock < producto.cantidad_max * 0.9:
            prod_escasos.append(producto)
    categorias = db.session.query(Categoria).all()
    for i in categorias:
        if i.eliminado == 0:
            categorias_sin_eliminar.append(i)
    return render_template("index.html", prod_escasos=prod_escasos, categorias=categorias_sin_eliminar,
                           cierra_sesion="Cerrar Sesión")


# ----------------------USUARIOS---------------------------------------

@login_manager_app.user_loader
def load_user(id):  # Carga el usuario que se loguea
    return db.session.query(Usuario).filter_by(id=id).first()


@app.route("/usuarios")
def usuarios():  # Carga una lista con todos los usuarios
    usuarios = db.session.query(Usuario).all()
    usuarios_sin_eliminar = []
    for i in usuarios:
        if i.eliminado == 0:
            usuarios_sin_eliminar.append(i)
    return render_template("usuarios.html", usuarios=usuarios_sin_eliminar, cierra_sesion="Cerrar Sesión",
                           eliminado=False)


@app.route("/registro")
def registro():  # Nos redirecciona a la pagina registro.html
    return render_template("registro.html")


@app.route("/formulario")
def formulario():  # Me redirecciona a formulario.html
    return render_template("formulario.html",
                           form=Usuario())  # Le paso objeto de Usuario vacío para que no me rellene los inputs


@app.route("/crear-usuario", methods=["GET", "POST"])  # Conecta el html con python
def crear_usuario():  # Crea usuarios nuevos
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():  # Valida si las contraseñas son iguales
        usuario = Usuario(form.usuario.data, form.telefono.data, form.email.data,
                          generate_password_hash(form.contrasenia.data), form.nombre.data,
                          form.apellido.data, form.direccion.data, form.poblacion.data, form.provincia.data)
        db.session.add(usuario)
        db.session.commit()
        flash('Usuario registrado correctamente')  # Flash viene con la libreria flask y manda mensajes por pantalla
        return render_template('registro.html')
    return render_template('formulario.html',
                           form=form)  # Si las contraseñas no coinciden devolvemos los datos recogidos en el formulario


@app.route("/comprueba_usuario", methods=["POST"])
def comprueba_usuario():  # Comprueba si el usuario y la contraseña se encuentran en la base de datos
    email = request.form["email"]
    contrasenia = request.form["contrasenia"]
    todos_los_usuarios = db.session.query(Usuario).all()
    for i in todos_los_usuarios:
        if i.email == email and i.eliminado == 0:
            if (i.check_contrasenia(i.contrasenia,
                                    contrasenia)):  # Comprobamos que la contraseña encriptada coincide con la introducida por el usuario
                session['id'] = i.id  # Creamos una sesión con el id del usuario
                usuario_logueado = db.session.query(Usuario).filter_by(id=i.id).first()
                login_user(usuario_logueado)  # Cargamos el usuario logueado
                session['usuario'] = i.usuario  # Almacenamos en la sesión el nombre del usuario
                session[
                    'admin'] = i.admin  # Almacenamos en la sesión el tipo de usuario (administrador, usuario o invitado)
                return redirect(url_for("home"))
            else:
                flash("Contraseña incorrecta")  # Enviamos un mensaje si la contraseña es incorrecta
                return render_template("registro.html")
    flash("Usuario no encontrado")  # Enviamos un mensaje si el usuario no se encuentra en la base de datos
    return render_template("registro.html")


@app.route("/eliminar_usuario/<id>")
@login_required  # Solo pueden acceder los usuarios registrados
def eliminar_usuario(id):  # Elimina un usuario por su id
    usuario_eliminar = db.session.query(Usuario).filter_by(id=int(id))
    usuario_eliminar.first().eliminado = 1
    db.session.commit()
    usuarios = db.session.query(Usuario).all()
    usuarios_sin_eliminar = []
    for i in usuarios:
        if i.eliminado == 0:
            usuarios_sin_eliminar.append(i)
    return render_template("usuarios.html", usuarios=usuarios_sin_eliminar, cierra_sesion="Cerrar Sesión",
                           eliminado=False)


@app.route("/reinicia_conecta")
def reinicia_conecta():  # Reinicia la sesión a modo invitado
    logout_user()  # Cierro sesión de usuario logueado
    session.clear()  # Libero la sesión
    return redirect(url_for("home"))


# ----------------------CATEGORÍAS---------------------------------------

@app.route("/categorias")
@login_required  # Solo pueden acceder los usuarios registrados
def categorias():
    categorias = db.session.query(Categoria).all()
    categorias_sin_eliminar = []
    for i in categorias:
        if i.eliminado == 0:
            categorias_sin_eliminar.append(i)
    return render_template("categorias.html", categorias=categorias_sin_eliminar, cierra_sesion="Cerrar Sesión")


@app.route("/crea_categorias")
@login_required  # Solo pueden acceder los usuarios registrados
def crea_categorias():  # Nos redirecciona a la pagina crea_categorias.html
    return render_template("crea_categorias.html", cierra_sesion="Cerrar Sesión")


@app.route("/crea_categoria", methods=["POST"])
@login_required  # Solo pueden acceder los usuarios registrados
def crea_categoria():  # Crea una categoría nueva
    imagen = request.files["imagen"]  # Recibimos un archivo de formato imagen
    img = Image.open(imagen)  # Abre e identifica el archivo proporcionado
    todas_categorias = db.session.query(Categoria).all()
    nombre_imagen = str(len(todas_categorias))  # Le ponemos nombre a la imagen que coincide con el número de categorías
    nombre_imagen = nombre_imagen + ".png"  # Es necesario ponerle extensión a la imagen
    img.save("static/imagenes/" + nombre_imagen)  # Guardamos la imagen en su carpeta
    categoria = Categoria(nombre=request.form["nombre"],
                          imagen="../static/imagenes/" + nombre_imagen)  # Creamos un objeto de la clase Categoria
    db.session.add(categoria)  # guarda los datos del formulario en la base de datos
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/eliminar_categoria/<nombre>")
@login_required  # Solo pueden acceder los usuarios registrados
def eliminar_categoria(nombre):  # Eliminamos una categoría dado el nombre de la categoría
    productos = db.session.query(Productos).filter_by(categoria=nombre)
    categoria = db.session.query(Categoria).filter_by(nombre=nombre)  # filtra el elemento que vamos a eliminar
    for i in productos:  # Los productos dependen de las categorías, así que si eliminamos una categoría se eliminan todos los productos que le pertenecen
        i.eliminado = 1
    categoria.first().eliminado = 1
    db.session.commit()
    categorias = db.session.query(Categoria).all()
    categorias_sin_eliminar = []
    for i in categorias:
        if i.eliminado == 0:
            categorias_sin_eliminar.append(i)
    return render_template("categorias.html", categorias=categorias_sin_eliminar, cierra_sesion="Cerrar Sesión")


# ----------------------PRODUCTOS---------------------------------------

@app.route("/productos")
def productos():  # Nos redirecciona a productos.html
    productos = db.session.query(Productos).order_by("categoria").all()
    productos_sin_eliminar = []
    for i in productos:
        if i.eliminado == 0:
            productos_sin_eliminar.append(i)
    return render_template("productos.html", productos=productos_sin_eliminar, cierra_sesion="Cerrar Sesión",
                           eliminado=False)


@app.route("/filtra_productos/<nombre>")
def filtra_productos(nombre):
    productos = db.session.query(Productos).filter_by(categoria=nombre)
    productos_sin_eliminar = []
    for i in productos:
        if i.eliminado == 0:
            productos_sin_eliminar.append(i)
    return render_template("productos.html", productos=productos_sin_eliminar, cierra_sesion="Cerrar Sesión",
                           eliminado=True,
                           categoria=nombre)


@app.route("/crea_producto/<id>")
@login_required  # Solo pueden acceder los usuarios registrados
def crea_producto(id):
    categorias = db.session.query(Categoria).all()
    proveedores = db.session.query(Proveedor).all()
    proveedores_sin_eliminar = []
    for i in proveedores:
        if i.eliminado == 0:
            proveedores_sin_eliminar.append(i)

    if id == "None":  # Si creamos un producto nuevo
        producto = Productos()  # Si vamos a crear un producto nuevo, enviamos un objeto vacío
    else:  # Si editamos un producto
        producto = db.session.query(Productos).filter_by(
            id=id).first()  # Cargo el producto a editar para mandarlo al formulario y así no tener que rellenar todos los campos
    return render_template("crea_producto.html", cierra_sesion="Cerrar Sesión", categorias=categorias,
                           proveedores=proveedores_sin_eliminar, producto=producto)


@app.route("/crear-producto", methods=["POST"])
@login_required  # Solo pueden acceder los usuarios registrados
def crear_producto():  # Recoge los datos del formulario crea_producto.html y lo almacena en la base de datos
    proveedor = db.session.query(Proveedor).filter_by(
        empresa=request.form["proveedor"]).first()  # Del formulario recibo el nombre del proveedor y busco el id
    beneficio = db.session.query(Contabilidad).order_by(
        desc(Contabilidad.id)).first()  # Busco el últimpo movimiento de contabiliadad
    producto = Productos(categoria=request.form["categoria"], marca=request.form["marca"],
                         modelo=request.form["modelo"],
                         descripcion=request.form["descripcion"], id_proveedor=proveedor.id,
                         precio_compra=request.form["precio_compra"],
                         precio_venta=request.form["precio_venta"], iva=request.form["iva"],
                         cantidad_max=request.form["cantidad_max"],
                         stock=request.form["stock"])
    db.session.add(producto)  # Alamaceno el nuevo producto
    db.session.commit()

    producto = db.session.query(Productos).order_by(desc(Productos.id)).first()
    contabilidad = Contabilidad(id_producto=producto.id, id_cliente=None, id_proveedor=proveedor.id,
                                cantidad=producto.stock,
                                beneficio=beneficio.beneficio - (float(producto.precio_compra) * int(producto.stock)))
    db.session.add(contabilidad)  # Almaceno un nuevo campo en contabilidad con lo que me ha costado el nuevo producto
    db.session.commit()

    productos = db.session.query(Productos).order_by("categoria").all()
    productos_sin_eliminar = []
    for i in productos:
        if i.eliminado == 0:
            productos_sin_eliminar.append(i)
    return render_template("productos.html", productos=productos_sin_eliminar, cierra_sesion="Cerrar Sesión",
                           eliminado=True)


@app.route("/editar-producto/<id>", methods=["POST"])
def editar_producto(id):  # Recoge los datos del formulario crea_producto.html y edita los campos que hemos modificado
    proveedor = db.session.query(Proveedor).filter_by(empresa=request.form["proveedor"]).first()

    # Recojo los datos nuevos
    producto = Productos(categoria=request.form["categoria"], marca=request.form["marca"],
                         modelo=request.form["modelo"],
                         descripcion=request.form["descripcion"], id_proveedor=proveedor.id,
                         precio_compra=request.form["precio_compra"],
                         precio_venta=request.form["precio_venta"], iva=request.form["iva"],
                         cantidad_max=request.form["cantidad_max"],
                         stock=request.form["stock"])

    contabilidad_editada = db.session.query(Contabilidad).filter_by(
        id_producto=id).first()  # Cargo los valores que voy a editar de contabilidad
    producto_editado = db.session.query(Productos).filter_by(
        id=int(id)).first()  # Cargo los valores que voy a editar del producto
    producto_editado.categoria = producto.categoria
    producto_editado.marca = producto.marca
    producto_editado.modelo = producto.modelo
    producto_editado.descripcion = producto.descripcion
    producto_editado.id_proveedor = proveedor.id
    contabilidad_editada.id_proveedor = proveedor.id
    producto_editado.precio_compra = producto.precio_compra
    producto_editado.precio_venta = producto.precio_venta
    producto_editado.iva = producto.iva
    producto_editado.cantidad_max = producto.cantidad_max
    producto_editado.stock = producto.stock

    beneficio = db.session.query(Contabilidad).order_by(desc(
        Contabilidad.id)).first()  # Busco el último elementeo de contabilidad para modificarlo según la nueva entrada
    contabilidad = Contabilidad(id_producto=id, id_cliente=None, id_proveedor=proveedor.id,
                                cantidad=int(producto.stock) - int(request.form["stock_antiquo"]),
                                beneficio=beneficio.beneficio - (
                                        (int(producto.stock) - int(request.form["stock_antiquo"])) * float(
                                    producto_editado.precio_compra)))
    if contabilidad.cantidad > 0:  # Si se modifica el stock del producto se tiene que sumar en la contabilidad
        db.session.add(contabilidad)
    db.session.commit()
    productos = db.session.query(Productos).order_by("categoria").all()
    productos_sin_eliminar = []
    for i in productos:
        if i.eliminado == 0:
            productos_sin_eliminar.append(i)
    return render_template("productos.html", productos=productos_sin_eliminar, cierra_sesion="Cerrar Sesión",
                           eliminado=False)


@app.route("/eliminar_producto/<id>")
@login_required  # Solo pueden acceder los usuarios registrados
def eliminar_producto(id):
    producto = db.session.query(Productos).filter_by(id=int(id))  # filtra el elemento que vamos a eliminar
    pedidos = db.session.query(Pedido)

    for pedido in pedidos.all():  # Elimina los productos eliminados de los pedidos
        pedidos_json = json.loads(pedido.pedido)
        if len(pedidos_json) == 1 and pedidos_json[0][0] == id:
            eliminar_pedido(pedidos[0].id)
        else:
            for prod in pedidos_json:
                if prod[0] == id:
                    pedidos_json.remove(prod)
                    pedido_rectificado = json.dumps(pedidos_json)
                    pedido.pedido = pedido_rectificado

    producto.first().eliminado = 1
    db.session.commit()
    productos = db.session.query(Productos).all()
    productos_sin_eliminar = []
    for i in productos:
        if i.eliminado == 0:
            productos_sin_eliminar.append(i)
    return render_template("productos.html", productos=productos_sin_eliminar, cierra_sesion="Cerrar Sesión",
                           eliminado=False)


# ----------------------PROVEEDORES---------------------------------------

@app.route("/proveedores")
@login_required  # Solo pueden acceder los usuarios registrados
def proveedores():
    proveedores = db.session.query(Proveedor).all()
    proveedores_sin_eliminar = []
    for i in proveedores:
        if i.eliminado == 0:
            proveedores_sin_eliminar.append(i)
    return render_template("proveedores.html", proveedores=proveedores_sin_eliminar, cierra_sesion="Cerrar Sesión")


@app.route("/registro_proveedores")
@login_required  # Solo pueden acceder los usuarios registrados
def registro_proveedores():
    return render_template("registro_proveedores.html", cierra_sesion="Cerrar Sesión")


@app.route("/crea_proveedor")
@login_required  # Solo pueden acceder los usuarios registrados
def crea_proveedor():
    return render_template("crea_proveedores.html", cierra_sesion="Cerrar Sesión")


@app.route("/crear-proveedor", methods=["POST"])  # Conecta el html con python
@login_required  # Solo pueden acceder los usuarios registrados
def crear_proveedor():  # Recoge los datos del formulario de index.html
    proveedores_sin_eliminar = []
    proveedor = Proveedor(empresa=request.form["empresa"], cif=request.form["cif"], telefono=request.form["telefono"],
                          email=request.form["email"], direccion=request.form["direccion"],
                          poblacion=request.form["poblacion"], provincia=request.form["provincia"])

    db.session.add(proveedor)  # guarda los datos del formulario en la base de datos
    db.session.commit()
    proveedores = db.session.query(Proveedor).all()
    for i in proveedores:
        if i.eliminado == 0:
            proveedores_sin_eliminar.append(i)
    return render_template("proveedores.html", proveedores=proveedores_sin_eliminar, cierra_sesion="Cerrar Sesión")


@app.route("/eliminar_proveedor/<id>")
@login_required  # Solo pueden acceder los usuarios registrados
def eliminar_proveedor(id):
    productos = db.session.query(Productos).filter_by(id_proveedor=id)
    proveedor = db.session.query(Proveedor).filter_by(id=id)  # filtra el elemento que vamos a eliminar
    proveedores_sin_eliminar = []
    for i in productos:
        i.eliminado = 1
    proveedor.first().eliminado = 1
    db.session.commit()
    proveedores = db.session.query(Proveedor).all()
    for i in proveedores:
        if i.eliminado == 0:
            proveedores_sin_eliminar.append(i)
    return render_template("proveedores.html", proveedores=proveedores_sin_eliminar, cierra_sesion="Cerrar Sesión")


# ----------------------PEDIDOS---------------------------------------

@app.route("/pedidos")
@login_required  # Solo pueden acceder los usuarios registrados
def pedidos():
    usuario = session['id']  # Uso el id en vez del admin, para poder usarlo 4 líneas más abajo
    if usuario == 1:
        pedidos = db.session.query(Pedido).all()
    else:
        pedidos = db.session.query(Pedido).filter_by(id_cliente=int(usuario))
    lista_todos_pedidos = []
    for pedido in pedidos:
        lista_pedidos = []
        lista_pedidos.append(pedido.id)
        cliente = db.session.query(Usuario).filter_by(id=pedido.id_cliente)
        lista_pedidos.append(cliente[0].usuario)
        productos = json.loads(pedido.pedido)  # Cargo en productos la lista de los productos del pedido
        lista_todos_productos = []
        for producto in productos:
            producto_pedido = db.session.query(Productos).filter_by(id=producto[0])
            lista_productos = []
            lista_productos.append(producto_pedido[0].id)
            lista_productos.append(producto_pedido[0].categoria)
            lista_productos.append(producto_pedido[0].marca)
            lista_productos.append(producto_pedido[0].modelo)
            lista_productos.append(producto[1])
            lista_productos.append(producto_pedido[0].precio_venta)
            lista_productos.append(producto_pedido[0].iva)
            precio_final = round((producto_pedido[0].iva / 100 * producto_pedido[0].precio_venta + producto_pedido[
                0].precio_venta) * int(producto[1]), 2)
            lista_productos.append(precio_final)
            lista_todos_productos.append(lista_productos)  # Creo una lista con toda la información del producto
        lista_pedidos.append(lista_todos_productos)  # Creo una lista con las listas de información de cada producto
        lista_todos_pedidos.append(
            lista_pedidos)  # Finalmente creo una lista con la  id del pedido, el usuario y los datos de todos los productos de su pedido
    return render_template("pedidos.html", lista_todos_pedidos=lista_todos_pedidos, cierra_sesion="Cerrar Sesión",
                           eliminado=False)


@app.route("/crear_pedido", methods=["POST"])
@login_required  # Solo pueden acceder los usuarios registrados
def crear_pedido():
    lista_productos = request.form.getlist(
        "id")  # Recibo del formulario una lista con los productos que el cliente ha seleccionado
    lista_cantidades = request.form.getlist(
        "cantidad")  # Recibo del formulario una lista con las cantidades de los productos que el cliente ha seleccionado

    lista_pedidos = []  # Guardará los productos y las cantidades
    for k in range(0, len(lista_productos)):
        if lista_cantidades[k] != "0":
            producto = db.session.query(Productos).filter_by(id=lista_productos[k]).first()
            if producto.stock < int(lista_cantidades[k]):  # Modifico el stock del producto
                lista_cantidades[k] = producto.stock
                producto.stock = 0
                flash("El producto no tiene stock suficiente, le hemos añadido el stock que nos queda")
            else:
                producto.stock = producto.stock - int(lista_cantidades[k])
            lista_pedidos.append((lista_productos[k], lista_cantidades[k]))

    if len(lista_pedidos) > 0:  # Compruebo que haya elegido alguna cantidad en al menos un producto
        json_pedido = json.dumps(lista_pedidos)

        pedido = Pedido(id_cliente=session['id'], pedido=json_pedido)
        db.session.add(pedido)
        db.session.commit()
    else:
        flash("Debe marcar alguna cantidad en al menos un producto")
        return redirect(url_for("productos"))

    return redirect(url_for("pedidos"))


@app.route("/eliminar_pedido/<id>")
@login_required  # Solo pueden acceder los usuarios registrados
def eliminar_pedido(id):
    pedido_json = db.session.query(Pedido).filter_by(id=id)  # Selecciono el pedido a eliminar
    productos = db.session.query((Productos)).all()
    pedidos = json.loads(pedido_json[0].pedido)
    for i in pedidos:  # Repongo el stock de los productos
        for j in productos:
            if i[0] == str(j.id):
                j.stock = str(int(j.stock) + int(i[1]))
    pedido_json.delete()
    db.session.commit()
    return redirect(url_for("pedidos"))


# ----------------------FACTURAS---------------------------------------

@app.route("/facturas")
@login_required  # Solo pueden acceder los usuarios registrados
def facturas():
    usuario = session['id']  # Uso el id en vez del admin, para poder usarlo 4 líneas más abajo
    if usuario == 1:
        facturas = db.session.query(Factura).order_by(
            desc(Factura.id)).all()  # Ordeno las facturas de más nueva a más antigua
    else:
        facturas = db.session.query(Factura).filter_by(id_cliente=int(usuario)).order_by(
            desc(Factura.id))  # Ordeno las facturas de más nueva a más antigua
    lista_todas_facturas = []
    for factura in facturas:
        lista_facturas = []
        lista_facturas.append(factura.id)  # Esto irá en la cabecera de las facturas
        cliente = db.session.query(Usuario).filter_by(id=factura.id_cliente)
        lista_facturas.append(cliente[0].usuario)  # # Esto irá en la cabecera de las facturas
        productos = json.loads(factura.factura)
        lista_todos_productos = []
        precio_total = 0
        for producto in productos:
            producto_factura = db.session.query(Productos).filter_by(id=producto[0])
            lista_productos = []
            lista_productos.append(producto_factura[0].id)
            lista_productos.append(producto_factura[0].categoria)
            lista_productos.append(producto_factura[0].marca)
            lista_productos.append(producto_factura[0].modelo)
            lista_productos.append(producto[1])
            lista_productos.append(producto_factura[0].precio_venta)
            lista_productos.append(producto_factura[0].iva)
            precio_final = round((producto_factura[0].iva / 100 * producto_factura[0].precio_venta + producto_factura[
                0].precio_venta) * int(producto[1]), 2)
            precio_total += precio_final
            precio_total = round(precio_total, 2)
            lista_productos.append(precio_final)
            lista_todos_productos.append(lista_productos)

        lista_facturas.append(precio_total)  # Esto irá en la cabecera de las facturas
        lista_facturas.append(factura.fecha)  # Esto irá en la cabecera de las facturas
        lista_facturas.append(lista_todos_productos)  # Esto irá en el cuerpo de la factura
        lista_todas_facturas.append(lista_facturas)
        lista_todas_facturas = lista_todas_facturas
        # print(lista_todas_facturas)

    return render_template("facturas.html", lista_todas_facturas=lista_todas_facturas,
                           cierra_sesion="Cerrar Sesión", eliminado=False)


@app.route("/crear-factura", methods=["POST"])
@login_required  # Solo pueden acceder los usuarios registrados
def crear_factura():
    id_pedido = request.form['pedido']
    pedido = db.session.query(Pedido).filter_by(id=id_pedido)
    factura = Factura(id_cliente=pedido[0].id_cliente, factura=pedido[0].pedido)
    id_cliente = pedido.first().id_cliente
    pedido_json = json.loads(pedido.first().pedido)
    for producto in pedido_json:  # Modifico la contabiliad
        id_producto = int(producto[0])
        producto_facturado = db.session.query(Productos).filter_by(id=id_producto).first()
        cantidad = int(producto[1])
        beneficio = db.session.query(Contabilidad).order_by(desc(Contabilidad.id)).first()
        beneficio_final = beneficio.beneficio
        contabilidad = Contabilidad(id_producto=id_producto, id_cliente=id_cliente,
                                    id_proveedor=producto_facturado.id_proveedor, cantidad=cantidad,
                                    beneficio=beneficio_final + (cantidad * producto_facturado.precio_final))
        db.session.add(contabilidad)
        db.session.commit()
    db.session.add(factura)
    pedido.delete()
    db.session.commit()
    return redirect(url_for("facturas"))


# ----------------------ESTADISTICAS---------------------------------------

# ÚLTIMOS MOVIMIENTOS
@app.route("/estadisticas")
def estadisticas():
    if session["admin"] == 1:  # Está conectado el administrador
        entradas = db.session.query(Contabilidad).all()[-10:]  # Seleccionamos las 10 últimas entradas de contabilidad
    elif session["admin"] == 2:  # Está conectado un usuario
        entradas = db.session.query(Contabilidad).filter_by(id_cliente=session["id"]).all()[
                   -10:]  # Filtramos por el usuario y seleccionamos sus últimas 10 entradas
    ultimas_entradas = []

    for ultimas in entradas:
        ult = []
        producto = db.session.query(Productos).filter_by(id=ultimas.id_producto).first()
        cliente = db.session.query(Usuario).filter_by(id=ultimas.id_cliente).first()
        if cliente == None:  # Significa que está que el movimiento ha sido una compra a un proveedor
            cliente = None
            precio = int(ultimas.cantidad) * float(producto.precio_compra) * (-1)  # La muestro negativo
        else:  # El movimiento ha sido una venta a un cliente
            cliente = cliente.usuario
            precio = round(int(ultimas.cantidad) * float(producto.precio_venta) * 1.21, 2)
        proveedor = db.session.query(Proveedor).filter_by(id=ultimas.id_proveedor).first()
        proveedor = proveedor.empresa
        ult.append(producto.modelo)
        ult.append(cliente)
        ult.append(proveedor)
        ult.append(ultimas.cantidad)
        ult.append(ultimas.fecha)
        ult.append(precio)
        if session["admin"] == 1:  # El beneficio solo se muestra cuando está logueado el administrador
            ult.append(round(ultimas.beneficio, 2))
        ultimas_entradas.append(ult)

    # DIFERENCIA PRECIOS COMPRA-VENTA
    if session["admin"] == 1:
        mayor_beneficio = db.session.query(Productos).all()
        df_beneficio = crea_df(mayor_beneficio)
        df_beneficio['beneficio'] = df_beneficio['Precio Venta'] - df_beneficio['Precio Compra']
        df_beneficio_mayor = df_beneficio.sort_values(by="beneficio").head(10)
        df_beneficio_mayor = df_beneficio_mayor.drop('beneficio', axis=1)

        df_beneficio_menor = df_beneficio.sort_values(by="beneficio", ascending=False).head(10)
        df_beneficio_menor = df_beneficio_menor.drop('beneficio', axis=1)

        df_beneficio_mayor.plot(x="Productos", kind="bar", stacked=True, rot=70)
        archivo = "static/imagenes/graficos/grafico1.png"

        plt.title("MAYOR BENEFICIO", color="red", fontweight="bold")
        plt.xlabel("Productos", color="red")
        plt.ylabel("EUROS (€)", color="red")

        plt.savefig(archivo, bbox_inches='tight')  # bbox_inches='tight', hace que se guarde la imagen completa
        plt.close()
        df_beneficio_menor.plot(x="Productos", kind="bar", stacked=True, rot=70)
        archivo = "static/imagenes/graficos/grafico2.png"
        plt.title("MENOR BENEFICIO", color="red", fontweight="bold")
        plt.xlabel("Productos", color="red")
        plt.ylabel("EUROS (€)", color="red")

        plt.savefig(archivo, bbox_inches='tight')  # bbox_inches='tight', hace que se guarde la imagen completa
        plt.close()

    # CONTABILIDAD
    if session["admin"] == 1:  # Conectado el administrador
        fechas = db.session.query(Contabilidad).all()  # Seleccionamos todos los campos de contabilidad
    elif session["admin"] == 2:  # Conectado un usuario
        fechas = db.session.query(Contabilidad).filter_by(
            id_cliente=session["id"]).all()  # Seleccionamos solo los productos que ha comprado
    anyos = []  # En esta lista añadiremos los años en los que ha habido compras y ventas

    for i in fechas:  # Recorro todos los campos de contabilidad
        if i.fecha.year not in anyos:  # Selecciono los años que no se repiten y los almaceno en una lista
            anyos.append(i.fecha.year)

    for i in anyos:  # Voy a crear una gráfica con la contabilidad de cada año por meses
        meses = []
        cantidad = []
        precios_producto = []
        for j in fechas:  # Recorro todos los campos de Contabilidad
            if j.fecha.year == i:  # Los voy filtrando por año
                mes = j.fecha.month
                if session["admin"] == 1:
                    meses.append(mes)  # Almaceno en una lista todos los meses en los que hay movimientos
                    cantidad.append(j.beneficio)  # Almaceno en una lista el beneficio final de cada movimiento
                elif session["admin"] == 2:
                    producto = db.session.query(Productos).filter_by(id=j.id_producto).first()
                    meses.append(mes)  # Almaceno en una lista todos los meses en los que hay movimientos
                    cantidad.append(j.cantidad)  # Almaceno en una lista el beneficio final de cada movimiento
                    precios_producto.append(producto.precio_final)

        nombre_meses = []
        cantidades = []
        if session["admin"] == 1:
            df1 = DataFrame({'mes': meses, 'beneficio': cantidad})  # Creo un dataframe con los meses y
            serie1 = df1.groupby("mes")[
                "beneficio"].last()  # Agrupo por meses y elijo el último movimiento de beneficio de cada mes
        elif session["admin"] == 2:
            df1 = DataFrame({'mes': meses, 'beneficio': cantidad, 'precio': precios_producto})
            df1["precio_total"] = df1["beneficio"] * df1["precio"]
            serie1 = df1.groupby("mes")["precio_total"].sum()  # Agrupo por meses y sumo los precios totales
        cont = 1
        for num_mes in range(1, 13):  # Asigno a cada mes la cantidad de ventas
            nombre_meses.append(calendar.month_name[num_mes])
            if num_mes in serie1.index:
                cantidades.append(serie1[num_mes])
            elif num_mes not in serie1.index and num_mes > serie1.index[0] and session["admin"] == 1:
                cantidades.append(serie1[num_mes - cont])
                cont += 1
            else:
                cantidades.append(0)

        df2 = DataFrame({'mes': nombre_meses, 'beneficio': cantidades})  # Creo un Dataframe
        plt.close("all")  # Cierro matplotlib por si estuviese abierto y evitar errores
        if session["admin"] == 1:
            sns.lineplot(x='mes', y='beneficio',
                         data=df2)  # Creo una gráfica de líneas con los valores del dataframe df2
        elif session["admin"] == 2:
            sns.barplot(x='mes', y='beneficio', data=df2)
        archivo = "static/imagenes/graficos/" + str(i) + ".png"  # Creo una ruta para almacenar la gráfica
        plt.title("Contabilidad " + str(i), color="red", fontweight="bold")
        plt.xlabel("Meses", color="red")
        if session["admin"] == 1:
            plt.ylabel("Beneficios", color="red")
        elif session["admin"] == 2:
            plt.ylabel("Gasto por mes", color="red")
        plt.xticks(rotation=30)  # Roto los valores del eje x para que no se pisen
        plt.savefig(archivo, bbox_inches='tight')  # Guardo la gráfica en la ruta
        plt.close("all")  # Cierro el matplotlib
    return render_template("estadisticas.html", ultimas_entradas=ultimas_entradas, nombre_imagenes=anyos,
                           cierra_sesion="Cerrar Sesión")


def crea_df(productos):  # Función que me crea Dataframes pasándole objetos de productos
    precios_totales = []
    for i in productos:
        precios = []
        precios.append(i.modelo)
        precios.append(i.precio_final)
        precios.append(i.precio_compra)
        precios_totales.append(precios)
    return pd.DataFrame(precios_totales, columns=['Productos', "Precio Compra", "Precio Venta"])


def status_401(
        error):  # Si el usuario intenta entrar a una página sin estar registrado lo redireccionamos a la página registro
    flash("Debe registrarse para poder acceder a la página")
    return redirect(url_for('registro'))


def status_404(
        error):  # Si el usuario introduce en el navegador una página que no existe lo redireccionamos a: página no encontrada
    return "<h1>Página no encontrada</h1>"


if __name__ == "__main__":
    # db.Base.metadata.create_all(db.engine)
    csrf.init_app(app)  # Para iniciar la aplicación
    app.register_error_handler(401, status_401)  # Registramos el error 401
    app.register_error_handler(404, status_404)  # Registramos el error 404
    app.run(debug=True)
