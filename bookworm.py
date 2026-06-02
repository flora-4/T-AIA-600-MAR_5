import subprocess,os,sys

try:
    import requests
except:
    subprocess.run([sys.executable,"-m","pip", "install","requests"])
    import requests

import lexdiv as ld

bookDir = os.path.join(os.path.dirname(__file__),"books")
cmd = sys.argv
param = cmd[1]
id = cmd[2]

print(param,id)
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
    downloadBook(id)
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



# result = reserch(site+"?"+params)
# downloadBook(id)

# GetOnlyBook(id)

def cliExecute (param,id): 
    match param :
        case "--lexdiv":
            print(ld.lexdiv(GetOnlyBook(id)))
        case "--topics":
            print("topics pour "+id)
        case "--entities":
            print("entities pour "+id)
        case "--summarize":
            print("summarize pour "+id)
        case "--similar":
            print("similar pour "+id)
        case "--card":
            print("similar pour "+id)
        case _:
            print("commande non trouver")

cliExecute(param,id)

"https://www.gutenberg.org/cache/epub/78788/pg78788.txt"