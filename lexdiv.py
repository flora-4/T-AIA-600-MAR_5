def lenghAverageWord(array):
    allCaracter = 0
    for i in array:
        allCaracter += len(i)
    return allCaracter/len(array)

def lexdiv(array):
    if not array:
        print("aucun livre a traité")
        return
    x = array[1].replace("\n"," ").replace("[Illustration]","").replace("“","").replace("”","").replace(".","").replace("[","").replace("]","").replace(",","").replace(";","")
    x = x.strip().split(" ")
    
    allword = []
    uniqueWord = []
    onlyOneWord = []

    for i in x:
        if i =="":
            continue
        allword.append(i)
        if not i.lower() in uniqueWord:
            uniqueWord.append(i.lower())
            onlyOneWord.append(i.lower())
        else:
            try:
                onlyOneWord.remove(i.lower())
            except:
                continue
    
    numberWord = len(allword)
    numberUniqueWord = len(uniqueWord)
    numberOnlyOneWord = len(onlyOneWord)
    ttr = numberUniqueWord / numberWord
    mwl = lenghAverageWord(allword)
    mwf = numberWord/numberUniqueWord

    return{
        "tok":numberWord, # total number of word tokens
        "typ":numberUniqueWord, # number of unique word tokens
        "hap":numberOnlyOneWord, # number of word tokens occurring only once
        "ttr":ttr, # number of unique words tokens divided by number of word tokens
        "mwl":mwl, # mean number of characters per word token
        "mwf":mwf # number of word token divided by number of unique word tokens
    }
    

