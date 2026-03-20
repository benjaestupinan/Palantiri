from gliner2 import GLiNER2

# Load model once, use everywhere
extractor = GLiNER2.from_pretrained("fastino/gliner2-base-v1")

# Extract entities in one line
text = "Pon master of puppets"
result = extractor.extract_entities(text, ["deviceID", "trackID"])

print(result)
# {'entities': {'company': ['Apple'], 'person': ['Tim Cook'], 'product': ['iPhone 15'], 'location': ['Cupertino']}}
