VER=$(shell git log -1 --pretty=format:"%H")

all:
	mkdir -p dist
	zip dist/anki21-$(VER) anki_hierarchy.py __init__.py config.json config.md config.py meta.json

clean:
	rm dist/anki21-$(VER).zip

full_clean:
	rm -rf dist/
