# code/analizar_arbolado_mza_train.R
# Requisitos: tidyverse, broom
suppressPackageStartupMessages({
  library(tidyverse)
  library(scales)
  library(broom)
})

# -----------------------
# Rutas y parámetros
# -----------------------
CSV_PATH <- "data/arbolado-mza-dataset-train-80.csv"
OUT_DIR  <- "outputs"
dir.create(OUT_DIR, showWarnings = FALSE, recursive = TRUE)

# -----------------------
# Leer dataset
# -----------------------
df <- read.csv(CSV_PATH, check.names = FALSE)

# Normalizar nombres (por si acaso)
names(df) <- names(df) |>
  stringr::str_trim() |>
  tolower() |>
  stringr::str_replace_all("\\s+", "_") |>
  stringr::str_replace_all("\\.+", "_")

if (!"inclinacion_peligrosa" %in% names(df)) {
  stop("No se encontró la columna 'inclinacion_peligrosa' en el archivo de entrenamiento.")
}

df <- df %>%
  filter(!is.na(inclinacion_peligrosa)) %>%
  mutate(inclinacion_peligrosa = as.integer(inclinacion_peligrosa))

# Función para IC
prop_ci_row <- function(x, n) {
  tt <- suppressWarnings(prop.test(x, n))
  c(tt$conf.int[1], tt$conf.int[2])
}

save_plot <- function(p, path, w=8, h=5) {
  ggsave(path, p, width = w, height = h, dpi = 150)
  message("Guardado: ", path)
}

# ============================================================
# (a) Distribución de la clase
# ============================================================
dist_tbl <- df %>%
  count(inclinacion_peligrosa, name = "n") %>%
  mutate(p = n / sum(n),
         clase = factor(inclinacion_peligrosa,
                        levels = c(0,1),
                        labels = c("0 = No peligrosa", "1 = Peligrosa")))

cat("=== (a) Distribución de la clase ===\n")
print(dist_tbl %>% mutate(p = percent(p)))
cat("\n")

p_a <- ggplot(dist_tbl, aes(x = clase, y = n, fill = clase)) +
  geom_col(show.legend = FALSE) +
  geom_text(aes(label = paste0(n, " (", percent(p, 0.1), ")")), vjust = -0.3) +
  labs(title = "Distribución de la clase: inclinacion_peligrosa",
       x = "Clase", y = "Cantidad de árboles") +
  theme_minimal()

save_plot(p_a, file.path(OUT_DIR, "a_distribucion_clase.png"), w=6, h=4)

# ============================================================
# (b) Secciones más peligrosas
# ============================================================
if ("seccion" %in% names(df)) {
  MIN_N_SECCION <- 50
  
  by_sec <- df %>%
    group_by(seccion) %>%
    summarise(
      n = n(),
      x = sum(inclinacion_peligrosa == 1),
      rate = x / n,
      .groups = "drop"
    ) %>%
    filter(n >= MIN_N_SECCION) %>%
    mutate(ci = purrr::map2(x, n, prop_ci_row),
           ci_low = purrr::map_dbl(ci, 1),
           ci_high = purrr::map_dbl(ci, 2)) %>%
    arrange(desc(rate))
  
  cat("=== (b) Tasa de peligrosidad por sección ===\n")
  print(head(by_sec, 10) %>% mutate(rate = percent(rate, 0.1)))
  cat("\n")
  
  p_b <- ggplot(by_sec, aes(x = reorder(as.factor(seccion), rate), y = rate)) +
    geom_col(fill = "#0072B2") +
    geom_errorbar(aes(ymin = ci_low, ymax = ci_high), width = 0.2) +
    geom_text(aes(label = paste0(percent(rate, 0.1), "\n(n=", n, ")")),
              vjust = -0.3, size = 3) +
    coord_flip() +
    labs(title = "Tasa de inclinación peligrosa por sección (n ≥ 50)",
         x = "Sección", y = "Tasa (± IC 95%)") +
    theme_minimal()
  
  save_plot(p_b, file.path(OUT_DIR, "b_seccion_tasa.png"), w=8, h=7)
}

# ============================================================
# (c) Especies más peligrosas
# ============================================================
if ("especie" %in% names(df)) {
  MIN_N_ESPECIE <- 50
  TOP_N <- 15
  
  by_esp <- df %>%
    group_by(especie) %>%
    summarise(
      n = n(),
      x = sum(inclinacion_peligrosa == 1),
      rate = x / n,
      .groups = "drop"
    ) %>%
    filter(n >= MIN_N_ESPECIE) %>%
    mutate(ci = purrr::map2(x, n, prop_ci_row),
           ci_low = purrr::map_dbl(ci, 1),
           ci_high = purrr::map_dbl(ci, 2)) %>%
    arrange(desc(rate)) %>%
    slice_head(n = TOP_N)
  
  cat("=== (c) Especies con mayor tasa de inclinación peligrosa ===\n")
  print(by_esp %>% mutate(rate = percent(rate, 0.1)))
  cat("\n")
  
  p_c <- ggplot(by_esp, aes(x = reorder(as.factor(especie), rate), y = rate)) +
    geom_col(fill = "#009E73") +
    geom_errorbar(aes(ymin = ci_low, ymax = ci_high), width = 0.2) +
    geom_text(aes(label = paste0(percent(rate, 0.1), "\n(n=", n, ")")),
              vjust = -0.3, size = 3) +
    coord_flip() +
    labs(title = "Top 15 especies con mayor tasa de inclinación peligrosa",
         x = "Especie", y = "Tasa (± IC 95%)") +
    theme_minimal()
  
  save_plot(p_c, file.path(OUT_DIR, "c_especie_tasa_top.png"), w=9, h=8)
}

cat("✔ Listo. Gráficos en 'outputs/'.\n")
