import json, os
from collections import Counter

bookDir = os.path.join(os.path.dirname(__file__),"books")
cacheDir = os.path.join(os.path.dirname(__file__),"cache")

template="""
"{bookTitle}", was released in {dateMonth} {dateYear} and written by {author}.
This book follows {mainCharacter}, one of the main figures of the narrative. Throughout the story, {mainCharacter} will meet multiple characters like {secondCharacter} and {thirdCharacter} who help in the development of that story.
The events take place mainly in {mainPlace}, a location that take an important place for the story.
Through all characters and places, "{bookTitle}" presents a narrative that gradually unfolds around the events, relationships, and situations encountered throughout the book.
The book covers themes including, {theme}.
"""

def getEntity(bookid):
    with open(cacheDir+f"/{bookid}.json","r",encoding='utf-8') as f:
        data = json.load(f)
        if data["--entities"]:
            characters = data["--entities"]["characters"]
            locations = data["--entities"]["locations"]
            return characters,locations

def getTopics(bookid):
    with open(cacheDir+f"/{bookid}.json","r",encoding='utf-8') as f:
        data = json.load(f)
        if data["--topics"]:
            element = data["--topics"]
            allTopic = []
            for i in element:
                indexStart = i.find(':')
                i = i[indexStart+2:]
                allTopic.append(i)
            result = [x for x, _ in Counter(allTopic).most_common()]
            return result

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
    themes = getTopics(bookid)
    conserveThemes =""
    count = 0
    for i in themes:
        if count == 0:
            conserveThemes = i
        elif count == len(themes)-1:
            conserveThemes = conserveThemes + " and " +i 
        elif count == 3:
            conserveThemes = conserveThemes + " and " +i 
            break
        else : 
            conserveThemes = conserveThemes+", "+i
        count +=1
    return(template.format(
        id=bookid,
        bookTitle=title,
        dateMonth=month,
        dateYear=year,
        author = author,
        mainCharacter = characters[0],
        secondCharacter = characters[1],
        thirdCharacter = characters[2],
        mainPlace=locations[0],
        theme=conserveThemes
    ))

