# MAPA DE RESULTADOS — FASE 5
### Dónde está todo, cómo se produjo, y qué creo que significa
**FONDECYT 11200469 · MRI estructural en MPPP/PPPD · actualizado 2026-07-28**

Este archivo es el **índice maestro**. Si vuelves a esto en tres meses y no recuerdas nada,
empieza aquí.

---

# 1. DÓNDE ESTÁ TODO

Todo vive en `~/Repos/F11200469_structural/011_mri_estructural_fase5/`
(repo público: `github.com/HayoBK/F11200469_structural`).
**Los datos NO están aquí** — se leen de `~/FS_FONDECYT/tablas/` por ruta absoluta.

## 1.1 Lo primero que hay que abrir

| Qué | Dónde | Nota |
|---|---|---|
| 🔴 **El documento exploratorio completo** | `docs/REPORTE_EXPLORATORIO.html` | **Ábrelo en el navegador.** Todo el análisis, etapa por etapa: método, N, tablas completas y todas las figuras candidatas. Es el archivo que pediste para elegir figuras. **No está en GitHub** (2,4 MB, se regenera con un comando). |
| El plan de análisis | `docs/PLAN_ANALISIS_FASE5.md` | Qué se iba a hacer y por qué, con las 7 decisiones que tomaste. |
| Este mapa | `docs/MAPA_DE_RESULTADOS.md` | Índice + disquisiciones. |

## 1.2 Tablas de resultados — `results/`

Una fila por prueba estadística. Todas versionadas en GitHub (son agregados, sin datos por sujeto).

| Archivo | Contenido |
|---|---|
| `SINTESIS_supervivientes_resultados.csv` | **Los 8 resultados que sobreviven al FDR.** Empieza por aquí. |
| `etapa0_tabla1_resultados_descriptivos.csv` | Tabla 1 del paper: demografía y clínica por grupo. |
| `etapa0_confundentes_resultados.csv` | Test de cada covariable candidata entre grupos. |
| `etapa0_supuestos_resultados.csv` | Normalidad, homocedasticidad y outliers de las 58 variables de A1. |
| `etapaA1_resultados_ancova.csv` | 58 pruebas × 2 modelos, ROIs prioridad ALTA, 3 grupos. |
| `etapaA2_resultados_ancova.csv` | 78 pruebas × 2 modelos, ROIs prioridad MEDIA, 3 grupos. |
| `etapaA3_resultados_ancova.csv` | 46 pruebas × 2 modelos, subcampos hipocampo / núcleos tálamo y amígdala. |
| `etapaAD_resultados_dirigido.csv` | 136 pruebas × 2 modelos, **contraste dirigido MPPP vs Vestibular**. |
| `etapaC1_resultados_indice_red.csv` | 16 índices compuestos de red, 3 grupos. |
| `etapaC1_resultados_dirigido.csv` | Los mismos índices, contraste dirigido. |
| `etapaB1_resultados_correlaciones.csv` | Índices de red × 8 outcomes conductuales (N=46). |
| `etapaB2_resultados_correlaciones.csv` | ROIs prioridad alta × outcomes primarios (N=46). |
| `etapaB3_resultados_correlaciones.csv` | **Dentro de pacientes** (n≈31) × conducta + Niigata + DHI. |
| `SINTESIS_disociacion_resultados.csv` | **La doble disociación LGI/grosor**, en una tabla. |
| `etapaC3_resultados_asimetria.csv` | 68 índices de asimetría L−R × 2 diseños. |
| `etapaC2_resultados_covarianza.csv` | Covarianza estructural de la red, MPPP vs Vestibular. |
| `etapaC2_matrices_resultados_por_grupo.csv` | Covarianza media de la red por grupo y medida. |
| `etapa*_enriquecimiento_resultados.csv` | Test de enriquecimiento por familia de cada etapa. |

**Columnas clave de cualquier tabla de resultados:**
`n` (N efectivo real, listwise) · `eta2p` + `eta2p_ic_low/high` (efecto del omnibus con IC) ·
`p_param` (paramétrico) · `p_hc3` (robusto) · **`p_perm`** (permutación — *el que se usa*) ·
`p_kw` (Kruskal-Wallis crudo, robustez) · **`p_fdr`** (corregido dentro de su familia) ·
`sobrevive_fdr` · `MPPP_vs_*_d` + `_d_ic_low/high` (d de Cohen ajustada con IC BCa) ·
`formula` (el modelo exacto que se ajustó) · `familia_fdr` (con qué se corrigió).

## 1.3 Figuras — `figs/`

**46+ figuras, cada una en PNG (200 dpi) y PDF vectorial** (el PDF es el que va al paper).

| Carpeta | Contiene |
|---|---|
| `figs/etapa0/` | Covariables por grupo, sexo, cobertura de datos conductuales. |
| `figs/etapaA1/` | Forest por medida × contraste, heatmap ROI × medida, volcán, violines, comparación modelos A/B. |
| `figs/etapaA2/`, `figs/etapaA3/` | Lo mismo para prioridad media y subestructuras. |
| `figs/etapaAD/` | Contraste dirigido + **comparación de diseños** (r = 0,99). |
| `figs/etapaC1/` | Índices de red: violines y forest comparando ambos diseños. |
| `figs/sintesis/` | 🔴 **`forest_LGI_todas_las_rois`** — la figura candidata a principal del paper. |

## 1.4 Código — `src/` y `notebooks/`

| Archivo | Qué hace |
|---|---|
| `src/config.py` | Rutas, constantes, carga con chequeos de integridad que fallan ruidosamente si el merge se rompe. |
| `src/rois.py` | La lista congelada de ROIs → columnas reales. Agregación ponderada por área. |
| `src/modelos.py` | **El motor**: ANCOVA, permutación Freedman-Lane, η²ₚ y d con IC BCa. |
| `src/test_modelos.py` | 7 tests sobre datos sintéticos. **Ejecútalo si tocas el motor.** |
| `src/multiplicidad.py` | FDR-BH por familia + test de enriquecimiento por permutación. |
| `src/pipeline.py` | El bucle común de todas las etapas + índice compuesto de red. |
| `src/figuras.py` | Sistema visual único (paleta validada para daltonismo). |
| `src/reporte.py` | Acumulador del documento HTML. |
| `notebooks/etapa*.py`, `sintesis.py` | Un script por etapa. Llevan marcadores `# %%`: **en PyCharm se ejecutan por celdas** (Scientific Mode). |

## 1.5 Cómo regenerar todo desde cero

```bash
cd ~/Repos/F11200469_structural/011_mri_estructural_fase5
V=~/FS_FONDECYT/.venv/bin/python
$V src/test_modelos.py                                    # valida el motor primero
$V notebooks/etapa0_descriptivos.py                       # crea el documento
$V notebooks/etapaA1_roi_alta.py
$V notebooks/etapaA2_roi_media.py
$V notebooks/etapaA3_subestructuras.py
$V notebooks/etapaC1_indice_red.py
$V notebooks/etapaAD_dirigido_mppp_vs_vestibular.py
$V notebooks/sintesis.py                                  # cierra el documento
open docs/REPORTE_EXPLORATORIO.html
```
Corre entero en ~4 minutos. Es determinista: la semilla es `11200469`, así que dos
ejecuciones dan exactamente los mismos números.

---

# 2. EL MÉTODO — cómo se llegó a cada número

## 2.1 El modelo de cada prueba
```
medida ~ C(Grupo) + Edad + C(Genero) + N_Educacional  [+ eTIV solo en volumen y área]
```
- **Omnibus** = F de tipo II sobre el efecto de grupo.
- **El p que se reporta es el de permutación** (Freedman-Lane, 10.000 remuestreos): permuta los
  residuos del modelo *sin* grupo y los re-suma a sus ajustados, destruyendo el efecto de grupo
  pero conservando la estructura de covariables. No depende de normalidad — decisivo con n=10.
- **η²ₚ** con IC 95% **bootstrap BCa estratificado por grupo** (preserva 17/19/10 y evita
  remuestras degeneradas).
- **d de Cohen ajustada** = diferencia de medias marginales / DE residual, con su IC BCa.
- Se guardan además `p_param`, `p_hc3` y `p_kw` para que se vea que la conclusión no depende
  del método elegido.

## 2.2 Multiplicidad
**FDR de Benjamini-Hochberg dentro de cada familia de medida**, y separado por etapa
(A1 primario, A2 secundario). Nunca sobre las 2.530 columnas: los tres atlas son tres
parcelaciones del mismo manto y están fuertemente correlacionados.

Además, un **test de enriquecimiento por familia**: permuta la etiqueta de grupo una vez por
remuestreo y la aplica a *todas* las variables de la familia a la vez, preservando su
correlación. Responde una pregunta distinta del FDR — no "qué ROI declaro" sino "hay más señal
aquí de la esperable por azar".

## 2.3 Los dos modelos en paralelo (tu decisión D5)
Todo se corre dos veces: **modelo A** sin ansiedad/depresión (N=46 o 36) y **modelo B**
añadiendo STAI-Rasgo y BDI (N≈34 o 26). Ambos completos, cada uno con su propio FDR,
reportados en paralelo. Re-testear solo los supervivientes de A habría condicionado el segundo
análisis al resultado del primero.

## 2.4 Validación del motor antes de usarlo
`src/test_modelos.py`, 7 tests sobre datos sintéticos con efectos conocidos. El más importante:
con grupos que difieren fuertemente en edad y un outcome que depende *solo* de la edad, sin
ajustar el efecto espurio aparece el **100%** de las veces y ajustando la tasa vuelve al **5,0%**
nominal.

---

# 3. QUÉ SE ENCONTRÓ

## 3.1 El resultado, en dos líneas
> **1.** La **girificación (LGI)** de la red DCNN es menor en MPPP que en pacientes
> vestibulares sin cronificación (d ≈ −0,9), y no se explica por ansiedad ni depresión.
> Pero **no se asocia con nada**: ni con conducta ni con severidad.
>
> **2.** El **grosor cortical** hace exactamente lo contrario: **no diferencia grupos en
> absoluto**, pero dentro de pacientes correlaciona fuertemente con la severidad sintomática
> (Niigata rho = −0,70; DHI rho = −0,69 en supramarginal derecho).
>
> **Es una doble disociación: el LGI se comporta como rasgo y el grosor como estado.**

## 3.2 Lo que sobrevive al FDR (8 de 350 pruebas)

| Etapa | ROI | Hemi | Medida | d | IC 95% | p FDR |
|---|---|---|---|---|---|---|
| C1d | **Índice de red DCNN** (PC1) | bilat | LGI | −0,94 | −1,73 a −0,03 | 0,040 |
| AD | Ínsula posterior | rh | LGI | −1,04 | −1,73 a −0,16 | 0,043 |
| AD | Temporal superior | rh | LGI | −1,04 | −1,74 a −0,23 | 0,043 |
| AD | Ínsula posterior | lh | LGI | −0,89 | −1,63 a −0,02 | 0,047 |
| AD | Giro supramarginal | lh | LGI | −0,88 | −1,55 a −0,07 | 0,047 |
| AD | Temporal superior | lh | LGI | −0,94 | −1,70 a −0,13 | 0,047 |
| AD | C. parahipocampal | lh | LGI | −0,85 | −1,66 a +0,13 | 0,047 |
| C1d | **Índice de red DCNN** (media z) | bilat | LGI | −0,91 | −1,64 a −0,01 | 0,047 |

**Todas son LGI. Todas en el contraste dirigido. Todas en ROIs de prioridad alta.**

## 3.3 La consistencia direccional — lo que ninguna corrección captura

| Análisis | ROIs | d mediana | Negativas |
|---|---|---|---|
| 3 grupos · A1 (alta) | 14 | −0,64 | **14/14** |
| 3 grupos · A2 (media) | 18 | −0,44 | 17/18 |
| 3 grupos · A1+A2 | 32 | −0,46 | **31/32** |
| Dirigido n=36 | 32 | −0,45 | **31/32** |

31 de 32 ROIs apuntan en la misma dirección, en dos diseños distintos. Eso no es un p.

## 3.4 La ansiedad NO explica el efecto

| Etapa | N sin → con | \|d\| medio sin | \|d\| medio con | Cambio |
|---|---|---|---|---|
| A1 | 45 → 31 | 0,637 | 0,721 | **+0,08** |
| A2 | 45 → 31 | 0,474 | 0,589 | **+0,12** |
| AD | 35 → 26 | 0,550 | 0,622 | **+0,07** |

Al controlar STAI-R y BDI el efecto **no baja: sube**. Lo que cae es el N, y con él la
precisión. Por eso ninguna prueba sobrevive al FDR en el modelo B — es pérdida de potencia,
no desaparición del efecto. Justamente por esto el plan exigía comparar efectos y no solo p.

## 3.5 Etapa B · la estructura sí se asocia con la clínica — pero es el GROSOR

**Dentro de pacientes (MPPP + Vestibular, n≈31), sobreviven al FDR:**

| ROI | Hemi | Medida | Outcome | rho | IC 95% | p FDR |
|---|---|---|---|---|---|---|
| Giro supramarginal | rh | grosor | **Niigata** | **−0,70** | −0,86 a −0,51 | **0,0005** |
| Giro supramarginal | rh | grosor | **DHI** | **−0,69** | −0,85 a −0,38 | 0,0012 |
| Temporal superior | rh | grosor | DHI | −0,65 | −0,81 a −0,40 | 0,0017 |
| Ínsula posterior | lh | grosor | Entropy-Ratio | +0,60 | +0,31 a +0,77 | 0,0034 |
| Temporal superior | rh | grosor | Niigata | −0,57 | −0,79 a −0,29 | 0,011 |
| **Índice de red** | bilat | grosor | DHI | −0,56 | −0,80 a −0,21 | 0,011 |
| Precúneo | rh | grosor | DHI | −0,51 | −0,76 a −0,16 | 0,024 |
| **Índice de red** | bilat | grosor | Niigata | −0,50 | −0,75 a −0,13 | 0,033 |
| Temporal superior | lh | grosor | Entropy-Ratio | +0,48 | +0,13 a +0,70 | 0,035 |
| Giro supramarginal | lh | grosor | DHI | −0,46 | −0,74 a −0,06 | 0,048 |

Y en la muestra completa (B2), una: **ínsula posterior izquierda, grosor ↔ Entropy-Ratio**
(rho = 0,45, p_FDR = 0,040).

**Lo que sostiene esta lectura:**
- La correlación grosor↔Niigata **se replica dentro de cada grupo por separado**:
  MPPP rho = −0,70 (n=14, p=0,005) · Vestibular rho = −0,69 (n=17, p=0,002).
  No es un artefacto de mezclar grupos.
- De las **19** correlaciones con p<0,05, **ninguna** tiene signo incoherente con sus
  intra-grupo → **no hay paradoja de Simpson operando**.
- Dirección coherente: menos grosor ↔ más síntomas.

**⚠️ Cautela obligatoria:** `Niigata` y `DHI` correlacionan entre sí **rho = 0,72**. Miden el
mismo constructo y **cuentan como un solo hallazgo**, no como dos. En cambio la severidad
clínica NO correlaciona con navegación (CSE↔Niigata rho = 0,26, p = 0,17): el eje clínico y el
conductual sí son dimensiones independientes.

## 3.6 La doble disociación (lo más publicable)

| | LGI | Grosor cortical |
|---|---|---|
| ¿Diferencia MPPP de Vestibular? | **Sí** (d ≈ −0,9, 8 resultados con FDR) | **No** (0 de 136 pruebas) |
| ¿Correlaciona con conducta? | No (\|rho\| ≤ 0,22) | Sí (Entropy-Ratio, rho ≈ 0,45–0,60) |
| ¿Correlaciona con severidad? | No | **Sí, fuerte** (rho ≈ −0,50 a −0,70) |
| Lectura | **rasgo predisponente** | **marcador de estado** |

La girificación se establece en el desarrollo y es estable en la adultez: no puede cambiar en
los meses que dura un MPPP, así que un efecto ahí apunta a predisposición. El grosor sí es
plástico y responde a procesos adquiridos, así que su asociación con la severidad actual se lee
como estado. **Dos medidas de la misma corteza contando dos historias distintas.**

## 3.7 Etapas C2 y C3 · dos hipótesis descartadas limpiamente

**C3 · Asimetría hemisférica L−R** — índice AI = (L−R)/(L+R) en 68 combinaciones
ROI × medida, en los dos diseños. **Cero supervivientes en ambos** (0/68 y 0/68), ninguna
familia enriquecida (p mínimo de enriquecimiento: 0,21 en LGI). El AI es adimensional, así que
no se ajusta por eTIV.

> **La lateralización no distingue grupos.** Esto descarta la lectura lateralizada que sugería
> la literatura VBM en PPPD. Que varios de nuestros hallazgos aparezcan en un solo hemisferio
> (parahipocampal izq, supramarginal der) refleja dónde está el efecto, no una diferencia en
> el *grado de asimetría* entre grupos. Es un resultado nulo, pero acota lo que hay que explicar.

**C2 · Covarianza estructural de la red** — matriz de correlación entre las 14 ROIs de
prioridad alta dentro de cada grupo (91 aristas), residualizada dentro de grupo, contrastada
por permutación.

| Medida | r medio MPPP | r medio Vestibular | p | p FDR |
|---|---|---|---|---|
| LGI | 0,438 | 0,430 | 0,95 | 0,95 |
| Grosor | 0,231 | 0,289 | 0,61 | 0,82 |
| Volumen | 0,126 | 0,269 | 0,22 | 0,43 |
| **Área** | **−0,016** | **0,216** | **0,018** | **0,070** |

> El área es el único contraste con p nominal < 0,05: la covarianza entre las áreas de la red
> es **prácticamente nula en MPPP** y moderada en el grupo vestibular. **No sobrevive al FDR de
> las 4 medidas** y no había hipótesis previa sobre covarianza de área. Con n=17 vs 19, una
> matriz de 91 aristas se estima con mucho ruido. **Es una observación para replicar, no un
> resultado**, y así hay que reportarla si se menciona.

⚠️ El grupo sano (n=10) se muestra pero **no se contrasta formalmente**: una matriz de
correlación de 14 variables con n=10 es demasiado inestable para sostener una comparación.

## 3.8 Lo que NO se encontró
- **Grosor cortical, entre grupos:** nada. Ni una prueba, ninguna familia enriquecida, sin
  consistencia direccional (12/18 es ruido). *Ojo: sí aparece en la etapa B — ver §3.5.*
- **LGI, correlacionado con conducta o severidad:** nada. El |rho| máximo del índice de
  girificación con cualquier outcome es 0,22, y ninguna de las 32 correlaciones sobrevive.
- **Volumen y área:** nada que sobreviva. El área del istmo del cíngulo derecho tenía el p más
  bajo de A1 (0,0097, d=+1,35) pero su familia no está enriquecida (p=0,45): lo trataría como ruido.
- **Subestructuras (A3):** ninguna familia enriquecida. Direccionalmente, amígdala 18/20 y
  hipocampo posterior 15/18 negativas, y el `presubiculum body` izquierdo se quedó en
  p_FDR = 0,056. Sugerente, no concluyente.
- **Diseño de 3 grupos:** **cero** supervivientes en 182 pruebas.

---

# 4. PROBLEMAS QUE PERCIBO

Ordenados por gravedad. Estos son los que un revisor va a encontrar.

### 4.1 🔴 No sabemos si es MPPP↓ o Vestibular↑
El contraste que sobrevive es contra Vestibular, no contra Sano. En z promedio:
**MPPP −0,28 · Sano +0,04 · Vestibular +0,24**. Los sanos quedan *en medio*, así que con n=10
no se puede decidir si la girificación está reducida en MPPP o aumentada en el vestibular
compensado. **Es la limitación más seria** y cambia por completo la interpretación biológica.
Hay que declararla sin rodeos en Discussion, no esconderla.

### 4.2 🔴 El diseño dirigido puede leerse como búsqueda selectiva
Nada sobrevive con 3 grupos; 6 cosas sobreviven con 2. Un revisor escéptico dirá que se
cambió el análisis hasta que salió algo. **La defensa es sólida pero hay que darla explícitamente:**
(a) el contraste dirigido se justificó *teóricamente* antes de verlo (ambos grupos comparten
patología vestibular; la pregunta es la cronificación); (b) **r = 0,99** entre las d de ambos
diseños — el efecto estimado es *el mismo*, solo se mide con más precisión; (c) la lista de
ROIs estaba congelada desde antes de cualquier resultado.

### 4.3 🟡 Los IC rozan el cero
Varias ROIs supervivientes tienen el extremo superior del IC en −0,02 o −0,01. Resisten la
corrección, pero su magnitud está mal determinada. Y hay un caso incoherente en apariencia:
**la corteza parahipocampal izquierda sobrevive al FDR (p=0,047) pero su IC BCa cruza el cero**
(−1,66 a +0,13). No es un error: el p viene de permutación y el IC de bootstrap, y con n=35 los
dos métodos no tienen por qué coincidir en el borde. Conviene reportar ambos y no esconder la
discrepancia.

### 4.4 🟡 Falta la convergencia con el vertex-wise
Todo esto es análisis por ROI. Mientras el whole-brain no confirme el patrón, la evidencia
descansa en una sola aproximación. El `-qcache` está completo para grosor, área y volumen —
pero **el LGI, justo la medida que importa, no lo tiene** y necesita un `mris_preproc` propio
antes de `mri_glmfit`.

### 4.5 🟡 El LGI hubo que recalcularlo
Las seis tablas originales contenían la **desviación estándar intrarregional**, no el LGI medio
(bug de `05_extraer_tablas.sh:55`, documentado en la especificación §5.1). Se usa `lgi_*` y nunca
`lgisd_*`. Debe ir en Methods: es exactamente el tipo de detalle que un revisor pregunta.

### 4.6 🟢 Menores
- `Niigata` tiene 4 sanos → solo analizable dimensionalmente dentro de pacientes (pendiente, Etapa B).
- `HeadAngMag_NI` es inutilizable (N=1); usar la versión RV.
- `ScanPath_time_RV` tiene N=27 — el outcome más frágil de la Etapa B.
- La lateralidad se imputó a diestro; los 3 no-diestros son todos del grupo vestibular.

---

# 5. DISQUISICIONES — qué creo que está pasando

**La doble disociación es el hallazgo, y es mejor que cualquiera de sus mitades.** Cuando solo
teníamos la etapa A, la lectura era "el LGI diferencia grupos". Con la etapa B se vuelve mucho
más específica: el LGI diferencia grupos **y no se mueve con la severidad**, mientras el grosor
**no diferencia grupos pero sigue a la severidad de cerca**. Dos medidas de la misma corteza,
en las mismas ROIs, con comportamientos opuestos y complementarios.

Eso encaja con lo que se sabe de cada medida. La girificación se establece en el desarrollo
temprano y es muy estable en la adultez: no es plausible que se modifique en los meses que dura
un cuadro de MPPP, así que un efecto ahí apunta a **rasgo predisponente** — una configuración
cortical previa que hace a ciertos pacientes más vulnerables a cronificar tras un evento
vestibular agudo. El grosor sí es plástico y responde a procesos adquiridos, de modo que su
correlación con la severidad actual se lee como **marcador de estado**. Es coherente con
Nigro et al. y con la clínica: no todo el que sufre una neuritis desarrolla MPPP, y entre los
que lo desarrollan, no todos están igual de graves.

**El modelo que sugiere:** una predisposición estructural (girificación) determina *quién*
cronifica; una vez cronificado, un proceso adquirido (adelgazamiento cortical en el nodo
TPJ/vestibular) escala con *cuán grave* está. Son dos preguntas distintas y este dataset
responde una parte de cada una.

**Lo que más me gusta metodológicamente** es que la disociación es difícil de producir por
azar. Si todo fuera ruido, no esperaríamos que una medida cargue toda la señal entre grupos y
la otra toda la señal con severidad, y que además ambas apunten a las mismas ROIs
(supramarginal, temporal superior, ínsula posterior). Que el patrón sea *ortogonal* y no
redundante es lo que lo hace convincente.

**Los resultados nulos de C2 y C3 refuerzan la historia en vez de debilitarla.** Si el
fenómeno fuera un artefacto global —peor calidad de imagen en un grupo, un sesgo de
procesamiento, atrofia difusa— esperaríamos verlo también en la asimetría y en la organización
de la red. No aparece en ninguna de las dos. El efecto está acotado a una medida (girificación)
y a un conjunto concreto de regiones, que es exactamente el perfil de un hallazgo específico y
no el de un sesgo. Un resultado nulo bien hecho vale como control.

**La topografía es coherente y no dispersa.** Las ROIs que sobreviven —ínsula posterior,
temporal superior, supramarginal, parahipocampal— son el núcleo vestibular cortical y el nodo
TPJ, no regiones sueltas repartidas por el manto. Y el efecto es mayor en prioridad alta que en
media, que es lo esperable si el fenómeno pertenece a la red DCNN y no es global.

**Lo que más me inquieta** es §4.1. Si el grupo vestibular resultara tener girificación
*aumentada* —por ejemplo, como marcador de compensación exitosa— la historia se invierte por
completo: pasaría de "déficit en MPPP" a "reserva estructural en quien compensa". Ambas son
publicables e interesantes, pero son artículos distintos. Con 10 sanos no se puede zanjar, y
sería honesto plantear ambas lecturas en la Discussion en vez de elegir la más favorable.

**Sobre el índice de red (C1):** que sobreviva con los dos métodos (media de z y PC1) y con la
misma magnitud que las ROIs individuales me da confianza en que no es un artefacto de la
agregación. Y es probablemente **la mejor figura para el paper**: una sola prueba, un efecto
grande, y la hipótesis teórica planteada tal como se formuló.

**Mi apuesta sobre qué resiste una revisión:** los dos ejes de la disociación (§3.6). El LGI en
el contraste dirigido, con la limitación de §4.1 declarada de entrada; y el grosor↔severidad
dentro de pacientes, que es el resultado más robusto de todo el análisis (p_FDR = 0,0005 y
replicado dentro de cada grupo). Volumen, área y subestructuras son ruido y no los defendería.

**Un aviso sobre la correlación grosor↔severidad:** con rho = −0,70 y n = 31 el efecto es
grande, pero el n sigue siendo pequeño y estos coeficientes están sesgados al alza cuando se
seleccionan por ser los mayores de un barrido. La replicación intra-grupo mitiga bastante esa
objeción, pero no la elimina. En el manuscrito reportaría el IC, no el rho puntual.

---

# 6. QUÉ FALTA (Fase 5 no está cerrada)

| Pendiente | Estado |
|---|---|
| ~~**Etapa B** — estructura ↔ conducta~~ | ✅ **corrida** (B1, B2, B3) |
| ~~**C4** — dimensional dentro de pacientes~~ | ✅ **corrida** (integrada como B3) |
| ~~**C2** — covarianza estructural entre ROIs~~ | ✅ **corrida** — nulo (ver §3.7) |
| ~~**C3** — asimetría hemisférica L−R~~ | ✅ **corrida** — nulo (ver §3.7) |
| **A4** — whole-brain por tabla, masa-univariante | no iniciada |
| **A5/B3-vertex** — vertex-wise `mri_glmfit` | ⚠️ el LGI necesita `mris_preproc` previo (~1–2 h) |
| **Etapa D** — figuras anatómicas de superficie | falta instalar `surfplot` |

**Prioridad ahora: el vertex-wise** (decisión del PI: dejarlo para la etapa siguiente). Con la
disociación en la mano, la pregunta concreta es si un mapa whole-brain —que no sabe nada de la
lista congelada de ROIs— ilumina las mismas regiones. Si lo hace, el argumento deja de depender
de una sola aproximación metodológica.

---

*Generado por Claude Code (Opus 5) en el M5. Contiene solo resultados agregados: ni un dato
por sujeto, ninguna variable identificadora.*
