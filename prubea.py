import json

media = {"peliculas":["Batman","Encanto"], "series": ["Avatar","Euphoria"]}


json_object = json.dumps(media, indent = len(media))
  
# Writing to sample.json
with open("media.json", "w") as outfile:
    outfile.write(json_object)

f = open ('media.json', "r")
data = json.loads(f.read())

print(data['peliculas'])

peli = ["hola","chao"]


print()