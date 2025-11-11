# Trabajo Práctico 7A: Introducción a ML

## 1. Flexibilidad de los Métodos de Aprendizaje de Máquinas

### a) $n$ extremadamente grande, $p$ pequeño

Respuesta: método flexible 


Justificación:
En este escenario ($n$ grande, $p$ pequeño), se espera que un **método flexible se comporte mejor**. La razón principal es que la gran cantidad de observaciones ($n$) mitiga el principal riesgo de los modelos flexibles: la alta varianza o sobreajuste. Un modelo flexible tiene un sesgo bajo, lo que le permite capturar patrones complejos o no lineales en $f$. Si bien esto normalmente podría llevarlo a "memorizar" el ruido en muestras pequeñas, un $n$ grande le permite distinguir el ruido de la señal verdadera. Además, un $p$ pequeño evita la maldición de la dimensionalidad, asegurando que los datos cubran densamente el espacio de predictores, lo que hace que la estimación de $f$ por parte del modelo flexible sea más estable y precisa.

### b) $p$ extremadamente grande, $n$ pequeño

Respuesta: no flexibe 

Justificación: 
En este escenario, es mejor utilizar un método no flexible. El pequeño $n$ eleva el riesgo de sobreajuste (overfitting), mientras que el gran $p$ causa la "maldición de la dimensionalidad", dispersando los pocos datos en un espacio de características enorme. Un modelo flexible (de baja sesgo) tendría una varianza altísima al intentar ajustarse al ruido en este espacio disperso. Por el contrario, un método inflexible (de alto sesgo) impone una estructura simple que controla la varianza, lo cual es esencial para prevenir el sobreajuste en esta situación.

### c) La relación entre predictores y variable dependiente es altamente no lineal

Respuesta: flexibe

Justificación: Se necesita un método flexible, sino, es probable que no se pueda capturar la "forma" de la función f. 


### d) La varianza de los términos de error, $\sigma^2 = \text{Var}(\epsilon)$, es extremadamente alta

Respuesta: no flexible

Justificación:
Cuando $\sigma^2$ (la varianza del error) es extremadamente alta, los datos están muy "ruidosos". Esto significa que las observaciones $Y$ están muy dispersas y lejos de la verdadera función $f(X)$.

---

## 2. Clasificación vs. Regresión e Inferencia vs. Predicción

### a) Salario de Directores Ejecutivos

* Inferencia: qué factores afectan al salario
* Regresión: qué salio tienen los directores ejecutivos 
* $n$:500
* $p$:3


### b) Éxito o Fracaso de Nuevo Producto

* Prediccion: si es exito o fracaso 
* Clasificacion: Si es exito o fracazo 
* $n$: 20
* $p$: 13

### c) Predicción del Tipo de Cambio USD/Euro

* Regrecion
* Prediccion
* $n$: 52
* $p$: 3

---

## 3. Ventajas y Desventajas de la Flexibilidad

### Ventajas de un enfoque flexible
- Puede **capturar relaciones no lineales** o complejas entre los predictores y la variable de salida.   
- Es ideal cuando se dispone de **muchos datos** y la verdadera relación subyacente es complicada.


### Desventajas de un enfoque flexible
- Tiende a tener **mayor varianza**, lo que significa que puede **sobreajustar (overfitting)** los datos de entrenamiento.  
- Requiere **más datos y poder computacional** para entrenarse correctamente.  
- Es más difícil de **interpretar**, ya que las relaciones aprendidas pueden ser muy complejas.

### Ventajas de un enfoque inflexible
- Tiende a tener **menor varianza**, por lo que es **más estable y menos propenso al sobreajuste (overfitting)**.  
- Funciona bien cuando el **número de observaciones es pequeño** o cuando los datos contienen **mucho ruido**.  
- Es **más fácil de interpretar**, ya que las relaciones entre las variables suelen ser simples y directas.  

---

### Desventajas de un enfoque inflexible  
- Su rendimiento disminuye cuando la **verdadera relación en los datos es altamente no lineal o complicada**.  
- Puede producir **predicciones menos precisas** si el modelo es demasiado rígido para la naturaleza del problema.


### Cuándo preferir un enfoque más flexible
- Cuando se dispone de **una gran cantidad de datos (n grande)**.  
- Cuando la relación entre los predictores y la variable objetivo es **altamente no lineal o compleja**.  
- Cuando el objetivo principal es **maximizar la precisión de la predicción**, más que la interpretabilidad.


### Cuándo preferir un enfoque menos flexible
- Cuando el conjunto de datos es **pequeño o ruidoso** (alta varianza en los errores).  
- Cuando se sospecha que la relación entre las variables es **simple o aproximadamente lineal**.  
- Cuando se busca **interpretabilidad** y **robustez** más que exactitud extrema.

---

## 4. Enfoque Paramétrico vs. No Paramétrico

Los **enfoques paramétricos** y **no paramétricos** difieren principalmente en la forma en que modelan la relación entre los predictores y la variable objetivo.

- Un **modelo paramétrico** asume una **forma funcional específica** para la relación entre las variables (por ejemplo, lineal, cuadrática, logística, etc.).  
  Una vez elegida esa forma, el aprendizaje consiste en **estimar los parámetros** del modelo a partir de los datos.

- Un **modelo no paramétrico**, en cambio, **no impone una forma funcional fija**.  
  En lugar de eso, **deja que los datos determinen la estructura del modelo**, permitiendo una mayor flexibilidad para capturar relaciones complejas o no lineales.

---

### 🔹 Diferencias principales

| Aspecto | Enfoque Paramétrico | Enfoque No Paramétrico |
|----------|--------------------|------------------------|
| **Suposición de forma del modelo** | Se asume una forma específica (ej. lineal) | No se asume una forma fija |
| **Número de parámetros** | Fijo, independiente de *n* | Crece con *n* |
| **Flexibilidad** | Menos flexible | Más flexible |
| **Requisitos de datos** | Funciona bien con pocos datos | Requiere muchos datos |
| **Complejidad computacional** | Baja | Alta |
| **Interpretabilidad** | Alta | Baja |
| **Ejemplos típicos** | Regresión lineal, regresión logística | KNN, árboles de decisión, redes neuronales |

---

### Ventajas del enfoque paramétrico
- **Simplicidad:** fácil de interpretar y de implementar.  
- **Menor riesgo de sobreajuste:** al estar restringido por una forma fija.  
- **Eficiencia computacional:** requiere menos recursos para entrenar.  
- **Buen rendimiento con pocos datos**, si la forma asumida del modelo es razonable.

---

### Desventajas del enfoque paramétrico
- **Alta dependencia de las suposiciones:** si la forma funcional elegida no refleja bien la realidad, el modelo tiene **alto sesgo (bias)**.  
- **Menor flexibilidad:** no captura bien relaciones complejas o no lineales.  

---

### Ventajas del enfoque no paramétrico
- **Alta flexibilidad:** puede modelar relaciones no lineales o complejas sin suponer una forma específica.  
- **Mejor ajuste cuando se dispone de muchos datos.**

---

### Desventajas del enfoque no paramétrico
- **Mayor varianza:** propenso al sobreajuste si los datos son pocos o ruidosos.  
- **Menor interpretabilidad.**  
- **Mayor costo computacional** y necesidad de más datos para generalizar bien.
---

## 5. K Vecinos Más Cercanos (KNN) para Clasificación

Punto de prueba: $X_1 = 0, X_2 = 0, X_3 = 0$.

### a) Distancia Euclidiana

| Obs. | $X_1$ | $X_2$ | $X_3$ | Distancia Euclidiana ($D_i$) |
| :---: | :---: | :---: | :---: | :---: |
| 1 | 0 | 3 | 0 | 3.000 |
| 2 | 2 | 0 | 0 | 2.000 |
| 3 | 0 | 1 | 3 | 3.162 |
| 4 | 0 | 1 | 2 | 2.236 |
| 5 | -1 | 0 | 1 | 1.414 |
| 6 | 1 | 1 | 1 | 1.732 |

### b) Predicción con $K = 1$

* Predicción: Verde
* Justificación: porque el vecino mas cercado que es la observacion 5 y su color es verde

### c) Predicción con $K = 3$

* Predicción: Rojo 
* Justificación: porque tengo 2 observaciones rojas y una verde 

### d) Valor de $K$ si el límite de decisión de Bayes es altamente no lineal

* Valor esperado de $K$: Si el **límite de decisión de Bayes** es altamente **no lineal**, se espera que el **mejor valor de K sea pequeño**.

* Razón: Cuando esa frontera es **compleja o muy curva**, un modelo **flexible** es necesario para poder aproximarla adecuadamente. En el caso del algoritmo **K-Nearest Neighbors (KNN)**: Un **K pequeño** permite que el modelo sea **muy sensible a los patrones locales**, adaptándose mejor a una frontera no lineal.  
