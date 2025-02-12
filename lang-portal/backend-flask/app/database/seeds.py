import os
import json
from datetime import datetime
from flask import current_app
from app.extensions import db
from app.models.word import Word
from app.models.group import Group
from app.models.study_activity import StudyActivity

class Seeder:
    @staticmethod
    def seed_all():
        """Run all seed operations"""
        Seeder.seed_words_and_groups()
        Seeder.seed_study_activities()
        db.session.commit()

    @staticmethod
    def seed_words_and_groups():
        """Seed words and groups from JSON files"""
        seeds_dir = os.path.join(current_app.root_path, 'database', 'seeds')
        
        # Process each JSON file in the seeds directory
        for filename in os.listdir(seeds_dir):
            if filename.endswith('.json') and filename != 'study_activities.json':
                with open(os.path.join(seeds_dir, filename)) as f:
                    data = json.load(f)
                    
                    # Create or get group
                    group = Group.query.filter_by(name=data['group_name']).first()
                    if not group:
                        group = Group(name=data['group_name'])
                        db.session.add(group)
                    
                    # Create words and associate with group
                    for word_data in data['words']:
                        word = Word.query.filter_by(
                            french=word_data['french'],
                            english=word_data['english']
                        ).first()
                        
                        if not word:
                            word = Word(
                                french=word_data['french'],
                                english=word_data['english'],
                                gender=word_data.get('gender'),  
                                parts=word_data.get('parts', [])
                            )
                            db.session.add(word)
                        
                        if group not in word.groups:
                            word.groups.append(group)

    @staticmethod
    def seed_study_activities():
        """Seed study activities from JSON file"""
        activities_file = os.path.join(current_app.root_path, 'database', 'seeds', 'study_activities.json')
        
        if os.path.exists(activities_file):
            with open(activities_file) as f:
                data = json.load(f)
                
                for activity_data in data['activities']:
                    activity = StudyActivity.query.filter_by(
                        name=activity_data['name']
                    ).first()
                    
                    if not activity:
                        activity = StudyActivity(
                            name=activity_data['name'],
                            thumbnail_url=activity_data['thumbnail_url'],
                            description=activity_data['description']
                        )
                        db.session.add(activity)