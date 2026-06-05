import json,os,sys
cache_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)),"cache")
if not os.path.exists(cache_directory):
    os.mkdir(cache_directory)

def openJson(path):
    with open(path,"r",encoding='utf-8') as f:
        data = json.load(f)
    return data

def makeInCache(id,param,value):
    path_file = os.path.join(cache_directory,f"{id}.json")
    if not os.path.exists(path_file):
       print("fichier cache manquant, utiliser la fonction createFile() pour crée automatiquement le fichier du cache")
       sys.exit()
    data = openJson(path_file)
    data[param]=value
    with open (path_file,"w",encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    

def getFromCache(id,param):
    path_file = os.path.join(cache_directory,f"{id}.json")
    if not os.path.exists(path_file):
        return
    
    data = openJson(path_file)
    if param in data:
        return data[param]
    elif param == "card":
        return data
    else:
        return

def cacheGestion(id,param,value=None):
    if value:
        makeInCache(id,param,value)
        cache = getFromCache(id,param)
        return cache

    cache = getFromCache(id,param)
    if cache:
        return cache
    
    return

def createFile(id,bookStart):
    print(bookStart)
    path_file = os.path.join(cache_directory,f"{id}.json")
    if not os.path.exists(path_file):
        with open (path_file,"w",encoding='utf-8') as f:
            json.dump({"info":{"id":id,"authors":"","bookshelves":""}}, f, indent=2, ensure_ascii=False)