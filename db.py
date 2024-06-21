from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# El engine permite a SQLAlchemy comunicarse con la base de datos en un dialecto concreto
# https://docs.sqlalchemy.org/en/20/core/engines.html
engine = create_engine('sqlite:///database/suministros_informaticos.db',
                       connect_args={"check_same_thread": False})
# Advertencia: Crear el engine no conecta inmediatamente con la DB, eso lo hacemos luego

# Ahora creamos la sesión, lo que nos permite realizar transacciones (operaciones)dentro de nuestra DB
Session = sessionmaker(bind=engine)  # Esto crea una clase especial
session = Session()  # Objeto de la clase Session, para hacer tareas en la base de datos

# Ahora vamos al fichero models.py en los modelos (clases) donde quereemos que se transformen en tablas,
# le añadiremos esta variable y esto se encarga de mapear y vincular cada clase a cada tabla
Base = declarative_base()  # Usamos Base para decir que clases convertimos en tabla y cual no
