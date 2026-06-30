suppressPackageStartupMessages({
  library(tidyverse)
  library(ggplot2)
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
eda_dir <- file.path(outputs_dir, "eda")

source(file.path(script_dir, "00_utils.R"))

train_clean_path <- file.path(outputs_dir, "train_clean.rds")

if (!file.exists(train_clean_path)) {
  stop("No se encontró ", train_clean_path, ". Ejecutar 01_load_and_preprocess.R primero.")
}

train_clean <- readRDS(train_clean_path)

message("Dimensiones train_clean: ", nrow(train_clean), " filas, ", ncol(train_clean), " columnas.")

message("Estructura general:")
capture.output(str(train_clean)) %>% writeLines()

message("Resumen numérico:")
capture.output(summary(train_clean)) %>% writeLines()

if ("inclinacion_peligrosa" %in% names(train_clean)) {
  clase_tabla <- table(train_clean$inclinacion_peligrosa)
  clase_prop <- prop.table(clase_tabla)
  message("Distribución de inclinacion_peligrosa:")
  print(clase_tabla)
  print(round(100 * clase_prop, 2))
}
# esto alimenta la sección i) del reporte.

ensure_parent_dir(file.path(eda_dir, "placeholder.txt"))

plot_numeric <- function(data, column, outfile) {
  if (!column %in% names(data)) {
    warning("No se encontró columna ", column, " para el histograma.")
    return(invisible(NULL))
  }

  p <- ggplot(data, aes(x = .data[[column]])) +
    geom_histogram(fill = "#2a9d8f", color = "#264653", bins = 30, alpha = 0.8) +
    labs(
      title = paste("Distribución de", column),
      x = column,
      y = "Frecuencia"
    ) +
    theme_minimal()

  ggsave(outfile, plot = p, width = 6, height = 4, dpi = 120)
}

plot_numeric(train_clean, "circ_tronco_cm", file.path(eda_dir, "hist_circ_tronco_cm.png"))
plot_numeric(train_clean, "altura", file.path(eda_dir, "hist_altura.png"))
