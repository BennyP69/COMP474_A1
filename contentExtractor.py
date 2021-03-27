import csv
import os
import io
import re
import PyPDF2
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfpage import PDFPage

def getFileNames(path):
	return os.listdir(path)

def searchFile(path, fileName):
    for root, dirs, files in os.walk(path):
        if fileName in files:
            return os.path.join(root, fileName)

def readPDF(name):
    pdfFileObj = open(name, 'rb') #PDF name
    pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
    print(pdfReader.numPages)
    pageObj = pdfReader.getPage(0)
    print(pageObj.extractText())
    pdfFileObj.close()

def extract_text_by_page(pdf_path):
	with open(pdf_path, 'rb') as fh:
		for page in PDFPage.get_pages(fh, caching=True, check_extractable=True):
			resource_manager = PDFResourceManager()
			fake_file_handle = io.StringIO()
			converter = TextConverter(resource_manager, fake_file_handle)
			page_interpreter = PDFPageInterpreter(resource_manager, converter)
			page_interpreter.process_page(page)

			text = fake_file_handle.getvalue()
			yield text

	# close open handles
	converter.close()
	fake_file_handle.close()

def export_as_csv(pdf_path, csv_path):
	filename = os.path.splitext(os.path.basename(pdf_path))[0]

	counter = 1
	with open(csv_path, 'w') as csv_file:
		writer = csv.writer(csv_file)
		for page in extract_text_by_page(pdf_path):
			text = page[0:100]
			words = text.split()
			writer.writerow(words)


if __name__ == '__main__':
	PATH = "COURSES/"
	COURSE = "COMP346/"
	COMPONENT = "LEC/"
	
	topics346 = getFileNames(PATH + COURSE + COMPONENT)

	for topic in topics346:
		topic = re.sub(r'[0-9]+', '', topic.replace("Lecture", "").replace(".pdf", "").replace('-', "").replace("_", " "))

	#COMP474 PDFs are unreadable...
	topics474 = ["Intelligent Systems", "Knowledge Graphs", "RDF", "Vocabularies", "Ontologies", "RDFS",
			 "OWL", "Knowledge Base Queries", "SPARQL", "Linked Open Data",
			 "Personalization & Recommender Systems", "Machine Learning",
			 "Natural Language Processing", "Text Mining",
			 "Artificial Neural Networks", "Deep Learning"]
	
	#FOR A1, I will copy the topics into topics.txt manually. - Gab