all:
	rm -rf logs
	cat example.mk|python ../preprocess.py > work.mk
	make -f work.mk
	cat example.mk|python ../dot_export.py > work.dot
	dot -Tpng work.dot > work.png
