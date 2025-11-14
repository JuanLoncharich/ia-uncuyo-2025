# Ejercicio 7 – Validación cruzada (k-fold) con árbol de decisión

## a) Creación de folds
Se implementó la función `create_folds()`, que divide aleatoriamente el dataset en *k = 10* subconjuntos de tamaño similar.  
Cada iteración usa 9 folds para entrenamiento y 1 fold para prueba, repitiendo el proceso hasta cubrir todos.

```r
create_folds <- function(df, k = 10) {
  n <- nrow(df)
  idx <- sample.int(n)               # mezcla aleatoria
  folds <- split(idx, cut(seq_along(idx), breaks = k, labels = FALSE))
  names(folds) <- paste0("Fold", seq_len(k))
  folds
}
```

## b) Entrenamiento y evaluación
Se implementó la función `cross_validation()`, que entrena un modelo **rpart** en cada fold y calcula las métricas:

- **Accuracy** = (TP + TN) / Total  
- **Precision** = TP / (TP + FP)  
- **Sensitivity (Recall)** = TP / (TP + FN)  
- **Specificity** = TN / (TN + FP)

El modelo se entrenó con la siguiente fórmula:

inclinacion_peligrosa ~ altura + circ_tronco_cm + lat + long + seccion + especie




```r
cross_validation <- function(df, k = 10,
                             formula = inclinacion_peligrosa ~ altura +
                               circ_tronco_cm + lat + long + seccion + especie) {

  # normalizar nombres
  names(df) <- tolower(trimws(names(df)))

  if (!"inclinacion_peligrosa" %in% names(df)) {
    stop("El dataframe no tiene la columna 'inclinacion_peligrosa'.")
  }

  # convertir columnas categóricas a factor ANTES de hacer folds
  if ("especie" %in% names(df)) {
    df$especie <- as.factor(df$especie)
  }
  if ("seccion" %in% names(df)) {
  }

  # quitar filas sin clase
  df <- df %>% filter(!is.na(inclinacion_peligrosa))

  folds <- create_folds(df, k)
  all_metrics <- list()
  i <- 1

  for (f_name in names(folds)) {
    test_idx  <- folds[[f_name]]
    test_df   <- df[test_idx, , drop = FALSE]
    train_df  <- df[-test_idx, , drop = FALSE]

    tree_model <- rpart(formula, data = train_df, method = "class")

    p <- predict(tree_model, newdata = test_df, type = "class")

    y_pred <- as.integer(as.character(p))
    y_true <- as.integer(as.character(test_df$inclinacion_peligrosa))

    m <- compute_metrics(y_true, y_pred)
    m$fold <- i
    all_metrics[[i]] <- m
    i <- i + 1
  }

  metrics_df <- bind_rows(all_metrics)

  summary_df <- metrics_df %>%
    summarise(
      accuracy_mean    = mean(accuracy, na.rm = TRUE),
      accuracy_sd      = sd(accuracy, na.rm = TRUE),
      precision_mean   = mean(precision, na.rm = TRUE),
      precision_sd     = sd(precision, na.rm = TRUE),
      sensitivity_mean = mean(sensitivity, na.rm = TRUE),
      sensitivity_sd   = sd(sensitivity, na.rm = TRUE),
      specificity_mean = mean(specificity, na.rm = TRUE),
      specificity_sd   = sd(specificity, na.rm = TRUE)
    )

  list(per_fold = metrics_df, summary = summary_df)
}

```






## c) Resultados obtenidos

| Fold | Accuracy | Precision | Sensitivity | Specificity |
|:----:|:---------:|:----------:|:-------------:|:-------------:|
| 1 | 0.883 | NA | 0 | 1 |
| 2 | 0.881 | NA | 0 | 1 |
| 3 | 0.892 | NA | 0 | 1 |
| 4 | 0.896 | NA | 0 | 1 |
| 5 | 0.886 | NA | 0 | 1 |
| 6 | 0.884 | NA | 0 | 1 |
| 7 | 0.878 | NA | 0 | 1 |
| 8 | 0.893 | NA | 0 | 1 |
| 9 | 0.899 | NA | 0 | 1 |
| 10 | 0.883 | NA | 0 | 1 |

**Promedios (k = 10):**

| Métrica | Media | Desvío estándar |
|----------|--------|----------------|
| Accuracy | 0.8879 | 0.0073 |
| Precision | NA | — |
| Sensitivity | 0 | 0 |
| Specificity | 1 | 0 |

## d) Interpretación
- El modelo obtiene una **exactitud alta (~88.8%)**, pero **no predice correctamente ningún caso positivo** (Sensitivity = 0).  
- Esto sugiere que el árbol entrenado tiende a **clasificar todo como clase 0 (no peligrosa)**, probablemente por el **desbalance severo** del dataset (muchos más árboles no peligrosos que peligrosos).  
- Aunque el Accuracy parece bueno, el modelo **no tiene capacidad de detección de riesgo real**, por lo que se debe ajustar (por ejemplo, balancear clases o ajustar parámetros de `rpart`).
