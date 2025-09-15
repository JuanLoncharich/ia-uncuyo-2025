# Reporte de Resultados en Frozen Lake

En este reporte vemos resultados sobre la aplicación de algunos algoritmos conocidos (**RANDOM, BFS, DFS, DLS 50/75/100, UCS, A***) al entorno de Frozen Lake de gymnasium, con cuadrillas de 100 x 100 y un p(F) = 0.92 (probabilidad de que la cuadrilla sea pisable) y una vida máxima (cantidad máxima de pasos) de 1000. Todas las pruebas se realizaron un total de 30 veces cada algoritmo, repitiendo la semilla para todos los algoritmos para poder estar en igualdad de condiciones.

## Interpretación de los gráficos

En todos los gráficos se tienen en cuenta solo las ejecuciones ganadoras.

- **bar_success_counts.png**: Cantidad total de ejecuciones ganadoras  
- **box_actions_cost.png**: Box plot de los costos de las acciones en el escenario 2  
- **box_actions_count.png**: Box plot de los costos de las acciones en el escenario 1  