# F11200469_structural

Análisis de **MRI estructural** del proyecto **FONDECYT de Iniciación 11200469**
(PI: Hayo Breinbauer) — morfometría FreeSurfer en **Mareo Postural Perceptual Persistente
(MPPP / PPPD)**, pacientes con patología vestibular periférica y voluntarios sanos.

---

## ⚠️ REGLA DE PRIVACIDAD (leer antes de commitear)

Este proyecto trabaja con **datos clínicos de pacientes reales**.

**A este repositorio va SOLO:** código, notebooks (sin outputs con datos), figuras agregadas
y documentos metodológicos.

**NUNCA se versiona:** datos por paciente, tablas con nombre/RUT/dirección, imágenes MRI,
salidas de FreeSurfer, ni ningún archivo del que no se haya verificado que está agregado.

Los datos viven **fuera del repositorio**, en `~/FS_FONDECYT/tablas/`, y se leen por ruta
absoluta declarada en `011_mri_estructural_fase5/src/config.py`.
El `.gitignore` es deliberadamente **estricto**: deniega por extensión y solo permite
excepciones nombradas. Ante la duda, excluir.

**Higiene de notebooks:** limpiar outputs antes de commitear.
```bash
nbstripout 011_mri_estructural_fase5/notebooks/*.ipynb
```

---

## Estructura

```
011_mri_estructural_fase5/     Fase 5 — estadística confirmatoria + figuras
├── notebooks/                 exploración e iteración (outputs limpios)
├── src/                       código reutilizable e importable
│   └── config.py              rutas a los datos (fuera del repo) y constantes
├── figs/                      figuras del paper (agregadas, versionables)
├── results/                   tablas de resultados agregados por ROI
└── docs/                      plan de análisis y bitácora de decisiones
```

## Entorno

Python 3.12.13, entorno `uv` en `~/FS_FONDECYT/.venv` (fuera del repo, junto a los datos).

```bash
~/FS_FONDECYT/.venv/bin/python -m ...      # invocación directa
uv pip install -r requirements.txt         # reproducir el entorno
```

FreeSurfer 8.2.0 (arm64) con `SUBJECTS_DIR=~/FS_FONDECYT/subjects`, necesario para la rama
exploratoria whole-brain (`mri_glmfit`, `mri_glmfit-sim`).

## Estado

| Fase | Estado |
|---|---|
| 1–3 · Preprocesamiento, recon-all, QC | ✅ cerrada · N=46 (MPPP 17 · Vestibular 19 · Sano 10) |
| 4 · Tabla maestra analítica | ✅ cerrada · `master_analitico.csv` 46 × 2.908 |
| 6 · ROIs a-priori (red DCNN) | ✅ lista congelada 2026-07-27 |
| **5 · Estadística + figuras** | 🔄 **en curso** |

Documentación metodológica completa (HITOs, especificación de la tabla maestra, lista
congelada de ROIs) en la carpeta OneDrive del proyecto, fuera de este repositorio.
