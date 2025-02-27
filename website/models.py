"""Database models for DevReady."""
from datetime import datetime
from flask_login import UserMixin
from .extensions import db

class User(db.Model, UserMixin):
    """Represents a user in the system."""
    userID = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128), nullable=False)
    passwordHash = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)

    submissions = db.relationship('Submission', back_populates='user', lazy=True)
    mastery_scores = db.relationship('MasteryScore', back_populates='user', lazy=True)

    def get_id(self):
        """Returns the user ID as a string."""
        return str(self.userID)

class Question(db.Model):
    """Represents a coding question."""
    questionID = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.String(50), nullable=False)
    createdDate = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    submissions = db.relationship('Submission', back_populates='question', lazy=True)
    questionTags = db.relationship('QuestionTag', back_populates='question', lazy=True)

    @property
    def tags(self):
        """Returns a list of tags associated with the question."""
        return [qt.tag for qt in self.questionTags]

class Tag(db.Model):
    """Represents a category/tag associated with coding questions."""
    tagID = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    questionTags = db.relationship('QuestionTag', back_populates='tag', lazy=True)
    mastery_scores = db.relationship('MasteryScore', back_populates='tag', lazy=True)

    @property
    def questions(self):
        """Returns a list of questions associated with this tag."""
        return [qt.question for qt in self.questionTags]

class QuestionTag(db.Model):
    """Associative table mapping questions to tags."""
    questionTagID = db.Column(db.Integer, primary_key=True)
    questionID = db.Column(db.Integer, db.ForeignKey('question.questionID'))
    tagID = db.Column(db.Integer, db.ForeignKey('tag.tagID'))

    question = db.relationship('Question', back_populates='questionTags')
    tag = db.relationship('Tag', back_populates='questionTags')

class Submission(db.Model):
    """Represents a user submission for a coding question."""
    submissionID = db.Column(db.Integer, primary_key=True)
    userID = db.Column(db.Integer, db.ForeignKey('user.userID'), nullable=False)
    questionID = db.Column(db.Integer, db.ForeignKey('question.questionID'), nullable=False)
    result = db.Column(db.String(50), nullable=False)
    runtime = db.Column(db.Integer, nullable=True)
    language = db.Column(db.String(50), nullable=False)
    time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship('User', back_populates='submissions')
    question = db.relationship('Question', back_populates='submissions')

class TestCase(db.Model):
    """Represents a test case for a coding question."""
    testCaseID = db.Column(db.Integer, primary_key=True)
    questionID = db.Column(db.Integer, db.ForeignKey('question.questionID'), nullable=False)
    inputData = db.Column(db.Text, nullable=False)
    expectedOutput = db.Column(db.Text, nullable=False)
    isSample = db.Column(db.Boolean, default=False)

    question = db.relationship('Question', backref='testCases')

class MasteryScore(db.Model):
    """Tracks a user's proficiency in different coding concepts."""
    __tablename__ = 'mastery_score'
    userID = db.Column(db.Integer, db.ForeignKey('user.userID'), primary_key=True)
    tagID = db.Column(db.Integer, db.ForeignKey('tag.tagID'), primary_key=True)
    score = db.Column(db.Float, nullable=False, default=0.0)

    user = db.relationship('User', back_populates='mastery_scores')
    tag = db.relationship('Tag', back_populates='mastery_scores')
