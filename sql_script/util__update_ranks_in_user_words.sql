SET SQL_SAFE_UPDATES=0;

update user_words t1
inner JOIN
	(
	select uw.id user_words_id, wr.id word_rank_id, uw.language_id
		from user_words uw
		join word_ranks wr
		on lower(uw.word) = lower(wr.word) and uw.language_id = wr.language_id
		) t2
	on t1.id = t2.user_words_id
	set t1.`rank_id` = t2.word_rank_id;

SET SQL_SAFE_UPDATES=1;