from selenium import webdriver
import sys
import os
import time

# Agregar el directorio raíz al path para importaciones
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Page.Page_Login import LoginPage
from Page.page_menu import MenuPage
from SOL.SOL_CAMBIO_PRECIO import SOLCambioPrecioClass
from SOL.SOL_SKU_INHOUSE import ejecutar_sku_inhouse_sol


def iniciar_sesion_sol():
    """Realiza el login y navega hasta la pantalla principal de SOL. Retorna el driver activo."""
    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()

    print("\n📝 Realizando login...")
    driver.get("http://was7tr1.siman.com/AccesoSUMMER/")

    login_page = LoginPage(driver)
    login_page.login("ELOPEZ", "MAY2025")
    print("✅ Login exitoso")

    time.sleep(10)

    print("\n📂 Navegando al menú SUMMER → SOL...")
    menu = MenuPage(driver)

    if not menu.acceder_frame_menu():
        raise Exception("No se pudo acceder al frame del menú")

    if not menu.hacer_click_en_summer():
        raise Exception("No se pudo hacer click en SUMMER")

    if not menu.click_SOL():
        raise Exception("No se pudo hacer click en SOL")

    print("✅ Navegación a SOL completada")
    return driver


def ejecutar_cambio_precio_sol(tipo_cambio="PMD", codigo_razon="03", archivo_xls=None):
    """Ejecuta el flujo completo de Cambio de Precio en SOL (Formulario + Importación Excel)."""
    driver = None
    try:
        print("\n🚀 Iniciando automatización SOL - Cambio de Precio")
        print("=" * 70)

        driver = iniciar_sesion_sol()

        print("\n💲 Accediendo a Crear Cambio de Precio...")
        sol_precio = SOLCambioPrecioClass(driver)
        if not sol_precio.acceder_crear_cambio_precio():
            raise Exception("Error al acceder a Crear Cambio de Precio")

        # PASO 1: Llenar el formulario según reglas de negocio
        print("\n📝 Llenando el formulario de Cambio de Precio...")
        sol_precio.llenar_formulario_crear_cambio_precio(
            tipo_cambio_precio=tipo_cambio,      # 'PMD', 'PMU', 'TMD'
            descripcion="CAMBIO PRECIO AUTOMATIZADO",
            codigo_razon=codigo_razon,            # '03' (NIVELACION), '04' (PROMOCION), '05' (LIQUIDACION)
            numero_evento="21",                   # Por defecto 21 + ENTER
            tipo_calculo='C',                     # Precio Regular
            ordenamiento_reporte="DPT/SKU",       # DPT/SKU
            clic_siguiente=True
        )

        # PASO 2: Importar archivo Excel si se especifica una ruta
        if archivo_xls and os.path.exists(archivo_xls):
            print(f"\n📂 Procesando archivo de plantilla: {archivo_xls}")
            sol_precio.importar_excel_cambio_precio(archivo_xls)

        print("\n✅ Proceso de Cambio de Precio completado!")
        print("=" * 70)
        time.sleep(30)
        return True

    except Exception as e:
        print(f"\n❌ ERROR en SOL Cambio de Precio: {e}")
        print("=" * 70)
        return False




def ejecutar_cambio_precio_variado(mezcla_tipos):
    """Procesa múltiples tipos y códigos de razón en un solo ciclo."""
    driver = None
    try:
        print("\n🚀 Iniciando automatización SOL - Cambio de Precio mixto")
        print("=" * 70)

        driver = iniciar_sesion_sol()

        sol_precio = SOLCambioPrecioClass(driver)
        sol_precio.procesar_archivos_por_tipos(mezcla_tipos)

        print("\n✅ Proceso mixto de Cambio de Precio completado!")
        print("=" * 70)
        time.sleep(30)
        return True

    except Exception as e:
        print(f"\n❌ ERROR en SOL Cambio de Precio mixto: {e}")
        print("=" * 70)
        return False


def mostrar_menu_principal():
    print("\n=== MENU SOL ===")
    print("1) Cambio de Precio")
    print("2) Cambio de Precio Mixto")
    print("3) SKU In-House")
    print("0) Salir")
    return input("Seleccione una opción: ").strip()


def mostrar_menu_sku_inhouse():
    print("\n--- SKU In-House ---")
    print("1) Ingresar nuevo SKU")
    print("2) Crear SKU Init")
    print("3) Mantenimiento de Usuarios")
    print("4) Mantenimiento de Source Vendor")
    print("5) Mantenimiento de Atributos en SUMMER")
    print("0) Volver")
    opcion = input("Seleccione una opción SKU: ").strip()

    opciones = {
        "1": "ingresar_nuevo_sku",
        "2": "crear_sku_init",
        "3": "mantenimiento_usuarios",
        "4": "mantenimiento_source_vendor",
        "5": "mantenimiento_atributos_summer",
    }

    if opcion == "0":
        return None
    return opciones.get(opcion)


def seleccionar_tipo_cambio():
    print("\n--- Tipo de Cambio ---")
    print("1) PMD")
    print("2) PMU")
    print("3) TMD")
    opcion = input("Seleccione tipo de cambio: ").strip()
    return {"1": "PMD", "2": "PMU", "3": "TMD"}.get(opcion, "PMD")


def seleccionar_codigo_razon():
    print("\n--- Código de Razón ---")
    print("1) 03 - Nivelación")
    print("2) 04 - Promoción")
    print("3) 05 - Liquidación")
    opcion = input("Seleccione código de razón: ").strip()
    return {"1": "03", "2": "04", "3": "05"}.get(opcion, "03")


def pedir_ruta_archivo():
    ruta = input("Ruta del archivo Excel (enter para omitir): ").strip()
    return ruta if ruta else None


if __name__ == "__main__":
    while True:
        opcion = mostrar_menu_principal()
        if opcion == "0":
            print("Saliendo...")
            break
        elif opcion == "1":
            tipo = seleccionar_tipo_cambio()
            codigo_razon = seleccionar_codigo_razon()
            archivo = pedir_ruta_archivo()
            ejecutar_cambio_precio_sol(tipo_cambio=tipo, codigo_razon=codigo_razon, archivo_xls=archivo)
        elif opcion == "2":
            mezcla_tipos = [
                {"tipo_cambio": "TMD", "codigo_razon": "05"},
                {"tipo_cambio": "PMU", "codigo_razon": "04"},
                {"tipo_cambio": "PMD", "codigo_razon": "03"},
            ]
            ejecutar_cambio_precio_variado(mezcla_tipos)
        elif opcion == "3":
            opcion_sku = mostrar_menu_sku_inhouse()
            if opcion_sku:
                ejecutar_sku_inhouse_sol(opcion_sku)
        else:
            print("Opción inválida, intente de nuevo.")

