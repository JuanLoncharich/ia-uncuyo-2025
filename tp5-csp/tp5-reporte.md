# TP5 – Satisfacción de Restricciones

## Introducción
El objetivo del trabajo práctico fue modelar y resolver problemas mediante satisfacción de restricciones (CSP). Se implementaron modelos concretos (Sudoku, mapa de Australia y N-Reinas), se analizaron algoritmos clásicos como AC-3, y se comparó backtracking con forward checking mediante experimentos cuantitativos.

## Ejercicio 1 – CSP para Sudoku
- **Variables:** 81 celdas identificadas por coordenadas `(fila, columna)`.
- **Dominios:** `{1,…,9}` para casillas vacías y dominio unitario para las ya completadas.
- **Restricciones:** todas las celdas en una misma fila, columna o subcuadro 3×3 deben contener valores distintos (restricciones binarias).

En `code/sudoku_csp.py` se encapsuló el modelo y se implementó:
1. **Verificación de consistencia** entre la celda actual y sus vecinos.
2. **Heurísticas MRV + LCV** para ordenar variables y dominios.
3. **Búsqueda con backtracking** complementada con **AC-3** como inferencia para reducir dominios en cada paso.

Al ejecutar el módulo se resuelve correctamente el Sudoku de ejemplo, verificando la consistencia del modelo y la efectividad de AC-3 para podar valores antes de expandir el árbol de búsqueda.

## Ejercicio 2 – AC-3 en el mapa de Australia
Se codificó el grafo de restricciones con las provincias {WA, NT, Q, NSW, V, SA, T} y el conjunto de colores {red, green, blue}. El script `code/ac3_demo.py` aplica AC-3 bajo dos configuraciones:

1. **Asignación parcial WA=red, V=blue:** AC-3 detecta inconsistencia porque las restricciones obligan a SA=green y NSW=red, dejando a Q sin colores disponibles y vaciando su dominio.
2. **Asignación parcial WA=red, V=red:** el algoritmo mantiene todos los dominios no vacíos, mostrando que la asignación puede extenderse a un coloreo completo.

La salida del script lista los dominios finales ordenados alfabéticamente, evidenciando cuándo se alcanza consistencia o no.

## Ejercicio 3 – Complejidad de AC-3
Para cada arco `(Xi, Xj)`, la operación `revise` compara cada valor del dominio de `Xi` con el de `Xj`. En el peor caso se revisan `d` valores en `Xi`, y por cada uno se recorre hasta `d` valores en `Xj`, lo que cuesta `O(d²)`. Un arco puede reinsertarse en la cola a lo sumo `d` veces (cada vez que se elimina un valor), por lo que la complejidad total es `O(e · d³)` siendo `e` la cantidad de arcos dirigidos.

Cuando la estructura del problema es un árbol (grafo sin ciclos), cada arco se revisa a lo sumo dos veces porque la eliminación en un nodo no vuelve a propagarse hacia ramas ya procesadas. Así, la complejidad se reduce a `O(n · d²)`, donde `n` es el número de variables y `d` el tamaño máximo del dominio.

## Ejercicio 4 – N-Reinas con CSP
- **Backtracking (`code/n_reinas_backtracking.py`):** variables por columna y dominios `{0,…,N−1}`. Se usan sets para filas y diagonales ocupadas, y se randomiza el orden de las filas para obtener distintas trazas en los experimentos.
- **Forward checking (`code/n_reinas_forward.py`):** a partir de la misma formulación, se aplica propagación al fijar cada columna, descartando valores de las columnas restantes incompatibles con filas o diagonales. El algoritmo reutiliza la estructura de resultados (`NQueensResult`) para reportar nodos explorados y tiempo.

Ambos módulos incluyen bloques `__main__` para ejecutar pruebas rápidas.

## Ejercicio 5 – Experimentos y comparación
`code/n_reinas_runner.py` automatiza los experimentos para `N = 4, 8, 10`, ejecutando 30 corridas por algoritmo con semillas `random.seed(i)` para `i = 1..30`. Por cada corrida se registra:

- solución encontrada (bool),
- tiempo de ejecución (`time.perf_counter`),
- nodos explorados.

Los resultados se consolidan en `tp5-Nreinas.csv`. Con `code/utils.py` se calculan estadísticas (`compute_stats`) y se generan boxplots (`make_boxplots`) guardados como `images/boxplot_tiempos.png` e `images/boxplot_nodos.png`.

### Estadísticas resumidas

| Algoritmo | N  | Éxito (%) | Tiempo prom. (s) | Desv. tiempo (s) | Nodos prom. | Desv. nodos |
|-----------|----|-----------|------------------|------------------|-------------|-------------|
| BT        | 4  | 100.0     | 0.000009         | 0.000005         | 8.20        | 2.86        |
| FC        | 4  | 100.0     | 0.000016         | 0.000019         | 6.07        | 1.26        |
| BT        | 8  | 100.0     | 0.000038         | 0.000025         | 23.10       | 15.32       |
| FC        | 8  | 100.0     | 0.000065         | 0.000033         | 16.57       | 7.04        |
| BT        | 10 | 100.0     | 0.000122         | 0.000127         | 59.03       | 60.82       |
| FC        | 10 | 100.0     | 0.000142         | 0.000119         | 32.00       | 25.25       |

Forward checking reduce entre un 25–45 % los nodos explorados respecto de backtracking puro, manteniendo tiempos muy similares (del orden de microsegundos para los N evaluados). Esto se observa también en los boxplots, donde las distribuciones de nodos para FC están desplazadas hacia valores menores, especialmente en `N = 10`.

### Comparación con TP4
En el TP4 se utilizaron algoritmos de búsqueda local (Hill Climbing y Simulated Annealing) que no garantizan completitud pero escalan mejor para `N` grandes. En cambio, las formulaciones de CSP garantizan encontrar soluciones cuando existen y permiten medir de forma directa la cantidad de nodos explorados gracias a la estructura de búsqueda sistemática. Forward checking actúa como un puente entre ambas ideas: introduce inferencia liviana que reduce significativamente el branching sin abandonar la completitud.

## Conclusiones
Los ejercicios cubren el ciclo completo de trabajo con CSP: modelado, propagación y experimentación. AC-3 se mostró efectivo para detectar inconsistencias tempranas tanto en Sudoku como en el mapa de Australia. En N-Reinas, forward checking ofreció mejoras notables en la cantidad de nodos explorados, destacando la importancia de incorporar inferencia liviana en algoritmos de backtracking. Finalmente, la comparación con el TP4 resalta los beneficios de los CSP cuando se requiere garantizar soluciones, aunque con un costo potencialmente mayor para instancias masivas. Las herramientas desarrolladas (scripts, reportes y gráficos) dejan asentada una base reutilizable para extensiones futuras.
