SRC_DIR = $(shell dirname `pwd`)

all:
	rm -rf logs
	export PYTHONPATH=$(SRC_DIR) \
		&& python ../make_profiler/__main__.py -i -f example.mk all
