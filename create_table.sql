-- create the table
CREATE TABLE festool (
  id SERIAL,
  datetime_collected TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  product_name VARCHAR,
  previous_price VARCHAR,
  current_price VARCHAR,
  PRIMARY KEY (id)
);
