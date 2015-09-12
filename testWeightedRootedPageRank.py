import sys
import random
import operator
import copy
from collections import OrderedDict
import math
import linkpred


if __name__== '__main__':
	if sys.argv is None or len(sys.argv) is not 4:
		print "Usage : python testRootedPageRank.py ddi_v2.0.txt  ddi_v3.0.txt column"
		exit()
	trainfile = file(sys.argv[1])
	testfile= file(sys.argv[2])
	
	trainnet = dict()
	testnet = dict()
	i=0 
	column=int(sys.argv[3])
	weights = dict()	
	for line in trainfile:
		line=line.strip().split("\t")
		#if len(line) != 2: continue
		node1=line[0]
		node2=line[1]
		w = float(line[column])
		# add link to the network (dictionary of node-neighborlist pair)
		linkpred.addLinkToNetwork(trainnet,node1, node2)
		linkpred.addLinkToNetwork(trainnet,node2, node1)
		weights[(node1,node2)]=w
		weights[(node2,node1)]=w
		i+=1

	for line in testfile:
		line=line.strip().split("\t")
		#if len(line) != 2: continue
		node1=line[0]
		node2=line[1]
		linkpred.addLinkToNetwork(testnet,node1, node2)
		linkpred.addLinkToNetwork(testnet,node2, node1)
		

	#weights = linkpred.computeRankedList(wholenet, wholenet.keys(), {}, func=rootedPagerank)
	#print weights
	#ranks= linkpred.pagerank(wholenet,weights=weights)
	#print sorted(ranks.items(),key=lambda x:x[1])
	
	testnet = linkpred.getDifference(testnet,trainnet)

	#core = set(trainnet.keys()).intersection(testnet)
	core = linkpred.getCoreNodes(trainnet,testnet,1,1)
	testnet_pruned = linkpred.prune(testnet,core)
		
	nLinks=linkpred.getNumberOfLinks(testnet_pruned)

	print "trainnet :", linkpred.getNumberOfLinks(trainnet)		
	print "testnet :",nLinks 
	#rankedList = linkpred.computeRankedList(trainnet, core, trainnet)
	rankedList = linkpred.computeRankedList(trainnet, core, trainnet, func=linkpred.rootedPagerank, weights=weights)
	ranking=OrderedDict(sorted(rankedList.items(),key=operator.itemgetter(1),reverse=True))
	#print ranking

	auc = linkpred.computeAUCBySampling(testnet_pruned,ranking)
	intersect =linkpred.computeTruePositive(ranking, testnet_pruned, nLinks)
	prec = intersect/float(nLinks)
	print "Correctly predicted :", intersect
	print "AUC :",auc 
	print "Precision :" , prec
	
