    sudo apt install python3-pip graphviz
    pip3 install more_itertools

Example of usage:

    ./preprocess.py -i Makefile_template -o Makefile
    ./clean.py -i Makefile_template any_targets you_like
    make -j -k
    ./dot_export.py -i Makefile_template
    xdg-open make.png