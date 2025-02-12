from datetime import datetime
from app.extensions import db

words_groups = db.Table('words_groups',
    db.Column('word_id', db.Integer, db.ForeignKey('words.id'), primary_key=True),
    db.Column('group_id', db.Integer, db.ForeignKey('groups.id'), primary_key=True)    
)

class Word(db.Model):
    __tablename__ = 'words'

    id = db.Column(db.Integer, primary_key=True)
    french = db.Column(db.String(100), nullable=False)
    english = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(20))
    parts = db.Column(db.JSON)
    
    # relationships
    groups = db.relationship('Group', secondary='words_groups', back_populates='words')
    review_items = db.relationship('WordReviewItem', back_populates='word')

    def __repr__(self):
        return f'<Word {self.french}>'

    def to_dict(self):
        """Basic dict representation of the Word"""
        return {
            'french': self.french,
            'english': self.english,
            'gender': self.gender,
            'parts': self.parts
        }

    def to_dict_with_stats(self):
        """Dict representation including review statistics"""
        correct_count = sum(1 for item in self.review_items if item.correct)
        wrong_count = sum(1 for item in self.review_items if not item.correct)
        
        base_dict = self.to_dict()
        base_dict.update({
            'correct_count': correct_count,
            'wrong_count': wrong_count
        })
        return base_dict

    def to_detail_dict(self):
        """Detailed dict representation including groups"""
        base_dict = self.to_dict_with_stats()
        base_dict['groups'] = [{'id': group.id, 'name': group.name} for group in self.groups]
        return base_dict