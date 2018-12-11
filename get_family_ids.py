from module import *

def get_family_id(url):
	"""get familyId of GPCR family from web"""
	res = request.Request(url)
	html_doc = request.urlopen(res).read()
	soup = BeautifulSoup(html_doc, 'html.parser')
	family_id_list = []
	for tag in soup('a'):
		link = tag.get('href')
		if link:
			try:
				#obtain the id
				fam_id = int(link.split("familyId=")[-1])
				family_id_list.append(fam_id)
			except ValueError as e:
				pass
	family_ids = family_id_list[7:]
	return(family_ids)


def dump_data(data, file_name):
	"""save python object to file"""
	output = open(file_name, "wb")
	dump(data, output)
	output.close()


def main():
	gpcrs_url = "http://www.guidetoimmunopharmacology.org/GRAC/ReceptorFamiliesForward?type=GPCR"
	family_ids = get_family_id(gpcrs_url)
	dump_data(family_ids, "family_ids.pkl")


if __name__ == "__main__":
	main()
