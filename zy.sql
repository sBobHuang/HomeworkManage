drop table students;
create table students
(
    id              TEXT not null
        primary key,
    real_name       TEXT,
    class_name       TEXT,
    course_names     TEXT,
    gender          INTEGER,
    mobile_phone    VARCHAR(64),
    created_at      DATETIME,
    last_updated_at DATETIME,
    extended_info   TEXT
);
drop table fileRecords;
create table fileRecords
(
	id INTEGER
		primary key,
	student_id Text,
	real_name TEXT,
	home_work_id INTEGER,
	courseName TEXT,
	score REAL,
	created_at DATETIME
);