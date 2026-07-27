# PLAN DE ANÁLISIS — FASE 5
### FONDECYT 11200469 · MRI estructural en MPPP/PPPD · versión 1.1 · 2026-07-27

> **Estado: decisiones del PI tomadas (§7). Infraestructura de código en construcción.**
> **Aún no se ha ejecutado ningún modelo sobre los datos reales.**

## DECISIONES DEL PI — 2026-07-27 (cierran §7)

| # | Decisión | Resuelto |
|---|---|---|
| **D1** | Lateralidad | **Fuera del modelo principal**; entra en robustez R4/R5. La imputación "diestro" se conserva y se declara en Methods. |
| **D2** | Agregación de labels múltiples | Ponderada por área (grosor, LGI) / suma (volumen, área). *Recomendación aceptada.* |
| **D3** | precentral/postcentral | **Dos ROIs separadas.** *Recomendación aceptada.* |
| **D4** | Subcampos hipocampales | **Eje posterior completo** (body+tail, 9×2=18), FDR propio. *Recomendación aceptada.* |
| **D5** | Ansiedad/depresión | **Dos análisis completos en paralelo** — ver nota abajo. |
| **D6** | Volumen cortical + subcortical | **Misma familia FDR.** *Recomendación aceptada.* |
| **D7** | Análisis mayores | **C1, C2, C3 y C4 activados.** C5/C6/C7 descartados. |

> **Nota sobre D5 (mejora sobre la v1.0).** El PI pidió el esquema habitual en la literatura: *un
> análisis sin ajustar por ansiedad y otro ajustando*, presentados en paralelo. Esto es **superior** a
> lo que proponía la v1.0 (re-testear solo las ROIs supervivientes), porque re-testear únicamente a
> los supervivientes **arrastra sesgo de selección**: condiciona el segundo análisis al resultado del
> primero. **Implementación adoptada:**
> - **Modelo A (principal, N=46):** sin STAI-R/BDI.
> - **Modelo B (paralelo, N≈34):** idéntico + STAI-Rasgo + BDI.
> - Ambos se corren sobre la **familia completa**, cada uno con **su propio FDR**, y se reportan en
>   **columnas contiguas** de la misma tabla. La lectura interesante es la comparación de los tamaños
>   de efecto entre A y B, no solo la de los p.

---

## 0. PRINCIPIO ORGANIZADOR

**No hay un modelo único.** Hay una **columna vertebral de etapas secuenciales**, cada una con su
pregunta, su familia de corrección por multiplicidad, sus tablas y sus figuras. Cada etapa se cierra
antes de abrir la siguiente, y cada una alimenta un documento acumulativo de exploración visual.

```
  ETAPA 0   Descriptivos, supuestos y confundentes          ← la Tabla 1 del paper
     │
  ETAPA A   ¿DIFIEREN LOS TRES GRUPOS CLÍNICOS?             ← categórica
     ├── A1  ROIs a-priori Prioridad ALTA      (confirmatorio primario)
     ├── A2  ROIs a-priori Prioridad MEDIA     (confirmatorio secundario)
     ├── A3  Subestructuras a-priori (subcampos hipocampo, núcleos tálamo/amígdala)
     ├── A4  Whole-brain por tabla — "pesca milagrosa" masa-univariante
     └── A5  Whole-brain vertex-wise en fsaverage (mri_glmfit) ← los mapas del paper
     │
  ETAPA B   ¿SE ASOCIA LA ESTRUCTURA CON LA CONDUCTA?       ← dimensional
     ├── B1  ROIs ALTA   × (CSE · entropía · Niigata)
     ├── B2  ROIs MEDIA  × (idem)
     └── B3  Whole-brain vertex-wise con regresor continuo
     │
  ETAPA C   ANÁLISIS MAYORES (opcionales, §8)               ← usan TODO el dato estructural
     │
  ETAPA D   FIGURAS ANATÓMICAS (superficie, subcortical)
     │
  ETAPA E   MEGA-DOCUMENTO exploratorio → selección de figuras finales
```

**Lógica de la jerarquía:** A1 es el test de la hipótesis DCNN. A2 la extiende. A3 baja de resolución.
A4–A5 son honestamente exploratorios. La Etapa B repite exactamente la misma escalera, pero
preguntando por asociación en vez de por diferencia de grupos.

---

## 1. ETAPA 0 — DESCRIPTIVOS, SUPUESTOS Y CONFUNDENTES

### 1.1 Tabla 1 (la que pide cualquier revisor)
Demografía y clínica por grupo: Edad, Genero, N_Educacional, lateralidad, eTIV, DHI, BDI, STAI-R/E,
MOCA, Niigata, y la batería vestibular (vHIT, VEMP).
Tests: **Kruskal-Wallis** para continuas (n pequeño), **χ² o Fisher exacto** para categóricas.
Reportar mediana [IQR] y n por celda, no media±DE.

### 1.2 ¿Qué confundentes están justificados? (se decide con datos, no por costumbre)
Para cada candidato se prueba si difiere entre grupos. Si difiere → entra al modelo; si no → se
declara y se usa solo en sensibilidad. Esto evita el ajuste ritual por variables inocuas.

| Candidato | Estado | Decisión propuesta |
|---|---|---|
| **Edad** | verificar (MPPP med. 48 · Vest 45 · Sano 43) | **Entra siempre.** Efecto masivo y conocido sobre grosor/volumen. |
| **Genero** | desbalanceado: 74% mujeres; Sano es el único 5/5 | **Entra siempre.** `Genero` y `Grupo` no son independientes. |
| **N_Educacional** | completo (46/46) | **Entra siempre.** Barato (1 df) y plausible. |
| **eTIV** | 1,33–1,96 M mm³ | **Entra SOLO en volumen y área.** Nunca en grosor ni LGI (no escalan con el cráneo). |
| **`glob_SurfaceHoles`** (proxy de Euler = calidad de reconstrucción) | **verificado: 25,8 / 26,5 / 26,7 — no difiere** | **No entra al modelo principal.** Se reporta el test como evidencia de que el QC no confunde. Sensibilidad opcional. ⭐ *aporte nuevo: es el estándar actual para descartar que un efecto sea artefacto de calidad de imagen.* |
| **Lateralidad** | tras imputar: 43 diestros / 3 no-diestros, **y los 3 son del grupo Vestibular** | **Ver §7, decisión D1.** Casi anidada en `Grupo`; aporta poco y gasta 1 df. |
| **Ansiedad/depresión** (STAI-R, BDI) | N=34 / N=33 | **Sensibilidad, nunca principal.** Es *el* confundente teórico del PPPD, pero cuesta 12 sujetos. Ver §7, decisión D5. |

---

## 2. ETAPA A — COMPARACIÓN ENTRE LOS TRES GRUPOS CLÍNICOS

### 2.1 El modelo, prueba por prueba
Unidad de análisis = **(ROI × hemisferio × medida)**. Para cada una:

```
medida ~ C(Grupo) + Edad + C(Genero) + N_Educacional  [+ eTIV si medida ∈ {volume, area}]
```

1. **Omnibus de 3 grupos:** test F de tipo II sobre `C(Grupo)`, con errores estándar **robustos HC3**
   (protege frente a heterocedasticidad, que con n=10 en un brazo es esperable).
2. **Validez del omnibus:** si los residuos fallan Shapiro-Wilk (p<0,05) o Levene, el p paramétrico
   no es fiable → se sustituye por **p de permutación** (10.000 permutaciones de la etiqueta `Grupo`,
   conservando las covariables mediante permutación de los residuos del modelo reducido,
   *Freedman-Lane*). **Recomendado: reportar el p de permutación siempre**, no solo cuando falla —
   es la opción defendible con n pequeño y no cuesta casi nada en cómputo.
3. **Post-hoc solo si el omnibus sobrevive al FDR de su familia.** Dos contrastes preespecificados:
   **MPPP vs Sano** y **MPPP vs Vestibular** (no los tres pares: el contraste Vestibular-vs-Sano no es
   hipótesis de este trabajo y se reporta solo descriptivamente).
4. **Tamaño de efecto SIEMPRE:** η²ₚ para el omnibus y **d de Cohen ajustada** (diferencia de medias
   marginales estimadas / DE residual) para cada post-hoc, ambas con **IC 95% bootstrap BCa**
   (10.000 remuestreos). Con n=10 sanos el IC será ancho: eso *es* el resultado y hay que mostrarlo.

> **Alternativa contemplada y descartada como principal:** Kruskal-Wallis. Es no-paramétrico pero
> **no admite covariables**, y renunciar a ajustar por edad y sexo en morfometría es peor que la
> no-normalidad. Se conserva como **columna de robustez** en la tabla de resultados (KW crudo), para
> mostrar que los hallazgos no dependen del modelo. Si prefieres un no-paramétrico *con* covariables,
> la opción correcta es **ANCOVA sobre rangos (Quade)**; puedo añadirla como tercera columna.

### 2.2 FDR estructurado — el conteo exacto de cada familia
**Benjamini-Hochberg (α=0,05) dentro de cada familia de medida, y dentro de cada etapa.**
A1 y A2 se corrigen por separado (jerarquía confirmatoria primaria/secundaria).

**A1 — Prioridad ALTA · 8 ROIs región · 58 pruebas**
7 corticales (ínsula posterior, supramarginal, superiortemporal, parahipocampal, entorrinal,
precúneo, istmo del cíngulo) + 1 subcortical (hipocampo).

| Familia | Pruebas |
|---|---|
| Grosor | 7 × 2 hemis = **14** |
| Área | 7 × 2 = **14** |
| Volumen | 7 × 2 cortical + 2 hipocampo = **16** |
| **LGI** (hipótesis ancla, Nigro) | 7 × 2 = **14** |
| | **58** |

**A2 — Prioridad MEDIA · 11 ROIs región · 78 pruebas**
9 corticales (superiorparietal, inferiorparietal, lateraloccipital, cuneus, middletemporal, ACC,
DLPFC, precentral, postcentral) + 3 subcorticales (tálamo, amígdala, cerebelo).

| Familia | Pruebas |
|---|---|
| Grosor | 9 × 2 = **18** |
| Área | 9 × 2 = **18** |
| Volumen | 9 × 2 + 3 × 2 = **24** |
| LGI | 9 × 2 = **18** |
| | **78** |

**A3 — Subestructuras a-priori** (familias propias, ver §7 decisión D3)
Subcampos hipocampales posteriores · núcleos talámicos anteriores (head-direction) · núcleos de
la amígdala.

**A4 — Whole-brain por tabla:** FDR dentro de cada **atlas × medida** (p. ej. "grosor DKT, 62 ROIs").
**Nunca** una sola corrección sobre las 2.530 columnas: los tres atlas son tres parcelaciones del
mismo manto y están fuertemente correlacionados (spec §5.4).

### 2.3 Variantes de robustez (se corren para las ROIs que sobreviven, no para todas)
| # | Variante | Para qué |
|---|---|---|
| R1 | Atlas **DK** en vez de DKT | Réplica independiente de la parcelación; comparabilidad con literatura PPPD |
| R2 | Con y sin **eTIV** | Verifica que el efecto de volumen no es de tamaño de cabeza |
| R3 | **Proporción** (ROI/eTIV) en vez de covariable | El otro método de normalización habitual |
| R4 | Excluir los **3 no-diestros** | Lateralidad sin imputar |
| R5 | Solo los **36 con Edinburgo real** | Sensibilidad a la imputación (§7 D1) |
| R6 | Añadir **STAI-R / BDI** (n=34/33) | ¿El efecto sobrevive al control de ansiedad? Clave en PPPD |
| R7 | Añadir **`glob_SurfaceHoles`** | ¿El efecto es artefacto de calidad de reconstrucción? |
| R8 | **Leave-one-out** por sujeto | ¿Un solo sujeto sostiene el hallazgo? Crítico con n=10 |

### 2.4 A5 — Whole-brain vertex-wise (los mapas del paper)
**Estado verificado: `-qcache` completo en los 47 sujetos.** Existen en `fsaverage`
`?h.{thickness,area,volume,curv,sulc}.fwhm{0,5,10,15,20,25}.fsaverage.mgh`. **El vertex-wise se puede
correr de inmediato** para grosor, área y volumen.
⚠️ **El LGI NO tiene qcache** (solo `?h.pial_lgi` nativo) → requiere un `mris_preproc` propio antes.

Pipeline: `mris_preproc` (o `--qcache`) → `mri_glmfit` con el mismo diseño de §2.1 (DODS) →
`mri_glmfit-sim` con **simulación de Monte Carlo por clusters**, umbral de formación de cluster
p<0,001, **CWP<0,05 corregido por dos hemisferios** (Bonferroni ×2). Suavizado fwhm10.
Contrastes: **MPPP−Sano · MPPP−Vestibular · Vestibular−Sano**, en ambas direcciones.

---

## 3. ETAPA B — ESTRUCTURA ↔ CONDUCTA / CLÍNICA

Misma escalera (ALTA → MEDIA → whole-brain), pero la pregunta es de **asociación**.

### 3.1 Los outcomes que elegiste, y su N real dentro de los 46
| Outcome | N | MPPP/Vest/Sano | Rol propuesto |
|---|---|---|---|
| **`CSE_NI`** (Cumulative Search Error) | **46** | 17/19/10 | **Primario.** Completo, y su gradiente por grupo valida el merge. |
| **`EntropyRatio_NI`** | **46** | 17/19/10 | **Primario.** Índice ancla de entropía del paper 2. |
| `Htotal_NI`, `Herror_NI`, `Hpath_NI`, `Entropia_Espacial_NI` | 46 | 17/19/10 | Secundarios (descomposición de la entropía) |
| `CSE_RV`, `Htotal_RV` | 43 | 16/18/9 | Réplica en realidad virtual |
| **`Niigata`** | **35** | 14/17/**4** | ⚠️ **Ver abajo** |

> ⚠️ **Niigata solo tiene 4 sanos.** Además es un cuestionario de síntomas de PPPD: en un voluntario
> sano el puntaje no es interpretable, es piso. **Propuesta: analizar Niigata SOLO dentro de
> pacientes (MPPP + Vestibular, n=31)**, como variable dimensional de severidad. No es una pérdida:
> es un análisis **más potente y más limpio** que forzar los 4 sanos, y responde mejor la pregunta
> ("¿la estructura escala con la severidad visuo-vestibular?"). Lo mismo aplica a DHI (5 sanos).

### 3.2 Estadística adecuada para correlacionar (n pequeño, no-normal)
1. **Spearman parcial** (`pingouin.partial_corr(method='spearman')`), controlando **Edad, Genero**
   (+ **eTIV** si la medida es volumen o área). Robusto a no-normalidad y a la escala.
2. **Dos niveles, siempre ambos:**
   - **Pooled** (los 46) con **`Grupo` como covariable** — responde "¿hay relación más allá de la
     pertenencia a grupo?".
   - **Dentro de cada grupo** (n=17/19/10) — muy frágil, se declara como tal.
   > ⚠️ **Obligatorio por paradoja de Simpson:** una correlación pooled fuerte puede ser un artefacto
   > de que los grupos difieren en ambas variables. Por eso **toda correlación se grafica coloreada
   > por grupo** y se reporta con y sin ajuste por grupo. Si el signo cambia, manda el intra-grupo.
3. **Robustez:** *skipped correlation* (`pingouin`, detecta outliers bivariados por distancia de
   Mahalanobis) — muy adecuada con n<50. Y **IC 95% bootstrap BCa** para cada ρ.
4. **FDR-BH por familia = (medida × outcome)**, dentro de cada etapa.
5. **Moderación por grupo (opcional, §8):** `outcome ~ ROI * C(Grupo) + covariables` — prueba si la
   *pendiente* estructura-conducta difiere entre grupos. Con n=46 solo detecta interacciones grandes;
   se reporta como exploratorio.

### 3.3 B3 — Whole-brain vertex-wise con regresor continuo
Mismo `mri_glmfit`, con CSE / EntropyRatio como covariable continua y contraste sobre su pendiente.
Variantes: pendiente común a los tres grupos, o pendiente por grupo (DODS) + test de interacción.

---

## 4. ETAPA D — FIGURAS ANATÓMICAS

| Figura | Herramienta | Estado |
|---|---|---|
| Mapas vertex-wise de los contrastes (clusters significativos) sobre `fsaverage` inflado | **`surfplot`** (más limpio para revista) o **`nilearn.plotting.plot_surf_stat_map`** | nilearn ✅ instalado · **surfplot ✗ hay que instalarlo** |
| ROIs DCNN pintadas sobre superficie inflada (mapa anatómico de la red) | nilearn + `?h.aparc.DKTatlas.annot` | ✅ posible ya |
| Overlay `aseg` / subcampos hipocampales en cortes representativos | `nilearn.plotting.plot_roi` sobre `orig.mgz` + `aseg.mgz` | ✅ posible ya |
| Screenshots de `freeview` en lote (respaldo, útil para cortes) | `freeview -ss salida.png` en modo batch | ✅ FreeSurfer 8.2.0 |

Todo se genera **desde scripts de Python en PyCharm**; `freeview` se invoca en modo no interactivo,
sin depender de XQuartz salvo para inspección manual.

---

## 5. ETAPA E — MEGA-DOCUMENTO EXPLORATORIO

Un **HTML acumulativo autogenerado** (`docs/REPORTE_EXPLORATORIO.html`) donde cada etapa va anexando
su sección: método aplicado, N efectivo, tabla completa de resultados, y **todas** las figuras
candidatas. Deliberadamente excesivo: es tu superficie de elección visual, no el paper.

- Se **regenera** con un comando; nunca se edita a mano.
- **No se versiona** (pesado, con imágenes embebidas). Al repo van solo las figuras que **elijas**,
  a `figs/`, y las tablas de resultados agregados a `results/`.
- Estructura por etapa: *Pregunta → Modelo → N → Tabla → Figuras → Lectura en una frase.*

**Figuras por etapa (catálogo):**
- **Etapa 0:** barras/violín de demografía; matriz de correlación de covariables; heatmap de faltantes.
- **A1/A2:** violín+box por grupo con puntos individuales y p/efecto anotado · **forest de d con IC 95%**
  (la figura más informativa con n pequeño) · heatmap ROI × medida coloreado por efecto, con marca de
  supervivencia al FDR · gráfico de volcán (efecto vs −log₁₀p).
- **A3:** perfil de subcampos hipocampales a lo largo del eje anterior-posterior.
- **A4:** manhattan por atlas/medida · glass-brain de ROIs señaladas.
- **A5/B3:** mapas de superficie de clusters.
- **B:** scatter con recta por grupo + banda de confianza · heatmap ROI × outcome de ρ parcial ·
  forest de ρ con IC.

---

## 6. ARQUITECTURA DE CÓDIGO (qué archivos se crean)

```
011_mri_estructural_fase5/
├── src/
│   ├── config.py         ✅ ya existe — rutas, constantes, carga con chequeos
│   ├── rois.py           lista congelada → columnas reales; agregación de labels múltiples
│   ├── modelos.py        ANCOVA + HC3 + permutación Freedman-Lane + η²/d + IC BCa
│   ├── multiplicidad.py  FDR-BH por familia; registro de la familia usada en cada prueba
│   ├── correlaciones.py  Spearman parcial, skipped, bootstrap, pooled vs intra-grupo
│   ├── figuras.py        estilo común del paper; violín, forest, scatter, heatmap, volcán
│   ├── superficie.py     nilearn/surfplot sobre fsaverage; wrappers de freeview
│   ├── glmfit.py         generación de FSGD/contrastes y llamadas a mri_glmfit(-sim)
│   └── reporte.py        acumulador del mega-documento HTML
├── notebooks/            00_descriptivos … 07_figuras_anatomicas
├── results/              tablas agregadas (*_resultados_*.csv se versionan)
├── figs/                 figuras elegidas (se versionan)
└── docs/                 este plan + bitácora de decisiones
```

**Regla de trazabilidad:** cada tabla de resultados incluye columnas `etapa`, `familia_fdr`,
`n_efectivo`, `modelo`, `p_param`, `p_perm`, `p_fdr`, `efecto`, `ic_low`, `ic_high`. Ninguna cifra del
paper existirá sin poder rastrear con qué modelo y qué N se produjo.

---

## 7. DECISIONES QUE NECESITO DE TI

| # | Decisión | Mi recomendación |
|---|---|---|
| **D1** | **Lateralidad en el modelo principal.** Tras imputar quedan 43 diestros / 3 no-diestros, y **los 3 son del grupo Vestibular** → casi anidada en `Grupo`, gasta 1 df y aporta poca información. | **Fuera del modelo principal**; entra como robustez R4/R5. Tu imputación se conserva y se declara en Methods. |
| **D2** | **Agregación de labels múltiples** (ACC = caudal+rostral anteriorcingulate; ínsula posterior = 2 labels de Destrieux). | **Ponderado por área** en grosor y LGI (el promedio simple sesga hacia la región pequeña); **suma** en volumen y área. Es lo correcto físicamente. |
| **D3** | **`precentral`/`postcentral`:** ¿una ROI o dos? Cambia el tamaño de la familia FDR. | **Dos ROIs separadas.** Son funcionalmente distintas (motora vs somatosensorial) y la ganancia de fusionarlas es cosmética. |
| **D4** | **Subcampos hipocampales:** ¿los 9 posteriores (body+tail) o solo tail + CA1/subiculum body? | **Los del eje posterior completo** (body+tail, 9×2=18), con FDR propio. La hipótesis es posterior, no de un subcampo puntual. |
| **D5** | **Ansiedad/depresión (STAI-R/BDI, n=34/33):** ¿sensibilidad o modelo principal? | **Sensibilidad (R6).** Es el confundente teórico central del PPPD, pero en el modelo principal cuesta 12 sujetos. Si sobrevive R6, es un resultado fuerte y se destaca. |
| **D6** | **Volumen cortical y volumen subcortical:** ¿misma familia FDR o separadas? | **Misma familia "volumen"** (16 en A1). Separarlas crearía una familia de n=2 que casi no corrige. |
| **D7** | **Análisis mayores (§8):** ¿cuáles activo? | Ver §8 — recomiendo **C1, C2 y C4**. |

---

## 8. ANÁLISIS MAYORES PROPUESTOS (usan *todo* el dato estructural)

| # | Análisis | Qué aporta | Veredicto con n=46 |
|---|---|---|---|
| **C1** | **Índice compuesto de red DCNN**: promedio de z-scores (o 1er componente principal) de las ROIs ALTA por medida → **una sola prueba por medida** | Colapsa 58 pruebas en 4. **Mucha más potencia**, y es literalmente la hipótesis "la red DCNN está alterada" en vez de "esta ROI lo está" | ✅ **Muy recomendado.** Es el análisis que mejor se ajusta a tu marco teórico y el más defendible con esta n |
| **C2** | **Covarianza estructural**: matriz de correlación entre las ROIs DCNN dentro de cada grupo → comparar matrices (permutación) | Pregunta por la **organización de la red**, no por su tamaño. Usa todos los datos estructurales de golpe | ✅ **Recomendado.** Sensible con n moderado; muy publicable en PPPD, donde la hipótesis es de red |
| **C3** | **Asimetría hemisférica** L−R: (L−R)/(L+R) por ROI | La literatura VBM en PPPD reporta hallazgos lateralizados a izquierda | ✅ Recomendado, barato — ya quedó como pendiente declarado de Fase 4 |
| **C4** | **Análisis dimensional dentro de pacientes** (n=31): severidad (Niigata/DHI) como continuo, sin sanos | Evita el cuello de botella de los 10 sanos; convierte la limitación en diseño | ✅ **Muy recomendado**, y encaja con §3.1 |
| **C5** | **MANCOVA / distancia de Mahalanobis** sobre el vector de ROIs DCNN | Test multivariado único de "la red difiere" | ⚠️ Posible, pero con 14+ variables y n=46 la matriz de covarianza es inestable. **C1 lo hace mejor y más simple** |
| **C6** | **Clasificación (ML)**: MPPP vs resto, regresión penalizada con LOOCV + permutación | Atractivo, pero con n=46 el IC del AUC será enorme | ⚠️ **Solo como apéndice**, con permutación obligatoria. Alto riesgo de sobreajuste optimista |
| **C7** | **Mediación** estructura → conducta | Tentador teóricamente | ❌ **Desaconsejado.** La mediación necesita cientos de sujetos para ser estable. No lo haría |

---

## 9. LO QUE ESTE PLAN **NO** HACE (y por qué)

- **No mete todas las variables en un modelo.** Cada prueba tiene 4–5 covariables y ~40 df residuales.
- **No usa las 2.847 columnas como familia de corrección.** Los tres atlas son redundantes entre sí.
- **No imputa datos conductuales.** N efectivo declarado modelo por modelo (listwise).
- **No usa `lgisd_*`** (es la DE intrarregional, no el LGI) ni **`HeadAngMag_NI`** (N=1).
- **No trata los hallazgos como confirmados.** Con n=10 sanos, todo A/B es **generador de hipótesis**,
  sostenido por tamaño de efecto y por convergencia entre etapas (ROI ↔ vertex-wise).

---

## 10. ORDEN DE EJECUCIÓN PROPUESTO

1. Etapa 0 (descriptivos + confundentes) → Tabla 1 y decisión empírica de covariables
2. `src/rois.py` + `src/modelos.py` con **tests unitarios sobre datos sintéticos** antes de tocar los reales
3. **A1** → tabla + forest + violines → revisión conjunta
4. **A2**, **A3** → idem
5. **C1** (índice de red) — corto y de alto rendimiento
6. **A4** (tabla) y **A5** (vertex-wise; LGI requiere `mris_preproc` previo)
7. **Etapa B** completa
8. **C2/C3/C4** según lo que hayas activado
9. **Etapa D** (figuras anatómicas) y **E** (mega-documento) — en realidad E se alimenta desde el paso 3

---

## 11. ENTORNO — instrucciones ad-hoc para PyCharm

1. **Abrir el proyecto:** `~/Repos/F11200469_structural` (no `~/FS_FONDECYT`, que contiene los datos).
2. **Intérprete:** *Settings → Project → Python Interpreter → Add → Existing environment* →
   `/Users/hayo/FS_FONDECYT/.venv/bin/python`
   (venv de `uv`, Python 3.12.13. **No tiene `pip`**: para instalar usar `uv pip install <pkg>` con
   `VIRTUAL_ENV=~/FS_FONDECYT/.venv`, o `python -m uv`.)
3. **Marcar `011_mri_estructural_fase5/src` como *Sources Root*** (clic derecho → *Mark Directory as*)
   para que `import rois, modelos` funcione en notebooks sin manipular `sys.path`.
4. **Instalar lo que falta** (antes de la Etapa D):
   ```bash
   VIRTUAL_ENV=~/FS_FONDECYT/.venv uv pip install surfplot brainspace nbstripout
   ```
5. **FreeSurfer en la terminal de PyCharm** (para A5/B3):
   ```bash
   export FREESURFER_HOME=/Applications/freesurfer/8.2.0
   source $FREESURFER_HOME/SetUpFreeSurfer.sh
   export SUBJECTS_DIR=~/FS_FONDECYT/subjects
   ```
6. **Higiene antes de commitear notebooks:** `nbstripout notebooks/*.ipynb` (el repo es **público**).

---

*Plan redactado por Claude Code (Opus 5) en el M5, 2026-07-27. Ningún modelo ejecutado.
Traduce `06_ROIs_apriori_DCNN.md` (lista congelada) y `06_ESPECIFICACION_TABLA_MAESTRA.md`.*
