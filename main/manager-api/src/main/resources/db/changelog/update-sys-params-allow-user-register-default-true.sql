-- Open user self-registration by default. Admins may set server.allow_user_register to false in 参数管理 to close it.
UPDATE sys_params SET param_value = 'true' WHERE param_code = 'server.allow_user_register';
