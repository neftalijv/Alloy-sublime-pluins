def getAll(doc):
	s = "("
	for i in doc:
		print i
		for j in doc[i]['properties']:
			s = s + doc[i]['properties'][j] + "|"
	print s + ")"
	return 0