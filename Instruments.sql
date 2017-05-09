CREATE DATABASE IF NOT EXISTS weborder;

USE weborder;

CREATE TABLE IF NOT EXISTS `instrument`(
id INT NOT NULL,
name VARCHAR(30) NOT NULL,
price FLOAT NOT NULL,
weight FLOAT NOT NULL,
description VARCHAR(200),
transportation_cost FLOAT NOT NULL,
image_path varchar(150),
deleted BOOLEAN DEFAULT false,
PRIMARY KEY(id)
) DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `order`(
id INT NOT NULL,
datetime DATETIME NOT NULL,
totalprice FLOAT NOT NULL,
PRIMARY KEY(id)
) DEFAULT CHARSET=UTF8;

CREATE TABLE IF NOT EXISTS `user`(
id INT NOT NULL AUTO_INCREMENT,
username varchar(30) NOT NULL,
password_hash varchar(128) NOT NULL,
PRIMARY KEY(id)
) DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `instrument_order`(
id INT NOT NULL AUTO_INCREMENT,
instrument_id INT NOT NULL,
order_id INT NOT NULL,
FOREIGN KEY(instrument_id) REFERENCES instrument(id) on delete cascade on update cascade,
FOREIGN KEY(order_id) REFERENCES `order`(id) on delete cascade on update cascade,
PRIMARY KEY(id)
) DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `user_order`(
id INT NOT NULL AUTO_INCREMENT ,
user_id INT NOT NULL,
order_id INT NOT NULL,
FOREIGN KEY(user_id) REFERENCES user(id) on delete cascade on update cascade,
FOREIGN KEY(order_id) REFERENCES `order`(id) on delete cascade on update cascade,
PRIMARY KEY(id)
) DEFAULT CHARSET=utf8;