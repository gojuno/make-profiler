
VAR1:='value'
VAR2=$(shell pwd)

NAME='some_name'

all: \
	target1 \
	target2 \
	target3 | target4 target5


$(NAME):
	sleep 1

target1: target11 target12 target13
ifeq ($(BUILD_TYPE),QA)
	echo 'target1: qa build'
else
	echo 'target1: build'
endif

target11:
	sleep 1

target12:
	sleep 1

target13: target11
	sleep 2


target2:
	sleep 2

target3: $(NAME)
	sleep 3

target4:
	for num in '5' '1' '3' '4' '5' '2' '4' ; do \
		echo "$${num}";\
	done \
		| sort | uniq
	sleep 5

target5:
	sleep 5
