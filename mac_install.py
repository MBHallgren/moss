import  os

#IMPORTANT NOT
#THE MOSS SYSTEM DOES NOT WORK ON A MAC.
#THIS SCRIPT WILL ONLY INSTALL MINIMUM REQUIREMENTS TO ALLOW FOR FRONT-END GUI DEVELOPMENT ON A MAC.

def main():
    print("Sudo is required for apt update")
    cmd = "/bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    os.system(cmd)
    cmd = "xcode-select --install"
    os.system(cmd)
    cmd = "brew install node@10"
    os.system(cmd)
    cmd = "brew install curl"
    os.system(cmd)
    print("Installing KMA")
    cmd = "git clone https://bitbucket.org/genomicepidemiology/kma.git; cd kma; git checkout nano; make; cd ..;"
    os.system(cmd)
    print("Installing CCphylo")
    cmd = "git clone https://bitbucket.org/genomicepidemiology/ccphylo.git; cd ccphylo && make; cd ..;"
    os.system(cmd)
    cmd = "curl -O https://bootstrap.pypa.io/ez_setup.py; python3 ez_setup.py; curl -O https://bootstrap.pypa.io/get-pip.py; python3 get-pip.py;"
    os.system(cmd)
    cmd = "brew install r"
    os.system(cmd)
    findersinstall()
    cmd = "python3 -m pip install fpdf"
    os.system(cmd)
    cmd = "pip install geocoder"
    os.system(cmd)
    cmd = "pip install geopy"
    os.system(cmd)
    cmd = "npm install mkdirp"
    os.system(cmd)
    cmd = "pip install Nominatim"
    os.system(cmd)
    print("Installing docker")
    cmd = "brew install docker;"
    os.system(cmd)
    #cmd = "newgrp docker"
    #os.system(cmd)
    #softwareupdate --install --all


def findersinstall():
    cmd = "python3 -m pip install tabulate biopython cgecore gitpython python-dateutil"
    os.system(cmd)
    cmd = "git clone https://bitbucket.org/genomicepidemiology/mlst.git; cd mlst; git checkout nanopore; git clone https://bitbucket.org/genomicepidemiology/mlst_db.git; cd mlst_db; git checkout nanopore; python3 INSTALL.py ../../kma/kma_index; cd ..; cd ..;"
    os.system(cmd)
    cmd = "git clone https://git@bitbucket.org/genomicepidemiology/resfinder.git; cd resfinder; git checkout nanopore_flag; cd cge; git clone https://bitbucket.org/genomicepidemiology/kma.git; cd kma && make; cd ..; curl -O ftp://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/2.10.1/ncbi-blast-2.10.1+-x64-linux.tar.gz; tar zxvpf ncbi-blast-2.10.1+-x64-linux.tar.gz; cd ..; git clone https://git@bitbucket.org/genomicepidemiology/resfinder_db.git db_resfinder; cd db_resfinder; git checkout minimizer_implementation; python3 INSTALL.py ../../kma_index non_interactive; cd ..; git clone https://git@bitbucket.org/genomicepidemiology/pointfinder_db.git db_pointfinder; cd db_pointfinder; python3 INSTALL.py ../../kma non_interactive; cd ..; cd ..;"
    os.system(cmd)
    cmd = "git clone https://bitbucket.org/genomicepidemiology/plasmidfinder.git; cd plasmidfinder; git clone https://bitbucket.org/genomicepidemiology/plasmidfinder_db.git; cd plasmidfinder_db; python3 INSTALL.py ../../kma/kma_index; cd ..; cd ..;"
    os.system(cmd)
    cmd = "git clone https://bitbucket.org/genomicepidemiology/virulencefinder.git; cd virulencefinder; git clone https://bitbucket.org/genomicepidemiology/virulencefinder_db.git; cd virulencefinder_db; python3 INSTALL.py ../../kma/kma_index; cd ..; cd ..;"
    os.system(cmd)


#Docker install missing

if __name__ == '__main__':
    main()