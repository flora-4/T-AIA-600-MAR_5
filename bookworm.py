import subprocess,os,sys,json

try:
    import requests
except:
    subprocess.run([sys.executable,"-m","pip", "install","requests"])
    import requests

import cache as ch

bookDir = os.path.join(os.path.dirname(__file__),"books")
cacheDir = os.path.join(os.path.dirname(__file__),"cache")
try:
    cmd = sys.argv
    param = cmd[1]
    id = cmd[2]
except:
    param = None
    id = None

if not os.path.exists(bookDir):
    os.mkdir(bookDir)


site = "https://www.gutenberg.org/ebooks/results/"

# title = "Notes on the cathedral libraries of England"
title = ""
author = "Beriah Botfield"

params = "title="+title.replace(" ","+")+"&"+"author="+author.replace(" ","+")


def reserch(url):
    try:
        result = requests.get(url)
        if result.status_code == 200:
            return result.text
        else:
            return
    except:
        print("l'url n'est pas correct")
        exit()

def downloadBook(ResultResearch):
    if ResultResearch.isnumeric():
        if(os.path.exists(os.path.join(bookDir,ResultResearch+".txt"))):
            return
        print("recherche du livre à télécharger")
        result = reserch(f"https://www.gutenberg.org/cache/epub/{ResultResearch}/pg{ResultResearch}.txt")
        if not result:
            print ("aucun livre trouver avec l'id",ResultResearch)
            sys.exit()
        with open(os.path.join(bookDir,ResultResearch+".txt"),"w", encoding="utf-8") as f:
            f.write(result)
        print(f"le livre {ResultResearch} a été télécharché")
        return

    if "pgdbfiles" in ResultResearch:
        indexStart = ResultResearch.find('<table class="pgdbfiles">')
        indexEnd = ResultResearch.find('</table>')
        tableOfResult = ResultResearch[indexStart:indexEnd]
        arrayTable = tableOfResult.split("\n")
        for i in arrayTable:
            if i.startswith("<td>"):
                EBookNo = i[4:-5]
                if EBookNo.isnumeric():
                    if(os.path.exists(os.path.join(bookDir,EBookNo+".txt"))):
                        continue
                    with open(os.path.join(bookDir,EBookNo+".txt"),"w", encoding="utf-8") as f:
                        f.write(reserch(f"https://www.gutenberg.org/cache/epub/{EBookNo}/pg{EBookNo}.txt"))
                    print(EBookNo)
    else:
        print ("aucun livre trouver avec",ResultResearch)
        sys.exit()

def GetOnlyBook(bookid):
    pathBook = os.path.join(bookDir,bookid+".txt")
    with open(os.path.join(bookDir,bookid+".txt"),"r",encoding="utf-8") as f:
        contenu = f.read()
        indexStart = contenu.find('*** START OF THE PROJECT GUTENBERG EBOOK')
        indexEnd = contenu.find('*** END OF THE PROJECT GUTENBERG EBOOK')
        contenuTop = contenu[:indexStart]
        contenuMid = contenu[indexStart+3:indexEnd]
        contenuMid = contenuMid[contenuMid.find("***")+3:]
        contenuEnd = contenu[indexEnd+3:]
        contenuEnd = contenuEnd[contenuEnd.find("***")+3:]
        
        return [contenuTop,contenuMid,contenuEnd]

cliCommande = ["--lexdiv","--topics","--entities","--summarize","--similar"]

def cliExecute (param,bookid): 
    if not os.path.exists(os.path.join(bookDir,bookid+".txt")):
        downloadBook(bookid)
    if not os.path.exists(os.path.join(cacheDir,bookid+".json")):
        ch.createFile(bookid,GetOnlyBook(bookid))
    cache = ch.cacheGestion(bookid,param)
    if cache and param != "--card":
        return cache
    match param :
        case "--lexdiv":
            print("exécution de la commande pour avoir la richesse du livre")
            import lexdiv as ld
            return ch.cacheGestion(bookid,param,ld.lexdiv(GetOnlyBook(bookid)))
        case "--topics":
            print("exécution de la commande pour avoir les thèmes du livre")
            from topics import extract_topics
            return ch.cacheGestion(bookid,param,extract_topics(bookid))
        case "--entities":
            print("exécution de la commande pour avoir les entitées présentes dans le livre")
            from entities import extract_entities
            return ch.cacheGestion(bookid,param,extract_entities(bookid))
        case "--summarize":
            print("exécution de la commande pour avoir un résumer du livre")
            print("summarize pour "+bookid)
        case "--similar":
            print("exécution de la commande pour avoir des livre ressemblant au livre")
            print("similar pour "+bookid)
        case "--card":
            print("exécution de la commande pour avoir une carte sur le livre avec toutes les informations")
            for i in cliCommande:
                cliExecute(i,bookid)
            return ch.cacheGestion(bookid,param)

result = cliExecute(param,id)
if result:
    print(json.dumps(result, indent=4, ensure_ascii=False))

"https://www.gutenberg.org/cache/epub/78788/pg78788.txt"