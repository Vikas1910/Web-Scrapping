import time
import pickle
import json
from bs4 import BeautifulSoup
import bs4
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from fuzzywuzzy import process
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize
from textblob import TextBlob
import matplotlib.pyplot as plt
import os 
import shutil
from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.

def index(request):
    return render(request,'index.html')

def images(user_input):
	dirs = os.listdir("/home/vikas/Zomato_UI/Zomato/static/data")
	count = 1
	a=[]
	l=[]
	for x in dirs:
		a.append(x.strip('.png'))
		if(count%3== 0 ):
			l.append(a)
			a=[]
		count +=1
	l.append(a)
	context = {"images": l,
				"res_name": user_input}
	return context

def create_words():
	global l
	with open('Name_binary','rb') as name:
		l = pickle.load(name)
	words = []
	for x in l:
		words.extend(x.split())
	words = list(set(words))
	words.sort() 
	words = [x.lower() for x in words]
	return words

def y(k,a,w):
	x = process.extractOne(a,w)
	k.append(x[0])
	return k

def spell_checker(words):
	s = temp_name.split()
	k = []
	for a in s:
		 k = y(k,a,words)
	return k

def find_match(x,s):
	flag = 0
	for q in s:
		if q in x:
			flag = 1
		else:
			flag = 0
			break
	if ( flag == 1):
		return True
	else:
		return False

def find_res_name(s,k):
	z=[]
	for x in l:
		if find_match(x.lower(),s):
			z.append(x)
	user_input=process.extractOne(k,z)[0]
	return user_input

def link_scrapping(user_input):
	browser.get("https://www.zomato.com/ahmedabad")
	page=None
	soup=None
	search = browser.find_element_by_id("keywords_input")
	search.send_keys(user_input)
	time.sleep(5)
	search.send_keys(Keys.RETURN)
	time.sleep(5)
	try:
		browser.find_element_by_xpath("//a[@class='ui ta-right pt10 fontsize3 zred pb10 pr10']").click()
	except:
		pass
	page = browser.page_source
	soup = BeautifulSoup(page,"lxml")
	name_dict={}
	count=0
	new = soup.find_all("a",attrs={'data-result-type':'ResCard_Name'})
	if(len(new) == 0 ):
		new = soup.find_all("a",attrs={'class':'ui large header left'}) 	
	for tag in new:
		count +=1
		if(tag.get_text().strip() == user_input):	
			name_dict.update({count:{"name":tag.text.strip(),"link":tag['href'].strip()}})
	return name_dict

def review_scrapping(name_dict):
	review_dict= {}                                                                       
	count = 0
	for x in name_dict:
		count += 1
		browser.get(name_dict[x]['link'])
		browser.find_element_by_xpath("//a[@data-sort='reviews-dd']").click()
		while True:
			try:
				browser.find_element_by_xpath("//div[@class='load-more bold ttupper tac cursor-pointer fontsize2']").click()
			except:
				break
		page = browser.page_source
		soup = BeautifulSoup(page,"lxml")
		review = []
		for tag in soup.find_all("div", attrs= {"class":"rev-text mbot0 "}):
			review.append(tag.get_text().strip())
		review_dict.update({count:{"name":soup.find("a",{"class":"ui large header left"}).text.strip(),"area":soup.find("a",{"class":"left grey-text fontsize3"}).text.strip(),"review":review}})
	return review_dict

def analyzie_review(review_dict):
	if os.path.exists('static/data'):
		shutil.rmtree('static/data')
	os.makedirs('static/data')
	for x in review_dict:
		reviews=[]
		for i in review_dict[x]["review"]:
			reviews.append(i.strip("Rated\xa0\n                               "))
			stop=stopwords.words("english")
			stop.extend(["\n","\xa0","/"])
			filter_data=[]
			temp=[]
			for j in reviews:
				for w in j.split():
					if w not in stop:
						temp.append(w)
				filter_data.append((" ").join(temp))
		
		filter_sentence=[]
		for m in filter_data:
			filter_sentence.extend(sent_tokenize(m))
		negative,positive,neutral=0,0,0
		for n in filter_sentence:
			if TextBlob(n).sentiment.polarity < 0:
				negative+=1	
			elif TextBlob(n).sentiment.polarity==0:
				neutral+=1
			elif TextBlob(n).sentiment.polarity > 0:
				positive+=1
		labels = 'Negative','Positive','Neutral'
		sizes = [negative,positive,neutral]
		colors = ['red', 'green','lightskyblue']
		explode = ( 0, 0.1, 0)
		plt.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%', shadow=True, startangle=140)
		plt.axis('equal')
		plt.savefig('static/data/' + review_dict[x]["area"] + '.png') 
		plt.clf()
	print("Analyzing done all images have been saved ")

l=[]
temp_name=None
browser=None
user_input = None

def main(request):
	global temp_name
	global browser
	temp_name = request.GET.get("res")
	words=create_words()
	k = spell_checker(words)
	global user_input 
	user_input = find_res_name(k," ".join(k))
	print(user_input)

	print("Opening browser")

	browser=webdriver.Firefox()

	print("Scrapping for links ")

	name_dict=link_scrapping(user_input)

	print("Scrapping for Reviews ")

	review_dict = review_scrapping(name_dict)

	print("Analyzing Reviews ")

	analyzie_review(review_dict)

	browser.close()

	#image = images()

	return render(request,'display.html',images(user_input))

def new(request):
	return render(request,'display.html',images(user_input))
