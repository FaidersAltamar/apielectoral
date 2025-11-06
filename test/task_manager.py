"""
Gestor de tareas para consultas masivas de Sisben
Maneja almacenamiento en memoria y persistencia en archivos JSON
"""
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import uuid

from utils.time_utils import get_current_timestamp
from scrapper.sisben_scraper import SisbenScraperAuto
from scrapper.procuraduria_scraper import ProcuraduriaScraperAuto
from scrapper.police_scraper import PoliciaScraperAuto

# Directorio para almacenar tareas
TASKS_DIR = Path("tasks")
TASKS_DIR.mkdir(exist_ok=True)

# Almacenamiento en memoria para tareas asíncronas
tasks_storage: Dict[str, Dict[str, Any]] = {}


# ==================== FUNCIONES DE PERSISTENCIA ====================

def save_task_to_file(task_id: str, task_data: Dict[str, Any]):
    """Guarda una tarea en un archivo JSON"""
    file_path = TASKS_DIR / f"{task_id}.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(task_data, f, ensure_ascii=False, indent=2)


def load_task_from_file(task_id: str) -> Optional[Dict[str, Any]]:
    """Carga una tarea desde un archivo JSON"""
    file_path = TASKS_DIR / f"{task_id}.json"
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def delete_task_file(task_id: str) -> bool:
    """Elimina el archivo JSON de una tarea"""
    file_path = TASKS_DIR / f"{task_id}.json"
    if file_path.exists():
        file_path.unlink()
        return True
    return False


def list_all_tasks() -> List[str]:
    """Lista todos los IDs de tareas guardadas"""
    return [f.stem for f in TASKS_DIR.glob("*.json")]


# ==================== GESTIÓN DE TAREAS ====================

def create_task(nuips: List[str], task_type: str = "sisben") -> Dict[str, Any]:
    """
    Crea una nueva tarea de consulta masiva
    
    Args:
        nuips: Lista de NUIPs a consultar
        task_type: Tipo de tarea ("sisben" o "name")
        
    Returns:
        dict: Información de la tarea creada
    """
    task_id = str(uuid.uuid4())
    
    # Inicializar tarea en el almacenamiento
    task_data = {
        "task_id": task_id,
        "task_type": task_type,
        "status": "pending",
        "created_at": get_current_timestamp(),
        "started_at": None,
        "completed_at": None,
        "nuips": nuips,
        "total_nuips": len(nuips),
        "progress": {
            "total": len(nuips),
            "processed": 0,
            "successful": 0,
            "failed": 0
        },
        "data": None,
        "error": None
    }
    
    # Guardar en memoria
    tasks_storage[task_id] = task_data
    
    # Guardar en archivo
    save_task_to_file(task_id, task_data)
    
    return {
        "success": True,
        "message": "Tarea creada exitosamente",
        "task_id": task_id,
        "task_type": task_type,
        "status": "pending",
        "total_nuips": len(nuips),
        "created_at": task_data["created_at"]
    }


def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene una tarea por su ID (de memoria o archivo)
    
    Args:
        task_id: ID de la tarea
        
    Returns:
        dict: Datos de la tarea o None si no existe
    """
    # Intentar obtener de memoria primero
    task = tasks_storage.get(task_id)
    
    # Si no está en memoria, intentar cargar desde archivo
    if task is None:
        task = load_task_from_file(task_id)
        
        # Si se encontró en archivo, cargar en memoria
        if task is not None:
            tasks_storage[task_id] = task
    
    return task


def delete_task(task_id: str) -> bool:
    """
    Elimina una tarea (de memoria y archivo)
    
    Args:
        task_id: ID de la tarea
        
    Returns:
        bool: True si se eliminó, False si no existía
    """
    # Verificar si existe
    task = get_task(task_id)
    if task is None:
        return False
    
    # Eliminar de memoria si existe
    if task_id in tasks_storage:
        del tasks_storage[task_id]
    
    # Eliminar archivo JSON
    delete_task_file(task_id)
    
    return True


def list_tasks(task_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Lista todas las tareas guardadas con información resumida
    
    Args:
        task_type: Filtrar por tipo de tarea ("sisben", "name", o None para todas)
    
    Returns:
        list: Lista de tareas con información resumida
    """
    task_ids = list_all_tasks()
    
    tasks_summary = []
    for task_id in task_ids:
        task = get_task(task_id)
        
        if task:
            # Filtrar por tipo si se especifica
            if task_type and task.get("task_type") != task_type:
                continue
                
            tasks_summary.append({
                "task_id": task_id,
                "task_type": task.get("task_type", "sisben"),
                "status": task.get("status"),
                "created_at": task.get("created_at"),
                "completed_at": task.get("completed_at"),
                "total_nuips": task.get("total_nuips"),
                "progress": task.get("progress")
            })
    
    return tasks_summary


# ==================== PROCESAMIENTO DE TAREAS ====================

async def process_bulk_sisben_task(task_id: str, nuips: List[str]):
    """
    Procesa una tarea de consulta masiva de Sisben en segundo plano
    
    Args:
        task_id: ID de la tarea
        nuips: Lista de NUIPs a consultar
    """
    try:
        # Actualizar estado a procesando
        tasks_storage[task_id]["status"] = "processing"
        tasks_storage[task_id]["started_at"] = get_current_timestamp()
        save_task_to_file(task_id, tasks_storage[task_id])
        
        results = []
        processed = 0
        errors = 0
        
        # Procesar cada NUIP
        for nuip in nuips:
            scraper = None
            try:
                scraper = SisbenScraperAuto(headless=True)
                result = scraper.scrape_name_by_nuip(nuip)
                
                # Extraer información relevante
                if result.get("success"):
                    results.append({
                        "nuip": nuip,
                        "success": True,
                        "name": result.get("name"),
                        "data": result
                    })
                    processed += 1
                else:
                    results.append({
                        "nuip": nuip,
                        "success": False,
                        "error": result.get("error", "No se encontró información")
                    })
                    errors += 1
                    
            except Exception as e:
                results.append({
                    "nuip": nuip,
                    "success": False,
                    "error": str(e)
                })
                errors += 1
            finally:
                if scraper:
                    try:
                        scraper.close()
                    except:
                        pass
            
            # Actualizar progreso
            tasks_storage[task_id]["progress"] = {
                "total": len(nuips),
                "processed": processed + errors,
                "successful": processed,
                "failed": errors
            }
            
            # Guardar progreso en archivo
            save_task_to_file(task_id, tasks_storage[task_id])
        
        # Marcar tarea como completada
        tasks_storage[task_id]["status"] = "completed"
        tasks_storage[task_id]["completed_at"] = get_current_timestamp()
        tasks_storage[task_id]["data"] = results
        
        # Guardar tarea completada en archivo
        save_task_to_file(task_id, tasks_storage[task_id])
        
    except Exception as e:
        # Marcar tarea como fallida
        tasks_storage[task_id]["status"] = "failed"
        tasks_storage[task_id]["error"] = str(e)
        tasks_storage[task_id]["completed_at"] = get_current_timestamp()
        
        # Guardar tarea fallida en archivo
        save_task_to_file(task_id, tasks_storage[task_id])


async def process_bulk_name_task(task_id: str, nuips: List[str], fecha_expedicion: Optional[str] = None):
    """
    Procesa una tarea de consulta masiva de nombres en segundo plano
    Busca secuencialmente en: Sisben -> Procuraduría -> Policía (si hay fecha)
    
    Args:
        task_id: ID de la tarea
        nuips: Lista de NUIPs a consultar
        fecha_expedicion: Fecha de expedición opcional para consulta de Policía
    """
    try:
        # Actualizar estado a procesando
        tasks_storage[task_id]["status"] = "processing"
        tasks_storage[task_id]["started_at"] = get_current_timestamp()
        save_task_to_file(task_id, tasks_storage[task_id])
        
        results = []
        processed = 0
        errors = 0
        
        # Procesar cada NUIP
        for nuip in nuips:
            name = ""
            source = None
            success = False
            error_msg = None
            
            try:
                # 1. Buscar en Sisben primero
                scraper_sisben = None
                try:
                    scraper_sisben = SisbenScraperAuto(headless=True)
                    result_sisben = scraper_sisben.scrape_name_by_nuip(nuip)
                    
                    if result_sisben.get("status") == "success":
                        extracted_name = result_sisben.get("name")
                        if extracted_name and extracted_name.strip():
                            name = extracted_name.strip()
                            source = "sisben"
                            success = True
                except Exception as e:
                    pass  # Continuar con la siguiente fuente
                finally:
                    if scraper_sisben:
                        try:
                            scraper_sisben.close()
                        except:
                            pass
                
                # 2. Si no se encontró en Sisben, buscar en Procuraduría
                if not name:
                    scraper_procuraduria = None
                    try:
                        scraper_procuraduria = ProcuraduriaScraperAuto(headless=True)
                        result_procuraduria = scraper_procuraduria.scrape_nuip(nuip)
                        
                        if result_procuraduria.get("status") == "success":
                            extracted_name = result_procuraduria.get("name")
                            if extracted_name and extracted_name.strip():
                                name = extracted_name.strip()
                                source = "procuraduria"
                                success = True
                    except Exception as e:
                        pass  # Continuar con la siguiente fuente
                    finally:
                        if scraper_procuraduria:
                            try:
                                scraper_procuraduria.close()
                            except:
                                pass
                
                # 3. Si no se encontró en Procuraduría y hay fecha_expedicion, buscar en Policía
                if not name and fecha_expedicion and fecha_expedicion.strip():
                    scraper_police = None
                    try:
                        scraper_police = PoliciaScraperAuto(headless=True)
                        result_police = scraper_police.scrape_name_by_nuip(nuip, fecha_expedicion)
                        
                        if result_police.get("status") == "success":
                            extracted_name = result_police.get("name")
                            if extracted_name and extracted_name.strip():
                                name = extracted_name.strip()
                                source = "policia"
                                success = True
                    except Exception as e:
                        pass  # No hay más fuentes
                    finally:
                        if scraper_police:
                            try:
                                scraper_police.close()
                            except:
                                pass
                
                # Agregar resultado
                if success:
                    results.append({
                        "nuip": nuip,
                        "success": True,
                        "name": name,
                        "source": source
                    })
                    processed += 1
                else:
                    results.append({
                        "nuip": nuip,
                        "success": False,
                        "name": "",
                        "error": "No se encontró el nombre en ninguna fuente"
                    })
                    errors += 1
                    
            except Exception as e:
                results.append({
                    "nuip": nuip,
                    "success": False,
                    "name": "",
                    "error": str(e)
                })
                errors += 1
            
            # Actualizar progreso
            tasks_storage[task_id]["progress"] = {
                "total": len(nuips),
                "processed": processed + errors,
                "successful": processed,
                "failed": errors
            }
            
            # Guardar progreso en archivo
            save_task_to_file(task_id, tasks_storage[task_id])
        
        # Marcar tarea como completada
        tasks_storage[task_id]["status"] = "completed"
        tasks_storage[task_id]["completed_at"] = get_current_timestamp()
        tasks_storage[task_id]["data"] = results
        
        # Guardar tarea completada en archivo
        save_task_to_file(task_id, tasks_storage[task_id])
        
    except Exception as e:
        # Marcar tarea como fallida
        tasks_storage[task_id]["status"] = "failed"
        tasks_storage[task_id]["error"] = str(e)
        tasks_storage[task_id]["completed_at"] = get_current_timestamp()
        
        # Guardar tarea fallida en archivo
        save_task_to_file(task_id, tasks_storage[task_id])


# ==================== UTILIDADES ====================

def get_tasks_directory() -> Path:
    """Retorna el directorio de tareas"""
    return TASKS_DIR


def get_task_count() -> int:
    """Retorna el número total de tareas guardadas"""
    return len(list_all_tasks())


def get_tasks_by_status(status: str) -> List[Dict[str, Any]]:
    """
    Obtiene todas las tareas con un estado específico
    
    Args:
        status: Estado a filtrar (pending, processing, completed, failed)
        
    Returns:
        list: Lista de tareas con el estado especificado
    """
    all_tasks = list_tasks()
    return [task for task in all_tasks if task.get("status") == status]
