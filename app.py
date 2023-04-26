import os
from flask import Flask, request, Response
import psycopg2
import json

app = Flask(__name__)

# Get environment variables
host = os.getenv('HOST_NAME')
db_name = os.getenv('DB_NAME')
db_user = os.getenv('DB_USER')
db_pass = os.getenv('DB_PASSWORD')

@app.route("/portfolio/<client_ID>", methods=["GET"])
def get_portfolio(client_ID):
    connection = None
    try:
        connection = psycopg2.connect(host=host, dbname=db_name, user=db_user, password=db_pass)
        cursor = connection.cursor()
        exists_query = "SELECT EXISTS(SELECT * FROM information_schema.tables WHERE table_name=%s)"
        cursor.execute(exists_query, (client_ID,))
        exists = cursor.fetchone()[0]

        if not exists:
            # Create table
            create_query = f"\
                CREATE TABLE {client_ID} (\
                \"ID\" integer NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 100 CACHE 1 ),\
                \"Name\" character varying(128) COLLATE pg_catalog.\"default\" NOT NULL,\
                \"Quantity\" integer  NOT NULL,\
                CONSTRAINT portfolio_pkey PRIMARY KEY (\"ID\"),\
                CONSTRAINT \"Name\" UNIQUE (\"Name\"))"
            
            cursor.execute(create_query)
            connection.commit()

        # Get components of portfolio
        select_query = f"SELECT * from {client_ID}"
        cursor.execute(select_query)

        records = cursor.fetchall()

        portfolio = {}
        for row in records:
            portfolio[row[1]] = row[2]
        
        return Response(json.dumps(portfolio), status=200)
        
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        if connection is not None:
            cursor.close()
            connection.close()
        return Response(status=400)

    finally:
        if connection is not None:
            cursor.close()
            connection.close()
    
@app.route("/portfolio/<client_ID>", methods=["PUT"])
def update_portfolio(client_ID):
    payload = request.get_json(force=True)

    for key in payload.keys():
        name = key
        quantity = int(payload[key])
        try:
            connection = psycopg2.connect(host=host, dbname=db_name, user=db_user, password=db_pass)
            cursor = connection.cursor()
            query = f"\
                UPDATE {client_ID}\
                SET \"Quantity\" = {quantity}\
                WHERE \"Name\" = \'{name}\'"
            
            cursor.execute(query)
            connection.commit()

            return Response(status=200)
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            if connection is not None:
                cursor.close()
                connection.close()
            return Response(status=400)

        finally:
            if connection is not None:
                cursor.close()
                connection.close()
    return Response(status=400)

if __name__ == "__main__":
    app.run(debug=False)