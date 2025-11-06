"""
Script de inicio para la API Electoral
Configura el event loop según el sistema operativo
"""
import sys
import asyncio
import os

# Configurar event loop según el sistema operativo
if sys.platform == 'win32':
    # Windows: Usar ProactorEventLoop para soporte de subprocesos
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    print("✅ WindowsProactorEventLoopPolicy configurado (Windows)")
    os.environ['PYTHONASYNCIODEBUG'] = '0'
else:
    # Linux: Usar el event loop por defecto
    print("✅ Usando event loop por defecto (Linux)")

import uvicorn

if __name__ == "__main__":
    # Configuración según entorno
    is_production = os.getenv('ENVIRONMENT', 'development') == 'production'
    
    # En Windows desarrollo: sin reload por problemas de event loop
    # En Linux producción: sin reload para estabilidad
    # En Linux desarrollo: con reload para comodidad
    if sys.platform == 'win32':
        use_reload = False
        print("⚠️  Reload desactivado en Windows")
    else:
        use_reload = not is_production
        if not use_reload:
            print("🚀 Modo producción: reload desactivado")
    
    # Puerto según entorno
    port = int(os.getenv('PORT', '8000'))
    
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=port,
        reload=use_reload,
        workers=1 if use_reload else int(os.getenv('WORKERS', '2'))
    )
