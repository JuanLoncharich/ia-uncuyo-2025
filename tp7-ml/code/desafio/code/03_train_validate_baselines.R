suppressPackageStartupMessages({
  library(tidyverse)
  library(rpart)
  library(pROC)
})

get_script_path <- function() {
  cmd_args <- commandArgs(trailingOnly = FALSE)
  file_arg_name <- "--file="
  script_path <- cmd_args[grep(file_arg_name, cmd_args)]
  if (length(script_path) > 0) {
    return(normalizePath(sub(file_arg_name, "", script_path)))
  }
  if (!is.null(sys.frames()[[1]]$ofile)) {
    return(normalizePath(sys.frames()[[1]]$ofile))
  }
  normalizePath(".", mustWork = FALSE)
}

script_path <- get_script_path()
script_dir <- dirname(script_path)
project_dir <- normalizePath(file.path(script_dir, ".."), mustWork = FALSE)
outputs_dir <- file.path(project_dir, "outputs")
metrics_dir <- file.path(outputs_dir, "metrics")
models_dir <- file.path(script_dir, "models")

dir.create(models_dir, recursive = TRUE, showWarnings = FALSE)

source(file.path(script_dir, "00_utils.R"))

train_clean_path <- file.path(outputs_dir, "train_clean.rds")
if (!file.exists(train_clean_path)) {
  stop("No se encontró ", train_clean_path, ". Ejecutar 01_load_and_preprocess.R primero.")
}

train_clean <- readRDS(train_clean_path)

set.seed(123)

target_var <- "inclinacion_peligrosa"

if (!target_var %in% names(train_clean)) {
  stop("El dataset limpio no contiene la variable objetivo: ", target_var)
}

n <- nrow(train_clean)
train_idx <- sample(seq_len(n), size = floor(0.8 * n))

train_part <- train_clean[train_idx, ]
val_part <- train_clean[-train_idx, ]

metrics_path <- file.path(metrics_dir, "val_results.csv")

predictors_base <- c("altura", "circ_tronco_cm", "lat", "long", "seccion", "especie")
predictors_base <- intersect(predictors_base, names(train_part))
formula_base <- as.formula(paste(target_var, "~", paste(predictors_base, collapse = " + ")))

message("Entrenando baseline rpart (default).")
tree_model_base <- rpart(
  formula_base,
  data = train_part,
  method = "class"
)

prob_base <- predict(tree_model_base, newdata = val_part, type = "prob")[, "1"]
metrics_base <- compute_classification_metrics(val_part[[target_var]], prob_base)
write_metrics_row(metrics_base, "rpart_baseline", metrics_path)

message("Entrenando baseline rpart (control).")
tree_model_tuned <- rpart(
  formula_base,
  data = train_part,
  method = "class",
  control = rpart.control(cp = 0.001, minsplit = 20)
)

prob_tuned <- predict(tree_model_tuned, newdata = val_part, type = "prob")[, "1"]
metrics_tuned <- compute_classification_metrics(val_part[[target_var]], prob_tuned)
write_metrics_row(metrics_tuned, "rpart_control", metrics_path)

if (requireNamespace("randomForest", quietly = TRUE)) {
  message("Entrenando baseline randomForest.")
  library(randomForest)
  rf_predictors <- c(
    "altura", "circ_tronco_cm", "lat", "long",
    "anio_modif", "mes_modif", "altura_rel", "densidad_seccion", "especie"
  )
  rf_predictors <- intersect(rf_predictors, names(train_part))
  rf_formula <- as.formula(paste(target_var, "~", paste(rf_predictors, collapse = " + ")))
  rf_model <- randomForest::randomForest(
    rf_formula,
    data = train_part,
    ntree = 300,
    mtry = max(floor(sqrt(length(rf_predictors))), 2),
    importance = TRUE
  )
  prob_rf <- predict(rf_model, newdata = val_part, type = "prob")[, "1"]
  metrics_rf <- compute_classification_metrics(val_part[[target_var]], prob_rf)
  write_metrics_row(metrics_rf, "random_forest", metrics_path)
  saveRDS(rf_model, file.path(models_dir, "random_forest_80_20.rds"))
} else {
  message("randomForest no está instalado. Saltando baseline random forest.")
}

message("Resultados guardados en ", metrics_path)
