# Girificación cortical reducida como marcador de rasgo y adelgazamiento cortical como marcador de estado en el Mareo Postural Perceptual Persistente

### Un estudio de morfometría estructural con FreeSurfer
**FONDECYT de Iniciación 11200469 · Fase 011 · Borrador metodológico, 2026-07-28**

> **Qué es este documento.** Un borrador de artículo destinado a **guiar la redacción del
> manuscrito**, no a sustituirla. Es deliberadamente **desproporcionado en Métodos**: explica
> cada decisión analítica y por qué se tomó, incluso cuando el detalle excede lo que una revista
> aceptaría, para que al escribir el paper real no haya que reconstruir nada. La sección teórica
> es mínima a propósito: se alimenta solo de los datos de este análisis y deberá completarse con
> la revisión de literatura (`02_Revision_Literatura_Areas_Cerebrales_PPPD.md`).
>
> Todos los números provienen de `results/`. Ninguno se ha redondeado a conveniencia.

---

# RESUMEN

**Antecedentes.** El Mareo Postural Perceptual Persistente (MPPP/PPPD) es un trastorno
vestibular funcional crónico que aparece tras un evento vestibular agudo en solo una fracción de
quienes lo sufren. No se sabe qué distingue a quien cronifica de quien se recupera, ni si esa
diferencia es previa al evento o consecuencia de él.

**Métodos.** Morfometría de superficie con FreeSurfer en 46 sujetos (17 MPPP, 19 pacientes
vestibulares sin cronificación, 10 voluntarios sanos). Se analizaron cuatro medidas —índice de
girificación local (LGI), grosor cortical, área y volumen— sobre 19 regiones de interés
congeladas *a priori*, más un barrido whole-brain por ROI y vertex-wise. El diseño principal fue
un contraste dirigido MPPP vs vestibular. Se evaluó además la asociación con desempeño en
navegación espacial alocéntrica (CSE, Entropy-Ratio) y con severidad sintomática (Niigata, DHI).

**Resultados.** Se observó una **doble disociación**. El LGI diferenció grupos —red DCNN,
d = −0,91 a −0,94; seis regiones individuales con d entre −0,85 y −1,04— pero **no se asoció con
ninguna medida conductual ni clínica** (|ρ| máximo 0,42; **0 de 260** correlaciones
sobrevivieron a la corrección). El grosor cortical hizo exactamente lo contrario: **no mostró ninguna diferencia
entre grupos** en 136 pruebas dirigidas ni en 278 whole-brain, pero correlacionó intensamente
con la severidad dentro de pacientes (**32 de 260** correlaciones sobrevivieron; ρ hasta −0,70). El
análisis vertex-wise replicó ambos patrones de forma independiente. El efecto del LGI se
reprodujo en las tres parcelaciones corticales (r = 0,95–0,997) y ningún hallazgo dependió de
un solo sujeto.

**Conclusión.** La girificación cortical, que se establece en el desarrollo temprano y es
estable en la adultez, se comporta como **marcador de rasgo** asociado a la cronificación; el
grosor cortical, plástico, se comporta como **marcador de estado** asociado a la gravedad
actual. La limitación central es que el contraste informativo se da frente a pacientes
vestibulares y no frente a sanos, lo que impide determinar la dirección causal del efecto.

---

# 1. INTRODUCCIÓN

*(Sección deliberadamente breve: se completará con la revisión de literatura del proyecto.)*

El MPPP se caracteriza por mareo no vertiginoso, inestabilidad perceptual y sensibilidad a
estímulos visuales complejos, persistiendo tres meses o más tras un evento vestibular
desencadenante. Su fisiopatología se ha descrito como una **reponderación maladaptativa** entre
las señales visual, vestibular y propioceptiva, con dependencia visual aumentada y control
postural rígido.

Dos observaciones motivan este trabajo:

1. **No todo el que sufre un evento vestibular agudo cronifica.** Esto sugiere factores de
   vulnerabilidad previos, pero el grupo de comparación adecuado para investigarlos no es el
   sujeto sano: es **el paciente vestibular que no cronificó**.
2. **La girificación cortical es un rasgo del desarrollo.** El LGI se establece
   perinatalmente y es notablemente estable en la adultez, de modo que una diferencia en LGI
   difícilmente puede ser consecuencia de un cuadro de meses de evolución. El grosor cortical,
   en cambio, sí responde a procesos adquiridos.

Se preinscribió una lista de 19 regiones de interés de la red de navegación
visuoespacial-vestibular (denominada aquí red DCNN), congelada **antes de examinar ningún
resultado**, y se preespecificó el plan estadístico completo.

---

# 2. MÉTODOS

Esta sección es intencionadamente exhaustiva.

## 2.1 Participantes y diseño

| Grupo | n | Definición |
|---|---|---|
| **MPPP** | 17 | Criterios Bárány de PPPD |
| **Vestibular** | 19 | Patología vestibular periférica documentada, **sin** cronificación perceptual |
| **Voluntario Sano** | 10 | Sin antecedente vestibular |
| **Total** | **46** | |

De una cohorte inicial de 53 sujetos, se excluyeron seis por ausencia o corrupción de imagen
cruda (P01, P03, P09, P22, P33, P48) y **uno por control de calidad** (P15, sub-extensión pial
global bilateral detectada en inspección visual). Un sujeto adicional (P14) careció de LGI
utilizable, de modo que **N = 46 en todas las medidas salvo LGI, donde N = 45**. Este
desfase se declara en cada análisis en lugar de imputarse.

### El contraste dirigido: justificación previa al resultado

El diseño de tres grupos está limitado por el brazo sano (n = 10). Se preespecificó por ello un
**contraste dirigido MPPP vs Vestibular (n = 36, 17 vs 19)**, con dos justificaciones
independientes:

- **Teórica.** Ambos grupos comparten historia de patología vestibular. Lo que los separa es la
  cronificación perceptual, que es *la* pregunta del estudio. Comparar MPPP con sanos confunde
  dos efectos: tener patología vestibular y haber cronificado.
- **Estadística.** Elimina la dependencia del brazo de n = 10 y produce dos grupos balanceados.

**Este contraste no es una búsqueda posterior de significación.** Se verificó empíricamente que
estima el *mismo* efecto que el diseño de tres grupos con mayor precisión: la correlación entre
los tamaños de efecto de ambos diseños, sobre las 136 pruebas, es **r = 0,99**. Es decir, el
diseño dirigido no cambia qué efecto se mide, solo con cuánto error se mide. Se reportan ambos.

## 2.2 Adquisición y procesamiento de imagen

Reconstrucción cortical completa con **FreeSurfer 8.2.0** (`recon-all -all -T2pial -qcache`)
sobre 47 sujetos. El flag `-T2pial` refina la superficie pial con la imagen T2, reduciendo la
sobre-extensión hacia duramadre. `-qcache` deja los datos remuestreados sobre `fsaverage` y
suavizados a varios anchos, lo que hizo posible el análisis vertex-wise sin preprocesamiento
adicional (salvo para LGI, ver §2.7).

**Control de calidad.** Inspección visual de las superficies. La única exclusión fue P15.

**Control de calidad cuantitativo.** Se usó `SurfaceHoles` —el número de agujeros topológicos
reparados durante la reconstrucción, relacionado con el número de Euler— como proxy objetivo de
calidad. **No difiere entre grupos** (mediana 29 / 26 / 25; Kruskal-Wallis p = 0,896), lo que
descarta que cualquier hallazgo posterior sea artefacto de calidad diferencial de reconstrucción.

### Medidas morfométricas

| Medida | Qué es | Ajuste por eTIV |
|---|---|---|
| **LGI** (`pial_lgi`) | Índice de girificación local: razón entre la superficie cortical contenida en los surcos y la superficie expuesta, calculada sobre un parche esférico. Cuantifica plegamiento. | **No** — es un cociente adimensional |
| **Grosor** | Distancia entre superficie blanca y pial | **No** — no escala con el tamaño craneal |
| **Área** | Superficie de la interfaz blanca | **Sí** |
| **Volumen** | Volumen de sustancia gris cortical | **Sí** |

### ⚠️ Corrección aplicada a la extracción del LGI

Durante la construcción de la tabla se detectó que el script de extracción leía la columna
`ThickStd` de los archivos `?h.<atlas>.pial_lgi.stats` —la **desviación estándar** intrarregional
del LGI— en lugar de `ThickAvg`, el LGI medio. Los valores se recalcularon desde los `.stats`
originales. **El rango resultante (1,64–4,98; mediana 2,71) corresponde al rango fisiológico
esperado**, mientras que la columna errónea tenía mediana 0,19. Todos los análisis usan el LGI
medio recalculado. *Este detalle debe constar en Methods.*

## 2.3 Regiones de interés preinscritas

Diecinueve regiones de la red de navegación visuoespacial-vestibular, congeladas el 2026-07-27
antes de examinar resultado alguno, estratificadas en dos niveles:

- **Prioridad alta (8):** ínsula posterior, giro supramarginal, temporal superior, hipocampo,
  parahipocampal, entorrinal, precúneo, istmo del cíngulo.
- **Prioridad media (11):** parietal superior e inferior, occipital lateral, cuneus, temporal
  medio, cingulada anterior, prefrontal dorsolateral, precentral, postcentral, tálamo, amígdala,
  cerebelo.

Atlas primario **DKT** (`aparc.DKTatlas`); Destrieux (`aparc.a2009s`) para ínsula posterior y
retroesplenial, que DKT no separa. Hemisferios analizados por separado.

**Agregación de regiones compuestas.** Dos ROIs requieren combinar etiquetas (ínsula posterior =
2 etiquetas Destrieux; cingulada anterior = caudal + rostral). Se agregaron **ponderando por
área** en grosor y LGI —cantidades intensivas, donde un promedio simple daría igual peso a una
región grande y a una pequeña— y **sumando** en volumen y área, que son extensivas.

## 2.4 Modelo estadístico

Para cada combinación (ROI × hemisferio × medida):

```
medida ~ C(Grupo) + Edad + C(Sexo) + Nivel_Educacional  [+ eTIV si volumen o área]
```

### Selección empírica de covariables

Las covariables **no** se eligieron por costumbre. Cada candidata se contrastó entre grupos:

| Covariable | p (Kruskal-Wallis) | ¿Difiere? |
|---|---|---|
| Edad | 0,816 | No |
| Sexo | 0,131 (χ²) | No |
| Nivel educacional | 0,749 | No |
| eTIV | 0,535 | No |
| SurfaceHoles | 0,896 | No |
| Lateralidad | 0,854 | No |

**Ninguna difiere entre grupos.** Los grupos están bien emparejados, de modo que el ajuste
**aumenta precisión pero no corrige sesgo de confusión**. Se mantuvo el ajuste por ser lo
esperado en morfometría y porque reduce la varianza residual. La colinealidad es despreciable
(VIF máximo 1,72).

**Lateralidad excluida del modelo principal.** El índice de Edinburgh estaba disponible en 36 de
46 sujetos. Se imputó "diestro" a los faltantes (33 de 36 observados eran diestros, 92%,
coincidente con la prevalencia poblacional). Sin embargo, tras la imputación quedan 43 diestros
y **3 no-diestros, todos del grupo vestibular**: la variable queda casi anidada en el factor de
grupo, aporta muy poca información y consume un grado de libertad. Se excluyó del modelo
principal y se conservó para análisis de sensibilidad.

### Inferencia por permutación

**El valor p reportado es el de permutación**, no el paramétrico. Con n = 10 en un brazo, la
distribución F asintótica es poco fiable. Se usó el procedimiento de **Freedman-Lane**
(10.000 permutaciones): se ajusta el modelo *sin* el efecto de grupo, se permutan sus residuos,
se re-suman a los valores ajustados y se reajusta el modelo completo. Esto destruye el efecto de
grupo **conservando la estructura de las covariables**, que es lo que hace falta en un diseño no
balanceado.

Se conservan en las tablas los valores p paramétrico, robusto (HC3) y de Kruskal-Wallis, para
que se compruebe que las conclusiones no dependen del método.

> **Sobre Kruskal-Wallis.** Se consideró como test principal y se descartó: es no-paramétrico
> pero **no admite covariables**, y renunciar a ajustar por edad y sexo en morfometría es peor
> problema que la no-normalidad. Se reporta como columna de robustez.

### Tamaños de efecto e intervalos

Siempre se reporta η²ₚ para el ómnibus y **d de Cohen ajustada** (diferencia de medias
marginales / desviación estándar residual) para los contrastes, ambos con **intervalo de
confianza del 95% bootstrap BCa** (corregido por sesgo y acelerado, 5.000 remuestreos),
**estratificado por grupo** para preservar los tamaños 17/19/10 y evitar remuestras degeneradas.

### Verificación del motor estadístico

Antes de aplicarlo a los datos reales, el código se validó con **siete pruebas sobre datos
sintéticos con efectos conocidos**. La más relevante: en un escenario donde los grupos difieren
fuertemente en edad y el resultado depende *solo* de la edad, el análisis sin ajustar detecta un
efecto de grupo espurio el **100%** de las veces, y el modelo ajustado devuelve la tasa de
rechazo al **5,0%** nominal. También se verificó el control del error de tipo I bajo la hipótesis
nula, la recuperación de tamaños de efecto conocidos con cobertura correcta del IC, y la
orientación de los contrastes.

## 2.5 Corrección por comparaciones múltiples

**FDR de Benjamini-Hochberg dentro de cada familia**, definida como **una medida dentro de una
etapa**. Nunca se corrigió sobre el conjunto total de pruebas.

Justificación: los tres atlas corticales son tres parcelaciones del mismo manto y sus columnas
están fuertemente correlacionadas; una corrección global sería estadísticamente incorrecta
además de innecesariamente brutal. Las regiones de prioridad alta y media se corrigieron por
separado (confirmatorio primario y secundario).

### Test de enriquecimiento de familia

Además del FDR se aplicó una prueba distinta: **¿contiene una familia más señal de la esperable
por azar, aunque ninguna región individual sobreviva?** El nulo se construyó permutando la
etiqueta de grupo **una sola vez por remuestreo y aplicándola simultáneamente a todas las
variables de la familia**, preservando así la correlación entre regiones y hemisferios. Un test
binomial sobre los valores p asumiría independencia y sería anticonservador.

## 2.6 Análisis de asociación con conducta y clínica

**Correlación parcial de Spearman**: se rankean ambas variables, se residualizan sobre las
covariables y se correlacionan los residuos. Robusto a no-normalidad y a valores extremos.
Covariables: edad, sexo y **grupo** (más eTIV en volumen y área). IC bootstrap BCa.

Dos ejes deliberadamente separados:

- **Navegación espacial:** CSE (Cumulative Search Error) y Entropy-Ratio, obtenidos en una
  tarea de navegación alocéntrica tipo laberinto acuático virtual.
- **Severidad de enfermedad:** Niigata PPPD Questionnaire y Dizziness Handicap Inventory.

**La severidad solo se analizó dentro de pacientes** (MPPP + vestibular, n ≈ 31). En un
voluntario sano el puntaje de estas escalas es piso, no información: incluirlos habría creado
una correlación artificial por separación de grupos.

### ⚠️ Control explícito de la paradoja de Simpson

Con tres grupos que difieren tanto en estructura como en conducta, una correlación global puede
ser un artefacto de la separación entre grupos e incluso tener signo opuesto al de la relación
dentro de cada uno. Por ello **toda correlación se reporta junto a sus correlaciones
intra-grupo**, con una columna que indica si los signos concuerdan. En el análisis principal
**ninguna** de las 19 correlaciones significativas resultó incoherente; en el barrido ampliado,
5 de 83 lo fueron y están marcadas como no interpretables individualmente.

## 2.7 Análisis vertex-wise whole-brain

El análisis por ROI obliga a aceptar la parcelación del atlas como unidad biológica. El
vertex-wise no promedia: ajusta el mismo modelo en cada uno de los ~164.000 vértices de la
superficie de `fsaverage`, alineados entre sujetos.

- **Modelo:** `mri_glmfit --doss` (Different Offset, Same Slope) — un intercepto por grupo y
  pendiente común para las covariables, que es exactamente el modelo de §2.4. (`--dods`
  estimaría pendientes distintas por grupo, un modelo con interacción que no es el nuestro.)
- **Corrección:** por **clusters** mediante simulación de Monte Carlo (`mri_glmfit-sim --cache`),
  umbral de formación **p < 0,001**, umbral corregido de cluster **CWP < 0,05**, y corrección
  adicional por los dos hemisferios (`--2spaces`). El umbral estricto de formación evita los
  cúmulos inflados que motivaron la crítica clásica a los umbrales laxos.
- **Correlaciones:** para los outcomes continuos, el contraste prueba la **pendiente del
  regresor** (un 1 en su columna, ceros en el resto).

### ⚠️ El LGI requiere un tratamiento distinto de suavizado

Al aplicar el suavizado estándar de 10 mm al LGI, la simulación de Monte Carlo **falló**: el
FWHM residual estimado alcanzó **37 mm**, fuera del rango de las tablas precomputadas de
FreeSurfer (que llegan a 30). Se midió entonces el suavizado intrínseco de cada medida:

| Medida | FWHM residual |
|---|---|
| LGI **sin** suavizado adicional | **10,5** |
| Grosor con fwhm10 | 14,5 |
| Volumen con fwhm10 | 14,5 |
| Área con fwhm10 | 20,1 |
| LGI con fwhm10 | **37,0** ← inutilizable |

El LGI, al integrar un parche de superficie amplio por construcción, **ya llega suavizado**:
sin añadir nada tiene un FWHM residual comparable al de las otras medidas ya suavizadas.
Se analizó por tanto **sin suavizado adicional**. Este punto es relevante para cualquier
replicación: aplicar el suavizado estándar al LGI impide la corrección por clusters, y el fallo
es silencioso.

## 2.8 Análisis de robustez

- **Réplica entre atlas (R1).** Los resultados usan DKT. Si el efecto fuera un artefacto de la
  parcelación, no aparecería en Desikan-Killiany ni en Destrieux, que dividen el mismo manto con
  criterios distintos.
- **Leave-one-out (R8).** Con n = 31–36, un solo sujeto influyente puede sostener un efecto
  completo. Se reestimó cada hallazgo eliminando un sujeto por vez.
- **Modelo con y sin ansiedad/depresión.** Todo el análisis se corrió **dos veces**: una sin
  ajustar por STAI-Rasgo y BDI (N completo) y otra ajustando (N ≈ 34 o 26), ambas completas y
  con su propio FDR. Re-testear únicamente las regiones supervivientes habría condicionado el
  segundo análisis al resultado del primero.

## 2.9 Reproducibilidad

Todo el análisis es determinista (semilla 11200469) y se regenera con una secuencia de comandos
documentada. Código en `github.com/HayoBK/F11200469_structural`. Los datos, que contienen
información clínica, permanecen fuera del repositorio.

---

# 3. RESULTADOS

## 3.1 Características de la muestra (Tabla 1)

Mediana [IQR]; contraste de Kruskal-Wallis, o χ² para sexo.

| Variable | N | Sano | Vestibular | MPPP | p |
|---|---|---|---|---|---|
| Edad (años) | 46 | 43,0 [32,5–49,8] | 45,0 [33,0–57,0] | 48,0 [34,0–60,0] | 0,816 |
| Sexo (F/M) | 46 | 5/5 | 16/3 | 13/4 | 0,131 |
| Nivel educacional | 46 | 4,0 | 4,0 | 4,0 | 0,749 |
| eTIV (×10⁶ mm³) | 46 | 1,67 | 1,53 | 1,57 | 0,535 |
| SurfaceHoles | 46 | 29,0 | 26,0 | 25,0 | 0,896 |
| **DHI** | 35 | 1,0 [1,0–33,0] | 34,0 [21,0–54,0] | **46,0 [40,0–63,0]** | **0,015** |
| **Niigata** | 35 | 1,0 [0,0–8,8] | 17,0 [8,0–30,0] | **30,0 [27,2–43,2]** | **0,004** |
| **STAI-Rasgo** | 34 | 20,0 | 23,0 | **27,0** | **0,004** |
| BDI | 33 | 3,0 | 16,0 | 12,0 | 0,055 |
| **MoCA** | 45 | 26,0 | 27,0 | **24,0** | **0,019** |
| **CSE** | 46 | 28,0 [22,5–44,2] | 38,0 [25,6–63,1] | **60,9 [42,2–80,1]** | **0,016** |
| **Entropy-Ratio** | 46 | 0,5 | 0,5 | **0,6** | **0,006** |

**Los grupos son demográficamente indistinguibles y clínicamente muy distintos.** MPPP presenta
mayor severidad, mayor ansiedad rasgo, peor cribado cognitivo y peor desempeño en navegación
alocéntrica.

## 3.2 Diferencias entre grupos: solo el LGI

### El diseño de tres grupos no produce ningún resultado

De **182 pruebas** en las regiones preinscritas (prioridad alta, media y subestructuras),
**ninguna** sobrevivió al FDR de su familia. Tampoco lo hizo ninguna de las **1.134** pruebas
del barrido whole-brain por tabla.

### El contraste dirigido sí

| Región | Hemi | Medida | d | IC 95% | p FDR |
|---|---|---|---|---|---|
| **Índice de red DCNN** | bilat | LGI | **−0,94** | −1,73 a −0,03 | **0,040** |
| Ínsula posterior | der | LGI | −1,04 | −1,73 a −0,16 | 0,043 |
| Temporal superior | der | LGI | −1,04 | −1,74 a −0,23 | 0,043 |
| Temporal superior | izq | LGI | −0,94 | −1,70 a −0,13 | 0,047 |
| Ínsula posterior | izq | LGI | −0,89 | −1,63 a −0,02 | 0,047 |
| Giro supramarginal | izq | LGI | −0,88 | −1,55 a −0,07 | 0,047 |
| Parahipocampal | izq | LGI | −0,85 | −1,66 a +0,13 | 0,047 |

**Todos los resultados son LGI. Ninguna prueba de grosor, área o volumen sobrevivió en ningún
diseño.**

### La consistencia direccional excede lo que captura cualquier p

| Análisis | ROIs | d mediana | Mismo signo |
|---|---|---|---|
| Prioridad alta | 14 | −0,64 | **14/14** |
| Prioridad media | 18 | −0,44 | 17/18 |
| **Conjunto** | **32** | **−0,46** | **31/32** |

Treinta y una de treinta y dos regiones apuntan en la misma dirección, en dos diseños distintos.

### El barrido whole-brain lo confirma sin declararlo

Aunque ninguna región sobrevivió al FDR, la distribución de la señal es informativa
(diseño dirigido, 1.134 pruebas):

| Medida | Pruebas | p < 0,05 observadas | Esperadas por azar | Razón |
|---|---|---|---|---|
| **LGI** | 278 | **73** | 13,9 | **5,3×** |
| Área | 278 | 21 | 13,9 | 1,5× |
| Volumen | 300 | 22 | 15,0 | 1,5× |
| **Grosor** | 278 | **3** | 13,9 | **0,2×** |

El LGI acumula cinco veces más señal de la esperable por azar en todo el manto cortical. **El
grosor acumula menos que el azar**: no hay ninguna diferencia de grosor entre grupos, en ningún
sitio. El test formal de enriquecimiento sobre la familia de prioridad alta confirma el
resultado del LGI (p = 0,0075).

### Gradiente entre grupos

En z-scores promediados sobre las regiones de prioridad alta:

**MPPP −0,28 · Sano +0,04 · Vestibular +0,24**

El grupo vestibular tiene la girificación más alta, MPPP la más baja, y los sanos quedan
**en posición intermedia**. Esto es central para la interpretación (§4.3).

## 3.3 Asociación con conducta y clínica: solo el grosor

De **1.372 correlaciones** en total, **33** sobrevivieron a la corrección. Su distribución por
medida es el hallazgo:

| Medida | Pruebas | **Sobreviven FDR** | \|ρ\| máx |
|---|---|---|---|
| **Grosor** | 260 | **32** | **0,702** |
| Área | 260 | 1 | 0,491 |
| Volumen | **592** | **0** | 0,551 |
| **LGI** | 260 | **0** | 0,421 |

Con 592 pruebas el volumen no produce ninguna. **El LGI tampoco: cero de 260.** El grosor, con
las mismas 260, produce 32.

### Grosor y severidad, dentro de pacientes (n ≈ 31)

| Región | Hemi | Outcome | ρ parcial | p FDR |
|---|---|---|---|---|
| Giro supramarginal | der | **Niigata** | **−0,70** | 0,0010 |
| Giro supramarginal | der | DHI | −0,69 | 0,0012 |
| Prefrontal dorsolateral | der | DHI | −0,68 | 0,0012 |
| Postcentral | izq | DHI | −0,68 | 0,0012 |
| Temporal superior | der | DHI | −0,65 | 0,0018 |
| Occipital lateral | der | DHI | −0,59 | 0,0081 |
| Postcentral | izq | Niigata | −0,59 | 0,0145 |
| Temporal superior | der | Niigata | −0,57 | 0,0163 |
| Parietal inferior | izq | DHI | −0,56 | 0,0115 |
| Cingulada anterior | izq | DHI | −0,55 | 0,0142 |

Menor grosor, mayor severidad. **La red implicada excede las regiones de prioridad alta**: es un
patrón extendido, no un foco.

**Comprobación clave:** la correlación supramarginal-Niigata **se replica dentro de cada grupo
por separado** — MPPP ρ = −0,70 (n = 14, p = 0,005) y vestibular ρ = −0,69 (n = 17, p = 0,002).
No es un artefacto de mezclar grupos.

**Cautela obligatoria:** Niigata y DHI correlacionan entre sí ρ = 0,72. Miden esencialmente el
mismo constructo y **cuentan como un solo hallazgo**. En cambio, la severidad clínica **no**
correlaciona con el desempeño en navegación (CSE–Niigata ρ = 0,26, p = 0,17): los dos ejes son
dimensiones independientes.

### El eje conductual es mucho más débil

Solo 2 de 612 pruebas sobrevivieron: ínsula posterior izquierda (grosor ↔ Entropy-Ratio,
ρ = +0,60) y prefrontal dorsolateral derecho (área ↔ Entropy-Ratio, ρ = −0,48). **La estructura
sigue mejor a la severidad clínica que al desempeño en navegación.**

## 3.4 Análisis vertex-wise: replicación independiente

### Diferencias entre grupos — 7 clusters, todos LGI

| Diseño | Hemi | Tamaño | CWP | Composición (atlas DK) |
|---|---|---|---|---|
| dirigido | izq | 606 mm² | **0,0002** | precentral 51% + superior frontal 48% |
| dirigido | der | 188 mm² | 0,0014 | superior frontal 55% + ACC caudal 45% |
| dirigido | der | 107 mm² | 0,035 | occipital lateral 100% |
| 3 grupos | izq | 786 mm² | **0,0002** | precentral 58% + superior frontal 41% |
| 3 grupos | der | 221 mm² | 0,0002 | occipital lateral 87% |
| 3 grupos | der | 183 mm² | 0,0016 | superior frontal 58% + ACC caudal 42% |
| 3 grupos | der | 125 mm² | 0,018 | fusiforme 100% |

**Cero clusters en grosor, área y volumen. Cero en cualquier contraste que involucre al grupo
sano.** Un procedimiento que desconoce por completo la lista preinscrita de regiones converge en
la misma medida, la misma dirección y el mismo contraste.

### Correlaciones — 5 clusters, y tres convergencias directas

| Outcome | Medida | Hemi | Tamaño | CWP | Región |
|---|---|---|---|---|---|
| **DHI** | grosor | der | 488 mm² | **0,0002** | **temporal superior** |
| **DHI** | grosor | izq | 336 mm² | 0,0008 | **postcentral** |
| DHI | volumen | der | 322 mm² | 0,0004 | transverso temporal |
| DHI | grosor | der | 172 mm² | 0,040 | superior frontal |
| Entropy-Ratio | área | der | 413 mm² | 0,006 | **prefrontal dorsolateral** |

**Tres regiones coinciden exactamente entre el análisis por ROI y el vertex-wise:**

| Hallazgo | Por ROI | Vertex-wise |
|---|---|---|
| Temporal superior der · grosor ↔ DHI | ρ = −0,65, p_FDR = 0,0018 | 488 mm², CWP = 0,0002 |
| Postcentral izq · grosor ↔ DHI | ρ = −0,68, p_FDR = 0,0012 | 336 mm², CWP = 0,0008 |
| Prefrontal dorsolateral der · área ↔ Entropy-Ratio | ρ = −0,48, p_FDR = 0,027 | 413 mm², CWP = 0,006 |

## 3.5 Robustez

### El efecto no depende de la parcelación

| Comparación | ROIs | r | Mismo signo | d medio |
|---|---|---|---|---|
| DKT vs DK | 16 | **0,997** | 16/16 | −0,644 / −0,651 |
| DKT vs Destrieux | 16 | **0,947** | 16/16 | −0,644 / −0,603 |
| DK vs Destrieux | 16 | **0,954** | 16/16 | −0,651 / −0,603 |

### Ningún sujeto sostiene ningún hallazgo

| Hallazgo | Observado | Rango leave-one-out | Reestimaciones que pierden p < 0,05 |
|---|---|---|---|
| Índice de red · LGI | d = −0,92 | −1,23 a −0,84 | **0 de 36** |
| Ínsula posterior der · LGI | d = −1,04 | −1,28 a −0,91 | **0 de 36** |
| Temporal superior der · LGI | d = −1,04 | −1,21 a −0,92 | **0 de 36** |
| Supramarginal der · grosor ↔ Niigata | ρ = −0,70 | −0,74 a −0,63 | — |
| Supramarginal der · grosor ↔ DHI | ρ = −0,69 | −0,75 a −0,64 | — |
| Temporal superior der · grosor ↔ DHI | ρ = −0,65 | −0,69 a −0,62 | — |
| Postcentral izq · grosor ↔ DHI | ρ = −0,68 | −0,72 a −0,63 | — |

Esto responde directamente la objeción más previsible: que un coeficiente de 0,70 con n = 31
esté inflado por un caso influyente.

### La ansiedad no explica el efecto

| Etapa | N sin → con | \|d\| medio sin | \|d\| medio con | Cambio |
|---|---|---|---|---|
| Prioridad alta | 45 → 31 | 0,637 | 0,721 | **+0,08** |
| Prioridad media | 45 → 31 | 0,474 | 0,589 | **+0,12** |
| Dirigido | 35 → 26 | 0,550 | 0,622 | **+0,07** |

Al ajustar por STAI-Rasgo y BDI **el tamaño de efecto no disminuye: aumenta**. Lo que cae es el
N, y con él la precisión. Que ninguna prueba sobreviva al FDR en el modelo ajustado es pérdida
de potencia, no desaparición del efecto — razón por la cual comparar tamaños de efecto, y no
solo valores p, era parte del plan preespecificado.

## 3.6 Resultados negativos

Se enumeran porque acotan lo que hay que explicar:

- **Asimetría hemisférica:** 0 de 68 índices (L−R)/(L+R) en ambos diseños. Ninguna familia
  enriquecida. **Descarta la lectura lateralizada** sugerida por la literatura VBM previa.
- **Covarianza estructural de la red:** sin diferencias. Solo el área insinúa una señal
  (r medio −0,02 en MPPP vs 0,22 en vestibular, p = 0,018) que **no sobrevive** al FDR de las
  cuatro medidas (p = 0,070) y carecía de hipótesis previa. Observación para replicar, no
  resultado.
- **Subestructuras** (subcampos hipocampales, núcleos talámicos y amigdalinos): ninguna familia
  enriquecida. Direccionalmente, amígdala 18/20 y eje hipocampal posterior 15/18 en la misma
  dirección, con `presubiculum` izquierdo rozando el umbral (p_FDR = 0,056). Sugerente, no
  concluyente.
- **Volumen cortical:** cero hallazgos en 484 correlaciones y en todo el análisis de grupo.

---

# 4. DISCUSIÓN

## 4.1 La doble disociación

El resultado central no es ninguno de los dos hallazgos por separado, sino su relación:

| | LGI | Grosor cortical |
|---|---|---|
| ¿Diferencia MPPP de vestibular? | **Sí** (d ≈ −0,9; 8 resultados; 7 clusters) | **No** (0 de 136 dirigidas; 0,2× el azar whole-brain) |
| ¿Correlaciona con conducta? | No (0 de 164) | Sí (ρ ≈ 0,45–0,60) |
| ¿Correlaciona con severidad? | **No** | **Sí** (ρ hasta −0,70; 21 supervivientes) |

Dos medidas de la misma corteza, en gran medida sobre las mismas regiones, con comportamientos
**ortogonales**. Esto es difícil de producir por azar: si todo fuera ruido no esperaríamos que
una medida concentrara toda la señal entre grupos y la otra toda la señal con severidad.

## 4.2 Interpretación: rasgo y estado

La disociación admite una lectura biológicamente coherente basada en lo que se sabe de cada
medida.

**La girificación cortical se establece en el desarrollo temprano** y es notablemente estable en
la adultez. No es plausible que se modifique en los meses que dura un cuadro de MPPP. Un efecto
en LGI apunta por tanto a un **rasgo predisponente**: una configuración cortical previa que hace
a ciertos individuos más vulnerables a cronificar tras un evento vestibular agudo. Que el LGI
**no** varíe con la severidad refuerza esta lectura: no se mueve con lo enfermo que esté el
paciente.

**El grosor cortical es plástico** y responde a procesos adquiridos. Su correlación con la
severidad actual, y su completa ausencia de diferencia entre grupos, lo sitúa como **marcador de
estado**.

El modelo que sugieren los datos es de dos tiempos: **una predisposición estructural determina
quién cronifica; un proceso adquirido en la red vestibular cortical escala con cuán grave está**.
Son dos preguntas distintas, y este conjunto de datos responde parcialmente a cada una.

## 4.3 ⚠️ La limitación central: no sabemos la dirección

**El contraste que sobrevive es contra el grupo vestibular, no contra los sanos.** El gradiente
observado —MPPP −0,28 · Sano +0,04 · Vestibular +0,24— sitúa a los voluntarios sanos **en
posición intermedia**. Caben dos lecturas incompatibles:

- **(a) Girificación reducida en MPPP** como marcador de vulnerabilidad. Predice que MPPP debería
  estar por debajo de los sanos, cosa que se observa pero débilmente (11/14 regiones).
- **(b) Girificación aumentada en el paciente vestibular que compensa bien**, como marcador de
  reserva estructural. Predice que el grupo vestibular debería estar por encima de los sanos,
  cosa que también se observa (11/14).

**Con n = 10 sanos no es posible decidir entre ambas.** Son dos artículos distintos, ambos
publicables, con implicaciones clínicas opuestas. **Recomendación fuerte: plantear ambas lecturas
en la Discusión** en lugar de elegir la más favorable. Un revisor competente lo notará, y es
mejor haberlo dicho primero.

## 4.4 Sobre el uso del contraste dirigido

Que nada sobreviva con tres grupos y sí con dos puede leerse como búsqueda selectiva de
resultados. La defensa, que debe darse **explícitamente** en el manuscrito:

1. El contraste se justificó **teóricamente antes** de ver ningún resultado, y la lista de
   regiones estaba congelada desde antes de cualquier análisis.
2. **r = 0,99** entre los tamaños de efecto de ambos diseños: el dirigido no estima un efecto
   distinto, lo estima con menos error.
3. Ambos diseños se reportan completos, no solo el favorable.

## 4.5 Convergencia entre métodos: dos hallazgos, dos grados de solidez

El eje **grosor↔severidad converge plenamente**: tres regiones coinciden entre el análisis por
ROI y el vertex-wise, en región, medida y dirección. Es el hallazgo más sólido del trabajo.

El eje **LGI↔grupo converge parcialmente**: coincide en medida, dirección y contraste, pero los
focos vertex-wise caen en regiones de prioridad media (precentral, cingulada anterior, occipital
lateral) y no en las de prioridad alta donde el análisis por ROI daba los mayores efectos.

**Explicación propuesta —y es hipótesis, no hecho:** los dos métodos tienen sensibilidades
distintas. El análisis por ROI **promedia toda la región** y detecta desplazamientos *difusos*;
el vertex-wise busca **picos focales** contiguos que superen p < 0,001. Que ínsula y temporal
superior aparezcan en uno y no en el otro sugiere un efecto extendido de magnitud media; que
precentral y cingulada anterior aparezcan en ambos sugiere que ahí hay además un foco. Apoya
esta lectura que los dos mayores efectos individuales del análisis por ROI fueran precentral
izquierdo (d = −1,04) y postcentral izquierdo (d = −1,10), justo donde cae el cluster mayor.

Consistentemente, **Niigata no produce ningún cluster** pese a tener el ρ más alto del estudio
(−0,70): su efecto es difuso, sin picos focales.

## 4.6 Otras limitaciones

- **Tamaño muestral.** n = 10 sanos limita el diseño de tres grupos; n = 31 en los análisis de
  severidad. Los intervalos de confianza son anchos y varios rozan el cero.
- **Diseño transversal.** La interpretación rasgo/estado es inferencia sobre las propiedades
  conocidas de cada medida, **no** una demostración longitudinal. Contrastarla requiere seguir
  pacientes vestibulares agudos hasta ver quién cronifica.
- **Niigata y DHI no son independientes** (ρ = 0,72): cuentan como un hallazgo.
- **Coeficientes seleccionados de un barrido** están sesgados al alza. La replicación
  intra-grupo y el leave-one-out mitigan la objeción, pero deben reportarse intervalos, no
  estimaciones puntuales.
- **Sin corrección del LGI en origen.** Se recalculó desde los `.stats`; las tablas originales
  del proyecto conservan la columna errónea y no deben usarse.

## 4.7 Qué haría falta para cerrar la pregunta

1. **Ampliar el brazo sano** hasta n ≈ 25–30. Es la única forma de resolver §4.3, y convertiría
   un hallazgo ambiguo en uno direccional.
2. **Seguimiento longitudinal** de pacientes vestibulares agudos, con imagen basal, para
   contrastar la hipótesis de rasgo predisponente de forma directa.
3. **Replicación independiente** del eje grosor↔severidad, que es el más robusto y el más
   fácilmente replicable.

---

# 5. PROPUESTA EDITORIAL

## 5.1 Qué publicaría, y cómo

**Un solo artículo**, articulado en torno a la disociación. Es más fuerte que sus dos mitades y
evita el troceo. Título propuesto:

> *Reduced cortical gyrification distinguishes persistent postural-perceptual dizziness from
> compensated vestibular patients, while cortical thickness scales with symptom severity: a
> double dissociation*

## 5.2 Figuras propuestas (todas ya generadas)

| # | Figura | Archivo |
|---|---|---|
| **1** | Forest de las 32 ROIs en LGI, contraste dirigido — 31/32 en la misma dirección | `figs/sintesis/forest_LGI_todas_las_rois.pdf` |
| **2** | Mapas de superficie de los clusters de LGI | `figs/etapaD/superficie_LGI_dirigido.pdf` |
| **3** | Dispersión grosor supramarginal ↔ Niigata, con recta por grupo | `figs/etapaB4/scatter_2_supramarginal_thickness_rh_Niigata.pdf` |
| **4** | Mapas de superficie de grosor ↔ DHI | `figs/etapaB5/superficie_thickness_sev_pac_DHI.pdf` |
| **5** | Tabla-figura de la doble disociación | `results/SINTESIS_disociacion_resultados.csv` |
| Supl. | Comparación de diseños (r = 0,99), leave-one-out, réplica entre atlas | `figs/etapaAD/`, `figs/etapaR/` |

## 5.3 Orden narrativo recomendado

1. Los grupos son demográficamente indistinguibles y clínicamente muy distintos (Tabla 1).
2. Ninguna diferencia de grosor, área o volumen — en ningún diseño, ni whole-brain.
3. El LGI sí, en el contraste teóricamente justificado, con 31/32 regiones concordantes.
4. Replicación vertex-wise independiente y en tres parcelaciones.
5. Giro: el LGI **no** se asocia a nada clínico ni conductual.
6. Pero el grosor **sí**, intensamente, con la severidad — y converge entre métodos.
7. Interpretación rasgo/estado, con **ambas** lecturas direccionales sobre la mesa.

## 5.4 Objeciones que hay que anticipar

| Objeción probable | Respuesta preparada |
|---|---|
| "Cambiaron el diseño hasta que salió algo" | r = 0,99 entre diseños; justificación teórica previa; ambos reportados |
| "n = 10 sanos es insuficiente" | Cierto, y por eso se declara §4.3 en lugar de elegir una lectura |
| "ρ = 0,70 con n = 31 está inflado" | Leave-one-out: rango −0,74 a −0,63; replicado dentro de cada grupo |
| "¿Es artefacto de calidad de imagen?" | SurfaceHoles no difiere entre grupos (p = 0,90) |
| "¿Y la ansiedad?" | Modelo paralelo completo: el efecto aumenta, no disminuye |
| "ROI y vertex-wise se contradicen" | §4.5: coinciden en medida, dirección y contraste; difieren en localización por sensibilidad distinta |
| "¿Por qué DKT y no DK?" | Réplica en las tres parcelaciones: r = 0,95–0,997 |

---

*Borrador generado a partir de 4.210 pruebas estadísticas en 17 bloques analíticos, de las que 53 sobreviven a la corrección de su familia. Todos los
números son trazables a `results/`; el detalle completo está en `docs/MAPA_DE_RESULTADOS.md` y
`docs/REPORTE_EXPLORATORIO.html`.*
