# split_arbolado_dataset.py
import pandas as pd
from sklearn.model_selection import train_test_split

# Ruta al archivo original
DATA_PATH = "arbolado-mza-dataset-descripcion.csv"

# Cargar el dataset
df = pd.read_csv(DATA_PATH)

# Verificar carga
print(f"Dataset completo: {df.shape[0]} filas, {df.shape[1]} columnas")

# Dividir 80% train / 20% test de forma aleatoria
train_df, test_df = train_test_split(df, test_size=0.2, random_state=42, shuffle=True)

# Guardar los subconjuntos
train_df.to_csv("arbolado-mendoza-dataset-train.csv", index=False)
test_df.to_csv("arbolado-mendoza-dataset-validation.csv", index=False)

print(f"Entrenamiento: {train_df.shape[0]} filas")
print(f"Evaluación: {test_df.shape[0]} filas")
print("✅ Archivos generados: arbolado-mza-train.csv y arbolado-mza-test.csv")

