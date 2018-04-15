CREATE TABLE categories(id INT(11) AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100), gname VARCHAR(100));

INSERT INTO categories(name, gname) VALUES ("Configuration Management", "Infrastrucure");
INSERT INTO categories(name, gname) VALUES ("Cloud Management", "Infrastrucure");
INSERT INTO categories(name, gname) VALUES ("Networking", "Infrastrucure");
INSERT INTO categories(name, gname) VALUES ("Virtualization", "Infrastrucure");
INSERT INTO categories(name, gname) VALUES ("Monitoring", "Infrastrucure");
INSERT INTO categories(name, gname) VALUES ("Object-based", "Infrastrucure");
INSERT INTO categories(name, gname) VALUES ("Key Management", "Infrastrucure");

INSERT INTO categories(name, gname) VALUES ("Change Control", "Security");
INSERT INTO categories(name, gname) VALUES ("Endpoint protection", "Security");
INSERT INTO categories(name, gname) VALUES ("Vulnerability Management", "Security");
INSERT INTO categories(name, gname) VALUES ("DLP", "Security");
INSERT INTO categories(name, gname) VALUES ("SIEM", "Security");
INSERT INTO categories(name, gname) VALUES ("APT Protection", "Security");
INSERT INTO categories(name, gname) VALUES ("Secure File Transfer", "Security");

INSERT INTO categories(name, gname) VALUES ("FW", "Firewalling");
INSERT INTO categories(name, gname) VALUES ("Web Application Firewall", "Firewalling");
INSERT INTO categories(name, gname) VALUES ("Proxy", "Firewalling");
INSERT INTO categories(name, gname) VALUES ("Firewall Audit Tools", "Firewalling");
INSERT INTO categories(name, gname) VALUES ("Priviledged Session Manager", "Firewalling");
INSERT INTO categories(name, gname) VALUES ("Loadbalancers", "Firewalling");

INSERT INTO categories(name, gname) VALUES ("Application Security Scanner", "Other");
INSERT INTO categories(name, gname) VALUES ("Hypercoverged", "Other");
INSERT INTO categories(name, gname) VALUES ("Governance", "Other");
