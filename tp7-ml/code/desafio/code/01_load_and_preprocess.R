suppressPackageStartupMessages({
  library(tidyverse)
  library(lubridate)
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
code_models_dir <- file.path(script_dir, "models")
outputs_dir <- file.path(project_dir, "outputs")

source(file.path(script_dir, "00_utils.R"))

train_path <- normalizePath(
  file.path(project_dir, "..", "..", "data", "arbolado-mza-dataset-train-80.csv"),
  mustWork = FALSE
)
test_path <- normalizePath(
  file.path(
    project_dir,
    "..",
    "..",
    "data",
    "arbolado-publico-mendoza-2025",
    "arbolado-mza-dataset-test.csv",
    "arbolado-mza-dataset-test.csv"
  ),
  mustWork = FALSE
)

normalize_names <- function(nms) {
  nms %>%
    stringr::str_trim() %>%
    stringr::str_to_lower() %>%
    stringr::str_replace_all("[\\.\\s]+", "_")
}

message("Leyendo datasets desde: ", train_path, " y ", test_path)

train_raw <- readr::read_csv(train_path, show_col_types = FALSE) %>%
  set_names(normalize_names(names(.)))

test_raw <- readr::read_csv(test_path, show_col_types = FALSE) %>%
  set_names(normalize_names(names(.)))

id_col <- "id"
if (!id_col %in% names(test_raw)) {
  stop("No se encontró columna 'id' en el dataset de test.")
}

train_ids <- train_raw[[id_col]]
test_ids <- test_raw[[id_col]]

train_df <- train_raw %>% select(-all_of(id_col))
test_df <- test_raw %>% select(-all_of(id_col))

textual_to_drop <- intersect(c("nombre_seccion"), names(train_df))
if (length(textual_to_drop) > 0) {
  message("Eliminando columnas textuales largas: ", paste(textual_to_drop, collapse = ", "))
  train_df <- train_df %>% select(-all_of(textual_to_drop))
  test_df <- test_df %>% select(-all_of(textual_to_drop))
}

altura_mapping <- c(
  "Muy bajo (1 - 2 mts)" = 1.5,
  "Bajo (2 - 4 mts)" = 3,
  "Medio (4 - 8 mts)" = 6,
  "Alto (> 8 mts)" = 9
)

if ("altura" %in% names(train_df)) {
  train_df <- train_df %>%
    mutate(altura = dplyr::recode(altura, !!!altura_mapping, .default = NA_real_))
  test_df <- test_df %>%
    mutate(altura = dplyr::recode(altura, !!!altura_mapping, .default = NA_real_))
}

# Parseo de fechas.
parse_fecha <- function(x) {
  suppressWarnings(lubridate::parse_date_time(
    x,
    orders = c("dmy HMS", "dmy HM", "ymd HMS", "ymd HM", "dmy", "ymd")
  ))
}

if ("ultima_modificacion" %in% names(train_df)) {
  train_df <- train_df %>%
    mutate(ultima_modificacion = parse_fecha(ultima_modificacion))
  test_df <- test_df %>%
    mutate(ultima_modificacion = parse_fecha(ultima_modificacion))

  train_df <- train_df %>%
    mutate(
      ultima_modificacion = as.Date(ultima_modificacion),
      anio_modif = lubridate::year(ultima_modificacion),
      mes_modif = lubridate::month(ultima_modificacion)
    )
  test_df <- test_df %>%
    mutate(
      ultima_modificacion = as.Date(ultima_modificacion),
      anio_modif = lubridate::year(ultima_modificacion),
      mes_modif = lubridate::month(ultima_modificacion)
    )

  train_df <- train_df %>% select(-ultima_modificacion)
  test_df <- test_df %>% select(-ultima_modificacion)
}

# Tipos y imputaciones.
numeric_candidates <- c("altura", "circ_tronco_cm", "area_seccion", "lat", "long")
numeric_cols <- intersect(numeric_candidates, names(train_df))

train_df <- train_df %>%
  mutate(across(all_of(numeric_cols), ~suppressWarnings(as.numeric(.x))))

test_df <- test_df %>%
  mutate(across(all_of(numeric_cols), ~suppressWarnings(as.numeric(.x))))

numeric_medians <- purrr::map_dbl(numeric_cols, ~median(train_df[[.x]], na.rm = TRUE))

train_df <- train_df %>%
  mutate(across(all_of(numeric_cols), ~ifelse(is.na(.x), numeric_medians[cur_column()], .x)))

test_df <- test_df %>%
  mutate(across(all_of(numeric_cols), ~ifelse(is.na(.x), numeric_medians[cur_column()], .x)))

rare_threshold <- 20
if ("especie" %in% names(train_df)) {
  train_df <- train_df %>%
    mutate(
      especie = stringr::str_trim(especie),
      especie = if_else(is.na(especie) | especie == "", "desconocido", especie)
    )

  especie_mode <- train_df %>%
    count(especie, sort = TRUE) %>%
    slice_head(n = 1) %>%
    pull(especie)

  rare_levels <- train_df %>%
    count(especie, sort = TRUE) %>%
    filter(n < rare_threshold) %>%
    pull(especie)

  train_df <- train_df %>%
    mutate(
      especie = if_else(especie %in% rare_levels, "OTRA", especie),
      especie = forcats::as_factor(especie)
    )

  test_df <- test_df %>%
    mutate(
      especie = stringr::str_trim(especie),
      especie = if_else(is.na(especie) | especie == "", especie_mode, especie),
      especie = if_else(especie %in% rare_levels, "OTRA", especie),
      especie = if_else(especie %in% levels(train_df$especie), especie, "OTRA"),
      especie = factor(especie, levels = levels(train_df$especie))
    )

} else {
  warning("No se encontró columna 'especie'; los scripts posteriores asumían su presencia.")
  especie_mode <- NA_character_
  rare_levels <- character()
  rare_threshold <- NA_real_
}

if ("inclinacion_peligrosa" %in% names(train_df)) {
  train_df <- train_df %>%
    mutate(
      inclinacion_peligrosa = as.integer(inclinacion_peligrosa),
      inclinacion_peligrosa = tidyr::replace_na(inclinacion_peligrosa, 0L),
      inclinacion_peligrosa = factor(inclinacion_peligrosa, levels = c(0, 1))
    )
} else {
  stop("El dataset de entrenamiento debe contener 'inclinacion_peligrosa'.")
}

if ("seccion" %in% names(train_df)) {
  train_df <- train_df %>%
    mutate(
      seccion = as.integer(seccion),
      seccion_f = as.factor(seccion)
    )
  test_df <- test_df %>%
    mutate(
      seccion = as.integer(seccion),
      seccion_f = factor(seccion, levels = levels(train_df$seccion_f))
    )
}

if (all(c("altura", "circ_tronco_cm") %in% names(train_df))) {
  train_df <- train_df %>%
    mutate(altura_rel = altura / (circ_tronco_cm + 1))
  test_df <- test_df %>%
    mutate(altura_rel = altura / (circ_tronco_cm + 1))
}

if (all(c("circ_tronco_cm", "area_seccion") %in% names(train_df))) {
  train_df <- train_df %>%
    mutate(densidad_seccion = circ_tronco_cm / (area_seccion + 1))
  test_df <- test_df %>%
    mutate(densidad_seccion = circ_tronco_cm / (area_seccion + 1))
}

train_clean <- train_df
test_clean <- test_df

preproc_params <- list(
  numeric_medians = numeric_medians,
  especie_mode = especie_mode,
  rare_levels = rare_levels,
  rare_threshold = rare_threshold,
  test_ids = test_ids,
  generated_at = Sys.time()
)

train_clean_path <- file.path(outputs_dir, "train_clean.rds")
test_clean_path <- file.path(outputs_dir, "test_clean.rds")
preproc_params_path <- file.path(outputs_dir, "preproc_params.rds")

ensure_parent_dir(train_clean_path)
ensure_parent_dir(test_clean_path)
ensure_parent_dir(preproc_params_path)

saveRDS(train_clean, train_clean_path)
saveRDS(test_clean, test_clean_path)
saveRDS(preproc_params, preproc_params_path)

message("Preprocesamiento finalizado. Archivos guardados en ", outputs_dir, ".")
