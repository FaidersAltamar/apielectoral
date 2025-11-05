"""
Script para limpiar el cache de drivers de Chrome
Útil cuando hay problemas con drivers corruptos o conflictos de archivos
"""
import os
import shutil
import sys

def clean_driver_cache():
    """Limpia el cache de drivers de Chrome"""
    print("=" * 60)
    print("🧹 LIMPIEZA DE CACHE DE DRIVERS DE CHROME")
    print("=" * 60)
    
    caches_to_clean = []
    
    # Cache de undetected-chromedriver
    uc_cache = os.path.join(os.getenv('APPDATA'), 'undetected_chromedriver')
    if os.path.exists(uc_cache):
        caches_to_clean.append(('undetected-chromedriver', uc_cache))
    
    # Cache de webdriver-manager
    wdm_cache = os.path.join(os.getenv('USERPROFILE'), '.wdm')
    if os.path.exists(wdm_cache):
        caches_to_clean.append(('webdriver-manager', wdm_cache))
    
    if not caches_to_clean:
        print("✅ No se encontraron caches para limpiar")
        return True
    
    print(f"\n📋 Se encontraron {len(caches_to_clean)} cache(s) para limpiar:")
    for name, path in caches_to_clean:
        size = get_folder_size(path)
        print(f"  • {name}: {path} ({format_size(size)})")
    
    response = input("\n¿Deseas continuar con la limpieza? (s/n): ").strip().lower()
    if response != 's':
        print("❌ Limpieza cancelada")
        return False
    
    print("\n🚀 Iniciando limpieza...")
    success = True
    
    for name, path in caches_to_clean:
        try:
            print(f"\n🧹 Limpiando {name}...")
            shutil.rmtree(path, ignore_errors=True)
            
            # Verificar que se eliminó
            if not os.path.exists(path):
                print(f"  ✅ {name} eliminado exitosamente")
            else:
                print(f"  ⚠️ {name} no se pudo eliminar completamente")
                success = False
        except Exception as e:
            print(f"  ❌ Error al eliminar {name}: {e}")
            success = False
    
    print("\n" + "=" * 60)
    if success:
        print("✅ LIMPIEZA COMPLETADA EXITOSAMENTE")
        print("\n💡 Próximos pasos:")
        print("  1. Los drivers se descargarán automáticamente en el próximo uso")
        print("  2. Ejecuta: python test_sisben_driver.py")
    else:
        print("⚠️ LIMPIEZA COMPLETADA CON ADVERTENCIAS")
        print("\n💡 Si persisten los problemas:")
        print("  1. Cierra todos los navegadores Chrome")
        print("  2. Ejecuta este script como administrador")
    print("=" * 60)
    
    return success

def get_folder_size(path):
    """Calcula el tamaño de una carpeta"""
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
    except Exception:
        pass
    return total_size

def format_size(size):
    """Formatea el tamaño en bytes a una unidad legible"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"

if __name__ == "__main__":
    try:
        success = clean_driver_cache()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Limpieza interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
