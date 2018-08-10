.PHONY: clean collectstatic

run:
	python manage.py runserver

docker:
	docker build -t hub.highcat.org/vkusnyan-prod -f Dockerfile.prod .
	docker push hub.highcat.org/vkusnyan-prod

clean:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '.\#*' -exec rm -f {} +
	find . -name '\#*\#' -exec rm -f {} +
	find . -depth -type d -empty -delete

collectstatic:
	python manage.py collectstatic  --noinput

celery:
	python manage.py celery worker -P prefork -c 2 --statedb=~/proj/vk/var/run/celery-common-worker.state

test:
	python manage.py test
