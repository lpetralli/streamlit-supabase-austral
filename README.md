# streamlit-supabase-austral

Este repositorio contiene el código base para una aplicación Streamlit integrada con Supabase para almacenamiento de datos y autenticación.

Este repositorio pueden clonarlo desde GitHub o copiar manualmente el código de `main.py` y `functions.py` para poder correr una app base que funcione en su propio repo. 

## Dependencias

Instalar las dependencias requeridas desde la terminal:

```bash
pip install -r requirements.txt
```

## Configuración del Entorno

Crear un archivo `.env` usando como ejemplo el archivo `.env.example`

El mismo debe completarse con los datos del Transaction Pooler de Supabase:

**Nota:** No completar sobre `.env.example` ya que este está a modo de ejemplo - para que funcione tiene que crear el archivo `.env` y completarlo

**Nota:** Los valores a completar en el archivo `.env` deben ir sin comillas

## Testear la conexión con la base de datos

Una vez creado el archivo `.env`, asegurarse de guardarlo y usar `test.ipynb` para probar la conexión. Si funciona en `test.ipynb` significa que luego va a funcionar en la app.

## Funciones genéricas en `functions.py`

El archivo `functions.py` contiene las siguientes funciones genéricas para interactuar con la base de datos de Supabase:

### `connect_to_supabase()`
- **Propósito**: Establece conexión con la base de datos PostgreSQL de Supabase
- **Retorna**: Objeto de conexión o `None` si hay error
- **Uso**: Se conecta automáticamente usando las variables del archivo `.env`

### `execute_query(query, conn=None, is_select=True, params=None)`
- **Propósito**: Ejecuta consultas SQL y retorna resultados como DataFrame de pandas
- **Parámetros**:
  - `query`: Consulta SQL a ejecutar
  - `conn`: Conexión existente (opcional)
  - `is_select`: `True` para SELECT, `False` para INSERT/UPDATE/DELETE
  - `params`: Parámetros para la consulta (opcional)
- **Retorna**: DataFrame con resultados o `True/False` para operaciones DML

### Funciones auxiliares específicas

El archivo `functions.py` también incluye múltiples funciones auxiliares específicas para diferentes tablas (usuarios, proveedores, productos, ventas, etc.) que sirven como ejemplos de cómo crear funciones CRUD personalizadas. Estas funciones muestran el patrón recomendado para:

- Crear funciones de inserción (`add_*`)
- Crear funciones de consulta (`get_*`)
- Crear funciones de actualización (`update_*`)
- Manejar relaciones entre tablas
- Usar parámetros seguros en las consultas

Puedes revisar estas funciones en `functions.py` para entender cómo implementar tus propias funciones auxiliares siguiendo el mismo patrón.

## Cómo probar las funciones

Usa el archivo `test.ipynb` para probar las funciones genéricas paso a paso:

1. **Importar funciones**: Ejecuta las celdas que importan las funciones desde `functions.py`
2. **Cargar variables de entorno**: Ejecuta `load_dotenv()` para cargar el archivo `.env`
3. **Probar conexión**: Ejecuta `connect_to_supabase()` para verificar la conexión
4. **Ejecutar consultas**: Usa `execute_query()` para probar consultas SELECT
5. **Probar funciones auxiliares**: Puedes probar las funciones específicas disponibles en `functions.py`

**Nota**: Si las pruebas en `test.ipynb` funcionan correctamente, la aplicación Streamlit también funcionará.

## Ejecutar la aplicación

Ejecuta la aplicación Streamlit:

```bash
streamlit run main.py
```

