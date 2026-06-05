import subprocess,os,sys,json
from topics import extract_topics
from entities import extract_entities

try:
    import requests
except:
    subprocess.run([sys.executable,"-m","pip", "install","requests"])
    import requests

import cache as ch
import lexdiv as ld

bookDir = os.path.join(os.path.dirname(__file__),"books")
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
        result = reserch(f"https://www.gutenberg.org/cache/epub/{ResultResearch}/pg{ResultResearch}.txt")
        if not result:
            return
        with open(os.path.join(bookDir,ResultResearch+".txt"),"w", encoding="utf-8") as f:
            f.write(result)
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
        print("aucun livre trouver avec l'élément donnée")

def GetOnlyBook(bookid):
    downloadBook(bookid)
    if not os.path.exists(os.path.join(bookDir,bookid+".txt")):
        print("id du livre non trouver")
        return
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
    if os.path.exists(os.path.join(bookDir,bookid+".txt")):
        ch.createFile(bookid,GetOnlyBook(bookid))
    cache = ch.cacheGestion(bookid,param)
    if cache:
        return cache
    match param :
        case "--lexdiv":
            return ch.cacheGestion(bookid,param,ld.lexdiv(GetOnlyBook(bookid)))
        case "--topics":
            return ch.cacheGestion(bookid,param,extract_topics(bookid))
        case "--entities":
            return ch.cacheGestion(bookid,param,extract_entities(bookid))
        case "--summarize":
            print("summarize pour "+bookid)
        case "--similar":
            print("similar pour "+bookid)
        case "--card":
            for i in cliCommande:
                cliExecute(i,bookid)
            print("card pour "+bookid)
            return ch.cacheGestion(bookid,param)

result = cliExecute(param,id)
if result:
    print(json.dumps(result, indent=4, ensure_ascii=False))

"https://www.gutenberg.org/cache/epub/78788/pg78788.txt"