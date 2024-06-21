from sqlalchemy import Column, Integer, Float, String, Date
from datetime import datetime
import db
from flask_login import UserMixin
from werkzeug.security import check_password_hash  # Librería de encriptación de contraseñas
from wtforms import Form, StringField, PasswordField, validators


class Usuario(db.Base, UserMixin):
    __tablename__ = "usuario"
    __table_args__ = {
        'sqlite_autoincrement': True}  # (Opcional) Para forzar que en mi tabla haya un identificador que vaya incrementando
    id = Column(Integer, primary_key=True)
    usuario = Column(String(20), nullable=False)
    telefono = Column(String(20), nullable=False)
    email = Column(String(100), nullable=False)
    contrasenia = Column(String(200), nullable=False)
    nombre = Column(String(30), nullable=False)
    apellido = Column(String(50), nullable=False)
    direccion = Column(String(100), nullable=False)
    poblacion = Column(String(50), nullable=False)
    provincia = Column(String(50), nullable=False)
    admin = Column(Integer, nullable=False)
    antiguedad = Column(Date, nullable=False)
    eliminado = Column(Integer, primary_key=True)

    def __init__(self, usuario=None, telefono=None, email=None, contrasenia=None, nombre=None, apellido=None,
                 direccion=None, poblacion=None, provincia=None, admin=2, eliminado=0):
        self.usuario = usuario
        self.telefono = telefono
        self.email = email
        self.contrasenia = contrasenia
        self.nombre = nombre
        self.apellido = apellido
        self.direccion = direccion
        self.poblacion = poblacion
        self.provincia = provincia
        self.admin = admin
        self.antiguedad = datetime.today()
        self.eliminado = eliminado

    def __str__(self):
        return "Usuario {}: Con nombre {} {} se hizo usuario en la fecha {}".format(self.usuario, self.nombre,
                                                                                    self.apellido, self.antiguedad)

    @classmethod  # Para utilizar el método sin instanciar la clase
    def check_contrasenia(self, hashed_contrasenia, contrasenia):  # Método para encriptar contraseñas
        return check_password_hash(hashed_contrasenia, contrasenia)


class Proveedor(db.Base):
    __tablename__ = "proveedor"
    __table_args__ = {
        'sqlite_autoincrement': True}  # (Opcional) Para forzar que en mi tabla haya un identificador que vaya incrementando
    id = Column(Integer, primary_key=True)
    empresa = Column(String(20), nullable=False)
    cif = Column(String(20), nullable=False)
    telefono = Column(String(20), nullable=False)
    email = Column(String(100), nullable=False)
    direccion = Column(String(100), nullable=False)
    poblacion = Column(String(50), nullable=False)
    provincia = Column(String(50), nullable=False)
    antiguedad = Column(Date, nullable=False)
    eliminado = Column(Integer, primary_key=True)

    def __init__(self, empresa, cif, telefono, email, direccion, poblacion, provincia, eliminado=0):
        self.empresa = empresa
        self.cif = cif
        self.telefono = telefono
        self.email = email
        self.direccion = direccion
        self.poblacion = poblacion
        self.provincia = provincia
        self.antiguedad = datetime.today()
        self.eliminado = eliminado

    def __str__(self):
        return "El proveedor {}: tiene el CIF {}, su teléfono es {} y su email es {}".format(self.empresa, self.cif,
                                                                                             self.telefono, self.email)


class Productos(db.Base):
    __tablename__ = "producto"
    __table_args__ = {'sqlite_autoincrement': True}
    id = Column(Integer, primary_key=True)
    categoria = Column(String(30), nullable=False)
    marca = Column(String(20), nullable=False)
    modelo = Column(String(20), nullable=False)
    descripcion = Column(String(200), nullable=False)
    id_proveedor = Column(Integer, nullable=False)
    precio_compra = Column(Float, nullable=False)
    precio_venta = Column(Float, nullable=False)
    iva = Column(Integer, nullable=False)
    cantidad_max = Column(Integer, primary_key=True)
    stock = Column(Integer, nullable=False)
    precio_final = Column(Float, nullable=False)
    eliminado = Column(Integer, primary_key=True)

    def __init__(self, categoria=None, marca=None, modelo=None, descripcion=None, id_proveedor=None, precio_compra=0,
                 precio_venta=0, cantidad_max=0, stock=0, iva=21, eliminado=0):
        self.categoria = categoria
        self.marca = marca
        self.modelo = modelo
        self.descripcion = descripcion
        self.id_proveedor = id_proveedor
        self.precio_compra = precio_compra
        self.precio_venta = precio_venta
        self.iva = iva
        self.cantidad_max = cantidad_max
        self.stock = stock
        self.precio_final = float(precio_venta) + (float(precio_venta) * int(iva) / 100)
        self.eliminado = eliminado

    def __str__(self):
        return "El producto marca {} y modelo {}, tiene un precio final de {} y hay en stock {} unidades".format(
            self.marca, self.modelo, self.precio_final, self.stock)


class Categoria(db.Base):
    __tablename__ = "categoria"
    __table_args__ = {
        'sqlite_autoincrement': True}  # (Opcional) Para forzar que en mi tabla haya un identificador que vaya incrementando
    id = Column(Integer, primary_key=True)
    nombre = Column(String(30), nullable=False)
    imagen = Column(String(200), nullable=False)
    eliminado = Column(Integer, primary_key=True)

    def __init__(self, nombre, imagen, eliminado=0):
        self.nombre = nombre
        self.imagen = imagen
        self.eliminado = eliminado

    def __str__(self):
        return "la categoría {} tiene una imagen en la ruta {}".format(self.nombre, self.imagen)


class Pedido(db.Base):
    __tablename__ = "pedido"
    __table_args__ = {'sqlite_autoincrement': True}
    id = Column(Integer, primary_key=True)
    id_cliente = Column(Integer, nullable=False)
    pedido = Column(String(2000), nullable=False)
    fecha = Column(Date, nullable=False)

    def __init__(self, id_cliente, pedido):
        self.id_cliente = id_cliente
        self.pedido = pedido
        self.fecha = datetime.today()

    def __str__(self):
        return "El pedido {} pertenece al cliente {} y se realizó en la fecha {}".format(self.id, self.id_cliente,
                                                                                         self.fecha)


class Factura(db.Base):
    __tablename__ = "factura"
    __table_args__ = {'sqlite_autoincrement': True}
    id = Column(Integer, primary_key=True)
    id_cliente = Column(Integer, nullable=False)
    factura = Column(String(2000), nullable=False)
    fecha = Column(Date, nullable=False)

    def __init__(self, id_cliente, factura):
        self.id_cliente = id_cliente
        self.factura = factura
        self.fecha = datetime.today()

    def __str__(self):
        return "La factura {} pertenece al cliente {} y se realizó en la fecha {}".format(self.id, self.id_cliente,
                                                                                          self.fecha)


class Contabilidad(db.Base):
    __tablename__ = "contabilidad"
    __table_args__ = {'sqlite_autoincrement': True}
    id = Column(Integer, primary_key=True)
    id_producto = Column(Integer, nullable=False)
    id_cliente = Column(Integer, nullable=False)
    id_proveedor = Column(Integer, nullable=False)
    cantidad = Column(Integer, nullable=False)
    fecha = Column(Date, nullable=False)
    beneficio = Column(Float, nullable=False)

    def __init__(self, id_producto=None, id_cliente=None, id_proveedor=None, cantidad=None, beneficio=0):
        self.id_producto = id_producto
        self.id_cliente = id_cliente
        self.id_proveedor = id_proveedor
        self.cantidad = cantidad
        self.fecha = datetime.today()
        self.beneficio = beneficio

    def __str__(self):
        return "La contabilidad está en {}€, tras la compra del producto {} por el cliente {}".format(self.beneficio,
                                                                                                      self.id_producto,
                                                                                                      self.id_cliente)


class RegistrationForm(Form):  # Clase para verificar los campos de los usuarios
    usuario = StringField('usuario', [validators.Length(min=4, max=25)])
    telefono = StringField('telefono', [validators.Length(min=4, max=25)])
    email = StringField('email', [validators.Length(min=6, max=35)])
    contrasenia = PasswordField('New Password', [
        validators.DataRequired("Las contraseñas no coinciden"),
        validators.EqualTo('repContrasenia', message='Las contraseñas no coinciden')
    ])
    repContrasenia = PasswordField('repContrasenia')
    nombre = StringField('nombre', [validators.Length(min=4, max=25)])
    apellido = StringField('apellido', [validators.Length(min=4, max=25)])
    direccion = StringField('direccion', [validators.Length(min=4, max=50)])
    poblacion = StringField('poblacion', [validators.Length(min=4, max=50)])
    provincia = StringField('provincia', [validators.Length(min=4, max=50)])
