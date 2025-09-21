_list:
    @just --list

# Install requirements
install args="":
    poetry install --sync {{args}}

# Install and start local server
dev: (install "-q")
    poetry run flask --app readable_af.rest run --debug

# Regenerate the requirements lockfile (requirements.txt)
lock:
    poetry run pip freeze --exclude-editable > requirements.txt

# Redeploy the website to production
deploy: lock
    fly deploy

# Repopulate secrets file from production instance
generate_dotenv:
    curl https://article-friend-dev.fly.dev > /dev/null
    poetry run python utils/generate_dotenv.py 
