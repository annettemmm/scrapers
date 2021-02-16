
import requests
import csv
import re
from requests import Request, Session
#from bs4 import BeautifulSoup
from collections import OrderedDict

MAIN_DOMAIN = 'https://ssb1.ccsf.edu:8105'

MAIN_SEARCH_PAGE = 'https://ssb1.ccsf.edu:8105/StudentRegistrationSsb/ssb/term/termSelection?mode=search'
GET_SEMESTERS_URL = 'https://ssb1.ccsf.edu:8105/StudentRegistrationSsb/ssb/classSearch/getTerms?'#searchTerm=&offset=1&max=4'#&_=1613108752285'
POST_SEARCH_SEMESTER = 'https://ssb1.ccsf.edu:8105/StudentRegistrationSsb/ssb/term/search?mode=search'
NEXT_SEARCH_GET = 'https://ssb1.ccsf.edu:8105/StudentRegistrationSsb/ssb/classSearch/classSearch'
GET_SUBJECTS_URL = 'https://ssb1.ccsf.edu:8105/StudentRegistrationSsb/ssb/classSearch/get_subject?' #ssearchTerm=&term=&offset=1&max=10&uniqueSessionId=9tn2q1613108078225&_=1613111019755'
GET_DEPARTMENTS_URL = 'https://ssb1.ccsf.edu:8105/StudentRegistrationSsb/ssb/classSearch/get_department?' #searchTerm=&term=202131&offset=1&max=10&uniqueSessionId=9tn2q1613108078225&_=1613111080375'
SEARCH_CLASSES = 'https://ssb1.ccsf.edu:8105/StudentRegistrationSsb/ssb/searchResults/searchResults?'#txt_subject=%s&txt_term=%s&startDatepicker=&endDatepicker=&uniqueSessionId=lomf11613113652936&pageOffset=0&pageMaxSize=10&sortColumn=subjectDescription&sortDirection=asc'
RESET_URL = 'https://ssb1.ccsf.edu:8105/StudentRegistrationSsb/ssb/classSearch/resetDataForm'

YEARS_TO_FETCH = 10*3
MAX_SEARCH_RESULTS = 100


def reset_search(sesh):
	sesh.post('https://ssb1.ccsf.edu:8105/StudentRegistrationSsb/ssb/classSearch/resetDataForm')


def get_json(sesh, url, params={}):
	try:
		response = sesh.get(url, params=params)
		response.raise_for_status()
		return response.json()
	except requests.exceptions.RequestException as e:
		print("Request Error: %s" % e)
	except Exception as e:
		print ("other error: %s" % e) 


def get_subjects(sesh, term):
	params = {
		'term': term,
		'offset': 1,
		'max': MAX_SEARCH_RESULTS,
	}
	return get_json(sesh, GET_SUBJECTS_URL, params=params)


def get_classes_for_subject(sesh, subject_code, term_code):
	params = {
		'txt_subject': subject_code,
		#'txt_department': '',
		'txt_term': term_code,
		'startDatepicker': '',
		'endDatepicker': '',
		'pageOffset': 0,
		'pageMaxSize': MAX_SEARCH_RESULTS,
		'sortColumn': 'subjectDescription',
		'sortDirection': 'asc'
	}
	result = get_json(sesh, SEARCH_CLASSES, params=params)
	reset_search(sesh)
	return result['totalCount']


def get_data():
	sesh = Session()
	data = OrderedDict()
	column_keys = ['semester', 'all credit', 'all noncredit']
	#import pdb; pdb.set_trace()
	semesters = get_json(sesh, GET_SEMESTERS_URL, {
		'offset': 1,
		'max': YEARS_TO_FETCH
		})

	for term in semesters:
		term_name = term['description']
		classes = {}

		noncredit = ''
		if re.search('Noncredit', term_name):
			noncredit = ' NC'
		all_type = 'all noncredit' if noncredit else 'all credit'

		term_code = term['code']
		post_req = sesh.post(url=POST_SEARCH_SEMESTER, data={'term': term_code})

		print('fetching classes for %s' % term_name)

		subjects = get_subjects(sesh, term_code)
		classes[all_type] = get_classes_for_subject(sesh, '', term_code)
		for subject in subjects:
			num_classes = get_classes_for_subject(sesh, subject['code'], term_code)
			class_name = subject['description'] + noncredit
			classes[class_name] = num_classes
			if class_name not in column_keys:
				column_keys.append(class_name)

		result = re.match('(Spring|Fall|Summer) \d{4}', term_name)
		if not result:
			print ('error no match %s' % term_name)
		simp_term_name = result.group()
		if simp_term_name not in data:
			classes['semester'] = simp_term_name
			data[simp_term_name] = classes
		else:
			data[simp_term_name].update(classes)

	return column_keys, data
	

def write_csv(column_keys, data):
	print('Writing csv file')
	csv_file = "class.csv"
	try:
		with open('../data/' + csv_file, 'w') as file:
			writer = csv.DictWriter(file, fieldnames=column_keys)
			writer.writeheader()
			for term, class_data in data.items():
				print('writing data for %s' % term)
				writer.writerow(class_data)
			
				
	except IOError:
		print('aah')

def main():
	column_keys, data = get_data()
	write_csv(column_keys, data)

if __name__ == "__main__":
	main()