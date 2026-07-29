# PROMPTS PARA RETOMAR — FONDECYT 11200469 · Fase 5

**Actualizado 2026-07-28, al cierre de la Fase 5.**

Este archivo contiene **dos prompts listos para copiar y pegar** en una sesión nueva:

1. **[PROMPT A](#prompt-a)** — retomar, revisar, modificar o extender cualquier análisis.
2. **[PROMPT B](#prompt-b)** — generar las figuras anatómicas de publicación con FreeSurfer.

## Dónde pegarlos

| Entorno | Cómo |
|---|---|
| **Claude Code en la terminal** (recomendado) | `cd ~/Repos/F11200469_structural && claude`, y pegar el prompt |
| **Claude Code dentro de PyCharm** | Abrir el proyecto `~/Repos/F11200469_structural` y pegar en el panel de Claude |
| **claude.ai/code** | Requiere que el repo esté accesible; los datos NO están en GitHub, así que solo sirve para revisar código y documentos, no para re-ejecutar |

> ⚠️ **Los análisis solo se pueden re-ejecutar en el M5**, porque los datos viven en
> `~/FS_FONDECYT/tablas/` y FreeSurfer necesita `~/FS_FONDECYT/subjects/`. En cualquier otra
> máquina se puede leer y discutir todo, pero no recalcular.

---

<a name="prompt-a"></a>
# PROMPT A · Retomar el análisis

> Copia desde la línea siguiente hasta el final del bloque.

---

Eres mi copiloto en el análisis de MRI estructural del **FONDECYT 11200469** (PPPD/MPPP).
La Fase 5 está **cerrada**; vengo a revisar, ajustar o extender lo hecho.

## Antes de proponer nada, lee en este orden

1. `~/Repos/F11200469_structural/011_mri_estructural_fase5/docs/MAPA_DE_RESULTADOS.md`
   — índice maestro. Empieza con un resumen de dos minutos; §4 son los problemas conocidos y
   §5 mi interpretación.
2. `.../docs/PAPER_BORRADOR.md` — el artículo redactado: métodos exhaustivos, resultados
   positivos y negativos, discusión y propuesta editorial.
3. `.../docs/PLAN_ANALISIS_FASE5.md` — qué se planeó y las 7 decisiones que tomó el PI.

No hace falta que leas el código para opinar: los dos primeros documentos contienen todos los
números y todas las decisiones.

## Reglas duras del proyecto

- **PII.** Los datos son clínicos y reales. El repo es **PÚBLICO**. A GitHub va solo código,
  documentos, figuras agregadas y tablas de resultados (una fila por prueba, nunca por sujeto).
  Los datos viven en `~/FS_FONDECYT/tablas/` y **nunca** se versionan. Antes de cualquier
  commit, verifica `git status` y audita el contenido de cualquier CSV nuevo.
- **La lista de ROIs está congelada** desde antes de ver resultados
  (`06_ROIs_apriori_DCNN.md`). Cualquier cambio es una enmienda fechada, no una edición.
- **Commits pequeños y frecuentes**, en español, explicando el *por qué*.
- Trabaja en pasos pequeños y dame un **reporte breve** al cerrar cada bloque.

## Estado al 2026-07-28

**N = 46** (MPPP 17 · Vestibular 19 · Sano 10); **N = 45 en LGI** (P14 sin LGI).
**4.210 pruebas en 17 bloques analíticos; 53 sobreviven a la corrección de su familia.**

**El resultado, en dos frases:** el **LGI** distingue MPPP de pacientes vestibulares
(d ≈ −0,9) pero no se asocia con nada clínico ni conductual (0 de 260 correlaciones). El
**grosor cortical** no distingue grupos en absoluto (0 de 136 dirigidas; 0,2× el azar en
whole-brain) pero sigue de cerca a la severidad (32 de 260; ρ hasta −0,70). **Doble
disociación: girificación = rasgo, grosor = estado.**

**Lo que lo sostiene:** replicado en las tres parcelaciones (r = 0,95–0,997), replicado
vertex-wise de forma independiente, leave-one-out limpio (0 de 36 reestimaciones pierden
significación), la ansiedad no lo explica (el efecto *sube* al ajustar), y la calidad de imagen
no difiere entre grupos (SurfaceHoles p = 0,90).

**La limitación central:** el contraste informativo es contra pacientes vestibulares, no contra
sanos, y **los sanos quedan en posición intermedia** (z: MPPP −0,28 · Sano +0,04 · Vestibular
+0,24). No se puede distinguir "girificación reducida en MPPP" de "aumentada en quien compensa
bien". Son dos artículos distintos. Está en §4.1 del mapa y §4.3 del paper.

## Cómo está organizado

```
~/Repos/F11200469_structural/011_mri_estructural_fase5/
├── docs/     MAPA_DE_RESULTADOS.md · PAPER_BORRADOR.md · PLAN_ANALISIS_FASE5.md
│             REPORTE_EXPLORATORIO.html (16 secciones, no versionado, se regenera)
├── src/      config · rois · modelos · multiplicidad · pipeline · correlaciones
│             figuras · reporte · glmfit · test_modelos
├── notebooks/  un script por etapa, con marcadores `# %%` (PyCharm Scientific Mode)
├── results/  37 tablas, una fila por prueba
└── figs/     PNG (200 dpi) + PDF vectorial
```

**Etapas:** 0 descriptivos · A1/A2/A3 ROIs a-priori · AD contraste dirigido · A4 whole-brain
por tabla · A5 vertex-wise · B/B4 correlaciones · B5 vertex-wise de correlaciones ·
C1 índice de red · C2 covarianza · C3 asimetría · D superficies · R robustez · síntesis.

**Convenciones que debes respetar si tocas código:**
- El p que se reporta es el de **permutación** (Freedman-Lane), no el paramétrico.
- **FDR por familia** = una medida dentro de una etapa. Nunca global.
- Efectos **siempre** con IC bootstrap BCa estratificado por grupo.
- Semilla `11200469` — todo es determinista.
- El **LGI va sin suavizado** en vertex-wise (con fwhm10 el FWHM residual llega a 37 y
  `mri_glmfit-sim` falla en silencio). Está documentado en `src/glmfit.py`.
- Si tocas `src/modelos.py`, ejecuta después `src/test_modelos.py` (7 tests sintéticos).

## Cómo regenerar todo

```bash
cd ~/Repos/F11200469_structural/011_mri_estructural_fase5
V=~/FS_FONDECYT/.venv/bin/python
$V src/test_modelos.py            # valida el motor primero
# luego la secuencia completa de notebooks/ documentada en MAPA_DE_RESULTADOS.md §1.5
```
Tarda ~50 min (los bootstraps de B4 son lo lento). **El equipo no debe dormirse durante la
ejecución**: `caffeinate` no basta con la tapa cerrada; usar `sudo pmset disablesleep 1`.

## Lo que NO haría, y por qué

- **Más análisis exploratorios.** Con 4.210 pruebas, el conjunto de datos ya dio lo que tenía.
  Lo que falta no es analítico sino de diseño (ampliar el brazo sano, seguimiento longitudinal).
- **Mediación estructura→conducta**: necesita cientos de sujetos.
- **Machine learning**: con n = 46 el IC del AUC sería enorme.

## Empieza así

Dime en qué quiero trabajar. Si no te lo digo, propón tú a partir de §6 del mapa
(pendientes) y de §4 (problemas conocidos), y espera mi OK antes de ejecutar nada.

---

<a name="prompt-b"></a>
# PROMPT B · Figuras anatómicas de publicación con FreeSurfer

> Copia desde la línea siguiente hasta el final del bloque.

---

Eres mi copiloto en el **FONDECYT 11200469** (MRI estructural en PPPD/MPPP). El análisis está
cerrado; necesito **las figuras anatómicas finales para publicación**.

**Lee primero:** `~/Repos/F11200469_structural/011_mri_estructural_fase5/docs/MAPA_DE_RESULTADOS.md`
(§3.8 y §3.9 tienen los clusters con sus coordenadas) y `docs/PAPER_BORRADOR.md` §5.2 (las
figuras propuestas).

## Qué existe ya, y por qué no basta

Ya hay mapas de superficie hechos con **nilearn** en `figs/etapaD/` y `figs/etapaB5/`. Son
correctos y muestran los clusters bien, pero tienen calidad de render funcional, no de
publicación: el sombreado de curvatura compite con los datos, no hay barra de color integrada,
y las vistas son solo lateral y medial.

**Quiero rehacerlas con FreeSurfer (`freeview` en modo batch), que da renders muy superiores.**

## Entorno

```bash
export FREESURFER_HOME=/Applications/freesurfer/8.2.0
source $FREESURFER_HOME/SetUpFreeSurfer.sh
export SUBJECTS_DIR=~/FS_FONDECYT/subjects
```
Python: `~/FS_FONDECYT/.venv/bin/python`. Los mapas ya calculados están en
`~/FS_FONDECYT/glm/{medida}/{diseno}/glm.{hemi}/{contraste}/`, y el que hay que pintar es
`cache.th*.abs.sig.masked.mgh` (**el enmascarado por clusters supervivientes**, nunca el mapa
crudo: pintar el crudo sugiere una extensión que la corrección no respalda).

## Las cuatro figuras que necesito

### Figura 1 — Los clusters de girificación (LGI), MPPP vs Vestibular
Mapa `~/FS_FONDECYT/glm/pial_lgi/dirigido/glm.{lh,rh}/MPPP_vs_Vestibular/`.
Superficie **inflada** de `fsaverage`, **seis vistas** (lateral, medial, dorsal de cada
hemisferio), fondo de curvatura suave en dos grises, barra de color, y anotación de los tres
clusters con su tamaño y CWP. Los clusters caen en: **precentral izq + superior frontal**
(606 mm², CWP = 0,0002), **ACC caudal der + superior frontal** (188 mm², 0,0014) y **occipital
lateral der** (107 mm², 0,035).

### Figura 2 — Grosor cortical y severidad (DHI), dentro de pacientes
Mapa `~/FS_FONDECYT/glm/thickness/sev_pac_DHI/glm.{lh,rh}/pendiente_DHI/`.
Mismo formato. Clusters: **temporal superior der** (488 mm², CWP = 0,0002), **postcentral izq**
(336 mm², 0,0008) y superior frontal der (172 mm², 0,040).

### Figura 3 — Mapa anatómico de la red DCNN (no existe todavía)
**Esta es la que más falta.** Una figura puramente anatómica que muestre **dónde están las 19
ROIs a-priori** sobre la superficie inflada, coloreadas por prioridad (alta / media). Sirve para
que el lector entienda la hipótesis antes de ver ningún resultado. Las etiquetas están en
`$SUBJECTS_DIR/fsaverage/label/?h.aparc.DKTatlas.annot` y la lista congelada en
`src/rois.py` (`ROIS_ALTA` y `ROIS_MEDIA`).

### Figura 4 — Panel resumen de la doble disociación
Una sola figura de dos filas: arriba los clusters de **LGI** (diferencia entre grupos), abajo
los de **grosor** (correlación con severidad), con un rótulo que deje ver que son fenómenos
distintos en regiones parcialmente solapadas. Es la figura que cuenta la historia del paper.

## Requisitos técnicos

- `freeview` en modo batch con `-ss archivo.png <magnificación> autotrim`, sin interacción.
- Salida en **PNG a 300 dpi y PDF vectorial** donde sea posible, a `figs/etapaD_freesurfer/`.
- Paleta coherente con el resto del proyecto (`src/figuras.py`): Sano `#2a78d6`,
  Vestibular `#1baf7a`, MPPP `#eb6834`; divergente azul↔rojo para valores con signo.
- Montaje de paneles en Python (matplotlib o PIL), no a mano.
- **Muestra cada figura renderizada y revísala** antes de darla por buena: los defectos de
  layout no se ven en el código.

## Cautelas

- Si `freeview` no puede correr sin display, usa `xvfb` o vuelve a nilearn y dilo claramente.
  **No inventes un resultado visual que no se generó.**
- Las figuras van al repo (son agregadas, sin datos identificables). Los mapas `.mgh` **no**.
- Al terminar, actualiza `docs/PAPER_BORRADOR.md` §5.2 con las rutas nuevas.

---

# Apéndice · datos útiles para cualquier sesión

| Qué | Dónde |
|---|---|
| Código | `~/Repos/F11200469_structural` · `github.com/HayoBK/F11200469_structural` (público) |
| Datos (NO versionar) | `~/FS_FONDECYT/tablas/master_analitico.csv` — 46 × 2.908 |
| FreeSurfer | `~/FS_FONDECYT/subjects` · FreeSurfer 8.2.0 |
| Mapas vertex-wise | `~/FS_FONDECYT/glm/` |
| Python | `~/FS_FONDECYT/.venv/bin/python` (uv, sin `pip`: usar `uv pip install`) |
| Documentación del proyecto | `…/OneDrive…/011-MRI Estructural 2026.07/` |

**Chequeo de integridad** (si algo parece raro, esto lo detecta):
`cfg.cargar_master()` falla ruidosamente si el N, el N por grupo o la mediana de `CSE_NI`
por grupo (60,9 / 38,0 / 28,0) no son los esperados.
