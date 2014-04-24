--
-- OV-chipkaart subscriptions
--

CREATE TABLE subscriptions_data (
		company INT NOT NULL,			-- transport company number
		id INT NOT NULL,			-- subscriptions id
		name VARCHAR(50),			-- name as used by transport company
		PRIMARY KEY (company, id)
        );
