def generateHigherTuples(candidateSet):
    L=[]
    for i in range(len(candidateSet)):
        for j in range((data.shape[1])):
            if (not data.columns[j] in candidateSet[i]):
                tuple1 = (data.columns[j],)
                tuple2 = (candidateSet[i],)
                newtuple = (tuple1 + tuple2)
                #newtuple = (data.columns[j] + candidateSet[i])
                L.append(newtuple)
    return L