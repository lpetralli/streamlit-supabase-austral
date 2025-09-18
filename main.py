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
    get_detalle_por_venta,
    get_venta_completa,
    update_venta_total,
    procesar_venta_completa_db,
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

    # Inicializar carrito en session_state
    if "carrito" not in st.session_state:
        st.session_state["carrito"] = []
    
    df_productos = get_productos()
    if df_productos.empty:
        st.warning("No hay productos cargados.")
        return

    # Mostrar información de debugging
    st.info(f"🆔 Usuario actual: {st.session_state['username']} (ID: {st.session_state['user_id']})")
    
    # Mostrar últimas ventas para verificar
    st.subheader("📋 Últimas ventas registradas")
    df_ventas = get_ventas(limit=5)
    if not df_ventas.empty:
        st.dataframe(df_ventas, hide_index=True, width='stretch')
    else:
        st.info("No hay ventas registradas aún.")

    st.divider()
    
    # === CARRITO DE COMPRAS ===
    st.subheader("🛒 Carrito de compras")
    
    # Mostrar carrito actual
    if st.session_state["carrito"]:
        st.write("**Productos en el carrito:**")
        total_carrito = 0
        
        for i, item in enumerate(st.session_state["carrito"]):
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
            with col1:
                st.write(f"📦 {item['nombre']}")
            with col2:
                st.write(f"${item['precio']:.2f}")
            with col3:
                st.write(f"x{item['cantidad']}")
            with col4:
                subtotal = item['precio'] * item['cantidad']
                st.write(f"${subtotal:.2f}")
                total_carrito += subtotal
            with col5:
                if st.button("🗑️", key=f"remove_{i}"):
                    st.session_state["carrito"].pop(i)
                    st.rerun()
        
        st.write(f"**💰 Total del carrito: ${total_carrito:.2f}**")
        
        # Botones para el carrito
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🧹 Limpiar carrito"):
                st.session_state["carrito"] = []
                st.rerun()
        with col2:
            if st.button("✅ Confirmar venta"):
                procesar_venta_completa(total_carrito)
        with col3:
            if st.button("➕ Agregar más productos"):
                st.rerun()
    else:
        st.info("🛒 El carrito está vacío. Agrega productos para comenzar.")
    
    st.divider()
    
    # === AGREGAR PRODUCTOS ===
    st.subheader("➕ Agregar productos al carrito")
    
    col1, col2 = st.columns(2)
    
    with col1:
        producto = st.selectbox("Producto", df_productos["nombre"].tolist())
        cantidad = st.number_input("Cantidad", min_value=1, value=1)
    
    with col2:
        # Mostrar información del producto seleccionado
        if producto:
            prod_row = df_productos[df_productos["nombre"] == producto].iloc[0]
            st.write(f"**Precio unitario:** ${prod_row['precio']:.2f}")
            st.write(f"**Stock disponible:** {prod_row['cantidad']}")
            subtotal = cantidad * float(prod_row["precio"])
            st.write(f"**Subtotal:** ${subtotal:.2f}")
    
    if st.button("➕ Agregar al carrito"):
        if producto and cantidad > 0:
            prod_row = df_productos[df_productos["nombre"] == producto].iloc[0]
            
            # Verificar stock
            if cantidad > int(prod_row["cantidad"]):
                st.error(f"❌ No hay suficiente stock. Disponible: {prod_row['cantidad']}")
            else:
                # Agregar al carrito
                nuevo_item = {
                    "id": int(prod_row["id"]),
                    "nombre": producto,
                    "precio": float(prod_row["precio"]),
                    "cantidad": int(cantidad)
                }
                st.session_state["carrito"].append(nuevo_item)
                st.success(f"✅ {producto} agregado al carrito")
                st.rerun()
        else:
            st.error("❌ Por favor selecciona un producto y cantidad")


def procesar_venta_completa(total_carrito):
    """Procesa la venta completa con todos los productos del carrito"""
    try:
        # Calcular descuento (por ahora 0, se puede agregar después)
        descuento = 0.0
        
        # Mostrar información antes de crear la venta
        st.info("🔄 Procesando venta completa...")
        
        # Usar la nueva función que maneja todo en una sola transacción
        success, result = procesar_venta_completa_db(
            int(st.session_state["user_id"]), 
            st.session_state["carrito"], 
            descuento
        )
        
        if success:
            venta_id = result
            st.success(f"🎉 Venta registrada exitosamente!")
            st.success(f"📄 Ticket ID: {venta_id}")
            st.success(f"📦 Productos: {len(st.session_state['carrito'])}")
            st.success(f"💰 Total: ${total_carrito:.2f}")
            
            # Mostrar el ticket completo
            st.subheader("📋 Detalle del ticket")
            detalle_df = get_detalle_por_venta(venta_id)
            if not detalle_df.empty:
                st.dataframe(detalle_df, hide_index=True, width='stretch')
            
            # Limpiar carrito
            st.session_state["carrito"] = []
            
            time.sleep(3)  # Sleep para que se vea el mensaje
            st.session_state["view"] = "home"
            st.rerun()
        else:
            st.error(f"❌ Error al procesar la venta: {result}")
            
    except Exception as e:
        st.error(f"Error registrando venta: {e}")
        st.error("Por favor, inténtalo de nuevo")


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
    st.dataframe(get_usuarios(), hide_index=True, width='stretch')

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
    st.dataframe(get_proveedores(), hide_index=True, width='stretch')

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
    st.dataframe(get_productos(), hide_index=True, width='stretch')


def show_reportes():
    st.title("Reportes")
    
    # Botón Volver arriba
    if st.button("⬅️ Volver"):
        st.session_state["view"] = "home"
        st.rerun()
    
    st.divider()
    
    # Mostrar estadísticas generales
    st.subheader("📊 Estadísticas de ventas")
    df = get_ventas(limit=50)
    if not df.empty:
        total_ventas = len(df)
        st.metric("Total de ventas", total_ventas)
        
        # Mostrar tabla de ventas
        st.subheader("📋 Lista de ventas")
        st.dataframe(df, hide_index=True, width='stretch')
        
        # Permitir ver detalle de una venta específica
        st.subheader("🔍 Ver detalle de venta")
        venta_ids = df['id'].tolist()
        if venta_ids:
            venta_seleccionada = st.selectbox("Selecciona una venta para ver su detalle:", venta_ids)
            if st.button("Ver detalle"):
                venta_info, detalle = get_venta_completa(venta_seleccionada)
                if not venta_info.empty:
                    st.subheader(f"📄 Ticket #{venta_seleccionada}")
                    st.write(f"**Fecha:** {venta_info.iloc[0]['fecha']}")
                    st.write(f"**Empleado:** {venta_info.iloc[0]['empleado']}")
                    st.write(f"**Descuento:** {venta_info.iloc[0]['descuento']*100:.1f}%")
                    st.write(f"**Total:** ${venta_info.iloc[0]['total']:.2f}")
                    
                    if not detalle.empty:
                        st.subheader("📦 Productos vendidos")
                        st.dataframe(detalle, hide_index=True, width='stretch')
                    else:
                        st.info("No hay productos en esta venta")
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