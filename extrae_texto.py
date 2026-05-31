import sys
import os
from playwright.sync_api import sync_playwright

def extraer_pagina_directa(url):
    print(f"Iniciando extractor rápido para: {url}")
    
    with sync_playwright() as p:
        # Usamos tu perfil existente para que use tu sesión activa de El Mercurio
        user_data_dir = r"D:\Mercurio\playwright_profile"
        
        browser = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False, # Lo dejamos visible para que veas la magia
            args=["--start-maximized"]
        )
        
        page = browser.pages[0]
        page.goto(url, wait_until="load")
        
        print("Esperando 5 segundos para que carguen las capas de texto...")
        page.wait_for_timeout(5000)
        
        # Extraemos todas las capas de texto idéntico a como lo hace tu M1
        capas_texto = page.locator(".textLayer").all_text_contents()
        
        if capas_texto:
            texto_final = "\n\n=== CAMBIO DE SECCIÓN / COLUMNA ===\n\n".join(capas_texto)
            print(f"¡Éxito! Se detectaron {len(capas_texto)} capas de texto.")
        else:
            print("No se detectó .textLayer, aplicando fallback al texto plano del Body...")
            texto_final = page.locator("body").inner_text()
            
        # Guardamos el botín en un archivo de texto plano
        nombre_archivo = "diario_extraido_puro.txt"
        with open(nombre_archivo, "w", encoding="utf-8") as f:
            f.write(texto_final)
            
        print(f"Todo el texto ha sido guardado en: {os.path.abspath(nombre_archivo)}")
        browser.close()

if __name__ == "__main__":
    # Si le pasas una URL por consola la usa, si no, usa la del 27 por defecto
    url_objetivo = sys.argv[1] if len(sys.argv) > 1 else "https://digital.elmercurio.com/2026/05/27/A"
    extraer_pagina_directa(url_objetivo)