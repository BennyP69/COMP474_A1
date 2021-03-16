import csv
import requests

baseURL = "https://opendata.concordia.ca/datasets/" #this will not change
categories = ["Experiential%20Learning/", "Facilities", "sis"] #this will not change
csvFiles = ["CATALOG.csv"] #we can add the different CSV files from https://opendata.concordia.ca/datasets/ that we may need here

CSV_URL = baseURL+categories[0]+csvFiles[0]

with requests.Session() as s:
	download = s.get(CSV_URL)
	decodedContent = download.content.decode('utf-8')
	cr = csv.reader(decodedContent.splitlines(), delimiter=',')
	myList = list(cr)
	for row in myList:
		print(row)

#Gotta code the "Topics" part of the assignment! - Gab