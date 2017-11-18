import numpy as np
import nltk
nltk.download('wordnet')
import re
import xmltodict
from pycorenlp import StanfordCoreNLP
from nltk.stem.wordnet import WordNetLemmatizer


def isNoun(x):
	#Penn part-of-speech tags
    if x in ['NN','NNS','NNP','NNPS']:
        return True
    return False

def isVerb(x):
	if x in ['VB','VBD','VBG','VBN','VBP','VBZ']:
		return True
	return False

def isAdj(x):
	if x in ['JJ','JJR','JJS']:
		return True
	return False

def Read_Xml(filepath):
	file = open('./data/train.txt', 'w')
	with open(filepath) as f:
		doc = xmltodict.parse(f.read())
		schema = [elem for elem in doc['collection']['schema']]
		for x in schema:
			text = ''
			text1 = x['text']['txt1']
			for tex in text1:
				if tex != '\n':
					text += tex
			text += ' ' + x['text']['pron'] + ' '
			text2 = x['text']['txt2']
			for tex in text2:
				if tex != '\n':
					text += tex
			target_pron = x['quote']['pron']
			ans1 = x['answers']['answer'][0]
			ans2 = x['answers']['answer'][1]
			try:
				ans3 = x['answers']['answer'][2]
			except:
				ans3 = 'NA'
			if (x['correctAnswer'] == 'A' or x['correctAnswer'] == 'A.'):
				corr_ans = x['answers']['answer'][0]
			elif (x['correctAnswer'] == 'B' or x['correctAnswer'] == 'B.'):
				corr_ans = x['answers']['answer'][1]
			elif (x['correctAnswer'] == 'C' or x['correctAnswer'] == 'C.'):
				corr_ans = x['answers']['answer'][2]
			print >> file, text
			print >> file, target_pron
			print >> file, ans1 + ',' + ans2 + ',' + ans3
			print >> file, corr_ans + '\n'

def Read_Text(filepath):
    with open(filepath) as f:
	lines = f.readlines()
    lines = [x.strip('\n') for x in lines]

    questionSet = []
    count = 0

    for i in range(0, len(lines), 5):
    	#Start from line 0, step = 5
    	count += 1
        sentence = lines[i].lower()
        Target_Pronoun = lines[i+1]
        try:
        	answerA, answerB, answerC = lines[i+2].lower().split(',')
        except:
        	answerA, answerB = lines[i+2].lower().split(',')
        	answerC = 'NA'

        Correct_Answer = lines[i+3].lower()
        if Correct_Answer == answerA:
            Correct_Answer = 'A'
        elif Correct_Answer == answerB:
            Correct_Answer = 'B'
        elif Correct_Answer == answerC:
        	Correct_Answer = 'C'
        else:
            print('ERROR: No VALID ANSWER')
            print(sentence)
            print(answerA)
            print(answerB)
            print(Correct_Answer)

	key = ['index', 'sentence', 'Target_Pronoun', 'A', 'B', 'C', 'Correct_Answer']
	questionSet.append(dict(zip(key, [count, sentence, Target_Pronoun, answerA, answerB, answerC, Correct_Answer])))

    return questionSet

def Process_Set(dataset):
	total = cor_count = wr_count = no_count = 0
	ans = ''
	corr_file = open('./output/Correct.txt', 'w')
	incorr_file = open('./output/Incorrect.txt', 'w')
	not_found_file = open('./output/NotFound.txt', 'w')

	for question in dataset:
		total += 1
		A = question['A']
		B = question['B']
		C = question['C']
		Target_Pronoun = question['Target_Pronoun']
		Correct_Answer = question['Correct_Answer']
		sentence = question['sentence']
		sentence = str(sentence)
		ans, line_num = Analyse_Sentence(sentence, A, B, C, Target_Pronoun)
		if ans == Correct_Answer:
			cor_count += 1
			print >> corr_file, 'Question number: ' + str(total)
			print >> corr_file, question['sentence']
			print >> corr_file, 'Found in line: ' + str(line_num) + '\n'
		elif ans == 'NA':
			no_count += 1
			print >> not_found_file, 'Question number: ' + str(total)
			print >> not_found_file, question['sentence'] + '\n'
		else:
			wr_count += 1
			print>>incorr_file, 'Question number: ' + str(total)
			print>>incorr_file, question['sentence']
			print>>incorr_file, 'Found in line: ' + str(line_num) + '\n'

	print("Correct Answer: %d out of %d: %.2f%%" %(cor_count, total, 100.0*cor_count/total))
	print("Wrong Answer: %d out of %d: %.2f%%" %(wr_count, total, 100.0*wr_count/total))
	print("Not Found: %d out of %d: %.2f%%" %(no_count, total, 100.0*no_count/total))

def Analyse_Sentence(sentence, A, B, C, Target_Pronoun):
	Candidate_A, Candidate_B, Candidate_C, sentence = Shrink_Sentence(sentence, A, B, C)
	NC1, NC2, NC3, line_num = Process_by_NC(Candidate_A, Candidate_B, Candidate_C, Target_Pronoun, sentence)
	#C1V, C2V, C1VW, C2VW, JC1, JC2 = Process_by_Google(Candidate_A, Candidate_B, Target_Pronoun, sentence)
	ans = ''
	if NC1 == 1:
		ans = 'A'
	elif NC2 == 1:
		ans = 'B'
	elif NC3 == 1:
		ans = 'C'
	else:
		ans = 'NA'
	#Z1, Z2 = re.split("because ", sentence)
	#C1V, C2V, C1VW, C2VW, JC1, JC2 = Process_by_Google(Candidate_A, Candidate_B, str(Z1), str(Z2))
	return ans, line_num

def print_depen(depen):
	file = open('output.txt', 'w')
	for de in depen:
		print >> file, de

def Process_by_NC(Candidate_A, Candidate_B, Candidate_C, Target_Pronoun, sentence):
	tokens = Get_Tokens(sentence)
	dependencies = Get_Dependencies(sentence)
	#print_depen(dependencies)
	#print(tokens)
	print(sentence)
	lemmatizer = WordNetLemmatizer()
	NC1 = NC2 = NC3 = 0
	line_num = 0

	Pronoun_Event_List = []
	Pronoun_Event_Role_List = []
	A_Event_Role_List = []
	B_Event_Role_List = []
	C_Event_Role_List = []
	Candidate_Event_Role_List = []
	Dependent_Gloss = []
	Dependent_Gloss_Type = []
	Nmod_Poss_Candidate = []
	Nmod_Poss_Pronoun = []

	for item in dependencies:
		#protect target pronoun event from 'xcomp'
		#john asked scientist what he could do to help.
		if lemmatizer.lemmatize(item['dependentGloss'], 'v') not in Dependent_Gloss:
			Dependent_Gloss.append(lemmatizer.lemmatize(item['dependentGloss'], 'v'))

	for element in Dependent_Gloss:
		for item in tokens:
			it = lemmatizer.lemmatize(item['word'], 'v')
			if element == it and it not in Dependent_Gloss_Type:
				Dependent_Gloss_Type.append(it)
				

	if len(Dependent_Gloss) == len(Dependent_Gloss_Type):
		#a dictionary: word to its type
		Dependencies_Tokens = dict(zip(Dependent_Gloss, Dependent_Gloss_Type))
	else:
		print(len(Dependent_Gloss))
		print(len(Dependent_Gloss_Type))
		print("ERROR: Dependencies_Tokens Length NOT Correct")

	Pronoun_Candidate = dict(zip(Nmod_Poss_Pronoun, Nmod_Poss_Candidate))
	
	for item in dependencies:
		#find events target pronoun and candidates in and their roles
		if (item['dep'] in ['nsubj', 'nsubj:xsubj', 'nsubjpass', 'dep']) and item['dependentGloss'] == Target_Pronoun:
			Pronoun_Event_Role_List.append(lemmatizer.lemmatize(item['governorGloss'], 'v') + '-s')
			Pronoun_Event_List.append(lemmatizer.lemmatize(item['governorGloss'],'v'))

		elif (item['dep'] in ['dobj', 'nmod', 'nmod:on', 'nsubjpass:xsubj']) and item['dependentGloss'] == Target_Pronoun:
			Pronoun_Event_Role_List.append(lemmatizer.lemmatize(item['governorGloss'], 'v') + '-o')
			Pronoun_Event_List.append(lemmatizer.lemmatize(item['governorGloss'],'v'))

		elif (item['dep'] in ['nsubj', 'nsubj:xsubj', 'nsubjpass']) and item['dependentGloss'] == Candidate_A:
			Candidate_Event_Role_List.append(lemmatizer.lemmatize(item['governorGloss'], 'v') + '-s')
			A_Event_Role_List.append(lemmatizer.lemmatize(item['governorGloss'],'v') + '-s')

		elif (item['dep'] in ['acl']) and item['governorGloss'] == Candidate_A:
			#tom attacked tim because he stole an elephant from zoo.
			Candidate_Event_Role_List.append(lemmatizer.lemmatize(item['dependentGloss'], 'v') + '-s')
			A_Event_Role_List.append(lemmatizer.lemmatize(item['dependentGloss'],'v') + '-s')

		elif (item['dep'] in ['dobj', 'nmod', 'nmod:on', 'nsubjpass:xsubj']) and item['dependentGloss'] == Candidate_A:
			Candidate_Event_Role_List.append(lemmatizer.lemmatize(item['governorGloss'], 'v') + '-o')
			A_Event_Role_List.append(lemmatizer.lemmatize(item['governorGloss'],'v') + '-o')

		elif (item['dep'] in ['nmod:poss']) and item['dependentGloss'] == Candidate_A:
			#recognize the real correct candidate
			#man stole neighbor's bike because he needed one.
			Nmod_Poss_Candidate.append(Candidate_A)
			Nmod_Poss_Pronoun.append(item['governorGloss'])
			Pronoun_Candidate = dict(zip(Nmod_Poss_Pronoun, Nmod_Poss_Candidate))

		elif (item['dep'] in ['nsubj', 'nsubj:xsubj', 'nsubjpass']) and item['dependentGloss'] == Candidate_B:
			Candidate_Event_Role_List.append(lemmatizer.lemmatize(item['governorGloss'], 'v') + '-s')
			B_Event_Role_List.append(lemmatizer.lemmatize(item['governorGloss'],'v') + '-s')

		elif (item['dep'] in ['dobj', 'nmod', 'nmod:on', 'nsubjpass:xsubj']) and item['dependentGloss'] == Candidate_B:
			Candidate_Event_Role_List.append(lemmatizer.lemmatize(item['governorGloss'], 'v') + '-o')
			B_Event_Role_List.append(lemmatizer.lemmatize(item['governorGloss'],'v') + '-o')

		elif (item['dep'] in ['nmod:poss']) and item['dependentGloss'] == Candidate_B:
			Nmod_Poss_Candidate.append(Candidate_B)
			Nmod_Poss_Pronoun.append(item['governorGloss'])
			Pronoun_Candidate = dict(zip(Nmod_Poss_Pronoun, Nmod_Poss_Candidate))

		elif (item['dep'] in ['nsubj', 'nsubj:xsubj', 'nsubjpass']) and item['dependentGloss'] == Candidate_C:
			Candidate_Event_Role_List.append(lemmatizer.lemmatize(item['governorGloss'], 'v') + '-s')
			C_Event_Role_List.append(lemmatizer.lemmatize(item['governorGloss'],'v') + '-s')

		elif (item['dep'] in ['dobj', 'nmod', 'nmod:on'], 'nsubjpass:xsubj') and item['dependentGloss'] == Candidate_C:
			Candidate_Event_Role_List.append(lemmatizer.lemmatize(item['governorGloss'], 'v') + '-o')
			C_Event_Role_List.append(lemmatizer.lemmatize(item['governorGloss'],'v') + '-o')

		elif (item['dep'] in ['nmod:poss']) and item['dependentGloss'] == Candidate_C:
			Nmod_Poss_Candidate.append(Candidate_C)
			Nmod_Poss_Pronoun.append(item['governorGloss'])
			Pronoun_Candidate = dict(zip(Nmod_Poss_Pronoun, Nmod_Poss_Candidate))

		elif (item['dep'] in ['dobj']) and any (item['dependentGloss'] in key for key in Pronoun_Candidate):
			for key in Pronoun_Candidate:
				if Pronoun_Candidate[key] == Candidate_A:
					Candidate_Event_Role_List.append(lemmatizer.lemmatize(item['governorGloss'], 'v') + '-o')
					A_Event_Role_List.append(lemmatizer.lemmatize(item['governorGloss'],'v') + '-o')
				elif Pronoun_Candidate[key] == Candidate_B:
					Candidate_Event_Role_List.append(lemmatizer.lemmatize(item['governorGloss'], 'v') + '-o')
					B_Event_Role_List.append(lemmatizer.lemmatize(item['governorGloss'],'v') + '-o')
				else:
					Candidate_Event_Role_List.append(lemmatizer.lemmatize(item['governorGloss'], 'v') + '-o')
					C_Event_Role_List.append(lemmatizer.lemmatize(item['governorGloss'],'v') + '-o')


	print(Pronoun_Event_Role_List)
	#print(Candidate_Event_Role_List)
	print(A_Event_Role_List)
	print(B_Event_Role_List)
	if C_Event_Role_List:
		print(C_Event_Role_List)
	#print(Dependencies_Tokens)

	for item in dependencies:
		#eliminate surface events of target pronoun and fit deep event in
		for Pronoun_Event in Pronoun_Event_List:
			#make sure it's verb not something else
			if (item['dep'] == 'xcomp' and isVerb(Dependencies_Tokens[lemmatizer.lemmatize(item['dependentGloss'], 'v')]) and lemmatizer.lemmatize(item['governorGloss'],'v') == Pronoun_Event):
				Pronoun_Event_Role_List.append(lemmatizer.lemmatize(item['dependentGloss'], 'v') + '-s')
				Pronoun_Event_Role_List = [x for x in Pronoun_Event_Role_List if (x != Pronoun_Event + '-s' and x != Pronoun_Event + '-o')]
			#recognize passive auxiliary
			if (item['dep'] == 'auxpass' and isVerb(Dependencies_Tokens[lemmatizer.lemmatize(item['governorGloss'], 'v')]) and lemmatizer.lemmatize(item['dependentGloss'], 'v') in ['be']):
				Pronoun_Event_Role_List.remove(lemmatizer.lemmatize(item['governorGloss'], 'v') + '-s')
				Pronoun_Event_Role_List.append(lemmatizer.lemmatize(item['governorGloss'], 'v') + '-o')

	Candidate_Event_Role_List = list(set(Candidate_Event_Role_List))

	count = 0
	found = False
	#candidate_answer = []
	likely_answer = []

	with open('./data/schemas-size12.txt') as f:
		lines = f.readlines()
		lines = [x.strip('\n') for x in lines]
    	for i in range(0, len(lines)):
    		count += 1
    		Token_List = lines[i].split()
    		for Pronoun_Event_Role in Pronoun_Event_Role_List:
    			if any (Pronoun_Event_Role in P for P in Token_List):
    				for Candidate_Event_Role in Candidate_Event_Role_List:
    					#candidate_answer.append({Pronoun_Event_Role, Candidate_Event_Role})
    					#make sure the most likely answer is secured
    					if any (Candidate_Event_Role in C for C in Token_List) and found == False and Pronoun_Event_Role != Candidate_Event_Role:
    						likely_answer.append(Candidate_Event_Role)
    						found = True
    						line_num = count
    						print('found: ' + Candidate_Event_Role + ', ' + Pronoun_Event_Role)
    						print("In line %d \n" %count)

	#print(likely_answer)
	#print(candidate_answer)

	for item in likely_answer:
		for Aitem in A_Event_Role_List:
			if Aitem == item:
				#print("A is answer")
				NC1 = 1
		for Bitem in B_Event_Role_List:
			if Bitem == item:
				#print("B is answer")
				NC2 = 1
		for Citem in C_Event_Role_List:
			if Citem == item:
				NC3	= 1
	
	return NC1, NC2, NC3, line_num

def Shrink_Sentence(sentence, A, B, C):
	tokens = Get_Tokens(sentence)
	Candidate_A = A
	Candidate_B = B
	Candidate_C = C

	for token in tokens:
		#replace 'the apple' to 'apple' for simplicity
		if token['word'] in A:
			if isNoun(token['pos']):
				Candidate_A = token['word']
		if token['word'] in B:
			if isNoun(token['pos']):
				Candidate_B = token['word']
		if token['word'] in C:
			if isNoun(token['pos']):
				Candidate_C = token['word']

	sentence = sentence.replace(A, Candidate_A)
	sentence = sentence.replace(B, Candidate_B)
	sentence = sentence.replace(C, Candidate_C)
	sentence = str(sentence)
	return Candidate_A, Candidate_B, Candidate_C, sentence

def Process_by_Google(Candidate_A, Candidate_B, Target_Pronoun, sentence):
	Z1, Z2 = re.split("because ", sentence)
	Z1 = str(Z1)
	Z2 = str(Z2)
	Z2Tokens = Get_Tokens(Z2)
	#Z2Dependencies = Get_Dependencies(Z2)
	#print(Z2Dependencies)
	V = ""
	J = ""
	for z2token in Z2Tokens:
		if isVerb(z2token['pos']):
			V = z2token['word']
		elif isAdj(z2token['pos']):
			J = z2token['word']

	nonsense, W = re.split(V, Z2)
	C1V = Candidate_A.encode('ascii') + " " + V.encode('ascii')
	C2V = Candidate_B.encode('ascii') + " " + V.encode('ascii')
	C1VW = C1V + W
	C2VW = C2V + W
	if J != "":
		JC1 = J.encode('ascii') + " " + Candidate_A.encode('ascii')
		JC2 = J.encode('ascii') + " " + Candidate_B.encode('ascii')
	else:
		JC1 = "NA"
		JC2 = "NA"
	#print(C1V)
	#print(C2V)
	#print(C1VW)
	#print(C2VW)
	#print(JC1)
	#print(JC2)
	return C1V, C2V, C1VW, C2VW, JC1, JC2

def Get_Tokens(sentence):
	nlp = StanfordCoreNLP('http://localhost:9000')
	output = nlp.annotate(sentence, properties = {'annotators': 'tokenize, ssplit, pos, depparse, parse, dcoref','outputFormat': 'json'})
	tokens = output['sentences'][0]['tokens']
	return tokens

def Get_Dependencies(sentence):
	nlp = StanfordCoreNLP('http://localhost:9000')
	output = nlp.annotate(sentence, properties = {'annotators': 'tokenize, ssplit, pos, depparse, parse, dcoref','outputFormat': 'json'})
	#print(output)
	dependencies = output['sentences'][0]['enhancedDependencies']
	#dependencies = output['sentences'][0]['basicDependencies']
	return dependencies

if __name__ == '__main__':

    print('Reading input files..')
    #the processed xml file will be saved to 'train.txt' in data folder
    Read_Xml('./data/PDPChallenge2016.xml')
    trainSet = Read_Text('./data/train.txt')
    testSet = Read_Text('./data/test.txt')
    sampleSet = Read_Text('./data/sample.txt')
    Process_Set(trainSet)