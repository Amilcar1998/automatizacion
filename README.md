# Automatización Web

Este proyecto contiene un flujo de automatización web desarrollado en Python utilizando Selenium. Está diseñado para ingresar al sistema, navegar por los menús correspondientes e importar archivos `.xls` de forma automática.

## Características Principales

- **Login Automático:** Inicio de sesión en el sistema usando credenciales.
- **Navegación de Menú:** Interacción con los iframes y menús (SUMMER, OCEANO) para llegar a la creación de PO (Purchase Orders).
- **Procesamiento de Archivos:** Búsqueda e importación automática de archivos `.xls` ubicados en las carpetas de `archivos/importadas` y `archivos/locales`.
- **Manejo de Errores y Tiempos de Espera (Waits):** Uso de `WebDriverWait` para gestionar tiempos de carga y ventanas emergentes (iframes y cuadros de diálogo).
- **Reportes:** Generación de un archivo `po_report.json` que contiene un resumen de los números de PO creados exitosamente.

## Requisitos

- Python 3.x
- Selenium
- WebDriver (ej. ChromeDriver) compatible con la versión del navegador instalada en el sistema.

## Estructura del Proyecto

- `Main.py`: Script principal que orquesta todo el flujo de inicio de sesión y creación de POs.
- `Page/`: Carpeta que contiene las clases utilizando el patrón Page Object Model (POM) para representar las páginas.
- `OCEANO/`: Carpeta con lógicas de automatización específicas de los flujos de negocio (OCEANO MAIN, llenar_po, etc.).
- `archivos/`: Directorio donde deben colocarse los archivos `.xls` a procesar (`importadas` o `locales`).

## Ejecución

1. Asegúrate de tener instaladas las dependencias necesarias.
2. Ejecuta el script principal:
   ```bash
   python Main.py
   ```
3. El proceso abrirá el navegador y comenzará la automatización. Revisa la consola o el archivo `automation.log` para seguir el proceso en tiempo real.
