-- upgrade --
CREATE TABLE IF NOT EXISTS "attachment" (
    "id" CHAR(36) NOT NULL  PRIMARY KEY,
    "type" VARCHAR(5) NOT NULL  /* empty: empty\nimage: image\nvoice: voice */,
    "path" VARCHAR(50) NOT NULL
);
CREATE TABLE IF NOT EXISTS "user" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "username" VARCHAR(30) NOT NULL UNIQUE,
    "password" VARCHAR(30) NOT NULL
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(20) NOT NULL,
    "content" JSON NOT NULL
);
