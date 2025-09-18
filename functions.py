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


def execute_query(query, conn=None, is_select=True, params=None, commit=True):
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
            if commit:
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
    """
    Crea una nueva venta (ticket) en la base de datos.
    Cada llamada a esta función crea un NUEVO ticket con un ID único.
    """
    query = """
        INSERT INTO ventas (empleado_id, descuento, total)
        VALUES (%s, %s, 0) RETURNING id, fecha
    """
    result = execute_query(query, params=(empleado_id, descuento), is_select=True)
    
    if not result.empty:
        print(f"✅ Nueva venta creada - ID: {result.iloc[0]['id']}, Fecha: {result.iloc[0]['fecha']}")
    else:
        print("❌ Error: No se pudo crear la venta")
    
    return result


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


def get_venta_completa(venta_id):
    """
    Obtiene la información completa de una venta incluyendo el detalle.
    """
    # Obtener información de la venta
    venta_query = """
        SELECT v.id, v.fecha, v.descuento, v.total, u.usuario AS empleado
        FROM ventas v
        JOIN usuarios u ON v.empleado_id = u.id
        WHERE v.id = %s
    """
    venta_info = execute_query(venta_query, params=(venta_id,), is_select=True)
    
    # Obtener detalle de la venta
    detalle = get_detalle_por_venta(venta_id)
    
    return venta_info, detalle


def update_venta_total(venta_id, total):
    """
    Actualiza el total de una venta después de agregar todos los productos.
    """
    query = "UPDATE ventas SET total = %s WHERE id = %s"
    return execute_query(query, params=(total, venta_id), is_select=False)


def procesar_venta_completa_db(empleado_id, productos_carrito, descuento=0.0):
    """
    Procesa una venta completa con múltiples productos en una sola transacción.
    Esto evita problemas de claves foráneas.
    """
    conn = None
    try:
        # Conectar a la base de datos
        conn = connect_to_supabase()
        if not conn:
            return False, "Error de conexión a la base de datos"
        
        cursor = conn.cursor()
        
        # 1. Crear la venta
        venta_query = """
            INSERT INTO ventas (empleado_id, descuento, total)
            VALUES (%s, %s, 0) RETURNING id
        """
        cursor.execute(venta_query, (empleado_id, descuento))
        venta_id = cursor.fetchone()[0]
        
        # 2. Calcular total y agregar detalles
        total_venta = 0
        for item in productos_carrito:
            subtotal = item['precio'] * item['cantidad']
            total_venta += subtotal
            
            # Insertar detalle
            detalle_query = """
                INSERT INTO venta_detalle (venta_id, producto_id, cantidad, subtotal)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(detalle_query, (
                venta_id,
                item['id'],
                item['cantidad'],
                subtotal
            ))
            
            # Actualizar stock del producto
            stock_query = """
                UPDATE productos 
                SET cantidad = cantidad - %s 
                WHERE id = %s
            """
            cursor.execute(stock_query, (item['cantidad'], item['id']))
        
        # 3. Actualizar el total de la venta
        total_query = "UPDATE ventas SET total = %s WHERE id = %s"
        cursor.execute(total_query, (total_venta, venta_id))
        
        # 4. Confirmar toda la transacción
        conn.commit()
        
        return True, venta_id
        
    except Exception as e:
        print(f"Error procesando venta completa: {e}")
        if conn:
            conn.rollback()
        return False, str(e)
    finally:
        if conn:
            conn.close()