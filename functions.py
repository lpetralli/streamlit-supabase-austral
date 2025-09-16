import psycopg2
import os
from dotenv import load_dotenv
import pandas as pd

# Load environment variables from .env file
load_dotenv()

# =====================================
# CONEXIÓN Y EJECUCIÓN DE QUERIES
# =====================================
def connect_to_supabase():
    """
    Conecta a la base de datos de Supabase.
    """
    try:
        host = os.getenv("SUPABASE_DB_HOST")
        port = os.getenv("SUPABASE_DB_PORT")
        dbname = os.getenv("SUPABASE_DB_NAME")
        user = os.getenv("SUPABASE_DB_USER")
        password = os.getenv("SUPABASE_DB_PASSWORD")

        if not all([host, port, dbname, user, password]):
            print("Error: faltan variables de entorno para la conexión.")
            return None

        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
        )
        return conn
    except psycopg2.Error as e:
        print(f"Error conectando a Supabase: {e}")
        return None


def execute_query(query, conn=None, is_select=True, params=None):
    """
    Ejecuta una query SQL. Devuelve un DataFrame si es SELECT,
    o True/False si es DML (INSERT, UPDATE, DELETE).
    """
    try:
        close_conn = False
        if conn is None:
            conn = connect_to_supabase()
            close_conn = True

        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        if is_select:
            results = cursor.fetchall()
            colnames = [desc[0] for desc in cursor.description]
            df = pd.DataFrame(results, columns=colnames)
            result = df
        else:
            conn.commit()
            result = True

        cursor.close()
        if close_conn:
            conn.close()

        return result
    except Exception as e:
        print(f"Error ejecutando query: {e}")
        if conn and not is_select:
            conn.rollback()
        return pd.DataFrame() if is_select else False


# =====================================
# FUNCIONES CRUD POR TABLA
# =====================================

# ---- Usuarios ----
def add_usuario(usuario, contraseña, tipo_usuario):
    query = """
        INSERT INTO usuarios (usuario, contraseña, tipo_usuario)
        VALUES (%s, %s, %s)
    """
    return execute_query(query, params=(usuario, contraseña, tipo_usuario), is_select=False)


def get_usuario_by_credentials(usuario, contraseña):
    query = """
        SELECT id, usuario, tipo_usuario
        FROM usuarios
        WHERE usuario = %s AND contraseña = %s
    """
    return execute_query(query, params=(usuario, contraseña), is_select=True)


def get_usuarios():
    query = "SELECT id, usuario, tipo_usuario FROM usuarios"
    return execute_query(query, is_select=True)


# ---- Proveedores ----
def add_proveedor(nombre):
    query = "INSERT INTO proveedores (nombre) VALUES (%s)"
    return execute_query(query, params=(nombre,), is_select=False)


def get_proveedores():
    query = "SELECT id, nombre FROM proveedores"
    return execute_query(query, is_select=True)


# ---- Productos ----
def add_producto(nombre, proveedor_id, cantidad, precio):
    query = """
        INSERT INTO productos (nombre, proveedor_id, cantidad, precio)
        VALUES (%s, %s, %s, %s)
    """
    return execute_query(query, params=(nombre, proveedor_id, cantidad, precio), is_select=False)


def update_producto_stock(producto_id, nueva_cantidad):
    query = "UPDATE productos SET cantidad = %s WHERE id = %s"
    return execute_query(query, params=(nueva_cantidad, producto_id), is_select=False)


def get_productos():
    query = "SELECT id, nombre, cantidad, precio FROM productos"
    return execute_query(query, is_select=True)


# ---- Ventas ----
def add_venta(empleado_id, descuento=0):
    query = """
        INSERT INTO ventas (empleado_id, descuento, total)
        VALUES (%s, %s, 0) RETURNING id
    """
    return execute_query(query, params=(empleado_id, descuento), is_select=True)


def get_ventas(limit=20):
    query = f"""
        SELECT v.id, v.fecha, u.usuario AS empleado, v.total, v.descuento
        FROM ventas v
        JOIN usuarios u ON v.empleado_id = u.id
        ORDER BY v.fecha DESC
        LIMIT {limit}
    """
    return execute_query(query, is_select=True)


# ---- Detalle de ventas ----
def add_venta_detalle(venta_id, producto_id, cantidad, subtotal):
    query = """
        INSERT INTO venta_detalle (venta_id, producto_id, cantidad, subtotal)
        VALUES (%s, %s, %s, %s)
    """
    return execute_query(query, params=(venta_id, producto_id, cantidad, subtotal), is_select=False)


def get_detalle_por_venta(venta_id):
    query = """
        SELECT vd.id, p.nombre, vd.cantidad, vd.subtotal
        FROM venta_detalle vd
        JOIN productos p ON vd.producto_id = p.id
        WHERE vd.venta_id = %s
    """
    return execute_query(query, params=(venta_id,), is_select=True)