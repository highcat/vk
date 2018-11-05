# -*- coding: utf-8 -*-
import os
import time
from datetime import datetime
import yaml
from fabric.api import run, cd, local, get, env, hide, settings
from fabric.colors import green, red

LOC_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
config = yaml.load(open(LOC_PROJECT_DIR + '/fabfile.yaml'))
env.use_ssh_config = True

PROJECT_DIR = 'vk'
TEMP_DIR = 'temp'

def prod():
    env.context = 'production'
    env.hosts = config['prod']['hosts']
    env.user = config['prod']['user']
    env.git_branch = config['prod']['git_branch']
    env.remote_db_name = config['prod']['db_name']
    env.crontab_file = config['prod']['crontab_file']
    env.local_db_name = config['local']['db_name']

def stage():
    env.context = 'stage'
    env.hosts = config['stage']['hosts']
    env.user = config['stage']['user']
    env.git_branch = config['stage']['git_branch']
    env.remote_db_name = config['stage']['db_name']
    env.crontab_file = config['stage']['crontab_file']
    env.local_db_name = config['local']['db_name']



def pull():
    with cd(PROJECT_DIR), hide('running', 'stdout', 'stderr'):
        run('git pull origin %s' % env.git_branch)

def restart_web():
    with cd(PROJECT_DIR):
        run('supervisorctl -c ~/supervisord.conf restart gunicorn')

def restart_celery():
    with cd(PROJECT_DIR):
        run('supervisorctl -c ~/supervisord.conf restart tasks')


# def stop_long_celery_tasks():
#     with cd(PROJECT_DIR):
#         run('supervisorctl -c ~/supervisord.conf stop celery-odoo-install')

def stop_all():
    with cd(PROJECT_DIR):
        # TODO never stop redis
        run('supervisorctl -c ~/supervisord.conf stop all')

def start_all():
    with cd(PROJECT_DIR):
        run('supervisorctl -c ~/supervisord.conf start all')

def start_web():
    with cd(PROJECT_DIR):
        # TODO:
        # 1. never stop redis,
        # 2. don't stop odoo in this script
        # 3. use supervisor's groups
        run('supervisorctl -c ~/supervisord.conf start gunicorn')


def install_deps():
    with cd(PROJECT_DIR):
        run('pip install -r conf/requirements-freezed.pip')

def collectstatic():
    with cd(PROJECT_DIR):
        # FIXME somehow it builds them into vk/static/gen instead of static/gen
        run('python manage.py assets build')
        run('python manage.py collectstatic --noinput')

def run_migrations():
    with cd(PROJECT_DIR):
        run('python manage.py migrate')


def clone_db():
    """replace local database with version from production server. Local database name should be "trueshelf2", user should have permissions to create Postgresql databases."""
    dump_filename = '%s-db-%s.sql.bz2' % (env.remote_db_name, time.time())
    with cd(TEMP_DIR):
        try:
            # Exclude large tables, if needed
            TABLES_TO_EXCLUDE = [
            ]
            if TABLES_TO_EXCLUDE:
                print 
                print "XXX EXCLUDING tables during clone:"
                print "  (if you want to clone these tables too, change `fabfile.py` script)"
                print "    {0}".format('\n    '.join(TABLES_TO_EXCLUDE))
                print 
                excl_string = ' '.join(['--exclude-table-data={0}'.format(d) for d in TABLES_TO_EXCLUDE])
            else:
                excl_string = ''
            run('pg_dump {dbname} {exclusions} | bzip2 > {dump_file}'.format(
                dbname=env.remote_db_name,
                exclusions=excl_string,
                dump_file=dump_filename,
            ))
            get(dump_filename, dump_filename)
            with settings(warn_only=True):
                local('dropdb %s' % env.local_db_name)
            local('createdb %s' % env.local_db_name)
            local('bzip2 -dc %s | psql %s' % (dump_filename, env.local_db_name))
            # Reset user passords for admins to "11"
            local('python manage.py user-passwords-to-11 --apply')
        finally:
            run('rm %s' % dump_filename)
            local('rm %s' % dump_filename)

def clone_media():
    """download all media files with rsync to your local media folder."""
    local('rsync -avz -e ssh %(user)s@%(host)s:%(project_dir)s/media ./' % {
        'user': env.user,
        'host': env.hosts[0], # XXX
        'project_dir': PROJECT_DIR,
    })


def clone_all():
    clone_db()
    clone_media()


def clean():
    """Get rid of old .pyc files, which can cause incorrect behaviour after refactoring"""
    with cd(os.path.join(PROJECT_DIR)):
        # run as one command for better speed
	run(';\n '.join([
            "find . -name '*.pyc' -exec rm -f {} +",
            "find . -name '*.pyo' -exec rm -f {} +",
            "find . -name '*~' -exec rm -f {} +",
            "find . -name '.\#*' -exec rm -f {} +",
            "find . -name '\#*\#' -exec rm -f {} +",
            "find . -type d -empty -delete",
        ]))


def crontab_deploy():
    with cd(os.path.join(PROJECT_DIR, 'conf')):
        # TODO verify 'crontab.txt' before deployment
        run("crontab {0}".format(env.crontab_file))


def deploy():
    """Perform full deployment from git repository to server."""
    pull()
    install_deps()

    # # Start/stop order to minimize web interface downtime
    # stop_long_celery_tasks()

    stop_all()
    clean()
    collectstatic()
    run_migrations()
    crontab_deploy()
    start_web()

    start_all()

    print(green('Deployed successfully', bold=True))


def deploy_nl():
    """minor fix - w/o libraries update"""
    pull()
    clean()
    collectstatic()
    run_migrations()
    restart_celery()
    restart_web()
    crontab_deploy()
    print(green('Deployed successfully', bold=True))
