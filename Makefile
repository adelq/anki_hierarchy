VER=$(shell git log -1 --pretty=format:"%H")

all:
	mkdir -p dist
	zip dist/anki20-$(VER) anki_hierarchy.py
	zip dist/anki21-$(VER) anki_hierarchy.py __init__.py

clean:
	rm dist/anki20-$(VER).zip
	rm dist/anki21-$(VER).zip

full_clean:
	rm -rf dist/
