
type = patch

publish:
	poetry version $(type)
	poetry build
	poetry publish

run:
	docker compose build 
	docker compose run awyes

commit: 
	git add -A
	git commit -m "$(message)"
	git tag -a v$(shell git describe --tags --abbrev=0 | ./version.sh)