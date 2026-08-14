import pathlib
import sys
import traceback
import time
import json
import logging

# Reconfigurar stdout a UTF-8 para prevenir errores de charmap en la consola de Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from Page.Page_Login import LoginPage
from Page.page_menu import MenuPage
from OCEANO.OCEANOMAIN import main_descripcion, llenar_po


# Carpetas donde están los archivos .xls a subir
CARPETA_ARCHIVOS = pathlib.Path(r"c:\Users\eliseo_lopezp\automatizacion_web\archivos")
CARPETA_IMPORTADAS = CARPETA_ARCHIVOS / "importadas"
CARPETA_LOCALES = CARPETA_ARCHIVOS / "locales"


def obtener_archivos_con_tipo() -> list[tuple[pathlib.Path, str]]:
    """Retorna la lista de tuplas (archivo_path, tipo_po) buscando en:
    - 'archivos/importadas' -> 'Importada'
    - 'archivos/locales' -> 'Local'
    - Archivos sueltos en 'archivos' -> 'Importada' (por defecto)
    """
    CARPETA_IMPORTADAS.mkdir(parents=True, exist_ok=True)
    CARPETA_LOCALES.mkdir(parents=True, exist_ok=True)

    archivos_con_tipo = []

    # 1. Archivos en carpetas específicas
    for f in sorted(CARPETA_IMPORTADAS.glob("*.xls")):
        archivos_con_tipo.append((f, "Importada"))

    for f in sorted(CARPETA_LOCALES.glob("*.xls")):
        archivos_con_tipo.append((f, "Local"))

    # 2. Archivos sueltos en la raíz de 'archivos'
    for f in sorted(CARPETA_ARCHIVOS.glob("*.xls")):
        archivos_con_tipo.append((f, "Importada"))

    return archivos_con_tipo


def importar_sku_desde_archivo(menu: MenuPage, full_path: str):
    """
    Lógica robusta para subir un archivo .xls, manejando iframes,
    elementos ocultos y la espera de la respuesta del servidor.
    """
    driver = menu.driver
    logging.info("Iniciando proceso de importación de archivo SKU...")

    # 1. Cambiar al iframe de importación
    try:
        logging.info("Cambiando al iframe 'frameImporSkuXlsF1'...")
        WebDriverWait(driver, 10).until(EC.frame_to_be_available_and_switch_to_it("frameImporSkuXlsF1"))
        WebDriverWait(driver, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')
    except TimeoutException:
        logging.error("No se pudo encontrar o cambiar al iframe 'frameImporSkuXlsF1'.")
        raise

    # 2. Asignar la ruta del archivo al input
    try:
        logging.info("Buscando el campo de entrada de archivo (input[type='file'])...")
        file_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file'], input[name='file']"))
        )
        driver.execute_script(
            "arguments[0].style.display = 'block'; arguments[0].style.visibility = 'visible';",
            file_input
        )
        time.sleep(0.5)
        logging.info(f"Asignando ruta: '{full_path}'")
        file_input.send_keys(full_path)
        time.sleep(1)
        val_asignado = file_input.get_attribute("value")
        if val_asignado:
            logging.info(f"Archivo asignado en el input. Valor: '{val_asignado}'")
        else:
            logging.warning("El navegador no muestra el 'value' en el input, pero se continuará con el envío.")
    except Exception as e:
        logging.exception("Error al asignar el archivo.")
        raise

    # 3. Hacer clic en el botón de 'Submit' para cargar el archivo
    try:
        logging.info("Buscando el botón para enviar el archivo (Submit)...")
        btn_submit = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@type='submit' and @value='Submit']"))
        )
        btn_submit.click()
        logging.info("Clic en el botón de envío 'Submit' realizado.")
    except Exception as e:
        logging.exception("Error al hacer clic en el botón 'Submit'.")
        raise

    # 4. Esperar la confirmación del servidor y cerrar el diálogo
    try:
        logging.info("Esperando respuesta del servidor...")
        success_xpath = "//*[contains(text(), 'Se termino el proceso exitosamente')]"
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.XPATH, success_xpath))
        )
        logging.info("Confirmación recibida: El archivo se procesó en el backend.")

        # Salir del iframe de importación para poder interactuar con el diálogo
        driver.switch_to.parent_frame()

        logging.info("Buscando y haciendo clic en el botón 'Cerrar' del diálogo...")
        close_button_xpath = "//div[contains(@class, 'ui-dialog-buttonpane')]//button[normalize-space()='Cerrar']"

        try:
            # Intento 1: Clic normal en el botón "Cerrar"
            close_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, close_button_xpath))
            )
            close_button.click()
            logging.info("Diálogo de importación cerrado con clic normal.")
        except TimeoutException:
            logging.warning("No se pudo hacer clic en el botón 'Cerrar' de forma normal. Intentando forzar el clic con JavaScript.")
            # Intento 2: Forzar el clic con JavaScript si el clic normal falla
            driver.execute_script(f"document.evaluate(\"{close_button_xpath}\", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.click();")
            logging.info("Diálogo de importación cerrado forzando el clic con JavaScript.")

        time.sleep(1) # Pequeña pausa después de cerrar el diálogo

    except TimeoutException:
        logging.error("No se recibió confirmación de éxito del servidor después de 60 segundos.")
        raise
    except Exception as e:
        logging.exception("Error durante la espera de confirmación o al cerrar el diálogo.")
        raise

    # Regresar al contexto principal para los siguientes pasos
    driver.switch_to.default_content()


def crear_po_para_archivo(driver, menu: MenuPage, archivo: pathlib.Path, tipo_po: str, indice: int, total: int):
    """Flujo completo de creación de PO para un único archivo .xls."""
    logging.info(f"============================================================")
    logging.info(f"[PROCESANDO] [{indice}/{total}] ({tipo_po}): {archivo.name}")
    logging.info(f"============================================================")

    try:
        menu.driver.switch_to.default_content()
        menu.esperar_pagina_lista(timeout=25)
        time.sleep(2)

        menu.acceder_frame_menu()
        menu.esperar_pagina_lista()
        menu.crear_po_menu()
        time.sleep(1)
        menu.crear_po()
        time.sleep(3)

        menu.acceder_frame_trabajo()
        menu.esperar_pagina_lista()
        main_descripcion(driver)
        llenar_po(driver, tipo_po=tipo_po)

        try:
            logging.info("Buscando y haciendo clic en el botón 'Continuar'...")
            menu.acceder_frame_trabajo()
            continuar_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "next")))
            continuar_button.click()
            logging.info("Clic en 'Continuar' (ID='next') realizado.")
            time.sleep(3)
        except TimeoutException:
            logging.warning("No se pudo hacer clic en el botón 'Continuar' por ID. Intentando con JavaScript.")
            try:
                menu.acceder_frame_trabajo()
                driver.execute_script("document.getElementById('next').click();")
                logging.info("Se forzó el clic en el botón con ID 'next' mediante JavaScript.")
                time.sleep(3)
            except Exception as e:
                logging.exception("Fallaron todos los intentos de hacer clic en 'Continuar'.")
                raise

        try:
            logging.info("Buscando y haciendo clic en el botón 'Importar SKU'...")
            menu.acceder_frame_trabajo()
            importar_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "importarSkusXlsF1")))
            importar_button.click()
            logging.info("Clic en 'Importar SKU' realizado.")
            time.sleep(2)
        except TimeoutException:
            logging.exception("No se pudo encontrar o hacer clic en el botón 'Importar SKU'.")
            raise

        importar_sku_desde_archivo(menu, str(archivo.resolve()))

        po_numero = menu.obtener_numero_po()
        menu.ir_a_resumen_orden()
        menu.enviar_a_aprobacion()

        logging.info(f"[EXITO] PO ({tipo_po}) N° Maestro [{po_numero}] creada exitosamente para: {archivo.name}")
        time.sleep(3)
        return po_numero

    except Exception as e:
        logging.exception(f"Ocurrió un error fatal procesando '{archivo.name}'.")
        return None


def test_login_exitoso():
    log_file = CARPETA_ARCHIVOS.parent / "automation.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, mode='w', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    driver = webdriver.Chrome()
    driver.maximize_window()
    driver.get("http://was7tr1.siman.com/AccesoSUMMER/")

    login_page = LoginPage(driver)
    login_page.login("ELOPEZ", "MAY2025")
    time.sleep(10)

    menu = MenuPage(driver)
    po_report = {}

    menu.acceder_frame_menu()
    menu.hacer_click_en_summer()
    menu.click_oceano()
    time.sleep(2)

    archivos = obtener_archivos_con_tipo()
    if not archivos:
        logging.warning(f"No se encontraron archivos .xls en: {CARPETA_ARCHIVOS}")
        driver.quit()
        return

    total = len(archivos)
    logging.info(f"Se encontraron {total} archivo(s) .xls para procesar.")

    for indice, (archivo, tipo_po) in enumerate(archivos, start=1):
        po_numero = crear_po_para_archivo(driver, menu, archivo, tipo_po, indice, total)
        if po_numero:
            po_report[po_numero] = {"archivo": archivo.name, "origen": tipo_po}

    if po_report:
        report_path = CARPETA_ARCHIVOS.parent / "po_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(po_report, f, indent=4, ensure_ascii=False)
        logging.info(f"Se ha guardado el reporte de POs en: {report_path}")

    logging.info(f"Proceso completado: {len(po_report)} PO(s) procesadas exitosamente de {total}.")
    time.sleep(5)
    # driver.quit()


if __name__ == "__main__":
    test_login_exitoso()