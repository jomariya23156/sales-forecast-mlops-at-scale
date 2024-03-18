CREATE USER mlflow_user WITH PASSWORD 'SuperSecurePwdHere' CREATEDB;
CREATE DATABASE mlflow_pg_db
    WITH 
    OWNER = mlflow_user
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.utf8'
    LC_CTYPE = 'en_US.utf8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

CREATE USER forecast_user WITH PASSWORD 'SuperSecurePwdHere' CREATEDB;
CREATE DATABASE forecast_pg_db
    WITH 
    OWNER = forecast_user
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.utf8'
    LC_CTYPE = 'en_US.utf8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

CREATE USER spark_user WITH PASSWORD 'SuperSecurePwdHere' CREATEDB;
CREATE DATABASE spark_pg_db
    WITH 
    OWNER = spark_user
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.utf8'
    LC_CTYPE = 'en_US.utf8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

CREATE USER airflow_user WITH PASSWORD 'SuperSecurePwdHere' CREATEDB;
CREATE DATABASE airflow_pg_db
    WITH 
    OWNER = airflow_user
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.utf8'
    LC_CTYPE = 'en_US.utf8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;