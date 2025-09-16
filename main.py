# main.py
import streamlit as st
import time
from functions import (
    get_usuario_by_credentials,
    get_productos,
    update_producto_stock,
    add_venta,
    add_venta_detalle,
    get_ventas,
    add_usuario,
    get_usuarios,
    add_proveedor,
    get_proveedores,
    add_producto
)

# --- Configuración de la página ---
st.set_page_config(
    page_title="Kiosco App",
    page_icon="🛒",
    layout="centered"
)

# --- Inicializar session_state ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "view" not in st.session_state:
    st.session_state["view"] = "login"
if "role" not in st.session_state:
    st.session_state["role"] = None
if "username" not in st.session_state:
    st.session_state["username"] = None
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None


# --- Funciones auxiliares ---
def login_user(username, password):
    df = get_usuario_by_credentials(username, password)
    if not df.empty:
        user = df.iloc[0]
        st.session_state["logged_in"] = True
        st.session_state["username"] = user["usuario"]
        st.session_state["role"] = user["tipo_usuario"]
        st.session_state["user_id"] = user["id"]
        st.session_state["view"] = "home"
        return True
    return False


def logout_user():
    for key in ["logged_in", "username", "role", "user_id", "view"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()


# --- Vistas ---
def show_login():
    st.title("Login")
    with st.form("login_form"):
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("🔑 Ingresar")
        if submitted:
            if login_user(username, password):
                st.success("Login exitoso")
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")


def show_home():
    st.title(f"Bienvenido, {st.session_state['username']} 👋")
    st.subheader("Menú principal")

    if st.button("🛒 Registrar venta"):
        st.session_state["view"] = "ventas"
        st.rerun()

    if st.button("📦 Modificar stock"):
        st.session_state["view"] = "stock"
        st.rerun()

    if st.session_state["role"] == "admin":
        if st.button("👥 ABM"):
            st.session_state["view"] = "abm"
            st.rerun()
        if st.button("📊 Reportes"):
            st.session_state["view"] = "reportes"
            st.rerun()

    if st.button("🚪 Logout"):
        logout_user()


def show_ventas():
    st.title("Registrar venta")
    
    # Botón Volver arriba
    if st.button("⬅️ Volver"):
        st.session_state["view"] = "home"
        st.rerun()
    
    st.divider()

    df_productos = get_productos()
    if df_productos.empty:
        st.warning("No hay productos cargados.")
        return

    producto = st.selectbox("Producto", df_productos["nombre"].tolist())
    cantidad = st.number_input("Cantidad", min_value=1, value=1)
    descuento = st.slider("Descuento", 0.0, 1.0, 0.0, 0.05)

    if st.button("✅ Confirmar venta"):
        try:
            # Insertar venta
            venta_df = add_venta(int(st.session_state["user_id"]), float(descuento))
            venta_id = int(venta_df.iloc[0]["id"])

            # Insertar detalle
            prod_row = df_productos[df_productos["nombre"] == producto].iloc[0]
            subtotal = cantidad * float(prod_row["precio"])
            add_venta_detalle(
                int(venta_id),          # 🔹 asegurar que sea int nativo
                int(prod_row["id"]),    # 🔹 asegurar que sea int nativo
                int(cantidad),          # 🔹 por si acaso
                float(subtotal)         # 🔹 asegurar float nativo
            )

            st.success(f"Venta registrada (ID: {venta_id})")
            time.sleep(2)  # Sleep para que se vea el mensaje
            st.session_state["view"] = "home"
            st.rerun()
        except Exception as e:
            st.error(f"Error registrando venta: {e}")


def show_stock():
    st.title("Modificar stock")
    
    # Botón Volver arriba
    if st.button("⬅️ Volver"):
        st.session_state["view"] = "home"
        st.rerun()
    
    st.divider()

    df_productos = get_productos()
    if df_productos.empty:
        st.warning("No hay productos cargados.")
        return

    producto = st.selectbox("Producto", df_productos["nombre"].tolist())
    nueva_cantidad = st.number_input("Nueva cantidad", min_value=0, value=0)

    if st.button("📦 Actualizar stock"):
        prod_id = int(df_productos[df_productos["nombre"] == producto].iloc[0]["id"])
        ok = update_producto_stock(prod_id, int(nueva_cantidad))
        if ok:
            st.success("Stock actualizado")
            time.sleep(2)  # Sleep para que se vea el mensaje
            st.rerun()
        else:
            st.error("Error al actualizar stock")
            time.sleep(2)  # Sleep para que se vea el mensaje


def show_abm():
    st.title("ABM (Admin)")
    
    # Botón Volver arriba
    if st.button("⬅️ Volver"):
        st.session_state["view"] = "home"
        st.rerun()
    
    st.divider()

    st.subheader("Usuarios")
    with st.form("form_usuario"):
        usuario = st.text_input("Usuario")
        contraseña = st.text_input("Contraseña", type="password")
        tipo = st.selectbox("Tipo", ["admin", "empleado"])
        if st.form_submit_button("👤 Agregar usuario"):
            ok = add_usuario(usuario, contraseña, tipo)
            if ok:
                st.success("Usuario agregado")
                time.sleep(2)  # Sleep para que se vea el mensaje
            else:
                st.error("Error al agregar usuario")
                time.sleep(2)  # Sleep para que se vea el mensaje
    st.dataframe(get_usuarios(), hide_index=True, use_container_width=True)

    st.subheader("Proveedores")
    with st.form("form_proveedor"):
        nombre = st.text_input("Nombre proveedor")
        if st.form_submit_button("🏢 Agregar proveedor"):
            ok = add_proveedor(nombre)
            if ok:
                st.success("Proveedor agregado")
                time.sleep(2)  # Sleep para que se vea el mensaje
            else:
                st.error("Error al agregar proveedor")
                time.sleep(2)  # Sleep para que se vea el mensaje
    st.dataframe(get_proveedores(), hide_index=True, use_container_width=True)

    st.subheader("Productos")
    proveedores = get_proveedores()
    with st.form("form_producto"):
        nombre = st.text_input("Nombre producto")
        proveedor = st.selectbox("Proveedor", proveedores["nombre"].tolist() if not proveedores.empty else [])
        cantidad = st.number_input("Cantidad inicial", min_value=0, value=0)
        precio = st.number_input("Precio", min_value=0.01, value=1.00)
        if st.form_submit_button("📦 Agregar producto"):
            if not proveedores.empty:
                prov_id = int(proveedores[proveedores["nombre"] == proveedor].iloc[0]["id"])
                ok = add_producto(nombre, prov_id, int(cantidad), float(precio))
                if ok:
                    st.success("Producto agregado")
                    time.sleep(2)  # Sleep para que se vea el mensaje
                else:
                    st.error("Error al agregar producto")
                    time.sleep(2)  # Sleep para que se vea el mensaje
    st.dataframe(get_productos(), hide_index=True, use_container_width=True)


def show_reportes():
    st.title("Reportes")
    
    # Botón Volver arriba
    if st.button("⬅️ Volver"):
        st.session_state["view"] = "home"
        st.rerun()
    
    st.divider()
    
    df = get_ventas(limit=20)
    if not df.empty:
        st.dataframe(df, hide_index=True, use_container_width=True)
    else:
        st.info("No hay ventas registradas.")


# --- Router ---
if not st.session_state["logged_in"]:
    show_login()
else:
    if st.session_state["view"] == "home":
        show_home()
    elif st.session_state["view"] == "ventas":
        show_ventas()
    elif st.session_state["view"] == "stock":
        show_stock()
    elif st.session_state["view"] == "abm":
        show_abm()
    elif st.session_state["view"] == "reportes":
        show_reportes()
    else:
        show_home()