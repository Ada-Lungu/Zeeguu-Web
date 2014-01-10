# -*- coding: utf8 -*-
import re
import random
import datetime

import sqlalchemy.orm.exc
import sys

from zeeguu import db
from zeeguu import util
import zeeguu


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.LargeBinary(255))
    password_salt = db.Column(db.LargeBinary(255))
    preferred_language_id = db.Column(
        db.String(2),
        db.ForeignKey("language.id")
    )
    preferred_language = sqlalchemy.orm.relationship("Language")

    def __init__(self, email, password, preferred_language=None):
        self.email = email
        self.update_password(password)
        self.preferred_language = preferred_language or Language.default()

    def __repr__(self):
        return '<User %r>' % (self.email)

    def read(self, text):
        if (Impression.query.filter(Impression.user == self)
                            .filter(Impression.text == text).count()) > 0:
            return
        for word in text.words():
            self.impressions.append(Impression(self, word, text))

    @classmethod
    def find(cls, email):
        return User.query.filter(User.email == email).one()

    @sqlalchemy.orm.validates("email")
    def validate_email(self, col, email):
        if "@" not in email:
            raise ValueError("Invalid email address")
        return email

    @sqlalchemy.orm.validates("password")
    def validate_password(self, col, password):
        if password is None or len(password) == 0:
            raise ValueError("Invalid password")
        return password

    def update_password(self, password):
        self.password_salt = "".join(
            chr(random.randint(0, 255)) for i in range(32)
        )
        self.password = util.password_hash(password, self.password_salt)

    @classmethod
    def authorize(cls, email, password):
        try:
            user = cls.query.filter(cls.email == email).one()
            if user.password == util.password_hash(password,
                                                   user.password_salt):
                return user
        except sqlalchemy.orm.exc.NoResultFound:
            return None
	
    def contribs_chronologically(self):
	    return Contribution.query.filter_by(user_id=self.id).order_by(Contribution.time.desc()).all()

    def contribs_by_date(self):
	def extract_day_from_date(contrib):
		return (contrib, contrib.time.replace(contrib.time.year, contrib.time.month, contrib.time.day,0,0,0,0))

	contribs = Contribution.query.filter_by(user_id=self.id).order_by(Contribution.time.desc()).all()
	contribs_by_date = dict()
				                                        
	for elem in map(extract_day_from_date, contribs):
		contribs_by_date.setdefault(elem[1],[]).append(elem[0])

	sorted_dates = contribs_by_date.keys()
	sorted_dates.sort(reverse=True)
	return contribs_by_date, sorted_dates



class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = db.relationship("User")
    last_use = db.Column(db.DateTime)

    def __init__(self, user, id_):
        self.id = id_
        self.user = user
        self.update_use_date()

    def update_use_date(self):
        self.last_use = datetime.datetime.now()

    @classmethod
    def for_user(cls, user):
        while True:
            id_ = random.randint(0, 1 << 31)
            if cls.query.get(id_) is None:
                break
        return cls(user, id_)


class Language(db.Model):
    id = db.Column(db.String(2), primary_key=True)
    name = db.Column(db.String(255), unique=True)

    def __init__(self, id, name):
        self.name = name
        self.id = id

    def __repr__(self):
        return '<Language %r>' % (self.id)

    @classmethod
    def default(cls):
        return cls.find("de")

    @classmethod
    def find(cls, id_):
        return cls.query.filter(Language.id == id_).one()


class Word(db.Model, util.JSONSerializable):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(255))
    language_id = db.Column(db.String(2), db.ForeignKey("language.id"))
    language = db.relationship("Language")

    def __init__(self, word, language):
        self.word = word
        self.language = language

    def __repr__(self):
        return '<Word %r>' % (self.word)

    def serialize(self):
        return self.word

    def importance_level(self):
        f=open(zeeguu.app.config.get("LANGUAGES_FOLDER").decode('utf-8')+self.language_id+".txt", "r")
        all_words = f.readlines()
        all_words_without_space = []
        for each_word in all_words:
            each_word_without_space = each_word[:-1]
            all_words_without_space.append(each_word_without_space)

        def importance_range(the_word, frequency_list):
            if the_word in frequency_list:
                position = frequency_list.index(the_word)
                return (position // 500) + 1
            else:
                return "" 

        return importance_range(self.word, all_words_without_space)

    @classmethod
    def find(cls, word, language):
        try:
            return (cls.query.filter(cls.word == word)
                             .filter(cls.language == language)
                             .one())
        except sqlalchemy.orm.exc.NoResultFound:
            return cls(word, language)

    @classmethod
    def translate(cls, from_lang, term, to_lang):
        return (cls.query.join(WordAlias, cls.translation_of)
                         .filter(WordAlias.word == term.lower())
                         .filter(cls.language == to_lang)
                         .filter(WordAlias.language == from_lang)
                         .all())


WordAlias = db.aliased(Word, name="translated_word")


class Contribution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    origin_id = db.Column(db.Integer, db.ForeignKey('word.id'))
    origin = db.relationship("Word", primaryjoin=origin_id == Word.id,
                             backref="translations")
    translation_id = db.Column(db.Integer, db.ForeignKey('word.id'))
    translation = db.relationship("Word",
                                  primaryjoin=translation_id == Word.id)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship("User", backref="contributions")
    time = db.Column(db.DateTime)

    def __init__(self, origin, translation, user):
        self.origin = origin
        self.translation = translation
        self.user = user
        self.time = datetime.datetime.now()

    def __init__(self, origin, translation, user, time):
        self.origin = origin
        self.translation = translation
        self.user = user
        self.time = time 



class Text(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(10000))
    content_hash = db.Column(db.LargeBinary(32))
    language_id = db.Column(db.String(2), db.ForeignKey("language.id"))
    language = db.relationship("Language")

    def __init__(self, content, language):
        self.content = content
        self.language = language
        self.content_hash = util.text_hash(content)

    def __repr__(self):
        return '<Text %r>' % (self.language.short)

    def words(self):
        for word in re.split(re.compile(u"[^\\w]+", re.U), self.content):
            yield Word.find(word, self.language)

    @classmethod
    def find(cls, text, language):
        try:
            query = (
                cls.query.filter(cls.language == language)
                         .filter(cls.content_hash == util.text_hash(text))
            )
            if query.count() > 0:
                query = query.filter(cls.content == text)
                try:
                    return query.one()
                except sqlalchemy.orm.exc.NoResultFound:
                    pass
            return cls(text, language)
        except:
            import traceback
            traceback.print_exc()


class Search(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = db.relationship("User", backref="searches")
    word_id = db.Column(db.Integer, db.ForeignKey("word.id"))
    word = db.relationship("Word")
    language_id = db.Column(db.String(2), db.ForeignKey("language.id"))
    language = db.relationship("Language")
    text_id = db.Column(db.Integer, db.ForeignKey("text.id"))
    text = db.relationship("Text")
    contribution_id = db.Column(db.Integer, db.ForeignKey("contribution.id"))
    contribution = db.relationship("Contribution", backref="search")

    def __init__(self, user, word, language, text=None):
        self.user = user
        self.word = word
        self.language = language
        self.text = text

    def __repr__(self):
        return '<Search %r>' % (self.word.word)


class Impression(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = db.relationship("User", backref="impressions")
    word_id = db.Column(db.Integer, db.ForeignKey("word.id"))
    word = db.relationship("Word")
    text_id = db.Column(db.Integer, db.ForeignKey("text.id"))
    text = db.relationship("Text")
    count = db.Column(db.Integer)
    last_search_id = db.Column(db.Integer, db.ForeignKey("search.id"))
    last_search = db.relationship("Search")

    def __init__(self, user, word, text=None):
        self.user = user
        self.word = word
        self.text = text

    def __repr__(self):
        return '<Impression %r>' % (self.word.word)
