-- IAM Database Schema
-- PostgreSQL and MySQL compatible
-- Naming: lowercase + snake_case
-- No quoted identifiers required

-- =========================
-- Applications
-- =========================
CREATE TABLE IF NOT EXISTS applications (
    app_id VARCHAR(10) PRIMARY KEY,
    app_name VARCHAR(50) NOT NULL UNIQUE,
    app_owner VARCHAR(100) NOT NULL
);

INSERT INTO applications (app_id, app_name, app_owner) VALUES
('A01','Workday','James.Smith'),
('A02','Salesforce','Sarah.Jones'),
('A03','ServiceNow','Michael.Brown'),
('A04','Jira','Olivia.Taylor'),
('A05','Concur','Aaron.Nichols'),
('A06','Slack','Bethany.Clark'),
('A07','Okta','Diana.Wong'),
('A08','Tableau','Gavin.Lee'),
('A09','SAP','Ethan.Reed'),
('A10','GitHub','Fiona.Gray'),
('A11','AzureAD','Hannah.Price');

-- =========================
-- Roles
-- =========================
CREATE TABLE IF NOT EXISTS roles (
    role_id VARCHAR(10) PRIMARY KEY,
    role_name VARCHAR(100) NOT NULL,
    app_name VARCHAR(50) NOT NULL,
    owner VARCHAR(100) NOT NULL,
    CONSTRAINT fk_roles_app
        FOREIGN KEY (app_name)
        REFERENCES applications (app_name)
        ON DELETE CASCADE
);

INSERT INTO roles (role_id, role_name, app_name, owner) VALUES
('R01','HR Analyst','Workday','Aaron.Nichols'),
('R02','Payroll Admin','Workday','Bethany.Clark'),
('R03','Sales Manager','Salesforce','Sarah.Jones'),
('R04','Case Resolver','ServiceNow','Michael.Brown'),
('R05','Project Lead','Jira','Olivia.Taylor'),
('R06','Expense Approver','Concur','Ethan.Reed'),
('R07','Collaboration Admin','Slack','Fiona.Gray'),
('R08','Identity Admin','Okta','Diana.Wong'),
('R09','Reporting Analyst','Tableau','Gavin.Lee'),
('R10','Developer','GitHub','Julia.Rogers'),
('R11','IT Admin','AzureAD','Kevin.Liu');

-- =========================
-- Users
-- =========================
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(10) PRIMARY KEY,
    user_name VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(150) NOT NULL UNIQUE,
    manager VARCHAR(100)
);

INSERT INTO users (user_id, user_name, email, manager) VALUES
('U01','Aaron.Nichols','Aaron.Nichols@test.com','James.Smith'),
('U02','Bethany.Clark','Bethany.Clark@test.com','James.Smith'),
('U03','Carlos.Mendez','Carlos.Mendez@test.com','Sarah.Jones'),
('U04','Diana.Wong','Diana.Wong@test.com','Sarah.Jones'),
('U05','Ethan.Reed','Ethan.Reed@test.com','Michael.Brown'),
('U06','Fiona.Gray','Fiona.Gray@test.com','Michael.Brown'),
('U07','Gavin.Lee','Gavin.Lee@test.com','Olivia.Taylor'),
('U08','Hannah.Price','Hannah.Price@test.com','Olivia.Taylor'),
('U09','Isaac.Khan','Isaac.Khan@test.com','James.Smith'),
('U10','Julia.Rogers','Julia.Rogers@test.com','Sarah.Jones'),
('U11','Kevin.Liu','Kevin.Liu@test.com','Sarah.Jones');
