#!/usr/bin/python
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import json, re, datetime, dateutil.parser, requests

initialfile = open("bytte-fastlege", "r")
initialpage = initialfile.read()

# First page (authenticator)

def get_id_token_page():
	URL = "https://helsenorge.no/min-helse/bytte-fastlege"
	return requests.get(URL).text

def get_id_token_data(page):
	# The ID data we need is primarily HN.Rest.__AnonymousHash__ and 
	# HN.Rest.__HNTimeStamp__. These are located inside a <script> tag as
	# Javascript assignment commands.

	# Find the <script> that contains the data, and extract the text from
	# it.
	soup = BeautifulSoup(page, "lxml")
	raw_id_vars = next(script.text for script in soup.find_all("script") if 
		"HN.Rest.__AnonymousHash__" in script.text)

	# Parse the JS data. https://stackoverflow.com/questions/18368058/
	id_tuples = re.findall(r'(.*?)=\s*(.*?);', raw_id_vars, re.DOTALL 
		| re.MULTILINE)

	# Dump the data into a dictionary and add a parsed timestamp as a datetime.
	id_data = {key.strip(): json.loads(value) for (key, value) in id_tuples}
	id_data["__ParsedTimeStamp__"] = dateutil.parser.parse(
		id_data["HN.Rest.__TimeStamp__"])

	return id_data

def has_id_token_timed_out(id_data):
	if not "HN.Rest.__TimeStamp__" in id_data:
		return True

	now = datetime.datetime.now(dateutil.tz.tzutc())
	since_token_granted = now  - id_data["__ParsedTimeStamp__"]

	return since_token_granted.total_seconds() * 1000 > \
    	id_data["HN.Rest.__TokenLifetime__"]

# Second page (actual GP availability data)

def get_doctor_data_page(id_data, kommune=None, bydel=None, legenavn=None):
	URL="https://helsenorge.no/_vti_bin/portal/rest.svc/execute?cmd=AvtaleSok"

	# This page expects auth data (AnonymousHash and TimeStamp) as part of the
	# headers, and the query fields (kommune, bydel, legenavn) as a JSON
	# body, delivered by POST.

	payload = {}

	if kommune:
		payload["Kommuner"] = [kommune]
	if bydel:
		payload["Bydeler"] = [bydel]
	if legenavn:
		payload["Legenavn"] = legenavn

	headers = { 'Content-Type': 'application/json',
				'HNAnonymousHash': id_data["HN.Rest.__AnonymousHash__"],
				'HNTimeStamp': id_data["HN.Rest.__TimeStamp__"]}

	response = requests.post(URL, data=json.dumps(payload), headers=headers)

	return response.text

def get_doctor_data(page):
	# We get JSON data directly.
	return json.loads(page)

# The previous parse_doc API, such as it is, was:
# Input to the check vacancies function is a list of names in Unicode format,
# as 'Lastname, Firstname', e.g.
# monitor_who = ["Hansen, Anneli Borge", u"Navnesen, Navn"]
# and returns a list of vacancy numbers, where the corresponding number is -1
# if the name was not found.
# We'll code to that "spec".

def get_vacancy_numbers(doctor_data, relevant_doctors, deleliste=True):
	vacancy_dict = {}

	for doc_entry in doctor_data["Resultater"]["Resultater"]:
		name = (doc_entry["Fastlege"]["Etternavn"] + ", " + \
			doc_entry["Fastlege"]["Fornavn"])
		vacancy_dict[name.lower()] = doc_entry["LedigePlasser"]

		if not deleliste or not doc_entry.get("Delelistelege", None):
			continue

		name = (doc_entry["Delelistelege"]["Etternavn"] + ", " + \
			doc_entry["Delelistelege"]["Fornavn"])
		vacancy_dict[name.lower()] = doc_entry["LedigePlasser"]

	vacancies_all = [vacancy_dict.get(relevant_doc.lower(), -1) for 
		relevant_doc in relevant_doctors]

	return vacancies_all

def test_vacancies():
	doctor_data = get_doctor_data(open("test-fastlege-data", "r").read())

	doctors = [u"Åserud, Erling", u"Navnesen, Navn", 
		u"Hansen, Anneli Borge"]

	expected_result = [11, -1, 0]

	return expected_result == get_vacancy_numbers(doctor_data, doctors)

# Tests
if __name__ == '__main__':
	with open ("bytte-fastlege", "r") as docfile:
		docpage = docfile.read()

	id_data = get_id_token_data(docpage)
	# These should return True
	print "Should return true:"
	print id_data["HN.Rest.__AnonymousHash__"] == u'RlVaJ4hcaJ4NA8rx20CWNRRnpMoiWzNbg6wijXJ1UbA1'
	print has_id_token_timed_out(id_data)
	print test_vacancies()