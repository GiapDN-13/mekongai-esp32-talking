DROP TABLE IF EXISTS sys_user;
DROP TABLE IF EXISTS sys_params;
DROP TABLE IF EXISTS sys_user_token;
DROP TABLE IF EXISTS sys_dict_type;
DROP TABLE IF EXISTS sys_dict_data;

-- System users
CREATE TABLE sys_user (
  id bigint NOT NULL COMMENT 'id',
  username varchar(50) NOT NULL COMMENT 'Username',
  password varchar(100) COMMENT 'Password',
  super_admin tinyint unsigned COMMENT 'Super admin: 0 no, 1 yes',
  status tinyint COMMENT 'Status: 0 disabled, 1 active',
  create_date datetime COMMENT 'Created at',
  updater bigint COMMENT 'Updated by user id',
  creator bigint COMMENT 'Created by user id',
  update_date datetime COMMENT 'Updated at',
  primary key (id),
  unique key uk_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='System users';

-- User tokens
CREATE TABLE sys_user_token (
  id bigint NOT NULL COMMENT 'id',
  user_id bigint NOT NULL COMMENT 'User id',
  token varchar(100) NOT NULL COMMENT 'Session token',
  expire_date datetime COMMENT 'Expires at',
  update_date datetime COMMENT 'Updated at',
  create_date datetime COMMENT 'Created at',
  PRIMARY KEY (id),
  UNIQUE KEY user_id (user_id),
  UNIQUE KEY token (token)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='User tokens';

-- Parameters (initial DDL; re-seeded in schema-sys-params-and-seed.sql)
create table sys_params
(
  id                   bigint NOT NULL COMMENT 'id',
  param_code           varchar(32) COMMENT 'Parameter code',
  param_value          varchar(2000) COMMENT 'Parameter value',
  param_type           tinyint unsigned default 1 COMMENT 'Kind: 0 system, 1 non-system',
  remark               varchar(200) COMMENT 'Note',
  creator              bigint COMMENT 'Created by',
  create_date          datetime COMMENT 'Created at',
  updater              bigint COMMENT 'Updated by',
  update_date          datetime COMMENT 'Updated at',
  primary key (id),
  unique key uk_param_code (param_code)
)ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COMMENT='Parameters';

-- Dictionary types
create table sys_dict_type
(
    id                   bigint NOT NULL COMMENT 'id',
    dict_type            varchar(100) NOT NULL COMMENT 'Dict type code',
    dict_name            varchar(255) NOT NULL COMMENT 'Dict type name',
    remark               varchar(255) COMMENT 'Note',
    sort                 int unsigned COMMENT 'Sort order',
    creator              bigint COMMENT 'Created by',
    create_date          datetime COMMENT 'Created at',
    updater              bigint COMMENT 'Updated by',
    update_date          datetime COMMENT 'Updated at',
    primary key (id),
    UNIQUE KEY(dict_type)
)ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COMMENT='Dictionary types';

-- Dictionary entries
create table sys_dict_data
(
    id                   bigint NOT NULL COMMENT 'id',
    dict_type_id         bigint NOT NULL COMMENT 'Dictionary type id',
    dict_label           varchar(255) NOT NULL COMMENT 'Display label',
    dict_value           varchar(255) COMMENT 'Stored value',
    remark               varchar(255) COMMENT 'Note',
    sort                 int unsigned COMMENT 'Sort order',
    creator              bigint COMMENT 'Created by',
    create_date          datetime COMMENT 'Created at',
    updater              bigint COMMENT 'Updated by',
    update_date          datetime COMMENT 'Updated at',
    primary key (id),
    unique key uk_dict_type_value (dict_type_id, dict_value),
    key idx_sort (sort)
)ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COMMENT='Dictionary data';
