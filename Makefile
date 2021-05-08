
type = patch

publish:
	poetry version $(type)
	poetry build
	poetry publish

run:
	docker compose build 
	docker compose run awyes
