
VAR1:='value'
VAR2=$(shell pwd)

NAME=some_name

all: \
	target1 \
	forgot_to_implement \
	fails \
	target3 | target4 target_order_only_directory ## Order only dependencies usually just clutter the graph so not rendered
	touch $@

not_all: target1 target2 cat_graph.png ## Second result target, builds just a part of pipeline

$(NAME): ## We don't support variable substitution - names rendered as is and no color inferred
	sleep 1
	touch $@

target1: target11 target12 target13 forgot_to_touch
ifeq ($(BUILD_TYPE),QA)
	echo 'target1: qa build'
else
	echo 'target1: build'
endif
	touch $@

target11:
	sleep 1
	touch $@

target12:
	sleep 1
	touch $@

cat_graph.png: target2 ## If your target generates visual content, it will be embedded into graph
	wget https://laurensmemory.files.wordpress.com/2011/05/20110526-092336.jpg -O $@

target13: target11 ## Sibling dependency 13 -> 11 is non-essential, thus rendered in grey
	sleep 2
	touch $@

forgot_to_touch: target11 ## Forgot to touch the file, visible in graph
	sleep 1

tool_target: ## Tool targets are the ones that don't depend on anything and nobody depends on them. Think 'clean'
	sleep 1
	touch $@

clean: ## Clean up things from previuous runs
	make_profile_clean target_order_only_1

target2:
	sleep 2
	touch $@

target3: $(NAME)
	sleep 3
	touch $@

target4:
	for num in '5' '1' '3' '4' '5' '2' '4' ; do \
		echo "$${num}";\
	done \
		| sort | uniq
	sleep 5
	touch $@

target_order_only_directory: ## Order only target should just be present. Useful for directories
	mkdir -p $@

fails: target11 ## This target fails, thus rendered in red
	sh -c 'exit 1'