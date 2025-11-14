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

source(file.path(script_dir, "00_utils.R"))

train_clean_path <- file.path(outputs_dir, "train_clean.rds")
if (!file.exists(train_clean_path)) {
  stop("No se encontró ", train_clean_path, ". Ejecutar 01_load_and_preprocess.R primero.")
}

train_clean <- readRDS(train_clean_path)

k <- 10
set.seed(123)

n <- nrow(train_clean)
fold_ids <- sample(rep(1:k, length.out = n))

target_var <- "inclinacion_peligrosa"

predictors_base <- c("altura", "circ_tronco_cm", "lat", "long", "seccion", "especie", "altura_rel", "densidad_seccion")
predictors_base <- intersect(predictors_base, names(train_clean))
formula_base <- as.formula(paste(target_var, "~", paste(predictors_base, collapse = " + ")))

cv_results <- purrr::map_dfr(
  seq_len(k),
  function(fold) {
    train_fold <- train_clean[fold_ids != fold, ]
    val_fold <- train_clean[fold_ids == fold, ]

    model <- rpart(
      formula_base,
      data = train_fold,
      method = "class",
      control = rpart.control(cp = 0.001, minsplit = 20)
    )

    prob <- tryCatch(
      predict(model, newdata = val_fold, type = "prob")[, "1"],
      error = function(e) {
        warning("Fold ", fold, ": no se pudo obtener predict(type = 'prob'). Se retorna NA. ", conditionMessage(e))
        rep(NA_real_, nrow(val_fold))
      }
    )

    metrics <- compute_classification_metrics(val_fold[[target_var]], prob)
    tibble(
      fold = fold,
      auc = metrics$auc,
      accuracy = metrics$accuracy,
      sensitivity = metrics$recall,
      specificity = metrics$specificity,
      precision = metrics$precision
    )
  }
)

cv_summary <- tibble(
  metric = c("auc", "accuracy", "sensitivity", "specificity", "precision"),
  mean = c(
    mean(cv_results$auc, na.rm = TRUE),
    mean(cv_results$accuracy, na.rm = TRUE),
    mean(cv_results$sensitivity, na.rm = TRUE),
    mean(cv_results$specificity, na.rm = TRUE),
    mean(cv_results$precision, na.rm = TRUE)
  ),
  sd = c(
    sd(cv_results$auc, na.rm = TRUE),
    sd(cv_results$accuracy, na.rm = TRUE),
    sd(cv_results$sensitivity, na.rm = TRUE),
    sd(cv_results$specificity, na.rm = TRUE),
    sd(cv_results$precision, na.rm = TRUE)
  )
)

ensure_parent_dir(file.path(metrics_dir, "cv_10fold.csv"))

readr::write_csv(cv_results, file.path(metrics_dir, "cv_10fold.csv"))
readr::write_csv(cv_summary, file.path(metrics_dir, "cv_10fold_summary.csv"))

message("Resultados de validación cruzada guardados en ", metrics_dir, ".")
# estos resultados entran en la sección ii) del reporte.
