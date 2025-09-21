_list:
    @just --list

# Install requirements
install args="":
    poetry install --sync {{args}}

# Install and start local server
dev:
    uv run flask --app readable_af.rest run --debug

# Regenerate the requriements.txt file
gen-requirements:
    uv export -q --no-hashes --no-dev --locked -o requirements.txt

# Redeploy the website to production
deploy: gen-requirements
    fly deploy

# Repopulate secrets file from production instance
gen-dotenv:
    curl https://article-friend-dev.fly.dev > /dev/null
    poetry run python utils/generate_dotenv.py 
