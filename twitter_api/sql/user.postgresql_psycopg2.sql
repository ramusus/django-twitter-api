--twitter_api_user_followers

CREATE UNIQUE INDEX twitter_api_user_followers_time_from_3col_uniq
ON twitter_api_user_followers (from_user_id, to_user_id, time_from)
WHERE time_from IS NOT NULL;

CREATE UNIQUE INDEX twitter_api_user_followers_time_from_2col_uniq
ON twitter_api_user_followers (from_user_id, to_user_id)
WHERE time_from IS NULL;

CREATE UNIQUE INDEX twitter_api_user_followers_time_to_3col_uniq
ON twitter_api_user_followers (from_user_id, to_user_id, time_to)
WHERE time_to IS NOT NULL;

CREATE UNIQUE INDEX twitter_api_user_followers_time_to_2col_uniq
ON twitter_api_user_followers (from_user_id, to_user_id)
WHERE time_to IS NULL;
