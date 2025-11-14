# Helper functions for TP7 Parte II pipeline.

suppressPackageStartupMessages({
  library(tidyverse)
  library(pROC)
})

ensure_parent_dir <- function(path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
}

compute_classification_metrics <- function(truth, prob, positive = "1", threshold = 0.5) {
  truth_factor <- as.factor(truth)
  if (length(levels(truth_factor)) != 2) {
    stop("compute_classification_metrics() currently supports binary outcomes.")
  }

  if (!positive %in% levels(truth_factor)) {
    stop("Positive level ", positive, " not found in truth levels.")
  }

  negative <- setdiff(levels(truth_factor), positive)
  pred_factor <- factor(
    ifelse(prob >= threshold, positive, negative),
    levels = levels(truth_factor)
  )

  tp <- sum(pred_factor == positive & truth_factor == positive)
  tn <- sum(pred_factor == negative & truth_factor == negative)
  fp <- sum(pred_factor == positive & truth_factor == negative)
  fn <- sum(pred_factor == negative & truth_factor == positive)

  accuracy <- (tp + tn) / length(truth_factor)
  precision <- ifelse((tp + fp) > 0, tp / (tp + fp), NA_real_)
  recall <- ifelse((tp + fn) > 0, tp / (tp + fn), NA_real_)
  specificity <- ifelse((tn + fp) > 0, tn / (tn + fp), NA_real_)

  auc <- NA_real_
  roc_obj <- tryCatch(
    pROC::roc(truth_factor, prob, levels = rev(levels(truth_factor)), direction = "<"),
    error = function(e) NULL,
    warning = function(w) NULL
  )
  if (!is.null(roc_obj)) {
    auc <- as.numeric(pROC::auc(roc_obj))
  }

  tibble(
    accuracy = accuracy,
    precision = precision,
    recall = recall,
    specificity = specificity,
    auc = auc
  )
}

write_metrics_row <- function(df, model_name, outfile) {
  df_wide <- df %>%
    mutate(
      modelo = model_name,
      fecha = format(Sys.time(), "%Y-%m-%d %H:%M:%S")
    ) %>%
    relocate(modelo, auc, accuracy, precision, recall, specificity, fecha)

  ensure_parent_dir(outfile)

  if (file.exists(outfile)) {
    readr::write_csv(df_wide, outfile, append = TRUE)
  } else {
    readr::write_csv(df_wide, outfile)
  }
}

