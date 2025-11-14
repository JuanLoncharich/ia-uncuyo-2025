#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(rpart)
  library(dplyr)
})

# -------------------------------------------------
# (a) crear folds
# -------------------------------------------------
create_folds <- function(df, k = 10) {
  n <- nrow(df)
  idx <- sample.int(n)               # mezcla aleatoria
  folds <- split(idx, cut(seq_along(idx), breaks = k, labels = FALSE))
  names(folds) <- paste0("Fold", seq_len(k))
  folds
}

# -------------------------------------------------
# helpers de métricas
# -------------------------------------------------
compute_metrics <- function(y_true, y_pred) {
  TP <- sum(y_true == 1 & y_pred == 1)
  TN <- sum(y_true == 0 & y_pred == 0)
  FP <- sum(y_true == 0 & y_pred == 1)
  FN <- sum(y_true == 1 & y_pred == 0)

  acc  <- (TP + TN) / (TP + TN + FP + FN)
  prec <- ifelse((TP + FP) == 0, NA, TP / (TP + FP))
  sens <- ifelse((TP + FN) == 0, NA, TP / (TP + FN))  # recall
  spec <- ifelse((TN + FP) == 0, NA, TN / (TN + FP))

  data.frame(
    accuracy    = acc,
    precision   = prec,
    sensitivity = sens,
    specificity = spec,
    TP = TP, TN = TN, FP = FP, FN = FN
  )
}

# -------------------------------------------------
# (b) cross-validation con rpart
# -------------------------------------------------
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

# -------------------------------------------------
# MAIN
# -------------------------------------------------
data_path <- "../../../data/arbolado-mza-dataset-train-80.csv"
df <- read.csv(data_path, check.names = FALSE)

set.seed(123)
res <- cross_validation(df, k = 10)

cat("=== Métricas por fold ===\n")
print(res$per_fold)

cat("\n=== Media y desvío (k=10) ===\n")
print(res$summary)

