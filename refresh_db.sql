CREATE PROCEDURE `refresh_db` ()
BEGIN

DROP TABLE facebook_comments.econtext_topics;
DROP TABLE facebook_comments.econtext_keywords;
DROP TABLE facebook_comments.comment_info;
DROP TABLE facebook_comments.post_info;
DROP TABLE facebook_comments.page_info;

CREATE TABLE page_info
(
	id INT(11) PRIMARY KEY NOT NULL AUTO_INCREMENT,
	datetime DATETIME NOT NULL,
	fb_id VARCHAR(128) NOT NULL,
	likes INT(11) NOT NULL,
	talking_about INT(11) NOT NULL,
	username VARCHAR(100) NOT NULL
);
CREATE INDEX page_info_fb_id_index ON page_info (fb_id);
CREATE UNIQUE INDEX page_info_id_uindex ON page_info (id);

CREATE TABLE post_info
(
	id INT(11) PRIMARY KEY NOT NULL AUTO_INCREMENT,
	fb_post_id VARCHAR(200) NOT NULL,
	message VARCHAR(800),
	likes_count BIGINT(20) UNSIGNED,
	time_created TIMESTAMP NULL,
	shares BIGINT(20) UNSIGNED,
	page_id INT(11) NOT NULL,
	link VARCHAR(800),
	type VARCHAR(50),
	status_type VARCHAR(50),
	time_updated TIMESTAMP NULL,
	FOREIGN KEY (page_id) REFERENCES page_info (id)
);
CREATE INDEX page_id ON post_info (page_id);
CREATE INDEX post_info_fb_post_id_index ON post_info (fb_post_id);

CREATE TABLE comment_info
(
	c_id INT(11) PRIMARY KEY NOT NULL AUTO_INCREMENT,
	comment_id VARCHAR(200),
	message VARCHAR(800),
	likes_count BIGINT(20) UNSIGNED,
	time_created TIMESTAMP NULL,
	post_id INT(11) NOT NULL,
	from_username VARCHAR(200),
	from_userid VARCHAR(200),
	replies_count BIGINT(20) UNSIGNED,
	sentiment VARCHAR(120),
	FOREIGN KEY (post_id) REFERENCES post_info (id)
);
CREATE INDEX post_id ON comment_info (post_id);

CREATE TABLE econtext_topics
(
  id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
  comment_id INT,
  econtext_id VARCHAR(64),
  topic_name VARCHAR(200),
  topic_path JSON,
  score DECIMAL(15,14),
  CONSTRAINT econtext_topics_ibfk_1 FOREIGN KEY (comment_id) REFERENCES comment_info (c_id)
);
CREATE INDEX comment_id ON econtext_topics (comment_id);


CREATE TABLE econtext_keywords
(
  id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
  comment_id INT,
  keyword VARCHAR(200),
  score DECIMAL(15,14),
  CONSTRAINT econtext_keyword_ibfk_1 FOREIGN KEY (comment_id) REFERENCES comment_info (c_id)
);
CREATE INDEX comment_id ON econtext_keywords (comment_id);

END
