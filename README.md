    sudo apt install python3-pip graphviz
    pip3 install more_itertools

Example of usage:

    python3 preprocess.py -i Makefile -o Makefile_work.mk
    make -j -k -f Makefile_work.mk
    python3 dot_export.py -i Makefile -db profile.db > make.dot
    xdg-open make.png

