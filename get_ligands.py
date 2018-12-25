# -*- coding: utf-8 -*-
"""
get ligands from web
"""
from module import *

def drop_blank(ser):
	#print(ser)
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


def get_ligands(url, url2, ligand_ids):
	"""obtain ligand table from web"""
	data = pd.DataFrame(columns=["Ligand", "Target", "Sp.", "Type", "Action", "Affinity", 
								 "Units",  "Reference"])
	data_ref = pd.DataFrame(columns=['ligand'])
	for ligand in ligand_ids:
		print(ligand)
		ligand_url = url + str(ligand)
		res = request.Request(ligand_url)
		html_doc = request.urlopen(res).read()
		soup = BeautifulSoup(html_doc, "lxml")
		if soup.title: 
			title = soup.title.string
			ligand_name = title.split("|")[0].strip()
			ligand_name = clear_tag(ligand_name)
			print(ligand_name)
		tables = soup.select("table")
		for table in tables:
			if table.get("id") != "Selectivity at GPCRs": continue
			table_df = pd.concat(pd.read_html(table.prettify()))
			drop_row = [i for i in range(len(table_df)) if i%2!=0]
			table_df = table_df.drop(drop_row, axis=0)
			drop_col = ["Unnamed: 1", "Unnamed: 2", "Unnamed: 10", "Concentration range (M)"]
			table_df = table_df.drop(drop_col, axis=1)
			table_df.index = range(len(table_df))
			#index = np.array(range(len(table_df)))*2
			col = pd.DataFrame(np.array(len(table_df)*[ligand_name]), 
							   columns=["Ligand"])
			fram = col.join(table_df).astype(object)
			fram["Units"] = drop_blank(fram["Units"])
			fram["Reference"] = drop_blank(fram["Reference"])
			data = data.append(fram)
		#get reference of ligand
		ligand_ref = url2 + str(ligand)
		res2 = request.Request(ligand_ref)
		html_doc2 = request.urlopen(res2).read()
		soup2 = BeautifulSoup(html_doc2, "lxml")
		tables2 = soup2.select("table")
		for table2 in tables2:
			if table2.get("class")[0] != "receptor_data_tables": continue
			table2_ref = pd.concat(pd.read_html(table2.prettify()))
			col_ref = pd.DataFrame(np.array(len(table2_ref)*[ligand_name]), columns=['ligand'])
			data_ref = data_ref.append(col_ref.join(table2_ref)[1:])
	data.index = range(len(data))
	data["Units"] = drop_blank(data["Units"])
	data["Reference"] = drop_blank(data["Reference"])
	data_ref.columns = ["ligand", "References"]
	print(data_ref)
	return(data, data_ref)


def main():
	LIGANDs_GPCR_DIR = "./LIGAND"
	ligand_url = "http://www.guidetopharmacology.org/GRAC/LigandDisplayForward?tab=biology&ligandId="
	ligand_ref = "http://www.guidetopharmacology.org/GRAC/LigandDisplayForward?tab=refs&ligandId="
	if os.path.exists(LIGANDs_GPCR_DIR):
		os.chdir(LIGANDs_GPCR_DIR)
	else:
		os.mkdir(LIGANDs_GPCR_DIR)
		os.chdir(LIGANDs_GPCR_DIR)
	writer = pd.ExcelWriter("Ligands_GPCR.xlsx")
	infile = open("../ligand_ids.pkl", "rb")
	ligand_ids = load(infile)
	gpcr_ligand, ligand_ref = get_ligands(ligand_url, ligand_ref, ligand_ids)
	gpcr_ligand.to_excel(writer, sheet_name="ligands", index=False)
	ligand_ref.to_excel(writer, sheet_name="references", index=False)
	writer.save()
	infile.close()


if __name__ == "__main__":
    main()
