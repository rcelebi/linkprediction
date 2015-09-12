import sys
import random
import operator
import copy
from collections import OrderedDict
import math

def addLinkToNetwork(net,source, target):
	if net.has_key(source):
		if target not in net[source]:  
			net[source].append(target)
	else:
		net[source] =[target]

def removeLinkToNetwork(net, source, target):
	if net.has_key(source):
		net[source].remove(target)

def getDifference(net1, net2):
	diff = dict()
	for item in net1.items():
		s= item[0]
		neighs=item[1]
		for t in neighs:
			if net2.has_key(s) and t in net2[s]: continue
			if net2.has_key(t) and s in net2[t]: continue
			addLinkToNetwork(diff, s, t)	
			addLinkToNetwork(diff, t, s)
	return diff

def selectRandomLinks(net,n):
	selectedLinks = dict()	
	i=0
	keylist=net.keys()
	while i<n:
		randNode=random.choice(keylist)
		neighs = net[randNode]
		randNeigh = random.choice(neighs)
		if selectedLinks.has_key(randNode) and randNeigh in selectedLinks[randNode]: continue
		if selectedLinks.has_key(randNeigh) and randNode in selectedLinks[randNeigh]: continue
		addLinkToNetwork(selectedLinks, randNode, randNeigh)	
		addLinkToNetwork(selectedLinks, randNeigh, randNode)
		i+=1

	return selectedLinks

def getNeighbors(net, x):
	if net.has_key(x):
		return net[x]
	else:
		return []

def getNumberOfCommonNeighbors(net, x, y, weights={}):
	if x== y:
		return len(getNeighbors(net,x))
	
	commons =set(getNeighbors(net,x)).intersection(getNeighbors(net,y))
	return len(commons)

def jaccard(net,x,y,weights={}):
	if x == y:
		return 1
	
	commons =set(getNeighbors(net,x)).intersection(getNeighbors(net,y))
	unions = set(getNeighbors(net,x)).union(getNeighbors(net,y))
	if len(unions) == 0:
		return 0.0
	return float(len(commons))/len(unions)

def adamic(net,x,y,weights={}):
	commons =set(getNeighbors(net,x)).intersection(getNeighbors(net,y))
	score =0.0
	for n in commons:
		score += 1.0/math.log(float(len(getNeighbors(net,n))))

	return score

def computeRankedList(trainnet, core, excludeLinks, func=getNumberOfCommonNeighbors, weights={}):
	ranking = dict()	
	for x in core:
		for y in core:
			if x == y: continue	
			if excludeLinks.has_key(x) and y in excludeLinks[x]: continue
			if excludeLinks.has_key(y) and x in excludeLinks[y]: continue
			score = func(trainnet,x,y,weights=weights)
			ranking[(x,y)]=score
	return ranking

def computeAUCBySampling(test,ranking):
	rankingOfMissingLinks = dict()
	rankingOfUnconnectedLinks = copy.deepcopy(ranking)
	for item in test.items():
		s = item[0]
		neighs = item[1]
		for t in neighs:
			if (s,t) in ranking:
				del rankingOfUnconnectedLinks[(s,t)]				
				rankingOfMissingLinks[(s,t)]=ranking[(s,t)]
				
			elif (t,s) in ranking:
				del rankingOfUnconnectedLinks[(t,s)]
				rankingOfMissingLinks[(t,s)]=ranking[(t,s)]

	n1=0 #number of the missing links having a higher score
	n2=0 #number of the missing links having the same score
	n=0  #number of total comparisons
	#n = len(rankingOfUnconnectedLinks)*len(rankingOfMissingLinks)/100
	n=2000000	
	keys1=rankingOfMissingLinks.keys()
	keys2=rankingOfUnconnectedLinks.keys()
	for i in xrange(n):
		randMissLink=random.choice(keys1)
		score1=rankingOfMissingLinks[randMissLink]
		randUnconnLink = random.choice(keys2)
		score2 = rankingOfUnconnectedLinks[randUnconnLink]
		if score1 > score2:
			n1+=1
		if score1 == score2:
			n2+=1
	
	auc=(n1+n2*0.5)/float(n)
	return auc	

def computeAUC(test,ranking):
	rankingOfMissingLinks = dict()
	rankingOfUnconnectedLinks = copy.deepcopy(ranking)
	for item in test.items():
		s = item[0]
		neighs = item[1]
		for t in neighs:
			if (s,t) in ranking:
				del rankingOfUnconnectedLinks[(s,t)]				
				rankingOfMissingLinks[(s,t)]=ranking[(s,t)]
				
			elif (t,s) in ranking:
				del rankingOfUnconnectedLinks[(t,s)]
				rankingOfMissingLinks[(t,s)]=ranking[(t,s)]

	n1=0 #number of the missing links having a higher score
	n2=0 #number of the missing links having the same score
	n=0  #number of total comparisons
	for item in rankingOfMissingLinks.items():
		score1=item[1]
		for item2 in rankingOfUnconnectedLinks.items():
			score2 = item2[1]
			if score1 > score2:
				n1+=1
			if score1 == score2:
				n2+=1
			n+=1
	
	auc=(n1+n2*0.5)/float(n)
	return auc	

def computeTruePositive(ranking, test, nLinksInTest):
	topranked = ranking.items()[0:nLinksInTest]
	#print topranked
	intersect =0
	for item in topranked:
		edge =item[0]
		s = edge[0]
		t = edge[1]
		if test.has_key(s) and t in test[s]: intersect+=1
		if test.has_key(t) and s in test[t]: intersect+=1

	return intersect			

def getCoreNodes(trainnet,testnet,ktrain,ktest):
	core=set()
	for n in testnet.keys():
		if trainnet.has_key(n):
			if len(trainnet[n]) >= ktrain and len(testnet[n]) >=ktest: 
				core.add(n)
	return core

def prune(net, core):
	pruned =dict()
	for item in net.items():
		s= item[0]
		neighs=item[1]
		for t in neighs:
			if s in core and t in core:
				if pruned.has_key(s):
					pruned[s].append(t)
				else:
					pruned[s]=[t]
	return pruned

def getNumberOfLinks(net):
	n=0
	for item in net.items():
		s = item[0]
		neighs = item[1]
		n+=len(neighs)
	return n 	

allRanks ={}
def rootedPagerank(net, start, end, damping_factor=0.85,max_iter=100,min_delta=0.00001, weights={}):
	if allRanks.has_key(start):
		if allRanks[start].has_key(end):
			return allRanks[start][end]
		else:
			return sys.float_info.min
	
	allRanks[start]=personalizedPagerank(net,start,damping_factor,max_iter,min_delta, weights)
	return allRanks[start][end]	

dist = {}	
def flodywarshall(net):
	for u in net:
		dist[u]={}
		for v in net:
			dist[u][v]=sys.maxint
		dist[u][u]=0
		for neigh in net[u]:
			dist[u][neigh] = 1
 	# given dist u to v, check if path u - t - v is shorter
	for t in net:
		for u in net:
			for v in net:
				newdist = dist[u][t] + dist[t][v]
				if newdist < dist[u][v]:
					dist[u][v]= newdist
	return dist


flodyDone =0
def graphDistance(net, start, end, weights={}):
	global flodyDone
	if not flodyDone:
		flodywarshall(net)
		flodyDone =1
	
	if dist.has_key(start):
		if dist[start].has_key(end):
			return -1.0*(dist[start][end])
		else:
			return -1.0*sys.float_info.max
	elif dist.has_key(end):
		if dist[end].has_key(start):
			return -1.0*(dist[end][start])
		else:
			return -1.0*sys.float_info.max
	else:
		return -1.0*sys.float_info.max

def personalizedPagerank(net, start=None, damping_factor=0.85,max_iter=100,min_delta=0.00001, weights={}):
	
	nodes= net.keys()
	numNodes = len(nodes)
	if numNodes == 0:
		return {}
	min_value= (1.0-damping_factor)/numNodes
	pagerank = dict.fromkeys(nodes,1.0/numNodes)
	for i in xrange(max_iter):
		diff =0
		for node in nodes:
			rank = 0.0
			for neigh in net[node]:
				if (node,neigh) in weights:
					weight =weights[(node,neigh)]
				else:
					weight=1.0
				rank += damping_factor*weight*pagerank[neigh]/len(net[neigh])
			
			if start == node:
				rank +=min_value
		
			diff += abs(pagerank[node]-rank)
			pagerank[node]=rank
		if diff < min_delta:
			break
	
	return pagerank
	

def pagerank(net,damping_factor=0.85,max_iter=100,min_delta=0.00001, weights={}):
	nodes= net.keys()
	numNodes = len(nodes)
	if numNodes == 0:
		return {}
	
	min_value= (1.0-damping_factor)/numNodes
	pagerank = dict.fromkeys(nodes,1.0/numNodes)
	for i in xrange(max_iter):
		diff =0
		for node in nodes:
			rank = min_value
			for neigh in net[node]:
				if (node,neigh) in weights:
					weight =weights[(node,neigh)]
				else:
					weight=1.0
				rank += damping_factor*weight*pagerank[neigh]/len(net[neigh])
			diff += abs(pagerank[node]-rank)
			pagerank[node]=rank
		if diff < min_delta:
			break

	return pagerank	

