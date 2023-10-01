# Use a pipeline as a high-level helper
from transformers import pipeline

generator = pipeline("text-generation", model="openchat/openchat")
result = generator("""What comes after things?""")
print(result)
