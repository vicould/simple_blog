drop table if exists categories;
create table categories (
    id integer primary key autoincrement,
    name text not null
);

drop table if exists articles;
create table articles (
    id integer primary key autoincrement,
    title text not null,
    date_posted text not null,
    content text not null,
    cat_id integer not null,
    Foreign Key('cat_id') references categories('id')
);

