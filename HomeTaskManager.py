from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
import sqlite3
import os
from openai import OpenAI
import json


app = Flask(__name__)

# Configure database
DB_PATH = 'tasks.db'

# Create database if it doesn't exist
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tasks table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        due_date TEXT,
        create_date TEXT,
        category TEXT,
        assigned_user TEXT,
        created_by TEXT,
        time_expectancy REAL,
        workflow TEXT,
        urgency TEXT
    )
    ''')
    
    # Create subtasks table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS subtasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER,
        title TEXT NOT NULL,
        description TEXT,
        workflow BOOLEAN,
        FOREIGN KEY (task_id) REFERENCES tasks (id)
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

@app.route('/askaifortask')
def createTasksAI():

    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM tasks WHERE workflow != "Done"')
    tasks = cursor.fetchall()

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key="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",
    )

    completion = client.chat.completions.create(
        extra_headers={
            "HTTP-Referer": "<YOUR_SITE_URL>", # Optional. Site URL for rankings on openrouter.ai.
            "X-Title": "<YOUR_SITE_NAME>", # Optional. Site title for rankings on openrouter.ai.
        },
        extra_body={},
        model="deepseek/deepseek-r1:free",
        messages=[
            {
                "role": "user",
                "content": """category:(Pessoal, Casa, Trabalho, Lazer) choose one of the 4 randomly ,The json should be in Portuguese from Portugal and adapt the Task with the category. Give me in form of json a daily task to improve my day that can be done any time of the day, with subtasks describing the task and giving a step by step to make the task append, the format of the json should be equal to this
                    Task = {title: '', description: '', due_date:today date like 27/03/2025, create_date:today date like 27/03/2025, category:one of the ones that u choose, assigned_user:Always Any,  created_by: Always Deepseek,time_expectancy:defined by you,workflow:Equal to new, urgency:sempre igual a Low, subtaks:{title:"",description:""},...}
                Give me only the Json without any additional information please.
                Dont Give tasks equal to this ones:
                """+ str(tasks)
            }
        ]
    )
    try:
        y = ""
        y = json.loads(str(completion.choices[0].message.content[8:-3]))
        print(y)
        #print(title, description, due_date, create_date, category, assigned_user, created_by, time_expectancy, workflow, urgency)
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Insert task into database
        cursor.execute('''
            INSERT INTO tasks (title, description, due_date, create_date, category, assigned_user, created_by, time_expectancy, workflow, urgency)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (y['title'],y['description'] ,y['due_date'] , y['create_date'],y['category'] ,y['assigned_user'] ,y['created_by'] ,y['time_expectancy'] ,y['workflow'] ,y['urgency'] ))
    
        # Get the id of the newly inserted task
        task_id = cursor.lastrowid

        for subtask in y['subtasks']:
            cursor.execute('''
            INSERT INTO subtasks (task_id, title, description, workflow)
            VALUES (?, ?, ?, ?)
            ''', (task_id, subtask["title"], subtask["description"], 0))

        conn.commit()
        conn.close()

        return redirect(url_for('index'))
    except:
        return redirect(url_for('index'))

@app.route('/')
def index():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM tasks WHERE workflow != "Done"')
    tasks = cursor.fetchall()
    
    # For each task, get its subtasks
    tasks_with_subtasks = []
    for task in tasks:
        cursor.execute('SELECT * FROM subtasks WHERE task_id = ?', (task['id'],))
        subtasks = cursor.fetchall()
        task_dict = dict(task)
        task_dict['subtasks'] = [dict(subtask) for subtask in subtasks]
        tasks_with_subtasks.append(task_dict)
    
    conn.close()
    


    return render_template('HomePage.html', tasks_json=tasks_with_subtasks)


@app.route('/concluded')
def concluded():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM tasks WHERE workflow == "Done"')
    tasks = cursor.fetchall()
    
    # For each task, get its subtasks
    tasks_with_subtasks = []
    for task in tasks:
        cursor.execute('SELECT * FROM subtasks WHERE task_id = ?', (task['id'],))
        subtasks = cursor.fetchall()
        task_dict = dict(task)
        task_dict['subtasks'] = [dict(subtask) for subtask in subtasks]
        tasks_with_subtasks.append(task_dict)
    
    conn.close()

    return render_template('HomePage.html', tasks_json=tasks_with_subtasks)

@app.route('/CreationPage')
def creation():
    return render_template('CreationPage.html')

@app.route('/create_task', methods=['POST'])
def create_task():
    # Get form data
    title = request.form['title']
    description = request.form['description']
    due_date = request.form['dueDate']
    create_date = request.form['createdOn']
    category = request.form['category']
    assigned_user = request.form['user']
    created_by = request.form['createdBy']
    time_expectancy = request.form['timeExpectancy']
    workflow = request.form['workflow']
    urgency = request.form['urgency']
 
    print(title, description, due_date, create_date, category, assigned_user, created_by, time_expectancy, workflow, urgency)
    
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Insert task into database
    cursor.execute('''
    INSERT INTO tasks (title, description, due_date, create_date, category, assigned_user, created_by, time_expectancy, workflow, urgency)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (title, description, due_date, create_date, category, assigned_user, created_by, time_expectancy, workflow, urgency))
    
    # Get the id of the newly inserted task
    task_id = cursor.lastrowid
    
    # Process subtasks
    # The form will send subtask data as subtasks[0][title], subtasks[0][description], etc.
    subtask_titles = [k for k in request.form.keys() if k.startswith('subtasks') and k.endswith('[title]')]
    
    for key in subtask_titles:
        index = key.split('[')[1].split(']')[0]
        subtask_title = request.form[f'subtasks[{index}][title]']
        subtask_description = request.form[f'subtasks[{index}][description]']
        
        if subtask_title:
            cursor.execute('''
            INSERT INTO subtasks (task_id, title, description, workflow)
            VALUES (?, ?, ?, ?)
            ''', (task_id, subtask_title, subtask_description, 0))
        print(subtask_title, subtask_description)
 
    
    conn.commit()
    conn.close()
       
    return redirect(url_for('index'))

#### EXEMPLO DE EXPORTÇÃO DE VARIAVEIS  
#@app.route('/hello/<name>')
#def hello(name=None):
#    return render_template('hello.html', person=name)
####

@app.route('/delete_task/<taskid>', methods=['POST', 'GET'])
def delete_task(taskid=None):
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()


    # Insert task into database
    cursor.execute('''
    DELETE FROM tasks WHERE id = ?
    ''', [taskid])
    
    cursor.execute('''
    DELETE FROM subtasks WHERE task_id = ?
    ''', [taskid])
    
    conn.commit()
    conn.close()
       
    return redirect(url_for('index'))

@app.route('/complete_subtask/<taskid>/<subtaskid>', methods=['POST', 'GET'])
def complete_subtask(taskid=None, subtaskid=None):
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
    UPDATE subtasks SET workflow=1 WHERE id=? AND task_id = ? 
    ''', [subtaskid,taskid])

    cursor.execute('''
    UPDATE tasks SET workflow="In Progress" WHERE id=?
    ''', [taskid])
    
    conn.commit()
    conn.close()
       
    return redirect(url_for('index'))

@app.route('/complete_task/<taskid>', methods=['POST', 'GET'])
def complete_task(taskid=None):
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
    UPDATE tasks SET workflow="Done" WHERE id=?
    ''', [taskid])
    
    conn.commit()
    conn.close()
       
    return redirect(url_for('index'))
 

if __name__ == '__main__':
    #Home
    #app.run(host='192.168.1.224', debug=True) 
    app.run(debug=True)
