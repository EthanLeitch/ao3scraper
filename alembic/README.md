# Locating the database
ao3scraper uses the platformdirs module to set a sane database location.
This database location can be found by running `ao3scraper -v`

# Migrations
ao3scraper will automatically handle upgrading the database with alembic. 
Failing this, a manual migration can be performed. 
To upgrade the database to the latest version, run `alembic upgrade head`.