"""
Pool de cuentas ScraperAPI para rotación cuando se agotan créditos.
Lee proxy.txt con formato: api_key | ScraperAPI | Créditos: X/Y | Concurrencia: Z
"""

import os
import re
from threading import Lock
from typing import List, Optional

# Ruta por defecto del archivo de proxies
PROXY_FILE = os.getenv('PROXY_FILE', 'proxy.txt')
# Si set, usar solo esta key (para pruebas)
SCRAPER_API_KEY_OVERRIDE = os.getenv('SCRAPER_API_KEY')


def _parse_proxy_file(path: str) -> List[str]:
    """
    Parsea proxy.txt y retorna lista de API keys.
    Excluye líneas con Créditos: 0/ (cuentas ya agotadas).
    """
    keys: List[str] = []
    credits_zero = re.compile(r'Créditos:\s*0/', re.IGNORECASE)

    if not os.path.isfile(path):
        return keys

    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Formato: api_key | ScraperAPI | Créditos: X/Y | Concurrencia: Z
            if credits_zero.search(line):
                continue
            parts = line.split('|')
            if parts:
                api_key = parts[0].strip()
                if api_key and len(api_key) == 32:
                    keys.append(api_key)

    return keys


class ScraperAPIAccountPool:
    """
    Pool thread-safe de API keys de ScraperAPI.
    Rotación round-robin; marca cuentas agotadas (403/401).
    Si todas se agotan, reinicia el ciclo para seguir intentando.
    """

    def __init__(self, proxy_path: Optional[str] = None):
        if SCRAPER_API_KEY_OVERRIDE:
            self._all_keys: List[str] = [SCRAPER_API_KEY_OVERRIDE.strip()]
        else:
            path = proxy_path or os.path.join(os.path.dirname(os.path.abspath(__file__)), PROXY_FILE)
            self._all_keys = _parse_proxy_file(path)
        self._active_keys: List[str] = list(self._all_keys)
        self._index = 0
        self._lock = Lock()

    def get_next_key(self) -> Optional[str]:
        """Devuelve la siguiente API key disponible (round-robin)."""
        with self._lock:
            if not self._active_keys:
                # Reiniciar ciclo: todas agotadas, volver a intentar
                self._active_keys = list(self._all_keys)
                self._index = 0
            if not self._active_keys:
                return None
            idx = self._index % len(self._active_keys)
            self._index = (self._index + 1) % len(self._active_keys)
            return self._active_keys[idx]

    def mark_exhausted(self, api_key: str) -> None:
        """Marca la cuenta como agotada; la excluye del ciclo."""
        with self._lock:
            if api_key in self._active_keys:
                self._active_keys.remove(api_key)
                # Ajustar índice si es necesario
                if self._index >= len(self._active_keys) and self._active_keys:
                    self._index = 0

    def get_pool_size(self) -> int:
        """Número de cuentas activas (no agotadas)."""
        with self._lock:
            return len(self._active_keys)

    def get_total_size(self) -> int:
        """Número total de cuentas cargadas."""
        return len(self._all_keys)


# Singleton del pool
_pool_instance: Optional[ScraperAPIAccountPool] = None
_pool_lock = Lock()


def get_scraper_pool(proxy_path: Optional[str] = None) -> ScraperAPIAccountPool:
    """Obtiene la instancia singleton del pool."""
    global _pool_instance
    with _pool_lock:
        if _pool_instance is None:
            _pool_instance = ScraperAPIAccountPool(proxy_path)
        return _pool_instance
