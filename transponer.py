import pandas as pd

# Leer el archivo CSV
df = pd.read_csv('energia_generada_1.csv', header=None)

# Transponer el DataFrame
df_transposed = df.T

# Imprimir el DataFrame transpuesto
print(df_transposed)

# Guardar el DataFrame transpuesto en un nuevo archivo CSV
df_transposed.to_csv('energia_generada_1_transpuesto.csv', index=False, header=False)
