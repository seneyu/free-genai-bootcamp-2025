from app.extensions import db

# the association table is already defined in word.py, but here is a reference
words_groups = db.Table('words_groups',
    db.Column('word_id', db.Integer, db.ForeignKey('words.id'), primary_key=True),
    db.Column('group_id', db.Integer, db.ForeignKey('groups.id'), primary_key=True)
)

# helper function for pagination
def get_pagination_dict(page, per_page, total):
    return {
        'current_page': page,
        'total_pages': (total + per_page - 1) // per_page,
        'total_items': total,
        'items_per_page': per_page
    }