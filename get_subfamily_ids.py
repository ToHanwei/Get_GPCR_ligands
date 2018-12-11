from module import *

def load_data(file_name):
	infile = open(file_name, "rb")
	family_ids = load(infile)
	infile.close()
	return(family_ids)


def get_subfamily_id(url, sub_ids):
	"""get objectId of GPCR from web"""
	#this dict's key is familyId, and value is objectId list
	subfamily_id_dict = defaultdict(list)
	for sub_id in sub_ids:
		#traverse familyId
		url_update = url + str(sub_id)
		res = request.Request(url_update)
		html_doc = request.urlopen(res).read()
		soup = BeautifulSoup(html_doc, 'html.parser')
		family_name = soup.title.string.split("|")[0].strip().replace(" ", "_")
		subfamily_id_list = []
		for tag in soup('div'):
			target = tag.get('id')
			if target:
				try:
					#obtain objectId
					obj_id = int(target.split("_")[-1])
					subfamily_id_list.append(obj_id)
				except ValueError as e:
					pass
		key = str(sub_id)+"#"+family_name
		subfamily_id_dict[key] = subfamily_id_list
	return subfamily_id_dict


def dump_data(data, file_name):
	outfile = open(file_name, "wb")
	dump(data, outfile)
	outfile.close()


def main():
	family_url = "http://www.guidetoimmunopharmacology.org/GRAC/FamilyDisplayForward?familyId="
	family_ids = load_data("family_ids.pkl")
	subfamily_dict = get_subfamily_id(family_url, family_ids)
	dump_data(subfamily_dict, "subfamily_data.pkl")


if __name__ == "__main__":
	main()
