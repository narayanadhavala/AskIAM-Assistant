CREATE DATABASE IF NOT EXISTS iamdb;
USE iamdb;

CREATE TABLE Applications (
    AppID VARCHAR(10) PRIMARY KEY,
    AppName VARCHAR(50) NOT NULL UNIQUE,
    AppOwner VARCHAR(100) NOT NULL
);

INSERT INTO Applications VALUES
('A01','Workday','James.Smith'),
('A02','Salesforce','Sarah.Jones'),
('A03','ServiceNow','Michael.Brown'),
('A04','Jira','Olivia.Taylor'),
('A05','Concur','Aaron.Nichols'),
('A06','Slack','Bethany.Clark'),
('A07','Okta','Diana.Wong'),
('A08','Tableau','Gavin.Lee'),
('A09','SAP','Ethan.Reed'),
('A10','GitHub','Fiona.Gray');

CREATE TABLE Roles (
    RoleID VARCHAR(10) PRIMARY KEY,
    RoleName VARCHAR(100) NOT NULL,
    AppName VARCHAR(50) NOT NULL,
    Owner VARCHAR(100) NOT NULL,
    FOREIGN KEY (AppName) REFERENCES Applications(AppName) ON DELETE CASCADE
);

INSERT INTO Roles VALUES
('R01','HR Analyst','Workday','Aaron.Nichols'),
('R02','Payroll Admin','Workday','Bethany.Clark'),
('R03','Sales Manager','Salesforce','Sarah.Jones'),
('R04','Case Resolver','ServiceNow','Michael.Brown'),
('R05','Project Lead','Jira','Olivia.Taylor'),
('R06','Expense Approver','Concur','Ethan.Reed'),
('R07','Collaboration Admin','Slack','Fiona.Gray'),
('R08','Identity Admin','Okta','Diana.Wong'),
('R09','Reporting Analyst','Tableau','Gavin.Lee'),
('R10','Developer','GitHub','Julia.Rogers');

CREATE TABLE Users (
    UserID VARCHAR(10) PRIMARY KEY,
    UserName VARCHAR(100) NOT NULL UNIQUE,
    Email VARCHAR(150) NOT NULL UNIQUE,
    Manager VARCHAR(100)
);

INSERT INTO Users VALUES
('U01','Aaron.Nichols','Aaron.Nichols@test.com','James.Smith'),
('U02','Bethany.Clark','Bethany.Clark@test.com','James.Smith'),
('U03','Carlos.Mendez','Carlos.Mendez@test.com','Sarah.Jones'),
('U04','Diana.Wong','Diana.Wong@test.com','Sarah.Jones'),
('U05','Ethan.Reed','Ethan.Reed@test.com','Michael.Brown'),
('U06','Fiona.Gray','Fiona.Gray@test.com','Michael.Brown'),
('U07','Gavin.Lee','Gavin.Lee@test.com','Olivia.Taylor'),
('U08','Hannah.Price','Hannah.Price@test.com','Olivia.Taylor'),
('U09','Isaac.Khan','Isaac.Khan@test.com','James.Smith'),
('U10','Julia.Rogers','Julia.Rogers@test.com','Sarah.Jones');
