# Sistema de diseño del ERP

La interfaz se siente como una app de iPhone o iPad: clara, tranquila, con
poco adorno y todo a un toque. Los valores viven como tokens en
`frontend/src/estilos/tokens.css`; ningún componente usa colores ni medidas
sueltas.

## Principios

1. **Contenido primero.** Fondo gris agrupado y tarjetas blancas sin borde.
   Se separa con espacio y color, no con cajas ni sombras.
2. **Un solo color de acción.** El azul marca lo que se puede tocar y lo
   activo. Rojo, verde y naranja solo para estados.
3. **Jerarquía por tamaño y peso**, no por mayúsculas: títulos grandes,
   rótulos en frase.
4. **Controles rellenos**, no contorneados: campos grises, botones «tinted»,
   controles segmentados e interruptores.
5. **Movimiento con resorte, corto**, que acompaña y no distrae.

## Color

| Rol | Claro | Oscuro | Token |
|---|---|---|---|
| Fondo de la página | `#F2F2F7` | `#000000` | `--papel` |
| Tarjetas | `#FFFFFF` | `#1C1C1E` | `--superficie` |
| Texto / secundario / tenue | `#000` · `#3C3C43` · `#6C6C70` | `#FFF` · `#EBEBF5` · `#A1A1A8` | `--tinta`, `--tinta-2`, `--tinta-3` |
| Relleno de controles | gris 12 % | gris 24 % | `--relleno` |
| Acción (relleno) | `#0071E3` | `#0071E3` | `--acento` |
| Acción (texto, enlaces) | `#0062C4` | `#4DA3FF` | `--acento-texto` |
| Bien / aviso / error | `#1F7A35` · `#B25000` · `#D70015` | `#30D158` · `#FF9F0A` · `#FF6961` | `--ok`, `--aviso`, `--error` |

Todo texto cumple contraste AA (4.5:1) sobre su fondo, en los dos temas. El
color nunca va solo: los estados llevan forma (círculo, cuadro, rombo) y texto.

## Tipografía

- La del sistema: **SF Pro** en equipos Apple; **Inter** en el resto
  (`@fontsource-variable/inter`).
- Base de 15 px. Título grande de página 34 px (`h1`), títulos de tarjeta
  17–20 px, rótulos 13 px en gris. Números tabulares en tablas y cifras.
- Los campos suben a 16 px en el celular para que iOS no haga zoom.

## Forma y movimiento

- Esquinas: 8 px chicas, 10 px controles, 16 px tarjetas, 22 px tarjetas
  grandes (cifras y ficha). Cápsulas (999 px) para estados y chips.
- Separadores de 0.5 px que empiezan donde empieza el texto, como en Ajustes.
- `--resorte` = `cubic-bezier(.32,.72,0,1)`; 160 ms (`--rapido`), 240 ms
  (`--normal`), 420 ms (`--lento`). Al pulsar, los botones se atenúan y se
  encogen un 3 %. Sin animaciones con `prefers-reduced-motion`.

## Componentes

| Pieza | Cómo es | Dónde |
|---|---|---|
| Barra lateral | Como la de iPadOS: íconos azules, elegido en relleno azul | `App.vue`, `estilos/marco.css` |
| Barra de pestañas | Abajo en el celular (≤ 900 px), material translúcido | `App.vue` |
| Barra superior | Translúcida con desenfoque; migas en escritorio, «‹ Atrás» y título en el celular | `App.vue` |
| Marco del módulo | Apartados en control segmentado + acción principal (en el celular, botón redondo «+») | `componentes/MarcoModulo.vue` |
| Botones | `.btn` relleno gris con texto azul · `.btn-primario` azul (uno por pantalla) · `.btn-fantasma` · `.btn-peligro` | `estilos/controles.css` |
| Casillas | Círculo con marca (selección de iOS) | idem |
| Interruptor | Una casilla dentro de `label.check` (ajustes sí/no) | idem |
| Pestañas de una ficha | Control segmentado (`Pestanas.vue`) | idem |
| Tablas | `TablaDatos`: tarjeta blanca, encabezado en frase; en el celular, una tarjeta por fila | `estilos/tablas.css` |
| Avisos | Banner en cápsula que baja desde arriba | `componentes/Avisos.vue` |
| Formularios | En la página (`PanelEnLinea`), sin ventanas emergentes | `componentes/PanelEnLinea.vue` |

## Lo que no se hace

- Mayúsculas sostenidas en rótulos o encabezados.
- Bordes alrededor de tarjetas o campos; sombras marcadas.
- Gradientes decorativos, emojis como íconos (se usan los de `Icono.vue`).
- Ventanas emergentes para formularios.
- Texto bajo 4.5:1 de contraste o foco invisible.

## Revisión antes de entregar

- [ ] Probado a 390, 768, 1024 y 1440 px, en claro y en oscuro.
- [ ] Sin desplazamiento horizontal de la página; nada tapado por las barras.
- [ ] Todo lo que se toca mide 44 px en pantallas táctiles.
- [ ] Foco visible con el teclado y `prefers-reduced-motion` respetado.
