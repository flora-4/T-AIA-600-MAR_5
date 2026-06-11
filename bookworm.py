import subprocess,os,re,sys,json

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

def clean_text(text):
    """
    Nettoie le texte pour faciliter les traitements NLP.

    NLP signifie Natural Language Processing :
    ce sont les traitements automatiques du langage.
    """

    # Supprime les retours chariot Windows.
    text = text.replace('\r', '')

    # Supprime les petits textes entre crochets.
    # Exemple : [Illustration]
    text = re.sub(r'\[[^\]]{0,80}\]', ' ', text)

    # Supprime certaines lignes qui sont des titres de chapitres ou de parties.
    text = re.sub(
        r'(?m)^[ \t]*(CHAPTER|Chapter|BOOK|PART|SECTION|ADVENTURE)\s+[\w\-\.]+[^\n]{0,60}$',
        '',
        text
    )

    # Supprime les chiffres romains seuls.
    # Exemple : I, II, III, IV...
    text = re.sub(r'(?m)^\s*[IVXLCDM]{1,6}\.?\s*$', '', text)

    # Remplace les guillemets typographiques par des espaces ou apostrophes simples.
    text = text.replace('\u201c', ' ').replace('\u201d', ' ')
    text = text.replace('\u2018', ' ').replace('\u2019', "'")

    # Supprime les underscores utilisés par Gutenberg pour l'italique.
    text = text.replace('_', ' ')

    # Remplace plusieurs espaces par un seul espace.
    text = re.sub(r' {2,}', ' ', text)

    # Réduit les grands blocs de lignes vides.
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Retourne le texte final sans espaces inutiles au début et à la fin.
    return text.strip()


def extract_body(text):
    """
    Extrait uniquement le vrai contenu du livre.

    Un fichier Gutenberg contient souvent :
    - un début avec des informations techniques et légales ;
    - le texte du livre ;
    - une fin avec des mentions légales.

    Cette fonction retire ce qui n'est pas le livre.
    """

    # On cherche le marqueur de début du livre.
    # La regex accepte "THE" ou "THIS" car Gutenberg varie selon les fichiers.
    match_start = re.search(
        r'\*{3}\s*START OF (THE|THIS) PROJECT GUTENBERG[^\n]*\n',
        text
    )

    # On cherche le marqueur de fin du livre.
    match_end = re.search(
        r'\*{3}\s*END OF (THE|THIS) PROJECT GUTENBERG',
        text
    )

    # Si on trouve un début et une fin, on garde seulement ce qui est entre les deux.
    if match_start and match_end:
        body = text[match_start.end():match_end.start()]

    # Sinon, on applique des solutions de secours.
    else:
        # Si on trouve seulement le début, on garde tout ce qui vient après.
        if match_start:
            body = text[match_start.end():]

        # Si aucun marqueur Gutenberg n'est trouvé, on essaye quand même de récupérer le livre.
        else:
            # Par défaut, on garde tout le texte.
            body = text

            # On cherche des marqueurs classiques de début de livre.
            for marker in ['CHAPTER I', 'Chapter I', 'PART ONE', 'BOOK ONE']:
                idx = text.find(marker)

                # Si on trouve un chapitre, on commence le texte à partir de là.
                if idx != -1:
                    body = text[idx:]
                    break

    # Liste de motifs qui peuvent indiquer une fin inutile ou légale.
    footer_patterns = [
        r'\n[A-Z][^\n]{0,60}\n\nMay be had wherever books are sold',
        r'\nEnd of (the )?Project Gutenberg',
        r'\nEND OF PROJECT GUTENBERG',
        r'\nEnd of Project',
        r'\n+\s*THE END\s*\n+',
    ]

    # earliest représente l'endroit le plus tôt où une fin parasite est trouvée.
    earliest = len(body)

    # On teste chaque motif de fin.
    for pattern in footer_patterns:
        # re.IGNORECASE permet d'ignorer les majuscules/minuscules.
        m = re.search(pattern, body, re.IGNORECASE)

        # Si un motif est trouvé avant les autres, on garde sa position.
        if m and m.start() < earliest:
            earliest = m.start()

    # Si on a trouvé une fin parasite, on coupe le texte avant cette partie.
    if earliest < len(body):
        body = body[:earliest]

    # On retourne le texte nettoyé des espaces au début et à la fin.
    return clean_text(body.strip())

def GetOnlyBook(bookid):
    pathBook = os.path.join(bookDir,bookid+".txt")
    if not os.path.exists(pathBook):
        downloadBook(bookid)
    with open(os.path.join(bookDir,bookid+".txt"),"r",encoding="utf-8") as f:
        contenu = f.read()
        indexStart = contenu.find('*** START ')
        indexEnd = contenu.find('*** END ')
        contenuTop = contenu[:indexStart]
        contenuMid = contenu[indexStart+3:indexEnd]
        contenuMid = contenuMid[contenuMid.find("***")+3:]
        contenuEnd = contenu[indexEnd+3:]
        contenuEnd = contenuEnd[contenuEnd.find("***")+3:]
        
        return [contenuTop,extract_body(contenuMid),contenuEnd]

cliCommande = ["--lexdiv","--topics","--entities","--summarize","--similar"]

def cliExecute (param,bookid): 
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
            return ch.cacheGestion(bookid,param,extract_topics(GetOnlyBook(bookid)))
        case "--entities":
            print("exécution de la commande pour avoir les entitées présentes dans le livre")
            from entities import extract_entities
            return ch.cacheGestion(bookid,param,extract_entities(GetOnlyBook(bookid)))
        case "--summarize":
            print("exécution de la commande pour avoir un résumer du livre")
            import summarize
            cliExecute("--entities",bookid)
            return ch.cacheGestion(bookid,param,summarize.summarize(bookid,GetOnlyBook(bookid)[0]))
        case "--similar":
            print("exécution de la commande pour avoir des livre ressemblant au livre")
            from similar import extract_similar, BOOKS

            books_content = {}
            target_book = GetOnlyBook(bookid)
            if target_book:
                books_content[int(bookid)] = target_book[1]

            for bid in BOOKS:
                current_book = GetOnlyBook(str(bid))
                if current_book:
                    books_content[bid] = current_book[1]

            return ch.cacheGestion(bookid, param, extract_similar(bookid, books_content))
        case "--card":
            print("exécution de la commande pour avoir une carte sur le livre avec toutes les informations")
            for i in cliCommande:
                cliExecute(i,bookid)
            return ch.cacheGestion(bookid,param)
        case _:
            print("Commande non reconnue :", param)
            print("Commandes disponibles :", ", ".join(cliCommande + ["--card"]))
            return None

result = None
if param and id:
    result = cliExecute(param,id)
if result:
    print(json.dumps(result, indent=4, ensure_ascii=False))

"https://www.gutenberg.org/cache/epub/78788/pg78788.txt"