"""1.0.0 (Switched to ao3_api for webscraping)

Revision ID: ca2dfefaf0b6
Revises: 
Create Date: 2022-12-17 06:56:03.870550

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import INTEGER, TEXT, Column, Table
from sqlalchemy.ext.declarative import declarative_base

# revision identifiers, used by Alembic.
revision = 'ca2dfefaf0b6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Connect to database and retrive all entires from fics table
    connection = op.get_bind()
    result = connection.execute("SELECT * FROM fics;")
    result = result.fetchall()

    # Save all rows from old fics table into old_table
    old_table = [dict(row) for row in result]

    # Split key nchapters into keys nchapters and expected_chapters
    for row in old_table:
        chapters_split = row['nchapters'].split('/')
        row['nchapters'] = chapters_split[0]

        if chapters_split[1] == '?':
            row['expected_chapters'] = 'None'
        else:
            row['expected_chapters'] = chapters_split[1] 

    # Drop old fics table and create the new one
    op.drop_table('fics')

    Base = declarative_base()

    op.create_table('fics', Base.metadata,
        Column('id', INTEGER),
        Column('date_edited', TEXT),
        Column('date_published', TEXT),
        Column('date_updated', TEXT),
        Column('bookmarks', TEXT),
        Column('categories', TEXT),
        Column('nchapters', TEXT),
        Column('characters', TEXT),
        Column('complete', TEXT),
        Column('comments', TEXT),
        Column('expected_chapters', TEXT),
        Column('fandoms', TEXT),
        Column('hits', TEXT),
        Column('kudos', TEXT),
        Column('language', TEXT),
        Column('rating', TEXT),
        Column('relationships', TEXT),
        Column('restricted', TEXT),
        Column('status', TEXT),
        Column('summary', TEXT),
        Column('tags', TEXT),
        Column('title', TEXT),
        Column('warnings', TEXT),
        Column('words', TEXT),
        Column('collections', TEXT),
        Column('authors', TEXT),
        Column('series', TEXT),
        Column('chapter_titles', TEXT)
    )

    # Insert the values from old_table into the newly-created fics table
    for row in old_table:
        op.execute(f"""INSERT INTO fics (id, title, nchapters, expected_chapters) VALUES ("{int(row['id'])}", "{row['title']}", "{row['nchapters']}", "{row['expected_chapters']}");""")

    print(f"Upgrade to revision {revision} finished.")


def downgrade() -> None:
    pass
