#!coding:utf-8

from module import *

def main():
	infile = open("subfamily_data.pkl", "rb")
	subfamily_dict = load(infile)
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
	infile.close()
	get_receptors(protein_url, subfamily_dict)
    

if __name__ == "__main__":
    main()
