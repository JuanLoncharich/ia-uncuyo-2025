suppressPackageStartupMessages({
  library(dplyr)
})

# ------------------------------------------------------------------
# (a) Función que asigna siempre la clase mayoritaria
# ------------------------------------------------------------------
biggerclass_classifier <- function(df) {
  # determinar clase mayoritaria (modo)
  mayoritaria <- df %>%
    summarise(m = names(sort(table(inclinacion_peligrosa), decreasing = TRUE))[1]) %>%
    pull(m) %>%
    as.integer()

  message("Clase mayoritaria detectada: ", mayoritaria)

  df %>%
    mutate(prediction_class = mayoritaria)
}

# ------------------------------------------------------------------
# (b) Aplicar al dataset de validación
# ------------------------------------------------------------------
validation_path <- "../../../data/arbolado-mza-dataset-test-20.csv"

val_df <- read.csv(validation_path, check.names = FALSE)
names(val_df) <- names(val_df) |> trimws() |> tolower()

if (!"inclinacion_peligrosa" %in% names(val_df)) {
  stop("No se encontró la columna 'inclinacion_peligrosa'.")
}

val_df <- val_df %>%
  mutate(inclinacion_peligrosa = as.integer(inclinacion_peligrosa))

# aplicar clasificador
val_scored <- val_df %>% biggerclass_classifier()

# ------------------------------------------------------------------
# Calcular TP, TN, FP, FN igual que en el ejercicio 4
# ------------------------------------------------------------------
resumen <- val_scored %>%
  summarise(
    TP = sum(inclinacion_peligrosa == 1 & prediction_class == 1),
    TN = sum(inclinacion_peligrosa == 0 & prediction_class == 0),
    FP = sum(inclinacion_peligrosa == 0 & prediction_class == 1),
    FN = sum(inclinacion_peligrosa == 1 & prediction_class == 0),
    n  = n()
  )

print(resumen)

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

