
build:
	echo "__version__ = '1.0.`date +%s`'" > make_profiler/__init__.py
	python3 setup.py sdist
