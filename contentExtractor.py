from tika import parser # Must have a java(7 or 7+) runtime installed as well
import spotlight
import os
import re

# Recusively getting all PDFs for every course we have the data for within the COURSES/ folder.
pdfs = [os.path.join(dp, f) for dp, dn, filenames in os.walk("COURSES/") for f in filenames if os.path.splitext(f)[1] == '.pdf']

# Creating the text file to save topics
courseTopicsTextFile = open("courseTopics.txt", "w")

for pdf in pdfs:
	pdf = pdf.replace("\\", "/")

	# Skip Outlines
	if "Outline" in pdf:
		continue

	# Extracting contents of the pdf file. https://www.geeksforgeeks.org/parsing-pdfs-in-python-with-tika/

	# Opening PDF file
	parsed_pdf = parser.from_file(pdf) #sample.pdf
	print("Processing " + pdf)

	# Saving content of PDF
	# To get the text only, use parsed_pdf['text'] - parsed_pdf['content'] returns string
	data = parsed_pdf['content']

	# Linking of content to dbpedia resource
	annotations = spotlight.annotate('https://api.dbpedia-spotlight.org/en/annotate', data, confidence=0.4, support=20)

	# To keep duplicates from being written to the file
	linesSeen = set() # Holds lines already seen

	# Adding the topics
	for elt in annotations:
		# Writing the topic data in the text file - topicLabel topic_dbpedia_URI PDF_URI COURSE-COMPONENT-#
		line = re.sub('[^A-Za-z0-9_-]+', '', elt.get("URI").replace("http://dbpedia.org/resource/", "")) + " " + elt.get("URI") + " " + pdf + " " + pdf.split("/")[1] + "-" + pdf.split("/")[2] + "-" + re.findall('[0-9]+', pdf.split("/")[-1])[0] + "\n"
		if line not in linesSeen and not line == "": # If the line is not a duplicate and it is not empty, add it to the topics file
			courseTopicsTextFile.write(line)
			linesSeen.add(line)

# Showing where the new file can be found
print("The Couse Topics File has been saved as " + courseTopicsTextFile.name + " in " + os.getcwd())

# Closing and saving the text file with the data
courseTopicsTextFile.close()