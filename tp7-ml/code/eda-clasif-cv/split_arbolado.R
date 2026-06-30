# split_arbolado.R
set.seed(42)

# archivo original de kaggle (el que SÍ tiene inclinacion_peligrosa)
df <- read.csv("data/arbolado-publico-mendoza-2025/arbolado-mza-dataset.csv/arbolado-mza-dataset.csv")

n <- nrow(df)
idx <- sample.int(n)

train_size <- floor(0.8 * n)

train_idx <- idx[1:train_size]
test_idx  <- idx[(train_size+1):n]

train_df <- df[train_idx, ]
test_df  <- df[test_idx, ]

# guardamos al lado, en data/ ya plano
write.csv(train_df, "data/arbolado-mza-dataset-train-80.csv", row.names = FALSE)
write.csv(test_df,  "data/arbolado-mza-dataset-test-20.csv",  row.names = FALSE)

cat("Filas totales:", n, "\n")
cat("Train 80%:", nrow(train_df), "\n")
cat("Test 20%:", nrow(test_df), "\n")
