suppressPackageStartupMessages({
  library(tidyverse)
  library(rpart)
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
models_dir <- file.path(script_dir, "models")

dir.create(models_dir, recursive = TRUE, showWarnings = FALSE)

source(file.path(script_dir, "00_utils.R"))

train_clean_path <- file.path(outputs_dir, "train_clean.rds")
test_clean_path <- file.path(outputs_dir, "test_clean.rds")
preproc_params_path <- file.path(outputs_dir, "preproc_params.rds")

missing_files <- c(train_clean_path, test_clean_path, preproc_params_path) %>%
  purrr::keep(~!file.exists(.x))

if (length(missing_files) > 0) {
  stop("Faltan archivos previos: ", paste(missing_files, collapse = ", "), ". Ejecutar scripts anteriores.")
}

train_clean <- readRDS(train_clean_path)
test_clean <- readRDS(test_clean_path)
preproc_params <- readRDS(preproc_params_path)

if (is.null(preproc_params$test_ids)) {
  stop("preproc_params debe contener test_ids para armar el envío.")
}

target_var <- "inclinacion_peligrosa"

predictors_final <- c(
  "altura", "circ_tronco_cm", "lat", "long",
  "seccion", "especie", "altura_rel", "densidad_seccion",
  "anio_modif", "mes_modif", "seccion_f"
)

predictors_final <- intersect(predictors_final, names(train_clean))
formula_final <- as.formula(paste(target_var, "~", paste(predictors_final, collapse = " + ")))

message("Entrenando modelo final (rpart con control).")
final_model <- rpart(
  formula_final,
  data = train_clean,
  method = "class",
  control = rpart.control(cp = 0.001, minsplit = 20)
)


prob_test <- predict(final_model, newdata = test_clean, type = "prob")[, "1"]

submission <- tibble(
  id = preproc_params$test_ids,
  inclinacion_peligrosa = prob_test
)

if (nrow(submission) != nrow(test_clean)) {
  warning("Cantidad de filas de submission y test_clean no coincide.")
}

submission_path <- file.path(outputs_dir, "submissions", "arbolado-envio-baseline.csv")
ensure_parent_dir(submission_path)
readr::write_csv(submission, submission_path)

saveRDS(final_model, file.path(models_dir, "rpart_final_model.rds"))

message("Archivo de envío generado: ", submission_path)
