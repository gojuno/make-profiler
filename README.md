#Makefile Profiler

Helps managing a large data processing pipeline written in Makefile.

##Features

* SVG build overview (example: https://github.com/gojuno/make-profiler/blob/master/make.svg);

* Inline pictures-targets into build overview;

* Logs for each target marked with timestamps;

* Distinguish a failed target execution from forgotten touch;

* Navigate to last run's logs from each target directly from call graph;

* Support for self-documented Makefiles according to 
http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html

##Example usage

    pip install make-profiler

    cd your_project
    make_profiler -h                # have a look at help

    make_profiler                   # generate overview graph without profiling data
    xdg-open make.svg               # have a look at call graph

    make_profiler_clean target_to_remove_with_children

    make_profiler -j -k target_name # run some target, record execution times and logs
    xdg-open make.svg               # have a look at call graph with timing data
