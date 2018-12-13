# -*- coding: utf-8 -*-

from module import *


def clear_tag(obj_name):
	"""Search and claer pair tag"""
	obj_name = obj_name.strip()
	start = re.compile("<.*?>")
	end = re.compile("</.*?>")
	tag_start = re.search(start, obj_name)
	tag_end = re.search(end, obj_name)
	if tag_start and tag_end:
		tag_start = tag_start.group()
		tag_end = tag_end.group()
		obj_name = obj_name.replace(tag_start, "").replace(tag_end, "")
	obj_name = obj_name.replace("/", "_")
	return(obj_name)


def write_sheet(writer, tables, id_name, ligand_name):
	"""select table from and write to sheet"""
	for table in tables:
		table_id = table.get('id')
		if table_id == id_name:
			table_df = pd.concat(pd.read_html(table.prettify()))
			drop_list = [i for i in table_df.index if i%2!=0]
			table_df = table_df.drop(drop_list, axis=0)
			drop_col = ["Unnamed: "+str(i) for i in range(1, 10)]
			table_df = table_df.drop(drop_col, axis=1)
			table_df.to_excel(writer, sheet_name=id_name, index=False)
			print("Sheet name "+ligand_name+" is add")



def get_ligand_table(url_list, sub_dict):
	"""get GPCR's ligand information from web"""
	for familyId, objectId in sub_dict.items():
		familyId, family_name = familyId.split("#")
		family_name = clear_tag(family_name)
		if os.path.exists(family_name):
			os.chdir(family_name)
		else:
			os.mkdir(family_name)
			os.chdir(family_name)
			print("GPCR family "+family_name+" is begin")
		for obj_id in objectId:
			obj_id = str(obj_id)
			url = url_list[0]+obj_id+url_list[1]+familyId+url_list[2]
			res = request.Request(url)
			html_doc = request.urlopen(res).read()
			soup = BeautifulSoup(html_doc, 'lxml')
			ligand_name = str(soup.title).split("|")[0][7:]
			ligand_name = clear_tag(ligand_name)
			file_name = ligand_name + ".xlsx"
			writer = pd.ExcelWriter(file_name)
			print(file_name+" is over")
			tables = soup.select('table')
			write_sheet(writer, tables, "agonists", ligand_name)
			write_sheet(writer, tables, "antagonists", ligand_name)
			write_sheet(writer, tables, "allosterics", ligand_name)
			soup2 = BeautifulSoup(html_doc, 'html.parser')
			divs = soup2.select('div')
			refe_list, pmid_list, link_list = [], [], []
			refer_df = pd.DataFrame()
			for div in divs:
				div_id = div.get('id')
				if div_id != "refs": continue
				pattern = re.compile("http://.*?\d{5,}")
				ps = div.find_all('p')
				for ps_line in ps:
					#obtain reference and PMID from <p> tage'string
					reference = ""
					for line in ps_line.strings:
						reference += line.strip()
					refer_list = reference.split(" "*3+"[")
					refe_list.append(refer_list[0].strip())
					try:
						pmid = refer_list[1].replace("]", "")
					except IndexError as e:
						pmid = "PMID:None"
					pmid_list.append(pmid.split(":")[1])
					#obtain link from <a> "herf" of <p>
					try:
						link = re.search(pattern, ps_line.a.get("href")).group()
					except AttributeError as e:
						link = "None"
					link_list.append(link)
			refer_df["reference"] = refe_list
			refer_df["link"] = link_list
			refer_df["PMID"] = pmid_list
			refer_df.to_excel(writer, sheet_name="reference", index=False)
			writer.save()
			#df = pd.concat(raw_list)
			#df.to_csv("test.csv")
		os.chdir("../")
