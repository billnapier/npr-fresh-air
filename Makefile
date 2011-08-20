
DEPLOY_DIR=deploy
PYTHON=python2.5
APPENGINE_SDK_PATH=/home/napier/Downloads/google_appengine
APPCFG=$(PYTHON) $(APPENGINE_SDK_PATH)/appcfg.py
DEV_APPSERVER=$(PYTHON) $(APPENGINE_SDK_PATH)/dev_appserver.py
CP=cp
SOY_COMPILER=java -jar external/closure/templates/SoyToJsSrcCompiler.jar
CLOSURE_BUILDER=external/closure/closure/bin/build/closurebuilder.py

CLOSURE_BUILDER_ARGS=--root external/closure/closure --root=external/closure/third_party/ --root=static --root=templates --output_mode=compiled --compiler_jar=external/closure/compiler/compiler.jar


# closure-library
closure_lib_goog_files := $(foreach f,$(filter %.js %.css,$(shell find external/closure/closure/goog)),$(DEPLOY_DIR)/static/$(subst external/closure/closure,closure,$(f)))
closure_lib_css_files := $(foreach f,$(filter %.css,$(shell find external/closure/closure/css)),$(DEPLOY_DIR)/static/$(subst external/closure/closure,closure,$(f)))
closure_lib_files := $(closure_lib_goog_files) $(closure_lib_css_files)

SOY_ARGS=--shouldProvideRequireSoyNamespaces

# Set up compiling soy templates
soy_templates_files := $(foreach f,$(filter %.soy,$(shell ls templates)),$f)
soy_templates_output_files := $(soy_templates_files:.soy=.js)
soy_templates_depends := $(foreach f,$(soy_templates_output_files),$(DEPLOY_DIR)/static/$(f))

template_files := $(foreach f,$(filter-out %~,$(filter %.html,$(shell ls templates))),$(DEPLOY_DIR)/templates/$f)
appengine_files := $(foreach f,$(filter-out %_test.py,$(filter %.yaml %.py,$(shell find appengine))),$(subst appengine/,,$(DEPLOY_DIR)/$(f)))

static_files:=$(foreach f,$(shell ls static),$(DEPLOY_DIR)/static/$f)
compiled_js_files:=$(foreach f,$(filter %.js,$(shell ls static)),$(DEPLOY_DIR)/static/$(subst .js,_compiled.js,$(f)))

soyutils_depends=$(DEPLOY_DIR)/static/soyutils.js $(DEPLOY_DIR)/static/soyutils_usegoog.js

dist: $(soy_templates_depends) $(soyutils_depends) $(DEPLOY_DIR)/closure_html.py $(closure_lib_files) $(template_files) $(appengine_files) $(static_files) test $(compiled_js_files)

define run_test 
	@echo "Running test on $(1)"
	@$(PYTHON) $(1) $(APPENGINE_SDK_PATH) $(2)

endef

define copy_file
	@echo "Copying file $(1) to $(2)"
	@mkdir -p `dirname $(2)`
	@$(CP) -f $(1) $(2)

endef

test_files := $(filter %_test.py, $(shell ls tests))
.PHONY: test
test: 
	$(foreach f,$(test_files), $(call run_test,tests/$(f),appengine))

tests: test

# Rule to compile soy files into deploy dir
$(DEPLOY_DIR)/static/%.js: templates/%.soy
	$(SOY_COMPILER) $(SOY_ARGS) --outputPathFormat $@ $<

# Convert the template html file into a python thing that can be included	
$(DEPLOY_DIR)/closure_html.py: templates/closure.html
	@mkdir -p `dirname $@`
	@echo 'TEMPLATE = """' > $@
	@cat templates/closure.html >> $@
	@echo '"""' >> $@

$(DEPLOY_DIR)/static/soyutils.js: external/closure/templates/soyutils.js
	$(call copy_file,$<,$@)

$(DEPLOY_DIR)/static/soyutils_usegoog.js: external/closure/templates/soyutils_usegoog.js
	$(call copy_file,$<,$@)

# Rule to compy closure library files into deploy dir
$(DEPLOY_DIR)/static/closure/%: external/closure/closure/%
	$(call copy_file,$<,$@)

# Rule to copy template files into deploy dir
$(DEPLOY_DIR)/templates/%: templates/%
	$(call copy_file,$<,$@)

# Rule to copy static files
$(DEPLOY_DIR)/static/%: static/%
	$(call copy_file,$<,$@)

# Copy appengine files
$(DEPLOY_DIR)/%: appengine/%
	$(call copy_file,$<,$@)

# Compile js files into compiled js files
$(DEPLOY_DIR)/static/%_compiled.js: static/%.js
	$(CLOSURE_BUILDER) $(CLOSURE_BUILDER_ARGS) --output_file=$@ --namespace=$(shell grep goog.provide $< | sed "s/goog.provide(\(.*\))/\1/g") 
	 
clean:
	@$(RM) -rf $(DEPLOY_DIR)
	@find . -name "*~" -exec rm {} \;
	@find . -name "*.pyc" -exec rm {} \;

.PHONY: debug
debug: dist
	$(DEV_APPSERVER) --datastore_path=deploy/dev_appserver.datastore deploy

.PHONY: update
update: dist
	$(APPCFG) update $(DEPLOY_DIR)
