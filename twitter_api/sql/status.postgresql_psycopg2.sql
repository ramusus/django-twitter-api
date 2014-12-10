--twitter_api_status_favorites_users

CREATE UNIQUE INDEX twitter_api_status_favorites_users_time_from_3col_uniq
ON twitter_api_status_favorites_users (status_id, user_id, time_from)
WHERE time_from IS NOT NULL;

CREATE UNIQUE INDEX twitter_api_status_favorites_users_time_from_2col_uniq
ON twitter_api_status_favorites_users (status_id, user_id)
WHERE time_from IS NULL;

CREATE UNIQUE INDEX twitter_api_status_favorites_users_time_to_3col_uniq
ON twitter_api_status_favorites_users (status_id, user_id, time_to)
WHERE time_to IS NOT NULL;

CREATE UNIQUE INDEX twitter_api_status_favorites_users_time_to_2col_uniq
ON twitter_api_status_favorites_users (status_id, user_id)
WHERE time_to IS NULL;
