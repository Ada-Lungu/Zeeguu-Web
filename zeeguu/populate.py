# -*- coding: utf8 -*-
import re

import zeeguu
import datetime
from zeeguu import model


WORD_PATTERN = re.compile("\[?([^{\[]+)\]?( {[^}]+})?( \[[^\]]\])?")


class WordCache(object):
    def __init__(self):
        self.cache = {}

    def __getitem__(self, args):
        word = self.cache.get(args, None)
        if word is None:
            word = model.UserWord(*args)
            zeeguu.db.session.add(word)
            self.cache[args] = word
        return word


def populate(from_, to, dict_file):
    cache = WordCache()
    with open(dict_file, "r") as f:
        for line in f:
            if line.startswith("#") or line.strip() == "":
                continue
            parts = line.split("\t")
            if len(parts) < 2:
                return
            orig = cache[clean_word(parts[0]), from_]
            trans = cache[clean_word(parts[1]), to]
            if trans not in orig.translations:
                orig.translations.append(trans)
def delete_duplicates(seq, current=None):
   # order preserving
   if current is None:
       def current(x): return x
   seen = {}
   result = []
   for item in seq:
       marker = current(item)
       # in old Python versions:
       # if seen.has_key(marker)
       # but in new ones:
       if marker in seen: continue
       seen[marker] = 1
       result.append(item)
   return result


def filter_word_list(word_list):
    filtered_word_list = []
    lowercase_word_list = []
    for word in word_list:
        lowercase_word_list.append(word.lower)
    lowercase_word_list = delete_duplicates(lowercase_word_list)
    for lc_word in lowercase_word_list:
        for word in word_list:
            if word.lower  == lc_word:
                filtered_word_list.append(word)
                break
    return filtered_word_list

def word_list(lang_code):
    words_file = open("../../languages/"+lang_code+".txt")
    words_list = words_file.read().splitlines()
    return words_list




def add_words_to_db(lang_code):
    zeeguu.app.test_request_context().push()
    zeeguu.db.session.commit()
    for word in filter_word_list(word_list(lang_code)):
        w = model.Word.find(word.decode('utf-8'))
        zeeguu.db.session.add(w)
    print 'karan the best'
    zeeguu.db.session.commit()

def add_word_ranks_to_db(lang_code):
    zeeguu.app.test_request_context().push()
    zeeguu.db.session.commit()
    from_lang = model.Language.find(lang_code)
    initial_line_number = 1
    for word in filter_word_list(word_list(lang_code)):
        w = model.Word.find(word.decode('utf-8'))
        zeeguu.db.session.add(w)
        r = model.WordRank(w, from_lang,initial_line_number)
        zeeguu.db.session.add(r)
        initial_line_number+=1
    print 'karan the worst'
    zeeguu.db.session.commit()

def clean_word(word):
    match = re.match(WORD_PATTERN, word)
    if match is None:
        print word
        return word.decode("utf8")
    return match.group(1).decode("utf8")

def add_words(original_word, translation_word):
    word1 = model.Word.find(original_word)
    word2 = model.Word.find(translation_word)
    zeeguu.db.session.add(word1)
    zeeguu.db.session.add(word2)
    zeeguu.db.session.commit()


def add_bookmark(user, original_language, original_word, translation_language, translation_word,  date, the_context, the_url, the_url_title):

    url = model.Url.find (the_url, the_url_title)
    text = model.Text(the_context, translation_language, url)

    word1 = model.Word.find(original_word)
    word2 = model.Word.find(translation_word)
    if model.WordRank.exists(word1.id):
        rank1 = model.UserWord.find_rank(word1, original_language)
        w1 = model.UserWord(word1, original_language,rank1)
    else:
        w1  = model.UserWord(word1, translation_language,None)
    if model.WordRank.exists(word2.id):
        rank2 = model.UserWord.find_rank(word2, translation_language)
        w2 = model.UserWord(word2, translation_language,rank2)
    else:
        w2  = model.UserWord(word2, translation_language,None)

    zeeguu.db.session.add(url)
    zeeguu.db.session.add(text)
    zeeguu.db.session.add(w1)
    zeeguu.db.session.add(w2)
    t1= model.Bookmark(w1,w2, user, text, date)
    zeeguu.db.session.add(t1)

    zeeguu.db.session.commit()
    return


def create_test_db():
    zeeguu.app.test_request_context().push()

    zeeguu.db.session.commit()
    zeeguu.db.drop_all()
    zeeguu.db.create_all()

    fr = model.Language("fr", "French")
    de = model.Language("de", "German")
    dk = model.Language("dk", "Danish")
    en = model.Language("en", "English")
    it = model.Language("it", "Italian")
    no = model.Language("no", "Norwegian")
    ro = model.Language("ro", "Romanian")
    es = model.Language("es", "Spanish")

    zeeguu.db.session.add(en)
    zeeguu.db.session.add(fr)
    zeeguu.db.session.add(de)
    zeeguu.db.session.add(dk)
    zeeguu.db.session.add(no)
    zeeguu.db.session.add(it)
    zeeguu.db.session.add(ro)
    zeeguu.db.session.add(es)
    zeeguu.db.session.commit()

    not_know = model.ExerciseOutcome("Do not know")
    retry = model.ExerciseOutcome("Retry")
    correct = model.ExerciseOutcome("Correct")
    wrong = model.ExerciseOutcome("Wrong")
    typo = model.ExerciseOutcome("Typo")
    i_know = model.ExerciseOutcome("I know")

    recognize = model.ExerciseSource("Recognize")
    translate = model.ExerciseSource("Translate")

    zeeguu.db.session.add(not_know)
    zeeguu.db.session.add(retry)
    zeeguu.db.session.add(correct)
    zeeguu.db.session.add(wrong)
    zeeguu.db.session.add(typo)
    zeeguu.db.session.add(i_know)

    zeeguu.db.session.add(recognize)
    zeeguu.db.session.add(translate)



    user = model.User("i@mir.lu", "Mircea", "pass", de, ro)
    user2 = model.User("i@ada.lu", "Ada", "pass", fr)

    zeeguu.db.session.add(user)


    jan111 = datetime.date(2011,01,01)
    ian101 = datetime.date(2001,01,01)
    jan14 = datetime.date(2014,1,14)


    today_dict = {
        'sogar':'actually',
        'sperren':'to lock, to close',
        'Gitter':'grates',
        'erfahren':'to experience',
        'treffen':'hit',
        'jeweils':'always',
        'Darstellung':'presentation',
        'Vertreter':'representative',
        'Knecht':'servant',
        'besteht':'smtg. exists'
    }
    initial_rank =1
    for key in today_dict:
        add_words(key, today_dict[key])

    dict = {
            u'Spaß': 'fun',
            'solche': 'suchlike',
            'ehemaliger': 'ex',
            'betroffen': 'affected',
            'Ufer':'shore',
            u'höchstens':'at most'
            }


    for key in dict:
        add_words(key, dict[key])



    french_dict = {
        'jambes':'legs',
        'de':'of',
        'et':'and'
            }


    for key in french_dict:
        add_words(key, french_dict[key])


    story_url = 'http://www.gutenberg.org/files/23393/23393-h/23393-h.htm'
    japanese_story = [
            # ['recht', 'right', 'Du hast recht', story_url],
            ['hauen', 'to chop', 'Es waren einmal zwei Holzhauer', story_url],
            [u'Wald','to arrive', u'Um in den Walden zu gelangen, mußten sie einen großen Fluß passieren. Um in den Walden zu gelangen, mußten sie einen großen Fluß passieren. Um in den Walden zu gelangen, mußten sie einen großen Fluß passieren. Um in den Walden zu gelangen, mußten sie einen großen Fluß passieren', story_url],
            ['eingerichtet','established',u'Um in den Wald zu gelangen, mußten sie einen großen Fluß passieren, über den eine Fähre eingerichtet war', story_url],
            [u'vorläufig','temporary',u'von der er des rasenden Sturmes wegen vorläufig nicht zurück konnte', story_url],
            [u'werfen', 'to throw',u'Im Hause angekommen, warfen sie sich zur Erde,', story_url],
            ['Tosen','roar',u'sie Tür und Fenster wohl verwahrt hatten und lauschten dem Tosen des Sturmes.sie Tür und Fenster wohl verwahrt hatten und lauschten dem Tosen des Sturmes.sie Tür und Fenster wohl verwahrt hatten und lauschten dem Tosen des Sturmes',story_url],
            ['Entsetzen','horror','Entsetzt starrte Teramichi auf die Wolke',story_url]
        ]

    for w in japanese_story:
        add_words(w[0], w[1])


    add_words_to_db('de')
    add_word_ranks_to_db('de')

    for key in today_dict:
        add_bookmark(user, de, key, en, today_dict[key], jan111, "Keine bank durfe auf immunitat pochen, nur weil sie eine besonders herausgehobene bedeutung fur das finanzsystem habe, sagte holder, ohne namen von banken zu nennen" + key,
                         "http://url2", "title of url2")

    for key in dict:
        add_bookmark(user, de, key, en, dict[key], ian101, "Deutlich uber dem medianlohn liegen beispielsweise forschung und entwicklung, tabakverarbeitung, pharma oder bankenwesen, am unteren ende der skala liegen die tieflohnbranchen detailhandel, gastronomie oder personliche dienstleistungen. "+key,
                         "http://url1", "title of url1")

    for key in dict:
        add_bookmark(user, de, key, en, dict[key], ian101, "Deutlich uber dem medianlohn liegen beispielsweise forschung und entwicklung, tabakverarbeitung, pharma oder bankenwesen, am unteren ende der skala liegen die tieflohnbranchen detailhandel, gastronomie oder personliche dienstleistungen. "+key,
                         "http://url1", "title of url1")
    for w in japanese_story:
        if w[0] == 'recht':
            # something special
            add_bookmark(user, de, w[0], en, w[1],jan14, w[2],w[3], "japanese story")
        else:
            add_bookmark(user, de, w[0], en, w[1],jan14, w[2],w[3], "japanese story")






    zeeguu.db.session.commit()
    # print "temp db recreated..."


if __name__ == "__main__":
    create_test_db()
