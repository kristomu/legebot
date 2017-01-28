#!/usr/bin/python
# -*- coding: utf-8 -*-

import parse_doc_2, urllib2, cPickle
import email, smtplib, time, random
from bs4 import BeautifulSoup
from email.mime.text import MIMEText

# 1. Load "last time we checked" information from pickle
# 2. Get web page
# 3. Spool information into a dict.
# 4. For each of the people we're interested in:
#	4.1	if any of them have values greater than the last time we checked,
#		4.1.1. send a mail
#	4.2. set "last time we checked" data to pickle.
# 5. wait some randomized time within defined limits, then go to 2.

#---#

# CONFIG

# BLUESKY: Read fylke/kommune names from the helsenorge API and
# support a text input here, e.g. "Bergen" instead of "1201"
# You can get the kommune name-number mapping by a GET request to
# https://helsenorge.no/_vti_bin/portal/rest.svc/execute?cmd=GetInitialData&OmitFylker=false
# but the page requires that you set the correct auth token data in your
# headers.

kommune = "1201"	# Kommune you want the GP vacancy data for

# Doctors/GPs you're particularly interested in
monitor_who = [u"Åserud, Erling", u"Navnesen, Navn", 
		u"Hansen, Anneli Borge"]

# Where to send the new vacancy message to

mail_user = "user@localhost"
mail_server = "localhost"

# Minimum and maximum sleep time between requests, in seconds

sleepmin = 60
sleepmax = 120

#----#

# MAIL

def send_mail(sender, recipient, subject, body, mail_server):
	msg = MIMEText(body)
	msg['Subject'] = subject
	msg['From'] = sender
	msg['To'] = recipient
	s = smtplib.SMTP(mail_server)
	s.sendmail(sender, [recipient], msg.as_string())
	s.quit()

#----#

# MAIN

# 1. Load "last time we checked" and auth information from pickle

try:
	last_seen_doc_stats = cPickle.load(open("lastseen.dat", "rb"))
	id_data = cPickle.load(open("id_data.dat", "rb"))
	last_seen_vacancies = parse_doc.get_vacancy_numbers(last_seen_doc_stats, 
		monitor_who)
except IOError:
	last_seen_doc_stats = None
	last_seen_vacancies = None
	id_data = {}

i = 0

while True:
	print "(" + str(i) + ")",
	i += 1
	
	# 2. Get web pages

	# 2.1. Refresh the auth data if required.

	if parse_doc_2.has_id_token_timed_out(id_data):
		print "Auth token is stale, refreshing."
		id_data = parse_doc_2.get_id_token_data(
			parse_doc_2.get_id_token_page())
		open("id_data.dat", "wb").write(cPickle.dumps(id_data))
	
	# 2.2. Get actual doc. info.
	doc_stats = parse_doc_2.get_doctor_data(
		parse_doc_2.get_doctor_data_page(id_data, kommune))

	vacancies = parse_doc_2.get_vacancy_numbers(doc_stats, monitor_who)

	if last_seen_vacancies == None:
		last_seen_vacancies = [-1]*len(vacancies)

	# 4. If there's an improvement...

	if any(i > j and i > 0 for i, j in zip(vacancies, last_seen_vacancies)):
		# Notify the user
		notification = "It seems some GP vacancies have opened up.\n"
		notification += "New vacancy vector:\n"
		for vacancy_result in zip(monitor_who, vacancies):
			notification += "\t" + vacancy_result[0].encode("utf-8") + ": " 
			notification += str(vacancy_result[1]) + "\n"
		send_mail(mail_user, mail_user, "GP notification", notification, mail_server)
		print notification

		# Update pickle.
		alreadyseen_file = open("lastseen.dat", "wb")
		alreadyseen_file.write(cPickle.dumps(doc_stats))
		alreadyseen_file.close()

		last_seen_doc_stats = doc_stats.copy()
		last_seen_vacancies = vacancies

	# 5. Wait some randomized time and repeat.
	time.sleep(random.randint(sleepmin, sleepmax))