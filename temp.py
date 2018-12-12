# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import os
import re
import pickle
import numpy as np
import pandas as pd
from urllib import request
from bs4 import BeautifulSoup
from collections import defaultdict
from html.parser import HTMLParser

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
	return family_id_list[7:]	#1-6 of this list is ClassId


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
        

def main():
	GPCRs_LIGAND_DIR = "./CPCRs_ligand"
	gpcrs_url = "http://www.guidetoimmunopharmacology.org/GRAC/ReceptorFamiliesForward?type=GPCR"
	family_url = "http://www.guidetoimmunopharmacology.org/GRAC/FamilyDisplayForward?familyId="
	protein_url = ["http://www.guidetoimmunopharmacology.org/GRAC/ObjectDisplayForward?objectId=", 
                   "&familyId=", "&familyType=GPCR"]	
	if os.path.exists(GPCRs_LIGAND_DIR):
		os.chdir(GPCRs_LIGAND_DIR)
	else:
		os.mkdir(GPCRs_LIGAND_DIR)
		os.chdir(GPCRs_LIGAND_DIR)
	#family_ids = get_family_id(gpcrs_url)
	#family_ids = [1, 2, 3, 17, 4, 6, 7, 8, 9, 10, 11, 12, 13, 338, 14, 15, 25, 5, 19, 20, 21, 22, 23, 24, 26, 27, 28, 29, 30, 31, 114, 33, 48, 34, 35, 36, 135, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 50, 51, 447, 52, 53, 55, 56, 57, 58, 59, 54, 60, 61, 446, 62, 63, 64, 65, 66, 67]
	#subfamily_dict = get_subfamily_id(family_url, family_ids)
	#subfamily_dict = {"1#5-Hydroxytryptamine": [1]}
	infile = open("subfamily_data.pkl", "rb")
	subfamily_dict = pickle.load(infile)
	infile.close()
	#subfamily_dict = {'1#5-Hydroxytryptamine_receptors': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 648, 11, 12], '2#Acetylcholine_receptors_(muscarinic)': [13, 14, 15, 16, 17], '3#Adenosine_receptors': [18, 19, 20, 21], '17#Adhesion_Class_GPCRs': [197, 198, 199, 174, 175, 176, 178, 179, 180, 202, 204, 182, 183, 184, 185, 177, 190, 191, 193, 195, 196, 186, 187, 188, 192, 194, 200, 201, 206, 207, 208, 181, 189], '4#Adrenoceptors': [22, 23, 24, 25, 26, 27, 28, 29, 30]}
	get_ligand_table(protein_url, subfamily_dict)
    


if __name__ == "__main__":
    main()
