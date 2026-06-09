import json, os

bookDir = os.path.join(os.path.dirname(__file__),"books")
cacheDir = os.path.join(os.path.dirname(__file__),"cache")

template="""
The book n°{id}, "{bookTitle}", was released in {dateMonth} {dateYear} and written by {author}.
This book follows {mainCharacter}, one of the main figures of the narrative. Throughout the story, {mainCharacter} will meet multiple characters like {secondCharacter} who help in the development of that story.
The events take place mainly in {mainPlace}, a location that take an important place for the story.
Through all characters and places, "{bookTitle}" presents a narrative that gradually unfolds around the events, relationships, and situations encountered throughout the book.
"""

def getEntity(bookid):
    with open(cacheDir+f"/{bookid}.json","r",encoding='utf-8') as f:
        data = json.load(f)
        if data["--entities"]:
            characters = data["--entities"]["characters"]
            locations = data["--entities"]["locations"]
            return characters,locations

def getInfo(StartBook):
    indexTitle = StartBook.find("Title")
    indexAuthor = StartBook.find("Author")
    title = StartBook[indexTitle+6:indexAuthor].strip().replace("  "," ")
    indexRelease = StartBook.find("Release date")
    author = StartBook[indexAuthor+7:indexRelease].strip()
    indexEndRelease = StartBook.find("[eBook")
    ReleaseDate = StartBook[indexRelease+13:indexEndRelease].strip().replace(",","")
    return title,author,ReleaseDate

def summarize(bookid,StartBook):
    title,author,ReleaseDate = getInfo(StartBook)
    month,day,year = ReleaseDate.split(" ")
    characters,locations = getEntity(bookid)
    return(template.format(
        id=bookid,
        bookTitle=title,
        dateMonth=month,
        dateYear=year,
        author = author,
        mainCharacter = characters[0],
        secondCharacter = characters[1],
        mainPlace=locations[0]
    ))

