# code/ej3_circ_tronco_cm.R
suppressPackageStartupMessages({
  library(tidyverse)
  library(scales)
})

# Ruta del dataset de entrenamiento
CSV_PATH <- "../../../data/arbolado-mza-dataset-train-80.csv"
OUT_DIR  <- "outputs"
dir.create(OUT_DIR, showWarnings = FALSE, recursive = TRUE)

# -----------------------------
# Leer y preparar datos
# -----------------------------
df <- read.csv(CSV_PATH, check.names = FALSE)
names(df) <- names(df) |>
  stringr::str_trim() |>
  tolower() |>
  stringr::str_replace_all("\\s+", "_") |>
  stringr::str_replace_all("\\.+", "_")

if (!"circ_tronco_cm" %in% names(df))
  stop("No se encontró la columna 'circ_tronco_cm'.")

df <- df %>%
  filter(!is.na(circ_tronco_cm), circ_tronco_cm > 0)

# -----------------------------
# (a) Histograma general
# -----------------------------
bins_list <- c(10, 20, 40)

for (b in bins_list) {
  p <- ggplot(df, aes(x = circ_tronco_cm)) +
    geom_histogram(bins = b, fill = "#0072B2", color = "white", alpha = 0.8) +
    labs(title = paste("Histograma de circ_tronco_cm (bins =", b, ")"),
         x = "Circunferencia del tronco (cm)",
         y = "Frecuencia") +
    theme_minimal()
  ggsave(file.path(OUT_DIR, paste0("3a_hist_circ_tronco_", b, "bins.png")), p, width = 7, height = 5)
}

message("✅ (a) Histogramas guardados en 'outputs/' con 10, 20 y 40 bins.")

# -----------------------------
# (b) Histograma por clase
# -----------------------------
if ("inclinacion_peligrosa" %in% names(df)) {
  df <- df %>%
    mutate(inclinacion_peligrosa = as.factor(inclinacion_peligrosa))
  
  p_b <- ggplot(df, aes(x = circ_tronco_cm, fill = inclinacion_peligrosa)) +
    geom_histogram(position = "identity", alpha = 0.5, bins = 30, color = "white") +
    labs(title = "Histograma de circ_tronco_cm separado por clase",
         x = "Circunferencia del tronco (cm)",
         y = "Frecuencia",
         fill = "Inclinación peligrosa") +
    theme_minimal()
  ggsave(file.path(OUT_DIR, "3b_hist_circ_tronco_por_clase.png"), p_b, width = 7, height = 5)
  message("✅ (b) Histograma por clase guardado.")
} else {
  warning("No se encontró la columna 'inclinacion_peligrosa'.")
}

# -----------------------------
# (c) Crear variable categórica circ_tronco_cm_cat
# -----------------------------
# Vamos a usar cuantiles (25%, 50%, 75%) como cortes
q <- quantile(df$circ_tronco_cm, probs = c(0.25, 0.5, 0.75))

cat("Cuantiles usados para los cortes:\n")
print(q)

df <- df %>%
  mutate(
    circ_tronco_cm_cat = cut(
      circ_tronco_cm,
      breaks = c(-Inf, q[1], q[2], q[3], Inf),
      labels = c("bajo", "medio", "alto", "muy_alto"),
      right = TRUE
    )
  )

# Guardar nuevo dataframe
OUT_CSV <- "../../../data/arbolado-mza-dataset-circ_tronco_cm-train.csv"
write.csv(df, OUT_CSV, row.names = FALSE)

message("✅ (c) Nueva variable 'circ_tronco_cm_cat' creada y guardada en:")
message(OUT_CSV)

# También podemos verificar distribución de categorías
cat("\nDistribución de circ_tronco_cm_cat:\n")
print(table(df$circ_tronco_cm_cat))

