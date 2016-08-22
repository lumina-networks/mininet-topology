help:
	@echo "  clean       remove artifacts from running python setup.py install"
	@echo "  package     creates a sdist"

clean:
	rm -Rf mininet-topology.egg-info && \
	rm -Rf build && \
	rm -Rf dist && \
	rm -Rf ChangeLog && \
	rm -Rf AUTHORS

package:
	make clean && \
	python setup.py sdist
