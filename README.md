# Lesson Crawler

## Code.org

### Source

[Code.org Courses](https://studio.code.org/courses) in Simplified Chinese Version

### Database

``` sql

CREATE DATABASE `stemweb` /*!40100 DEFAULT CHARACTER SET utf8 */;

CREATE TABLE `lesson` (
  `id` varchar(100) NOT NULL,
  `creatorId` varchar(100) DEFAULT NULL,
  `difficulty` int(11) DEFAULT NULL,
  `likeCount` int(11) DEFAULT NULL,
  `name` varchar(100) DEFAULT NULL,
  `thumbnail` varchar(100) DEFAULT NULL,
  `viewCount` int(11) DEFAULT NULL,
  `createTime` datetime DEFAULT NULL,
  `ageRangeId` varchar(100) DEFAULT NULL,
  `categoryId` varchar(100) DEFAULT NULL,
  `typeId` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `lesson_stage` (
  `lesson_id` varchar(255) NOT NULL,
  `lesson_stage_id` int(11) NOT NULL,
  `stage_id` varchar(255) NOT NULL,
  PRIMARY KEY (`lesson_id`,`lesson_stage_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `stage` (
  `id` varchar(255) NOT NULL DEFAULT '',
  `stage_name` varchar(255) NOT NULL DEFAULT '',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `stage_sub_stage` (
  `stage_id` varchar(255) NOT NULL,
  `stage_sub_stage_id` int(11) NOT NULL,
  `sub_stage_id` varchar(255) NOT NULL,
  PRIMARY KEY (`stage_id`,`stage_sub_stage_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `stage_level` (
  `stage_id` varchar(255) NOT NULL,
  `stage_level_id` int(11) NOT NULL,
  `level_id` varchar(255) NOT NULL,
  PRIMARY KEY (`stage_id`,`stage_level_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `level` (
  `id` varchar(255) NOT NULL,
  `level_name` varchar(255) NOT NULL DEFAULT '',
  `level_url` varchar(255) NOT NULL DEFAULT '',
  `type_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `level_code_org` (
  `id` varchar(255) NOT NULL,
  `level_name` varchar(255) DEFAULT NULL,
  `level_url` varchar(255) NOT NULL DEFAULT '',
  `game_name` varchar(63) DEFAULT NULL,
  `skin_name` varchar(63) DEFAULT NULL,
  `base_url` varchar(255) DEFAULT NULL,
  `app_name` varchar(63) DEFAULT NULL,
  `level_properties` text,
  `script_id` int(11) DEFAULT NULL,
  `script_name` varchar(63) DEFAULT NULL,
  `stage_position` int(11) DEFAULT NULL,
  `level_position` int(11) DEFAULT NULL,
  `has_contained_levels` tinyint(4) DEFAULT NULL,
  `skip_sound` tinyint(4) DEFAULT NULL,
  `skip_level` tinyint(4) DEFAULT NULL,
  `skip_dialog` tinyint(4) DEFAULT NULL,
  `pre_title` varchar(63) DEFAULT NULL,
  `level_type` varchar(63) DEFAULT NULL,
  `script_src` varchar(63) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

```

### ChromeDriver

Download from [ChromeDriver - WebDriver for Chrome](https://sites.google.com/a/chromium.org/chromedriver/)

Put it into the source code folder, or specify the path of it in the parameters

### Python Env

Python 3

## Code Camp

### Source

[Github: freeCodeCamp/freeCodeCamp/Seed/Challenge](https://github.com/freeCodeCamp/freeCodeCamp/tree/staging/seed/challenges)

**ATTENTION**: You need to delete `./07-contribute-to-open-source-and-help-nonprofits/` and replace '_id' to 'id' in `./08-coding-interview-questions-and-take-home-assignments/project-euler-problems.json`