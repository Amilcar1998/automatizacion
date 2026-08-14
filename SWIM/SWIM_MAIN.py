import os
import sys
import time
from selenium import webdriver

# Agregar el directorio raíz al path para importaciones
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Page.Page_Login import LoginPage
from Page.page_menu import MenuPage


def ejecutar_acceso_swim():
    """
    Script independiente para acceder al módulo SWIM:
    1. Login en el sistema
    2. Navegar a SUMMER -> SWIM
    """
    driver = None
    try:
        print("\n🚀 Iniciando automatización - Acceso a SWIM")
        print("=" * 70)

        driver = webdriver.Chrome()
        driver.maximize_window()

        print("\n📝 Realizando login...")
        driver.get("http://was7tr1.siman.com/AccesoSUMMER/")

        login_page = LoginPage(driver)
        login_page.login("ELOPEZ", "MAY2025")
        print("✅ Login exitoso")

        time.sleep(10)

        print("\n📂 Navegando al menú SUMMER → SWIM...")
        menu = MenuPage(driver)

        if not menu.acceder_frame_menu():
            raise Exception("No se pudo acceder al frame del menú")

        if not menu.hacer_click_en_summer():
            raise Exception("No se pudo hacer click en SUMMER")

        if not menu.click_swim():
            raise Exception("No se pudo hacer click en SWIM")

        print("✅ Acceso al módulo SWIM completado con éxito.")
        print("=" * 70)

        time.sleep(15)
        return True

    except Exception as e:
        print(f"\n❌ ERROR al acceder a SWIM: {e}")
        print("=" * 70)
        return False


if __name__ == "__main__":
    ejecutar_acceso_swim()
