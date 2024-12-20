import duckdb

# Connect to the DuckDB database (will create a file-based database if it doesn't exist)
conn = duckdb.connect('email_database.db')

# Create the 'emails' table without an auto-increment constraint for 'id'
conn.execute('''
    CREATE TABLE IF NOT EXISTS emails (
        id INTEGER PRIMARY KEY,    -- Regular 'id' column without auto-increment
        sender VARCHAR NOT NULL,   -- Email address of the sender
        recipient VARCHAR NOT NULL,-- Email address of the recipient
        subject VARCHAR,           -- Subject of the email
        body TEXT,                 -- Body content of the email
        timestamp TIMESTAMP DEFAULT NOW(),  -- Time the email was sent
        attachment BLOB            -- Attachment data, could be a file in binary format
    );
''')

# importance INTEGER NOT NULL -- AI generated importance

def insert_email(sender, recipient, subject, body, attachment=None):
    conn = duckdb.connect('email_database.db')
    conn.execute('''
        INSERT INTO emails (sender, recipient, subject, body, attachment)
        VALUES (?, ?, ?, ?, ?);
    ''', (sender, recipient, subject, body, attachment))
    conn.commit()
    conn.close()

def get_emails_by_sender(sender):
    conn = duckdb.connect('email_database.db')
    result = conn.execute("SELECT * FROM emails WHERE sender = ?;", (sender,)).fetchall()
    conn.close()
    return result

emails_from_john = get_emails_by_sender('john.doe@example.com')
print(emails_from_john)

def get_emails_by_date(start_date, end_date):
    conn = duckdb.connect('email_database.db')
    query = '''
        SELECT * FROM emails
        WHERE timestamp BETWEEN ? AND ?;
    '''
    result = conn.execute(query, (start_date, end_date)).fetchall()
    conn.close()
    return result


#emails_in_range = get_emails_by_date('2024-01-01', '2024-12-31')
#print(emails_in_range)


def update_email_subject(email_id, new_subject):
    conn = duckdb.connect('email_database.db')
    conn.execute("UPDATE emails SET subject = ? WHERE id = ?", (new_subject, email_id))
    conn.commit()
    conn.close()


def delete_email(email_id):
    conn = duckdb.connect('email_database.db')
    conn.execute("DELETE FROM emails WHERE id = ?", (email_id,))
    conn.commit()
    conn.close()


# Insert a few emails
#insert_email('77','john.doe@example.com', 'jane.smith@example.com', 'Meeting Reminder', 'Dont forget about the meeting!')
#insert_email('3','alice@example.com', 'bob@example.com', 'Work Update', 'Here is the latest work progress.')

# Fetch emails sent by 'john.doe@example.com'
emails_from_john = get_emails_by_sender('john.doe@example.com')
print(emails_from_john)


# Insert a sample email into the 'emails' table
#conn.execute("INSERT INTO emails (id,sender, recipient, subject, body) VALUES ('12345','john.doe@example.com', 'jane.smith@example.com', 'Meeting Update', 'The meeting is at 10 AM tomorrow.')")

# Commit the changes
conn.commit()

# Close the connection
conn.close()
