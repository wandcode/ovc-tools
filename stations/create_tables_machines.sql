--
-- OV-chipkaart machines
--

CREATE TABLE machines_data (
		company INT NOT NULL,			-- transport company number
		machineid INT NOT NULL,			-- machine id
		ovcid INT,				-- corresponding station
		vehicleid INT,				-- or corresponding vehicle
		PRIMARY KEY (company, machineid) --,
		-- FOREIGN KEY (company, ovcid) REFERENCES stations_data(company, ovcid) DEFERRABLE INITIALLY DEFERRED
        );
