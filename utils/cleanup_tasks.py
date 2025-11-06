"""
Script de limpieza para gestionar archivos JSON de tareas
"""
import json
from pathlib import Path
from datetime import datetime, timedelta
import argparse

TASKS_DIR = Path("tasks")

def get_task_info(task_file):
    """Obtiene información de un archivo de tarea"""
    try:
        with open(task_file, 'r', encoding='utf-8') as f:
            task = json.load(f)
        
        # Fecha de modificación del archivo
        mtime = datetime.fromtimestamp(task_file.stat().st_mtime)
        
        return {
            'file': task_file,
            'task_id': task.get('task_id'),
            'status': task.get('status'),
            'created_at': task.get('created_at'),
            'modified_at': mtime,
            'total_nuips': task.get('total_nuips'),
            'size_kb': task_file.stat().st_size / 1024
        }
    except Exception as e:
        print(f"Error leyendo {task_file.name}: {e}")
        return None

def list_tasks(status_filter=None, days_old=None):
    """Lista tareas con filtros opcionales"""
    if not TASKS_DIR.exists():
        print("❌ Carpeta tasks/ no existe")
        return []
    
    tasks = []
    cutoff_date = datetime.now() - timedelta(days=days_old) if days_old else None
    
    for task_file in TASKS_DIR.glob("*.json"):
        info = get_task_info(task_file)
        if info:
            # Aplicar filtros
            if status_filter and info['status'] != status_filter:
                continue
            
            if cutoff_date and info['modified_at'] > cutoff_date:
                continue
            
            tasks.append(info)
    
    return tasks

def print_task_summary(tasks):
    """Imprime resumen de tareas"""
    if not tasks:
        print("No se encontraron tareas")
        return
    
    print(f"\nTotal de tareas: {len(tasks)}")
    
    # Agrupar por estado
    by_status = {}
    total_size = 0
    
    for task in tasks:
        status = task['status']
        by_status[status] = by_status.get(status, 0) + 1
        total_size += task['size_kb']
    
    print("\nPor estado:")
    for status, count in by_status.items():
        print(f"  {status}: {count}")
    
    print(f"\nEspacio total: {total_size:.2f} KB ({total_size/1024:.2f} MB)")

def delete_tasks(tasks, dry_run=True):
    """Elimina tareas"""
    if not tasks:
        print("No hay tareas para eliminar")
        return 0
    
    deleted = 0
    
    for task in tasks:
        if dry_run:
            print(f"[DRY RUN] Eliminaría: {task['task_id']} ({task['status']})")
        else:
            try:
                task['file'].unlink()
                print(f"✓ Eliminado: {task['task_id']} ({task['status']})")
                deleted += 1
            except Exception as e:
                print(f"✗ Error eliminando {task['task_id']}: {e}")
    
    return deleted

def main():
    parser = argparse.ArgumentParser(description='Gestión de archivos JSON de tareas')
    parser.add_argument('action', choices=['list', 'clean', 'stats'], 
                       help='Acción a realizar')
    parser.add_argument('--status', choices=['pending', 'processing', 'completed', 'failed'],
                       help='Filtrar por estado')
    parser.add_argument('--days', type=int,
                       help='Filtrar tareas más antiguas que X días')
    parser.add_argument('--execute', action='store_true',
                       help='Ejecutar eliminación (por defecto es dry-run)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("GESTIÓN DE TAREAS JSON")
    print("=" * 60)
    
    # Obtener tareas
    tasks = list_tasks(status_filter=args.status, days_old=args.days)
    
    if args.action == 'list':
        print(f"\nListando tareas...")
        if args.status:
            print(f"Filtro de estado: {args.status}")
        if args.days:
            print(f"Filtro de antigüedad: > {args.days} días")
        
        print_task_summary(tasks)
        
        if tasks:
            print("\nDetalle:")
            for i, task in enumerate(tasks, 1):
                print(f"\n[{i}] {task['task_id']}")
                print(f"    Estado: {task['status']}")
                print(f"    Creado: {task['created_at']}")
                print(f"    Modificado: {task['modified_at'].strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"    NUIPs: {task['total_nuips']}")
                print(f"    Tamaño: {task['size_kb']:.2f} KB")
    
    elif args.action == 'stats':
        print("\nEstadísticas de tareas:")
        print_task_summary(tasks)
        
        if tasks:
            # Estadísticas adicionales
            oldest = min(tasks, key=lambda t: t['modified_at'])
            newest = max(tasks, key=lambda t: t['modified_at'])
            largest = max(tasks, key=lambda t: t['size_kb'])
            
            print(f"\nMás antigua: {oldest['task_id']}")
            print(f"  Fecha: {oldest['modified_at'].strftime('%Y-%m-%d %H:%M:%S')}")
            
            print(f"\nMás reciente: {newest['task_id']}")
            print(f"  Fecha: {newest['modified_at'].strftime('%Y-%m-%d %H:%M:%S')}")
            
            print(f"\nMás grande: {largest['task_id']}")
            print(f"  Tamaño: {largest['size_kb']:.2f} KB")
    
    elif args.action == 'clean':
        print("\nLimpieza de tareas...")
        if args.status:
            print(f"Filtro de estado: {args.status}")
        if args.days:
            print(f"Filtro de antigüedad: > {args.days} días")
        
        print_task_summary(tasks)
        
        if tasks:
            if args.execute:
                print("\n⚠️  EJECUTANDO ELIMINACIÓN...")
                deleted = delete_tasks(tasks, dry_run=False)
                print(f"\n✓ Eliminadas {deleted} tareas")
            else:
                print("\n[DRY RUN] Simulación de eliminación:")
                delete_tasks(tasks, dry_run=True)
                print("\nPara ejecutar la eliminación, usa --execute")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    # Si se ejecuta sin argumentos, mostrar ayuda
    import sys
    if len(sys.argv) == 1:
        print("Uso:")
        print("  python cleanup_tasks.py list                    # Listar todas las tareas")
        print("  python cleanup_tasks.py list --status completed # Listar tareas completadas")
        print("  python cleanup_tasks.py list --days 7           # Listar tareas > 7 días")
        print("  python cleanup_tasks.py stats                   # Ver estadísticas")
        print("  python cleanup_tasks.py clean --status completed --days 30  # Limpiar completadas > 30 días")
        print("  python cleanup_tasks.py clean --status completed --execute  # Ejecutar limpieza")
        print("\nEjemplos:")
        print("  # Ver tareas completadas")
        print("  python cleanup_tasks.py list --status completed")
        print()
        print("  # Simular limpieza de tareas completadas > 7 días")
        print("  python cleanup_tasks.py clean --status completed --days 7")
        print()
        print("  # Ejecutar limpieza de tareas completadas > 30 días")
        print("  python cleanup_tasks.py clean --status completed --days 30 --execute")
    else:
        main()
