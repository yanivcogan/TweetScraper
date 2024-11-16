create table accounts
(
    id              int auto_increment
        primary key,
    create_date     datetime                                                        default CURRENT_TIMESTAMP not null,
    update_date     datetime                                                        default CURRENT_TIMESTAMP not null on update CURRENT_TIMESTAMP,
    account         varchar(250)                                                                              not null,
    scraping_status enum ('not_scraped', 'in_progress', 'error', 'partial', 'done') default 'not_scraped'     not null,
    constraint accounts_handle
        unique (account)
);

create table jobs
(
    id            int auto_increment
        primary key,
    create_date   datetime default CURRENT_TIMESTAMP not null,
    update_date   datetime default CURRENT_TIMESTAMP not null on update CURRENT_TIMESTAMP,
    started_at    datetime                           not null,
    ended_at      datetime                           not null,
    user_id       varchar(250)                       not null,
    fetch_method  varchar(250)                       not null,
    covering_from datetime                           not null,
    covering_to   datetime                           not null,
    tweet_count   int                                not null,
    commit_id     varchar(250)                       null
);

create table tweets
(
    id          int auto_increment
        primary key,
    create_date datetime default CURRENT_TIMESTAMP not null,
    update_date datetime default CURRENT_TIMESTAMP not null on update CURRENT_TIMESTAMP invisible,
    job_id      int                                not null,
    tweet_id    varchar(250)                       not null,
    data        json                               not null,
    hash_val    varchar(250)                       not null,
    constraint tweet_snowflake_unq
        unique (tweet_id)
);

