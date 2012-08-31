drop table if exists categories;
create table categories (
    name text primary key
);

drop table if exists articles;
create table articles (
    id integer primary key autoincrement,
    title text not null,
    date_posted text not null,
    content text not null,
    cat_name text not null,
    Foreign Key('cat_name') references categories('name')
);

drop table if exists authors;
create table authors (
	id integer primary key autoincrement,
	name text not null,
	hash text not null
);

