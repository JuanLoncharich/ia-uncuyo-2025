# 4_random_classifier.R
# necesita dplyr
suppressPackageStartupMessages({
  library(dplyr)
})

# ------------------------------------------------------------------
# (a) función que agrega prediction_prob aleatoria
# ------------------------------------------------------------------
add_random_probs <- function(df) {
  df %>%
    mutate(prediction_prob = runif(n()))
}

# ------------------------------------------------------------------
# (b) función random_classifier
# ------------------------------------------------------------------
random_classifier <- function(df) {
  df %>%
    mutate(
      prediction_class = if_else(prediction_prob > 0.5, 1L, 0L)
    )
}

# ------------------------------------------------------------------
# (c) cargar el validation y aplicar funciones
# ------------------------------------------------------------------
# ajustá la ruta según tu estructura
validation_path <- "../../../data/arbolado-mza-dataset-train-80.csv"

val_df <- read.csv(validation_path, check.names = FALSE)

# defensivo: por si viene con mayúsculas/espacios
names(val_df) <- names(val_df) |>
  trimws() |>
  tolower()

if (!"inclinacion_peligrosa" %in% names(val_df)) {
  stop("No se encontró la columna 'inclinacion_peligrosa' en el validation.")
}

val_df <- val_df %>%
  # por si viene como char
  mutate(inclinacion_peligrosa = as.integer(inclinacion_peligrosa))

# aplicar las funciones (a) y (b)
val_scored <- val_df %>%
  add_random_probs() %>%
  random_classifier()

# ------------------------------------------------------------------
# (d) calcular TP, TN, FP, FN con dplyr
# ------------------------------------------------------------------
# ground truth
# y = inclinacion_peligrosa
# y_hat = prediction_class
resumen <- val_scored %>%
  summarise(
    TP = sum(inclinacion_peligrosa == 1 & prediction_class == 1),
    TN = sum(inclinacion_peligrosa == 0 & prediction_class == 0),
    FP = sum(inclinacion_peligrosa == 0 & prediction_class == 1),
    FN = sum(inclinacion_peligrosa == 1 & prediction_class == 0),
    n  = n()
  )

print(resumen)

# ------------------------------------------------------------------
# (v) armar matriz de confusión “bonita”
# ------------------------------------------------------------------
TP <- resumen$TP
TN <- resumen$TN
FP <- resumen$FP
FN <- resumen$FN
n  <- resumen$n

conf_mat <- matrix(
  c(TN, FP,
    FN, TP),
  nrow = 2,
  byrow = TRUE,
  dimnames = list(
    "Actual" = c("NO (0)", "YES (1)"),
    "Predicted" = c("NO (0)", "YES (1)")
  )
)

cat("\nMatriz de confusión (n =", n, "):\n")
print(conf_mat)

