from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
import re
from datetime import datetime


class PeticionRequest(BaseModel):
    nuip: str = Field(..., description="Número único de identificación personal", min_length=1)
    fecha_expedicion: Optional[str] = Field(default=None, description="Fecha de expedición en formato dd/mm/yyyy")
    enviarapi: bool = Field(default=False, description="Si es True, envía los datos al API externo")
    
    @validator('fecha_expedicion')
    def validate_fecha_format(cls, v):
        #Validar formato dd/mm/yyyy
        pattern = r'^(\d{2})/(\d{2})/(\d{4})$'
        if v and not re.match(pattern, v):
            raise ValueError('La fecha debe estar en formato dd/mm/yyyy')
        
        # Validar que sea una fecha válida
        if v:
            try:
                day, month, year = map(int, v.split('/'))
                datetime(year, month, day)
            except ValueError:
                raise ValueError('Fecha inválida')
        
        return v


class BulkSisbenRequest(BaseModel):
    nuips: List[str] = Field(..., description="Lista de NUIPs a consultar", min_items=1, max_items=50)
    
    @validator('nuips')
    def validate_nuips(cls, v):
        if not v:
            raise ValueError('Debe proporcionar al menos un NUIP')
        if len(v) > 50:
            raise ValueError('Máximo 50 NUIPs por consulta')
        # Validar que todos los NUIPs no estén vacíos
        for nuip in v:
            if not nuip or not nuip.strip():
                raise ValueError('Todos los NUIPs deben ser válidos')
        return v


class BulkNameRequest(BaseModel):
    nuips: List[str] = Field(..., description="Lista de NUIPs a consultar", min_items=1, max_items=50)
    
    
    @validator('nuips')
    def validate_nuips(cls, v):
        if not v:
            raise ValueError('Debe proporcionar al menos un NUIP')
        if len(v) > 50:
            raise ValueError('Máximo 50 NUIPs por consulta')
        # Validar que todos los NUIPs no estén vacíos
        for nuip in v:
            if not nuip or not nuip.strip():
                raise ValueError('Todos los NUIPs deben ser válidos')
        return v


class ConsultaNombreRequest(BaseModel):
    nuips: List[str] = Field(..., description="Lista de NUIPs a consultar", min_items=1, max_items=100)
    enviarapi: bool = Field(default=False, description="Si es True, envía los datos al API externo")
    consultarpuesto: bool = Field(default=True, description="Si es True, consulta el puesto de votación en Registraduría")
    consultarnombre: bool = Field(default=True, description="Si es True, consulta nombre en Sisben y Procuraduría")
    
    @validator('nuips')
    def validate_nuips(cls, v):
        if not v:
            raise ValueError('Debe proporcionar al menos un NUIP')
        if len(v) > 100:
            raise ValueError('Máximo 100 NUIPs por consulta')
        # Validar que todos los NUIPs no estén vacíos
        for nuip in v:
            if not nuip or not nuip.strip():
                raise ValueError('Todos los NUIPs deben ser válidos')
        return v
   