import AO3

"""
vars(work) -> return every attribute of object, along with values
AO3.Work.metadata -> returns the property object
AO3.Work(X).metadata

inspect.getmembers(AO3.Work.metadata)

AO3.common.get_work_from_banner(workid)

for item in attributes:
    print(type(attributes[i]))

list(work.metadata) -> get keys as list
work.metadata.keys() -> get keys as dict_keys
"""

# Retrive example AO3 work (This can be any, but a smaller one is quicker.)
work = AO3.Work(26754208, load_chapters=False)

# List each key in work.metadata
key_list = list(work.metadata.keys())

TABLE_COLUMNS = []

# Exclude 'id' from list
for item in key_list:
    if item != 'id':
        TABLE_COLUMNS.append(item)

# Print final columns
print(TABLE_COLUMNS)