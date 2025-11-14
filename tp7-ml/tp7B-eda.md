# Informe de Análisis: Inclinación Peligrosa en Árboles Urbanos


# Ejericicio 2

## 1. Introducción

Este informe presenta un análisis exhaustivo sobre la inclinación peligrosa en árboles urbanos, examinando la distribución de casos, las especies más afectadas y las secciones con mayor riesgo. El estudio se basa en un conjunto de datos de 25,529 árboles evaluados.

## 2. Distribución de la Clase: Inclinación Peligrosa

![alt text](parte1/ej2/outputs/a_distribucion_clase.png)

### 2.1. Resumen General

El análisis de la distribución de clases revela un marcado **desbalance** en el dataset:

- **Árboles sin inclinación peligrosa (Clase 0)**: 22,668 árboles (88.8%)
- **Árboles con inclinación peligrosa (Clase 1)**: 2,861 árboles (11.2%)

### 2.2. Interpretación

La baja prevalencia de inclinación peligrosa (11.2%) indica que:
- La mayoría de los árboles urbanos se encuentran en condiciones estructuralmente estables
- Existe un **desbalanceo significativo** de clases, lo que representa un desafío para el desarrollo de modelos predictivos
- Es necesario implementar técnicas de balanceo (oversampling, undersampling o SMOTE) para mejorar la capacidad predictiva de modelos de machine learning

## 3. Top 15 Especies con Mayor Tasa de Inclinación Peligrosa

![alt text](parte1/ej2/outputs/c_especie_tasa_top.png)

### 3.1. Especies de Alto Riesgo

Las especies con mayor tasa de inclinación peligrosa son:

| Ranking | Especie | Tasa | N | Observaciones |
|---------|---------|------|---|---------------|
| 1 | Morera | 18.4% | 1,552 | Mayor riesgo identificado |
| 2 | Acacia SP | 15.5% | 574 | Alto riesgo |
| 3 | Aguaribay | 11.2% | 232 | Riesgo moderado-alto |
| 4 | Tipa | 10.1% | 69 | Muestra pequeña, alta variabilidad |
| 5 | Jacarandá | 9.5% | 275 | Riesgo moderado |

### 3.2. Especies de Riesgo Moderado

| Ranking | Especie | Tasa | N |
|---------|---------|------|---|
| 6 | Plátano | 9.1% | 2,429 |
| 7 | Paraíso | 8.8% | 1,321 |
| 8 | Acacia visco | 7.6% | 66 |
| 9 | Fresno americano | 5.8% | 129 |
| 10 | Álamo blanco | 5.1% | 99 |

### 3.3. Especies de Bajo Riesgo

| Ranking | Especie | Tasa | N |
|---------|---------|------|---|
| 11 | Caducifolio | 4.4% | 364 |
| 12 | Fresno europeo | 4.2% | 444 |
| 13 | Ailanthus | 3.6% | 169 |
| 14 | Prunus | 3.5% | 316 |
| 15 | Perenne | 3.2% | 253 |



## 4. Tasa de Inclinación Peligrosa por Sección

![alt text](parte1/ej2/outputs/b_seccion_tasa.png)

### 4.1. Ranking de Secciones por Riesgo

| Ranking | Sección | Tasa | N | Clasificación |
|---------|---------|------|---|---------------|
| 1 | 3 | 15.0% | 2,263 | Riesgo Alto |
| 2 | 2 | 14.6% | 2,922 | Riesgo Alto |
| 3 | 5 | 12.9% | 1,184 | Riesgo Moderado-Alto |
| 4 | 4 | 12.6% | 1,692 | Riesgo Moderado-Alto |
| 5 | 1 | 11.2% | 2,481 | Riesgo Moderado |
| 6 | 7 | 9.1% | 1,012 | Riesgo Moderado |
| 7 | 6 | 6.1% | 1,117 | Riesgo Bajo |
| 8 | 8 | 3.0% | 857 | Riesgo Muy Bajo |

### 4.2. Análisis por Zona

**Secciones 3 y 2: Zona de Máximo Riesgo**
- Tasas superiores al 14.5%
- Muestras grandes (>2,200 árboles) garantizan estimaciones robustas
- Intervalos de confianza relativamente estrechos
- **Requieren intervención prioritaria e inmediata**

**Secciones 5 y 4: Zona de Riesgo Moderado-Alto**
- Tasas entre 12.6% y 12.9%
- Requieren monitoreo intensivo
- Planificación de intervenciones preventivas a corto plazo

**Secciones 1 y 7: Zona de Riesgo Moderado**
- Tasas entre 9.1% y 11.2%
- Monitoreo regular
- Mantenimiento preventivo programado

**Secciones 6 y 8: Zona de Bajo Riesgo**
- Tasas inferiores al 7%
- La sección 8 presenta la menor tasa (3.0%)
- Mantenimiento rutinario suficiente

### 4.3. Consideraciones Geoespaciales

La variabilidad entre secciones (3.0% - 15.0%) sugiere que factores locales influyen en la inclinación peligrosa:
- Condiciones del suelo y drenaje
- Exposición al viento dominante
- Densidad de construcciones y espacio disponible para raíces
- Edad promedio del arbolado
- Historia de mantenimiento y poda

# Ejercicio 3

## 1. Distribución por Clase: Inclinación Peligrosa

![alt text](parte1/ej3/outputs/3b_hist_circ_tronco_por_clase.png)

### 1.1. Observaciones Principales

**Clase 0 (Sin inclinación peligrosa - Rosa)**
- Distribución aproximadamente normal con ligero sesgo hacia la derecha
- Moda principal entre 100-140 cm
- Concentración mayoritaria en el rango 60-200 cm
- Presencia mínima de árboles con circunferencias superiores a 250 cm

**Clase 1 (Con inclinación peligrosa - Verde azulado)**
- Distribución similar a la Clase 0 pero con menor frecuencia absoluta
- Moda entre 100-140 cm
- Mayor proporción relativa de árboles en el rango 100-180 cm
- Prácticamente ausencia de árboles con circunferencias superiores a 300 cm

### 1.2. Análisis Comparativo

- Ambas clases presentan distribuciones similares en forma y tendencia central
- Los árboles con inclinación peligrosa muestran una concentración ligeramente mayor en el rango medio (100-180 cm)
- Los árboles de mayor porte (>250 cm) raramente presentan inclinación peligrosa
- La similitud de distribuciones sugiere que la circunferencia del tronco por sí sola no es un predictor fuerte de inclinación peligrosa

## 2. Distribución General de circ_tronco_cm

### 2.1. Histograma con 40 bins

![alt text](parte1/ej3/outputs/3a_hist_circ_tronco_40bins.png)

- **Moda principal**: ~120 cm
- **Distribución**: Unimodal con sesgo a la derecha

### 2.2. Histograma con 20 bins

![alt text](parte1/ej3/outputs/3a_hist_circ_tronco_20bins.png)

- **Pico máximo**: ~120-140 cm con ~3,800 árboles
- **Forma**: Distribución normal sesgada a la derecha
- **Observación**: Segunda concentración menor entre 60-100 cm (~3,200 árboles)
- **Transición**: Decrecimiento rápido después de 180 cm

### 2.3. Histograma con 10 bins

![alt text](parte1/ej3/outputs/3a_hist_circ_tronco_10bins.png)

- **Máximo absoluto**: Rango 100-150 cm con ~7,200 árboles
- **Segundo pico**: Rango 50-100 cm con ~6,500 árboles
- **Distribución agregada**: Concentración evidente en 50-200 cm


## 3. Creación de Variable Categórica: circ_tronco_cm_cat

### 3.1. Cuantiles de Corte

Los puntos de corte calculados son:
```
Q1 (25%): Primer cuartil de circ_tronco_cm
Q2 (50%): Mediana de circ_tronco_cm  
Q3 (75%): Tercer cuartil de circ_tronco_cm
```

### 3.2. Definición de Categorías

| Categoría | Criterio | Interpretación |
|-----------|----------|----------------|
| **bajo** | circ_tronco_cm ≤ Q1 | Árboles jóvenes o de especies pequeñas |
| **medio** | Q1 < circ_tronco_cm ≤ Q2 | Árboles en desarrollo o adultos pequeños |
| **alto** | Q2 < circ_tronco_cm ≤ Q3 | Árboles adultos maduros |
| **muy_alto** | circ_tronco_cm > Q3 | Árboles ancianos o de gran porte |

### 3.3. Distribución Esperada

Por definición de cuantiles:
- 25% de los árboles en categoría "bajo"
- 25% en "medio"
- 25% en "alto"
- 25% en "muy_alto"
