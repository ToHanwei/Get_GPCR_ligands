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
from time import sleep
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


def build_DataFrame(receptor, df):
	"""add receptor column in first column of df"""
	col = pd.DataFrame(np.array(len(df)*[receptor]), columns=["receptor"])
	df_new = col.join(df)
	return(df_new)


def write_sheet(writer, tables, id_name, receptor_name):
	"""select table from and write to sheet"""
	for table in tables:
		table_id = table.get('id')
		if table_id == id_name:
			table_df = pd.concat(pd.read_html(table.prettify()))
			drop_list = [i for i in table_df.index if i%2!=0]
			table_df = table_df.drop(drop_list, axis=0)
			drop_col = ["Unnamed: "+str(i) for i in range(1, 10)]
			table_df = table_df.drop(drop_col, axis=1)
			data_df = build_DataFrame(receptor_name, table_df)
			data_df.to_excel(writer, sheet_name=id_name, index=False, merge_cells=True)
			print("Sheet name "+receptor_name+" is add")


def drop_blank(ser):
	for i in range(len(ser)):
		try:
			ser[i] = ser[i].replace(" ", "")
		except AttributeError as e:
			pass
	return(ser)


def merge_DataFrame(data_frame, tables, id_name, receptor_name):
	"""select table from and write to sheet"""
	for table in tables:
		table_id = table.get('id')
		if table_id == id_name:
			table_df = pd.concat(pd.read_html(table.prettify()))
			#drop_list = [i for i in table_df.index if i%2!=0]
			#table_df = table_df.drop(drop_list, axis=0)
			drop_col = ["Unnamed: "+str(i) for i in range(1, 10)]
			drop_col.append("Unnamed: 15")
			table_df = table_df.drop(drop_col, axis=1)
			data_df = build_DataFrame(receptor_name, table_df)
			drop_list = [i for i in data_df.index if i%2!=0]
			data_df = data_df.drop(drop_list, axis=0).astype(object)
			data_frame = data_frame.merge(data_df, how="outer").astype(object)
	return(data_frame)


def get_ligand_ids(tables):
	"""obtain ligand id from web"""
	out_list = []
	id_names = ["agonists", "antagonists", "allosterics"]
	for table in tables:
		table_id = table.get("id")
		if table_id not in id_names: continue
		if not table.a: continue
		id_list = table.a.get("href").split("LigandDisplayForward?ligandId=")
		if len(id_list) != 2: continue
		try:
			out_list.append(int(id_list[1]))
		except : pass
	return(out_list)
			

def get_ligand_table(url_list, sub_dict):
	"""get GPCR's ligand information from web"""
	ligand_ids = []
	for familyId, objectId in sub_dict.items():
		familyId, family_name = familyId.split("#")
		family_name = clear_tag(family_name)
		file_name = family_name+".xlsx"
		#if os.path.exists(family_name):
		#	os.chdir(family_name)
		#else:
		#	os.mkdir(family_name)
		#	os.chdir(family_name)
		#	print("GPCR family "+family_name+" is begin")
		if os.path.exists(file_name): os.remove(file_name)
		writer = pd.ExcelWriter(file_name)
		data_agon = pd.DataFrame(columns=["receptor", "Ligand", "Sp.", "Action", "Affinity", "Units", "Reference"], dtype="object")
		data_anta = pd.DataFrame(columns=["receptor", "Ligand", "Sp.", "Action", "Affinity", "Units", "Reference"], dtype="object")
		data_allo = pd.DataFrame(columns=["receptor", "Ligand", "Sp.", "Action", "Affinity", "Units", "Reference"], dtype="object")
		data_refe = pd.DataFrame(columns=["reference", "link", "PMID"], dtype="object")
		print("GPCR family "+family_name+" is begin")
		for obj_id in objectId:
			obj_id = str(obj_id)
			url = url_list[0]+obj_id+url_list[1]+familyId+url_list[2]
			res = request.Request(url)
			html_doc = request.urlopen(res).read()
			soup = BeautifulSoup(html_doc, 'lxml')
			receptor_name = str(soup.title).split("|")[0][7:]
			receptor_name = clear_tag(receptor_name)
			#file_name = receptor_name + ".xlsx"
			#writer = pd.ExcelWriter(file_name)
			#print(file_name+" is over")
			tables = soup.select('table')
			ligand_ids.extend(get_ligand_ids(tables))
			data_agon = merge_DataFrame(data_agon, tables, "agonists", receptor_name)
			#print(data_agon)
			data_anta = merge_DataFrame(data_anta, tables, "antagonists", receptor_name)
			#print(data_anta)
			data_allo = merge_DataFrame(data_allo, tables, "allosterics", receptor_name)
			#print(data_allo)
			#write_sheet(writer, tables, "agonists", receptor_name)
			#write_sheet(writer, tables, "antagonists", receptor_name)
			#write_sheet(writer, tables, "allosterics", receptor_name)
			soup2 = BeautifulSoup(html_doc, 'html.parser')
			divs = soup2.select('div')
			refe_list, pmid_list, link_list = [], [], []
			refer_df = pd.DataFrame(dtype="object")
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
			refer_df = build_DataFrame(receptor_name, refer_df)
			data_refe = data_refe.merge(refer_df, how="outer")
			#refer_df.to_excel(writer, sheet_name=receptor_name+"_reference", index=False,
			#				  merge_cells=True)
			#writer.save()
		data_agon["Units"] = drop_blank(data_agon["Units"])
		data_agon["Reference"] = drop_blank(data_agon["Reference"])
		data_anta["Units"] = drop_blank(data_anta["Units"])
		data_anta["Reference"] = drop_blank(data_anta["Reference"])
		data_allo["Units"] = drop_blank(data_allo["Units"])
		data_allo["Reference"] = drop_blank(data_allo["Reference"])
		data_agon.to_excel(writer, sheet_name="agonists", index=False)
		data_anta.to_excel(writer, sheet_name="antagonists", index=False)
		data_allo.to_excel(writer, sheet_name="allosterics", index=False)
		data_refe.to_excel(writer, sheet_name="reference", index=False)
		writer.save()
		#os.chdir("../")
		print("GPCR family "+family_name+" is over")
	ligand_ids = list(set(ligand_ids))
	ligand_out = open("ligand_ids.pkl", "wb")
	pickle.dump(ligand_ids, ligand_out)
	ligand_out.close()  


def get_ligands(url, ligand_ids):
	"""obtain ligand table from web"""
	for ligand in ligand_ids:
		url += str(ligand)
		res = request.Request(url)
		html_doc = request.urlopen(res).read()
		soup = BeautifulSoup(html_doc, "lxml")
		if soup.title: 
			title = soup.title.string
			ligand_name = title.split("|")[0].strip()
			print(ligand_name)
		tables = soup.select("table")
		for table in tables:
			if table.get("id") != "Selectivity at GPCRs": continue
			table_df = pd.concat(pd.read_html(table.prettify()))
			drop_row = [i for i in range(len(table_df)) if i%2!=0]
			table_df = table_df.drop(drop_row, axis=0)
			drop_col = ["Unnamed: 1", "Unnamed: 2", "Unnamed: 10"]
			table_df = table_df.drop(drop_col, axis=1)
			#table_df.to_excel("test.xlsx", index=False)
		sleep(3)
	return(table_df)


def main():
	GPCRs_LIGAND_DIR = "./GPCRs_ligand"
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
	#subfamily_dict = get_subfamily_id(family_url, family_ids)
	infile = open("../subfamily_data.pkl", "rb")
	subfamily_dict = pickle.load(infile)
	infile.close()
	get_ligand_table(protein_url, subfamily_dict)


def main2():
	LIGANDs_GPCR_DIR = "./LIGAND"
	ligand_url = "http://www.guidetopharmacology.org/GRAC/LigandDisplayForward?tab=biology&ligandId="
	if os.path.exists(LIGANDs_GPCR_DIR):
		os.chdir(LIGANDs_GPCR_DIR)
	else:
		os.mkdir(LIGANDs_GPCR_DIR)
		os.chdir(LIGANDs_GPCR_DIR)
	#family_ids = get_family_id(gpcrs_url)
	#subfamily_dict = get_subfamily_id(family_url, family_ids)
	infile = open("../ligand_ids.pkl", "rb")
	ligand_ids = pickle.load(infile)
	infile.close()
	get_ligands(ligand_url, ligand_ids)
    


if __name__ == "__main__":
    main2()
