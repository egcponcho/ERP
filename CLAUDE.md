# Instrucciones para trabajar en este repositorio

- Todo en español: identificadores, comentarios, mensajes y documentación.
- Antes de cambiar la estructura, lea `docs/ARQUITECTURA.md`. Un módulo solo
  importa de `app.core` (backend) o de `src/nucleo` y `src/componentes`
  (frontend) y de sí mismo; se conecta con otros por registros de `core`.
- Nada propio de un rubro o país en columnas, listas fijas ni datos de
  fábrica (ver `docs/DESDE_FACTURACION.md`): es un atributo o una configuración.
- Interfaz: siga `design-system/ERP.md` y use los tokens de
  `frontend/src/estilos/tokens.css`.
- Antes de entregar: `pytest` y `ruff check .` en `backend`; `npm run lint`
  y `npm run build` en `frontend`.
