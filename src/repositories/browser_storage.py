"""Small direct IndexedDB store with a guarded one-time IDBFS migration."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Awaitable, Callable, Optional


_cached_content: Optional[str] = None
_writes_enabled = False
_bridge: Any = None


def _install_bridge():
    import js

    js.eval(
        """
        (() => {
          if (globalThis.__gumliStorage) return;
          const DB_NAME = 'gumli-direct-storage';
          const STORE_NAME = 'app-data';
          const DATA_KEY = 'checklists-json';

          const open = () => new Promise((resolve, reject) => {
            const request = indexedDB.open(DB_NAME, 1);
            request.onupgradeneeded = () => {
              const db = request.result;
              if (!db.objectStoreNames.contains(STORE_NAME)) {
                db.createObjectStore(STORE_NAME);
              }
            };
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
          });

          globalThis.__gumliStorage = {
            async get() {
              const db = await open();
              return new Promise((resolve, reject) => {
                const transaction = db.transaction(STORE_NAME, 'readonly');
                const request = transaction.objectStore(STORE_NAME).get(DATA_KEY);
                request.onsuccess = () => resolve(request.result ?? null);
                request.onerror = () => reject(request.error);
                transaction.oncomplete = () => db.close();
                transaction.onerror = () => reject(transaction.error);
              });
            },
            async put(value) {
              const db = await open();
              return new Promise((resolve, reject) => {
                const transaction = db.transaction(STORE_NAME, 'readwrite');
                transaction.objectStore(STORE_NAME).put(value, DATA_KEY);
                transaction.oncomplete = () => { db.close(); resolve(true); };
                transaction.onerror = () => { db.close(); reject(transaction.error); };
                transaction.onabort = () => { db.close(); reject(transaction.error); };
              });
            },
            putSoon(value) {
              this.put(value).catch((error) => console.error('[GUMLI STORAGE] Direct write failed', error));
            },
            async getFamilyConnection() {
              const db = await open();
              return new Promise((resolve, reject) => {
                const transaction = db.transaction(STORE_NAME, 'readonly');
                const request = transaction.objectStore(STORE_NAME).get('family-connection-v1');
                request.onsuccess = () => resolve(request.result ?? null);
                request.onerror = () => reject(request.error);
                transaction.oncomplete = () => db.close();
                transaction.onerror = () => reject(transaction.error);
              });
            },
            async putFamilyConnection(value) {
              const db = await open();
              return new Promise((resolve, reject) => {
                const transaction = db.transaction(STORE_NAME, 'readwrite');
                transaction.objectStore(STORE_NAME).put(value, 'family-connection-v1');
                transaction.oncomplete = () => { db.close(); resolve(true); };
                transaction.onerror = () => { db.close(); reject(transaction.error); };
                transaction.onabort = () => { db.close(); reject(transaction.error); };
              });
            },
            async deleteFamilyConnection() {
              const db = await open();
              return new Promise((resolve, reject) => {
                const transaction = db.transaction(STORE_NAME, 'readwrite');
                transaction.objectStore(STORE_NAME).delete('family-connection-v1');
                transaction.oncomplete = () => { db.close(); resolve(true); };
                transaction.onerror = () => { db.close(); reject(transaction.error); };
                transaction.onabort = () => { db.close(); reject(transaction.error); };
              });
            },
            async getFamilyBootstrap() {
              const db = await open();
              return new Promise((resolve, reject) => {
                const transaction = db.transaction(STORE_NAME, 'readonly');
                const request = transaction.objectStore(STORE_NAME).get('family-bootstrap-v1');
                request.onsuccess = () => resolve(request.result ?? null);
                request.onerror = () => reject(request.error);
                transaction.oncomplete = () => db.close();
                transaction.onerror = () => reject(transaction.error);
              });
            },
            async putFamilyBootstrap(value) {
              const db = await open();
              return new Promise((resolve, reject) => {
                const transaction = db.transaction(STORE_NAME, 'readwrite');
                transaction.objectStore(STORE_NAME).put(value, 'family-bootstrap-v1');
                transaction.oncomplete = () => { db.close(); resolve(true); };
                transaction.onerror = () => { db.close(); reject(transaction.error); };
                transaction.onabort = () => { db.close(); reject(transaction.error); };
              });
            }
          };
        })();
        """
    )
    return js.globalThis.__gumliStorage


async def prepare_browser_storage(
    legacy_loader: Callable[[], Awaitable[bool]],
    legacy_path: str,
    bridge=None,
) -> str:
    """Load direct storage, or safely migrate a confirmed legacy IDBFS file."""
    global _bridge, _cached_content, _writes_enabled

    _bridge = bridge if bridge is not None else _install_bridge()
    try:
        direct_content = await _bridge.get()
        direct_available = True
    except Exception:
        direct_content = None
        direct_available = False
    if direct_content is not None:
        _cached_content = str(direct_content)
        _writes_enabled = True
        return "direct"

    legacy_ready = await legacy_loader()
    if not legacy_ready:
        # Do not persist defaults when the old store could not be checked.
        _cached_content = None
        _writes_enabled = False
        return "legacy-unavailable"

    path = Path(legacy_path)
    legacy_content = path.read_text(encoding="utf-8") if path.is_file() else None
    _cached_content = legacy_content
    _writes_enabled = direct_available

    if legacy_content:
        if not direct_available:
            return "legacy-read-only"
        try:
            await _bridge.put(legacy_content)
            return "migrated"
        except Exception:
            _writes_enabled = False
            return "legacy-read-only"
    return "empty" if direct_available else "legacy-unavailable"


def read_cached() -> Optional[str]:
    return _cached_content


def write_cached(content: str) -> bool:
    """Update the session immediately and persist only after safe initialization."""
    global _cached_content
    _cached_content = content
    if not _writes_enabled or _bridge is None:
        return False
    _bridge.putSoon(content)
    return True


async def read_family_connection() -> Optional[str]:
    if _bridge is None:
        return None
    value = await _bridge.getFamilyConnection()
    return None if value is None else str(value)


async def write_family_connection(content: str) -> None:
    if _bridge is None:
        raise RuntimeError("Webbläsarlagringen är inte redo")
    await _bridge.putFamilyConnection(content)


async def delete_family_connection() -> None:
    if _bridge is None:
        return
    await _bridge.deleteFamilyConnection()


async def read_family_bootstrap() -> Optional[str]:
    if _bridge is None:
        return None
    value = await _bridge.getFamilyBootstrap()
    return None if value is None else str(value)


async def write_family_bootstrap(content: str) -> None:
    if _bridge is None:
        raise RuntimeError("Webbläsarlagringen är inte redo")
    await _bridge.putFamilyBootstrap(content)


def reset_storage_state():
    """Reset module state for isolated tests."""
    global _bridge, _cached_content, _writes_enabled
    _bridge = None
    _cached_content = None
    _writes_enabled = False
