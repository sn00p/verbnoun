CREATE TABLE components(id INT(11) AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100), category VARCHAR(100), gname VARCHAR(100), link VARCHAR(1024));

-- Infrastrucure
INSERT INTO components(name, category, gname, link) VALUES ("Chef", "Configuration Management", "Infrastrucure", "");
INSERT INTO components(name, category, gname, link) VALUES ("Puppet", "Configuration Management", "Infrastrucure", "");
INSERT INTO components(name, category, gname, link) VALUES ("Ansible", "Configuration Management", "Infrastrucure", "");
INSERT INTO components(name, category, gname, link) VALUES ("CloudCenter", "Cloud Management", "Infrastrucure", "");
INSERT INTO components(name, category, gname, link) VALUES ("vRealize", "Cloud Management", "Infrastrucure", "");
INSERT INTO components(name, category, gname, link) VALUES ("Morpheus", "Cloud Management", "Infrastrucure", "");
INSERT INTO components(name, category, gname, link) VALUES ("ACI", "Networking", "Infrastrucure", "");
INSERT INTO components(name, category, gname, link) VALUES ("NSX", "Networking", "Infrastrucure", "");
INSERT INTO components(name, category, gname, link) VALUES ("OpenStack", "Networking", "Infrastrucure", "");
INSERT INTO components(name, category, gname, link) VALUES ("VMWare", "Virtualization", "Infrastrucure", "");
INSERT INTO components(name, category, gname, link) VALUES ("KVM", "Virtualization", "Infrastrucure", "");
INSERT INTO components(name, category, gname, link) VALUES ("OpenStack", "Virtualization", "Infrastrucure", "");
INSERT INTO components(name, category, gname, link) VALUES ("AppDynamics", "Monitoring", "Infrastrucure", "");
INSERT INTO components(name, category, gname, link) VALUES ("Riverbed", "Monitoring", "Infrastrucure", "");
INSERT INTO components(name, category, gname, link) VALUES ("IBM Netcool", "Monitoring", "Infrastrucure", "");
INSERT INTO components(name, category, gname, link) VALUES ("Microsoft SCOM", "Monitoring", "Infrastrucure", "");
INSERT INTO components(name, category, gname, link) VALUES ("CA Spectrum", "Monitoring", "Infrastrucure", "");
INSERT INTO components(name, category, gname, link) VALUES ("ServiceTrace", "Monitoring", "Infrastrucure", "");
INSERT INTO components(name, category, gname, link) VALUES ("Nagios", "Monitoring", "Infrastrucure", "");
INSERT INTO components(name, category, gname, link) VALUES ("ScienceLogic", "Monitoring", "Infrastrucure", "");
INSERT INTO components(name, category, gname, link) VALUES ("HCP", "Object-based", "Infrastrucure", "");
INSERT INTO components(name, category, gname, link) VALUES ("Cleversafe", "Object-based", "Infrastrucure", "");
INSERT INTO components(name, category, gname, link) VALUES ("CEPH", "Object-based", "Infrastrucure", "");
INSERT INTO components(name, category, gname, link) VALUES ("Gemalto KeySecure", "Key Management", "Infrastrucure", "");
INSERT INTO components(name, category, gname, link) VALUES ("Thales netHSM", "Key Management", "Infrastrucure", "");

-- Security
INSERT INTO components(name, category, gname, link) VALUES ("ServiceNow", "Change Control", "Security", "");
INSERT INTO components(name, category, gname, link) VALUES ("Chernell", "Change Control", "Security", "");
INSERT INTO components(name, category, gname, link) VALUES ("BMC", "Change Control", "Security", "");
INSERT INTO components(name, category, gname, link) VALUES ("IBM", "Change Control", "Security", "");
INSERT INTO components(name, category, gname, link) VALUES ("CLOUDST", "Endpoint protection", "Security", "");
INSERT INTO components(name, category, gname, link) VALUES ("TRAPS/WF", "Endpoint protection", "Security", "");
INSERT INTO components(name, category, gname, link) VALUES ("CarbonBlack", "Endpoint protection", "Security", "");
INSERT INTO components(name, category, gname, link) VALUES ("Tanium", "Endpoint protection", "Security", "");
INSERT INTO components(name, category, gname, link) VALUES ("Cylance", "Endpoint protection", "Security", "");
INSERT INTO components(name, category, gname, link) VALUES ("Nessus", "Vulnerability Management", "Security", "");
INSERT INTO components(name, category, gname, link) VALUES ("Qualys", "Vulnerability Management", "Security", "");
INSERT INTO components(name, category, gname, link) VALUES ("Trustwave", "Vulnerability Management", "Security", "");
INSERT INTO components(name, category, gname, link) VALUES ("Forcepoint", "DLP", "Security", "");
INSERT INTO components(name, category, gname, link) VALUES ("RSA DLP", "DLP", "Security", "");
INSERT INTO components(name, category, gname, link) VALUES ("McAfee DLP", "DLP", "Security", "");
INSERT INTO components(name, category, gname, link) VALUES ("Symantec DLP", "DLP", "Security", "");
INSERT INTO components(name, category, gname, link) VALUES ("HP ArcSight", "SIEM", "Security", "");
INSERT INTO components(name, category, gname, link) VALUES ("IBM Qradar", "SIEM", "Security", "");
INSERT INTO components(name, category, gname, link) VALUES ("FireEye", "APT Protection", "Security", "");
INSERT INTO components(name, category, gname, link) VALUES ("TrendMicro", "APT Protection", "Security", "");
INSERT INTO components(name, category, gname, link) VALUES ("Mandiant", "APT Protection", "Security", "");
INSERT INTO components(name, category, gname, link) VALUES ("Cryptshare", "Secure File Transfer", "Security", "");
INSERT INTO components(name, category, gname, link) VALUES ("Cyberark", "Secure File Transfer", "Security", "");

-- Firewalling
INSERT INTO components(name, category, gname, link) VALUES ("PAN", "FW", "Firewalling", "");
INSERT INTO components(name, category, gname, link) VALUES ("SRX", "FW", "Firewalling", "");
INSERT INTO components(name, category, gname, link) VALUES ("Cisco ASA", "FW", "Firewalling", "");
INSERT INTO components(name, category, gname, link) VALUES ("NSX", "FW", "Firewalling", "");
INSERT INTO components(name, category, gname, link) VALUES ("Imperva", "Web Application Firewall", "Firewalling", "");
INSERT INTO components(name, category, gname, link) VALUES ("Fortinet", "Web Application Firewall", "Firewalling", "");
INSERT INTO components(name, category, gname, link) VALUES ("F5", "Web Application Firewall", "Firewalling", "");
INSERT INTO components(name, category, gname, link) VALUES ("Bluecoat", "Proxy", "Firewalling", "");
INSERT INTO components(name, category, gname, link) VALUES ("Forcepoint", "Proxy", "Firewalling", "");
INSERT INTO components(name, category, gname, link) VALUES ("Zscaler", "Proxy", "Firewalling", "");
INSERT INTO components(name, category, gname, link) VALUES ("Tufin", "Firewall Audit Tools", "Firewalling", "");
INSERT INTO components(name, category, gname, link) VALUES ("SkyBox", "Firewall Audit Tools", "Firewalling", "");
INSERT INTO components(name, category, gname, link) VALUES ("Firemon", "Firewall Audit Tools", "Firewalling", "");
INSERT INTO components(name, category, gname, link) VALUES ("Utimaco HSM", "Priviledged Session Manager", "Firewalling", "");
INSERT INTO components(name, category, gname, link) VALUES ("Cyberark", "Priviledged Session Manager", "Firewalling", "");
INSERT INTO components(name, category, gname, link) VALUES ("Balabit", "Priviledged Session Manager", "Firewalling", "");
INSERT INTO components(name, category, gname, link) VALUES ("Centrify", "Priviledged Session Manager", "Firewalling", "");
INSERT INTO components(name, category, gname, link) VALUES ("F5", "Loadbalancers", "Firewalling", "");
INSERT INTO components(name, category, gname, link) VALUES ("Netscaler", "Loadbalancers", "Firewalling", "");
INSERT INTO components(name, category, gname, link) VALUES ("Avi ELB", "Loadbalancers", "Firewalling", "");

-- Other
INSERT INTO components(name, category, gname, link) VALUES ("ServiceNow", "Governance", "Other", "");
INSERT INTO components(name, category, gname, link) VALUES ("RSA/Archer", "Governance", "Other", "");
INSERT INTO components(name, category, gname, link) VALUES ("MetricStream", "Governance", "Other", "");
INSERT INTO components(name, category, gname, link) VALUES ("IBM", "Governance", "Other", "");
INSERT INTO components(name, category, gname, link) VALUES ("LockPath", "Governance", "Other", "");
INSERT INTO components(name, category, gname, link) VALUES ("Veracode", "Application Security Scanner", "Other", "");
INSERT INTO components(name, category, gname, link) VALUES ("HP Fortify", "Application Security Scanner", "Other", "");
INSERT INTO components(name, category, gname, link) VALUES ("IBM AppScan", "Application Security Scanner", "Other", "");
