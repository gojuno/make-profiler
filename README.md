    sudo apt install python3-pip graphviz
    pip3 install more_itertools

Example of usage:

    ./preprocess.py -i Makefile_template -o Makefile
    ./clean.py -i Makefile_template any_targets you_like
    make -j -k
    ./dot_export.py -i Makefile_template
    xdg-open make.png

Features:

* SVG build overview;

* inlining of images into build overview;

* Logs for each target marked with timestamps;

* Easily distinguish a failed target execution from failed touch;

* Support for self-documented Makefiles according to 
http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html;