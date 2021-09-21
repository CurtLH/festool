-- create the table
CREATE TABLE festool (
  id SERIAL,
  datetime_collected TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  product_name VARCHAR,
  original_price NUMERIC (10, 2),
  refurb_price NUMERIC (10, 2),
  discount NUMERIC (10, 2),
  PRIMARY KEY (id)
);
