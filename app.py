from collections import OrderedDict
from flask import Flask, render_template, flash, redirect, url_for, session, request, logging, send_file, make_response
from flask_jsglue import JSGlue
from flask_mail import Mail
from flask_mail import Message
from flask_mysqldb import MySQL
from functools import wraps
from jinja2 import Environment, FileSystemLoader, PackageLoader, select_autoescape
import json
import pandas as pd
from passlib.hash import sha256_crypt
import os
import re
import sys
from weasyprint import HTML
from wtforms import Form, StringField, TextAreaField, SelectField, SelectMultipleField, PasswordField, validators
import numpy as np
import ldap3
from tzlocal import get_localzone

jsglue = JSGlue()

app = Flask(__name__)

jsglue.init_app(app)

app.config['MYSQL_HOST'] = os.environ.get('VERBNOUN_MYSQL_SERVICE_HOST')
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = os.environ.get('VERBNOUN_MYSQL_ROOT_PASSWORD')
app.config['MYSQL_DB'] = 'verbnoun'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['LDAP_SERVER'] = os.environ.get('VERBNOUN_LDAP_SERVER')
mysql = MySQL(app)

app.config['MAIL_SERVER']='smtp.mail.ru'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = os.environ.get('VERBNOUN_MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('VERBNOUN_MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = True
mail = Mail(app)

# Adjust printing attribute in pandas for troubleshooting
#pd.set_option('display.height', 1000)
#pd.set_option('display.max_rows', 500)
#pd.set_option('display.max_columns', 500)
#pd.set_option('display.width', 1000)

app.config['LDAP_SERVER'] = os.environ.get('VERBNOUN_LDAP_SERVER')

app.secret_key='secret123'



@app.route('/')
def index():
    return render_template('home.html')

class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min = 1, max = 50)])
    username = StringField('Username', [validators.Length(min = 5, max = 25)])
    email = StringField('E-mail', [validators.Length(min = 6, max = 50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message = 'Passwords do not match'),
    ])
    confirm = PasswordField('Confirm password', [validators.DataRequired()])

@app.route('/register', methods = ['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))
        mysql.connection.commit()
        cur.close()

        flash('You are now registered and can login.', 'success')
        return redirect(url_for('index'))

    return render_template('register.html', form = form)

@app.route('/login', methods = ['GET', 'POST'])
def login():
    form = RegisterForm(request.form)
    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])
        if result > 0:
            data = cur.fetchone()
            password = data['password']
            session['role'] = data['role']
            if sha256_crypt.verify(password_candidate, password):
                session['logged_in'] = True
                session['username'] = username
                flash('You are now logged in.', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid password'
                return render_template('login.html', error = error)
        elif result == 0 :
            try:
                if (ldap3.Connection(app.config['LDAP_SERVER'], username + '@xentaurs.com', password_candidate)):
                    session['logged_in'] = True
                    session['username'] = username
                    session['role'] = 'employee'
                    flash('You are now logged in.', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    error = 'Invalid login'
                    return render_template('login.html', error = error)
                except:
                    error = 'Username not found'
                    return render_template('login.html', error = error)
        else:
            error = 'Username not found'
            return render_template('login.html', error = error)
        cur.close()
    return render_template('login.html', form = form)

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized. Please login.', 'danger')
            return redirect(url_for('login'))
    return wrap

@app.route('/dashboard', methods = ['GET', 'POST'])
@is_logged_in
def dashboard():
    session['id'] = ''
    session['customer'] = ''
    session['components'] = ''
    session['body'] = ''
    session['create_date'] = ''

    cur = mysql.connection.cursor()
    sql = ""
    if session['role'] != "client":
        sql = "SELECT * FROM articles"
    else:
        r = cur.execute("SELECT company FROM users WHERE username='" + session['username'] + "'")
        c = cur.fetchone()
        sql = "SELECT * FROM articles WHERE customer='" + c['company'] + "'"
    result = cur.execute(sql)
    articles = cur.fetchall()
    result = cur.execute("SELECT id, customer, username FROM articles")
    vns = cur.fetchall()
    vnJSON = json.JSONEncoder().encode(vns)

    if request.method == 'POST':
        req = json.JSONDecoder().decode(request.data.decode('utf-8'))
        cursor = mysql.connection.cursor()
        if (req['delete']):
            res = cursor.execute("SELECT project_id FROM articles WHERE id="+ str(req['id']))
            pr = cursor.fetchone()
            cursor.execute("DELETE FROM projects WHERE id="+str(pr['project_id']))
            cursor.execute("DELETE FROM articles WHERE id="+str(req['id']))
        elif (req['edit']):
            result = cursor.execute("SELECT * FROM articles WHERE id="+str(req['id']))
            vn = cursor.fetchone()
            cursor.execute("UPDATE projects SET is_active=TRUE, editor='" + session['username'] + "' WHERE id="+str(vn['project_id']))
        mysql.connection.commit()
        cursor.close()


    if result > 0:
        return render_template('dashboard.html', articles = articles, vnJSON = vnJSON)
        cur.close()
    else:
        msg = 'No articles found.'
        return render_template('dashboard.html', msg = msg)
        cur.close()

@app.route('/newarticle')
@is_logged_in
def newarticle():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM articles WHERE create_date = (SELECT MAX(create_date) FROM articles  WHERE username = '" + session['username'] + "')")
    article = cur.fetchone()
    cur.close()
    chosenSolutions = json.JSONDecoder().decode(article['chosen_solutions'])
    productComp = json.JSONDecoder().decode(article['product_comp'])
    customer = article['customer']
    #create_date = str(article['create_date'])

    return render_template('article.html', article = article, customer = customer, chosenSolutions = chosenSolutions, productComp = productComp, tz = get_localzone())

@app.route('/article/<string:id>/')
@is_logged_in
def article(id):
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])
    article = cur.fetchone()
    cur.close()
    chosenSolutions = json.JSONDecoder().decode(article['chosen_solutions'])
    productComp = json.JSONDecoder().decode(article['product_comp'])
    customer = article['customer']
    return render_template('article.html', article = article, customer = customer, chosenSolutions = chosenSolutions, productComp = productComp, tz = get_localzone())

@app.route("/export", methods=['POST'])
@is_logged_in
def export_to_pdf():
    id = request.form['id']
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM articles WHERE id = %s", [id])
    article = cur.fetchone()
    cur.close()
    chosenSolutions = json.JSONDecoder().decode(article['chosen_solutions'])
    productComp = json.JSONDecoder().decode(article['product_comp'])
    productCompTable = '<table class="productComp">'
    # update top level header
    article_date = article['create_date'].strftime('%Y-%m-%d')
    customer = article['customer']
    article_title = 'VerbNoun-' + customer + '-' + article_date
    article_body = eval(article['body'])
    i = 0
    while len(article_body[0]) > i:
        k = 2
        if isinstance(article_body[0][i], int):
            # Find int value which mean how many columns do i have
            k = article_body[0][i]
            # remove column with number columns
            del article_body[0][i]
            # append all required columns from string value
            for j in range(1, k):
                article_body[0].insert(i-1+j, article_body[0][i - 1])
        i += k-1
    pd.set_option('max_colwidth', 400)
    df = pd.DataFrame(article_body)
    # Remove html tags
    df[0].replace({'<b>': ''}, regex=True, inplace=True)
    df[0].replace({'</b>': ''}, regex=True, inplace=True)
    #df[0].replace({'<b>': ''})
    #df[0].replace({'</b>': ''})
    # Convert object to int where it's possible
    ### Append subtotal row
    # firstly remove total row for grouping
    total = df.tail(1)
    df = df[:-1]
    # secondly add subtotal row
    df = df.groupby(df[0].str[:2], sort=False).apply(sum_group, ).reset_index(drop=True)
    # Add total row
    df = df.append(total, ignore_index=True)
    # create a html string  of header
    header_table = df.iloc[0]
    header_list = []
    j = 0
    for i in range(0, len(header_table)):
        if i != 0 and header_table.values[i] == header_table.values[i - 1]:
            j += 1
            header_list[-1] = '<td colspan=' + str(j) + '>' + header_table.values[i] + '</td>'
        else:
            j = 1
            header_list.append('<td colspan=' + str(j) + '>' + header_table.values[i] + '</td>')
    header_html = '\n' + '\n'.join(header_list) + '\n'
    header_html = '<tbody >\n<tr class=header>' + header_html + '</tr>\n'
    #Product comparsion table
    #Header
    productCompTable = productCompTable + header_html.replace('<td colspan=3></td>', '<td rowspan=2></td>') + '<tr>'
    for product in productComp['products']:
        productCompTable = productCompTable + '<td><b>' + product + '</b></td>'
    productCompTable = productCompTable + '</tr>'
    #Business
    productCompTable = productCompTable + '<tr><td>Business Requirement Scorecard</td>'
    for i in range(len(productComp['business']['weights'])):
        if (i in productComp['business']['max']):
            productCompTable = productCompTable + '<td class="greenColumn">' + str(productComp['business']['weights'][i]) + '</td>'
        else:
            productCompTable = productCompTable + '<td>' + str(productComp['business']['weights'][i]) + '</td>'
    productCompTable = productCompTable + '</tr>'
    #Technical
    productCompTable = productCompTable + '<tr><td>Technical Requirement Scorecard</td>'
    for i in range(len(productComp['technical']['weights'])):
        if (i in productComp['technical']['max']):
            productCompTable = productCompTable + '<td class="greenColumn">' + str(productComp['technical']['weights'][i]) + '</td>'
        else:
            productCompTable = productCompTable + '<td>' + str(productComp['technical']['weights'][i]) + '</td>'
    #Governance
    productCompTable = productCompTable + '</tr>'
    productCompTable = productCompTable + '<tr><td>Governance Requirement Scorecard</td>'
    for i in range(len(productComp['governance']['weights'])):
        if (i in productComp['governance']['max']):
            productCompTable = productCompTable + '<td class="greenColumn">' + str(productComp['governance']['weights'][i]) + '</td>'
        else:
            productCompTable = productCompTable + '<td>' + str(productComp['governance']['weights'][i]) + '</td>'
    #Total
    productCompTable = productCompTable + '</tr>'
    productCompTable = productCompTable + '<tr><td>Total</td>'
    for i in range(len(productComp['total']['weights'])):
        if (i in productComp['total']['max']):
            productCompTable = productCompTable + '<td class="greenColumn">' + str(productComp['total']['weights'][i]) + '</td>'
        else:
            productCompTable = productCompTable + '<td>' + str(productComp['total']['weights'][i]) + '</td>'
    productCompTable = productCompTable + '</tbody></table>'
    # Replace int values in priorities and weights to readable values
    priorities = ['', 'Nice to have', 'Whish list', 'Based on Policy', 'Best Practice', 'Must have']
    weights = ['N/A', 'No', 'Partial', 'Yes']
    update_series = df[2].ix[df[1] != 'Subtotal:']
    for i in range(len(priorities)):
        update_series = update_series.replace(i, priorities[i])
    df[2].ix[df[1] != 'Subtotal:'] = update_series
    # Need add to fix situation when total value will be weights or priorities
    for j in range(3, len(df.iloc[0])):
        update_series = df[j].ix[df[1] != 'Subtotal:']
        for k in range(len(weights)):
            update_series = update_series.replace(k, weights[k])
        df[j].ix[df[1] != 'Subtotal:'] = update_series
    # Create an index of rows where subtotal located
    list_sub = []
    for index, row in df.iterrows():
        if row[1] == 'Subtotal:':
            list_sub.append(index)
    # Initialize table with second header
    data_html = df.iloc[1:2].to_html(header=False, index=False, sparsify=False)
    data_html = data_html.replace('<tr>', '<tr class=header>')
    # Fill html string with data
    i = 1
    replace_part = '</tbody>\n</table>'
    for sub_ in list_sub:
        # i is value from which create html, initial value is equal 1 because header was created before
        part_data_html = (df.iloc[i+1:sub_].to_html(header=False, index=False, sparsify=False)).replace(
            '<table border="1" class="dataframe">\n  <tbody>\n', '')
        data_html = data_html.replace(replace_part, part_data_html)
        # Append subtotal row
        data_html = data_html.replace(replace_part, append_total_html(df.iloc[sub_]))
        i = sub_
    # Append last row to html string
    data_html = data_html.replace(replace_part, append_total_html(df.iloc[-1]))
    # Add first header to html string
    full_html = data_html.replace('<tbody>\n', header_html)
    full_html = full_html.replace('<td>N/A</td>', '<td class="greyColumn">N/A</td>')
    full_html = full_html.replace('<td>Yes</td>', '<td class="greenColumn">Yes</td>')
    full_html = full_html.replace('<td>No</td>', '<td class="redColumn">No</td>')
    full_html = full_html.replace('<td>Partial</td>', '<td class="yellowColumn">Partial</td>')
    # Create a html file for converting
    env = Environment(
        loader=FileSystemLoader('templates'),
        autoescape=select_autoescape(['html', 'htm', 'xml'])
    )
    template = env.get_template("article_export.html")
    font_size = 11
    template_vars = {"article": article, "article_title": article_title, "data_export": full_html, "customer": customer, "chosenSolutions": chosenSolutions, "productCompTable": productCompTable, "date": article_date, "font_size": getFontSize(len(header_table))}
    rendered = template.render(template_vars)
    pdf_output = HTML(string=rendered).write_pdf(stylesheets=['static/css/export_pdf.css'])
    response = make_response(pdf_output)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename={}.pdf'.format(article_title.replace(' ', '_'))
    response.mimetype = 'application/pdf'
    #logger = logging.getLogger('weasyprint')
    #logger.addFilter(LoggerFilter())
    return response

def getFontSize(cols):
    if cols <= 6:
        return 11
    if cols <= 8 and cols > 6:
        return 10
    if cols <= 10 and cols > 8:
        return 9
    elif cols <= 12 and cols > 10:
        return 8
    elif cols <= 14 and cols > 12:
        return 7
    elif cols <= 16 and cols > 14:
        return 6
    elif cols <= 18 and cols > 16:
        return 5
    elif cols <= 21 and cols > 18:
        return 4
    elif cols <= 24 and cols > 21:
        return 5
    elif cols <= 27 and cols > 24:
        return 2
    else:
        return 1

@app.route("/openPDF/<int:id>", methods=['POST', 'GET'])
@is_logged_in
def openPDF(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM articles WHERE id = %s", [id])
    article = cur.fetchone()
    cur.close()
    chosenSolutions = json.JSONDecoder().decode(article['chosen_solutions'])
    productComp = json.JSONDecoder().decode(article['product_comp'])
    productCompTable = '<table class="productComp">'
    # update top level header
    article_date = article['create_date'].strftime('%Y-%m-%d')
    customer = article['customer']
    article_title = 'VerbNoun-' + customer + '-' + article_date
    article_body = eval(article['body'])
    i = 0
    while len(article_body[0]) > i:
        k = 2
        if isinstance(article_body[0][i], int):
            # Find int value which mean how many columns do i have
            k = article_body[0][i]
            # remove column with number columns
            del article_body[0][i]
            # append all required columns from string value
            for j in range(1, k):
                article_body[0].insert(i-1+j, article_body[0][i - 1])
        i += k-1
    pd.set_option('max_colwidth', 400)
    df = pd.DataFrame(article_body)
    # Remove html tags
    df[0].replace({'<b>': ''}, regex=True, inplace=True)
    df[0].replace({'</b>': ''}, regex=True, inplace=True)
    # Convert object to int where it's possible
    ### Append subtotal row
    # firstly remove total row for grouping
    total = df.tail(1)
    df = df[:-1]
    # secondly add subtotal row
    df = df.groupby(df[0].str[:2], sort=False).apply(sum_group, ).reset_index(drop=True)
    # Add total row
    df = df.append(total, ignore_index=True)
    # create a html string  of header
    header_table = df.iloc[0]
    header_list = []
    j = 0
    for i in range(0, len(header_table)):
        if i != 0 and header_table.values[i] == header_table.values[i - 1]:
            j += 1
            header_list[-1] = '<td colspan=' + str(j) + '>' + header_table.values[i] + '</td>'
        else:
            j = 1
            header_list.append('<td colspan=' + str(j) + '>' + header_table.values[i] + '</td>')
    header_html = '\n' + '\n'.join(header_list) + '\n'
    header_html = '<tbody >\n<tr class=header>' + header_html + '</tr>\n'
    #Product comparsion table
    #Header
    productCompTable = productCompTable + header_html.replace('<td colspan=3></td>', '<td rowspan=2></td>') + '<tr>'
    for product in productComp['products']:
        productCompTable = productCompTable + '<td><b>' + product + '</b></td>'
    productCompTable = productCompTable + '</tr>'
    #Business
    productCompTable = productCompTable + '<tr><td>Business Requirement Scorecard</td>'
    for i in range(len(productComp['business']['weights'])):
        if (i in productComp['business']['max']):
            productCompTable = productCompTable + '<td class="greenColumn">' + str(productComp['business']['weights'][i]) + '</td>'
        else:
            productCompTable = productCompTable + '<td>' + str(productComp['business']['weights'][i]) + '</td>'
    productCompTable = productCompTable + '</tr>'
    #Technical
    productCompTable = productCompTable + '<tr><td>Technical Requirement Scorecard</td>'
    for i in range(len(productComp['technical']['weights'])):
        if (i in productComp['technical']['max']):
            productCompTable = productCompTable + '<td class="greenColumn">' + str(productComp['technical']['weights'][i]) + '</td>'
        else:
            productCompTable = productCompTable + '<td>' + str(productComp['technical']['weights'][i]) + '</td>'
    #Governance
    productCompTable = productCompTable + '</tr>'
    productCompTable = productCompTable + '<tr><td>Governance Requirement Scorecard</td>'
    for i in range(len(productComp['governance']['weights'])):
        if (i in productComp['governance']['max']):
            productCompTable = productCompTable + '<td class="greenColumn">' + str(productComp['governance']['weights'][i]) + '</td>'
        else:
            productCompTable = productCompTable + '<td>' + str(productComp['governance']['weights'][i]) + '</td>'
    #Total
    productCompTable = productCompTable + '</tr>'
    productCompTable = productCompTable + '<tr><td>Total</td>'
    for i in range(len(productComp['total']['weights'])):
        if (i in productComp['total']['max']):
            productCompTable = productCompTable + '<td class="greenColumn">' + str(productComp['total']['weights'][i]) + '</td>'
        else:
            productCompTable = productCompTable + '<td>' + str(productComp['total']['weights'][i]) + '</td>'
    productCompTable = productCompTable + '</tbody></table>'
    # Replace int values in priorities and weights to readable values
    priorities = ['', 'Nice to have', 'Whish list', 'Based on Policy', 'Best Practice', 'Must have']
    weights = ['N/A', 'No', 'Partial', 'Yes']
    update_series = df[2].ix[df[1] != 'Subtotal:']
    for i in range(len(priorities)):
        update_series = update_series.replace(i, priorities[i])
    df[2].ix[df[1] != 'Subtotal:'] = update_series
    # Need add to fix situation when total value will be weights or priorities
    for j in range(3, len(df.iloc[0])):
        update_series = df[j].ix[df[1] != 'Subtotal:']
        for k in range(len(weights)):
            update_series = update_series.replace(k, weights[k])
        df[j].ix[df[1] != 'Subtotal:'] = update_series
    # Create an index of rows where subtotal located
    list_sub = []
    for index, row in df.iterrows():
        if row[1] == 'Subtotal:':
            list_sub.append(index)
    # Initialize table with second header
    data_html = df.iloc[1:2].to_html(header=False, index=False, sparsify=False)
    data_html = data_html.replace('<tr>', '<tr class=header>')
    # Fill html string with data
    i = 1
    replace_part = '</tbody>\n</table>'
    for sub_ in list_sub:
        # i is value from which create html, initial value is equal 1 because header was created before
        part_data_html = (df.iloc[i+1:sub_].to_html(header=False, index=False, sparsify=False)).replace(
            '<table border="1" class="dataframe">\n  <tbody>\n', '')
        data_html = data_html.replace(replace_part, part_data_html)
        # Append subtotal row
        data_html = data_html.replace(replace_part, append_total_html(df.iloc[sub_]))
        i = sub_
    # Append last row to html string
    data_html = data_html.replace(replace_part, append_total_html(df.iloc[-1]))
    # Add first header to html string
    full_html = data_html.replace('<tbody>\n', header_html)
    full_html = full_html.replace('<td>N/A</td>', '<td class="greyColumn">N/A</td>')
    full_html = full_html.replace('<td>Yes</td>', '<td class="greenColumn">Yes</td>')
    full_html = full_html.replace('<td>No</td>', '<td class="redColumn">No</td>')
    full_html = full_html.replace('<td>Partial</td>', '<td class="yellowColumn">Partial</td>')
    # Create a html file for converting
    env = Environment(
        loader=FileSystemLoader('templates'),
        autoescape=select_autoescape(['html', 'htm', 'xml'])
    )
    template = env.get_template("article_export.html")
    font_size = 11
    template_vars = {"article": article, "article_title": article_title, "data_export": full_html, "customer": customer, "chosenSolutions": chosenSolutions, "productCompTable": productCompTable, "date": article_date, "font_size": getFontSize(len(header_table))}
    rendered = template.render(template_vars)
    pdf_output = HTML(string=rendered).write_pdf(stylesheets=['static/css/export_pdf.css'])
    response = make_response(pdf_output, 200)
    response.headers['Content-Type'] = 'application/pdf'
    #response.headers['Content-Disposition'] = 'attachment; filename={}.pdf'.format(article_title)
    response.mimetype = 'application/pdf'
    #logger = logging.getLogger('weasyprint')
    #logger.addFilter(LoggerFilter())
    print(productCompTable)
    return response


class ArticleAddWizard1Form(Form):
    customer = SelectField(u'Customer', choices=[])

@app.route('/article_add_wizard_1', methods = ['GET', 'POST'])
@is_logged_in
def article_add_wizard_1():
    #form = ArticleAddWizard1Form(request.form)
    cur = mysql.connection.cursor()
    project_customername = ""
    project_flag = False
    customers = []
    result = cur.execute("SELECT * FROM customers")
    if result > 0:
        custs = cur.fetchall()
        #customer_choices = []
        for customer in custs:
            customers.append(customer)
            #customer_choices.append((str(customer['id']), customer['name']))
        #form.customer.choices = customer_choices
    else:
        msg = 'No customers found.'
        return render_template('dashboard.html', msg = msg)
    #cur.close()

    #check project
    project_data = cur.execute("SELECT * FROM projects WHERE editor = \"" + session['username'] + "\" AND is_active IS TRUE")
    if project_data > 0:
        data = cur.fetchall()
        project_customername = data[project_data-1]['customer_name']
        project_flag = True
    else:
        project_flag = False 
    cur.close()

    #process POST
    if request.method == 'POST':
        customer = json.JSONDecoder().decode(request.data.decode('utf-8'))
        session['customer'] = customer['name']
        cursor = mysql.connection.cursor()
        c_res = cursor.execute("SELECT * FROM customers WHERE name='" + customer['name'] + "'")
        if c_res == 0:
            cursor.execute("INSERT INTO customers(name) VALUES ('" + customer['name'] + "')")
        if (project_flag):
            cursor.execute("UPDATE projects SET customer_name = \"" + customer['name'] + "\" WHERE editor = \"" + session['username'] + "\" AND is_active IS TRUE")
        else:
            cursor.execute("INSERT INTO projects(username, editor, customer_name, is_active) VALUES (\"" + session['username'] + "\", \"" +session['username']+"\", \"" + customer['name'] + "\", TRUE)")
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('article_add_wizard_2'))

    return render_template('article_add_wizard_1.html', project_customername = project_customername, customers = customers)

class ArticleAddWizard2Form(Form):
    groups = SelectMultipleField('Groups', choices=[])
    categories = SelectMultipleField('Components', choices=[])
    components = SelectMultipleField('Products', choices=[])
    components_selected = SelectMultipleField('Selected products', choices=[])

@app.route('/article_add_wizard_2', methods = ['GET', 'POST'])
@is_logged_in
def article_add_wizard_2():
    form = ArticleAddWizard2Form(request.form)
    cur = mysql.connection.cursor()
    project_components = ""
    project_flag = False
    result = cur.execute("SELECT * FROM components")
    if result > 0:
        components = cur.fetchall()
    else:
        msg = 'No components found in the given category.'
        return render_template('dashboard.html', msg = msg)
    #cur.close()

    #check project
    project_data = cur.execute("SELECT * FROM projects WHERE editor = \"" + session['username'] + "\" AND is_active IS TRUE")
    if project_data > 0:
        data = cur.fetchall()
        project_components = data[project_data-1]['components']
        project_flag = True
    else: 
        project_flag = False
    cur.close()

    #process post
    if request.method == 'POST':
        cursor = mysql.connection.cursor()
        if (project_flag):
            cursor.execute("UPDATE projects SET components ='%s' WHERE editor='%s' " % (request.data.decode('utf-8'), (session['username'])))
        else:
            sql = "INSERT INTO projects(username, editor, components, is_active) VALUES (%s, %s, %s, TRUE)"
            cursor.execute(sql, (session['username'], session['username'], request.data.decode('utf-8')))
        mysql.connection.commit()
        cursor.close()
        #session['components'] = request.data.decode('utf-8')

    return render_template('article_add_wizard_2.html', form = form, components_list = json.JSONEncoder().encode(components), project_components = project_components)

@app.route('/save_requirements/<string:body>')
@is_logged_in
def save_requirements(body):
    return redirect(url_for('add_requirement_w3'))

class ArticleAddRequirementForm(Form):
    requirements = SelectMultipleField(u'Requirements (multiple select)', choices=[])

@app.route('/article_add_wizard_3', methods = ['GET', 'POST'])
@is_logged_in
def add_requirement_w3():
    form = ArticleAddRequirementForm(request.form)
    vars = request.data
    project_breqs = ""
    project_flag = False
    reqs = []
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM requirements WHERE rgroup='business'")
    if result > 0:
        requirements = cur.fetchall()
        requirement_choices = []
        for requirement in requirements:
            requirement_choices.append((str(requirement['id']), requirement['description']))
            reqs.append(str(requirement['description']))
        form.requirements.choices = requirement_choices
    else:
        msg = 'No requirements found.'
        return render_template('dashboard.html', msg = msg)
    #cur.close()
    reqJSON = json.JSONEncoder().encode(reqs)

    #check project
    project_data = cur.execute("SELECT * FROM projects WHERE editor = \"" + session['username'] + "\" AND is_active IS TRUE")
    if project_data > 0:
        data = cur.fetchall()
        project_breqs = data[project_data-1]['business_requirements']
        project_flag = True
    else: 
        project_flag = False
    cur.close()

    if request.method == 'POST':
        cursor = mysql.connection.cursor()
        if (project_flag):
            cursor.execute("UPDATE projects SET business_requirements ='%s' WHERE editor='%s' " % (request.data.decode('utf-8'), (session['username'])))
        else:
            sql = "INSERT INTO projects(username, editor, business_requirements, is_active) VALUES (%s, %s, %s, true)"
            cursor.execute(sql, (session['username'], session['username'], request.data.decode('utf-8')))
        mysql.connection.commit()
        cursor.close()

    return render_template('article_add_wizard_3.html', form = form, reqJSON = reqJSON, project_breqs = project_breqs)

@app.route('/article_add_wizard_4', methods = ['GET', 'POST'])
@is_logged_in
def article_add_wizard_4():
    form = ArticleAddRequirementForm(request.form)
    reqs = []
    project_treqs = ""
    project_flag = False
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM requirements WHERE rgroup='technical'")
    if result > 0:
        requirements = cur.fetchall()
        requirement_choices = []
        for requirement in requirements:
            requirement_choices.append((str(requirement['id']), requirement['description']))
            reqs.append(str(requirement['description']))
        form.requirements.choices = requirement_choices
    else:
        msg = 'No requirements found.'
        return render_template('dashboard.html', msg = msg)
    #cur.close()
    reqJSON = json.JSONEncoder().encode(reqs)

    #check project
    project_data = cur.execute("SELECT * FROM projects WHERE editor = \"" + session['username'] + "\" AND is_active IS TRUE")
    if project_data > 0:
        data = cur.fetchall()
        project_treqs = data[project_data-1]['technical_requirements']
        project_flag = True
    else: 
        project_flag = False
    cur.close()

    if request.method == 'POST':
        cursor = mysql.connection.cursor()
        if (project_flag):
            cursor.execute("UPDATE projects SET technical_requirements ='%s' WHERE editor='%s' " % (request.data.decode('utf-8'), (session['username'])))
        else:
            sql = "INSERT INTO projects(username, editor, technical_requirements, is_active) VALUES (%s, %s, TRUE)"
            cursor.execute(sql, (session['username'], session['username'], request.data.decode('utf-8')))
        mysql.connection.commit()
        cursor.close()
        #session['trequirements'] = request.data.decode('utf-8')

    return render_template('article_add_wizard_4.html', form = form, reqJSON = reqJSON, project_treqs = project_treqs)

@app.route('/article_add_wizard_5', methods = ['GET', 'POST'])
@is_logged_in
def article_add_wizard_5():
    form = ArticleAddRequirementForm(request.form)
    cur = mysql.connection.cursor()
    reqs = []
    project_greqs = ""
    project_flag = False
    result = cur.execute("SELECT * FROM requirements WHERE rgroup='governance'")
    if result > 0:
        requirements = cur.fetchall()
        requirement_choices = []
        for requirement in requirements:
            requirement_choices.append((str(requirement['id']), requirement['description']))
            reqs.append(str(requirement['description']))
        form.requirements.choices = requirement_choices
    else:
        msg = 'No requirements found.'
        return render_template('dashboard.html', msg = msg)
    #cur.close()
    reqJSON = json.JSONEncoder().encode(reqs)

    #check project
    project_data = cur.execute("SELECT * FROM projects WHERE editor = \"" + session['username'] + "\" AND is_active IS TRUE")
    if project_data > 0:
        data = cur.fetchall()
        project_greqs = data[project_data-1]['governance_requirements']
        project_flag = True
    else: 
        project_flag = False
    cur.close()

    if request.method == 'POST':
        cursor = mysql.connection.cursor()
        if (project_flag):
            cursor.execute("UPDATE projects SET governance_requirements ='%s' WHERE editor='%s' " % (request.data.decode('utf-8'), (session['username'])))
        else:
            sql = "INSERT INTO projects(username, editor, governance_requirements, is_active) VALUES (%s, %s, TRUE)"
            cursor.execute(sql, (session['username'], session['username'], request.data.decode('utf-8')))
        mysql.connection.commit()
        cursor.close()
        #session['grequirements'] = request.data.decode('utf-8')

    return render_template('article_add_wizard_5.html', form = form, reqJSON = reqJSON, project_greqs = project_greqs)

@app.route('/article_add_wizard_6', methods = ['GET', 'POST'])
@is_logged_in
def article_add_wizard_6():
    username = session['username']
    customer = session['customer']
    project_id = 0
    project_vn = ""
    #componentsJSON = session['components']
    #requirementsJSON = "[" + session['brequirements'] + ", " + session['trequirements'] + ", " + session['grequirements'] + "]"
    componentsJSON = "[]"
    requirementsJSON = "[]"
    br = """["Business requirements"]"""
    tr = """["Technical requirements"]"""
    gr = """["Governance requirements"]"""
    cursor = mysql.connection.cursor()
    result = cursor.execute("SELECT * FROM projects WHERE editor='" + session['username'] + "'  AND is_active IS TRUE")
    if result > 0:
        vndata = cursor.fetchall()
        if (vndata[result-1]['components'] != None):
            componentsJSON = vndata[result-1]['components']
        if (vndata[result-1]['business_requirements'] != None):
            br = vndata[result-1]['business_requirements']
        if (vndata[result-1]['technical_requirements'] != None):
            tr = vndata[result-1]['technical_requirements']
        if (vndata[result-1]['governance_requirements'] != None):
            gr = vndata[result-1]['governance_requirements']
        project_id = vndata[result-1]['id']
        customer = vndata[result-1]['customer_name']
        project_vn = vndata[result-1]['vn']
    else:
        sql = "INSERT INTO projects(editor, governance_requirements, is_active) VALUES (%s, %s, TRUE)"
        cursor.execute(sql, (session['username'], request.data.decode('utf-8')))
        result = cursor.execute("SELECT id FROM projects WHERE editor='" + session['username'] + "'  AND is_active IS TRUE")
        p_id = cursor.fetchone()
        project_id = p_id['id']
    article_id = "0"
    res = cursor.execute("SELECT * FROM articles WHERE project_id="+ str(project_id))
    if res > 0:
        a_id = cursor.fetchone()
        article_id = a_id['id']
    cursor.close()
    requirementsJSON = "[" + br + ", " + tr + ", " + gr + "]"


    if request.method == 'POST':
        body = request.data.decode('utf-8')
        cells = json.JSONEncoder().encode(json.JSONDecoder().decode(body)['cells'])
        project = json.JSONEncoder().encode(json.JSONDecoder().decode(body)['project'])
        chosenSolutions = json.JSONEncoder().encode(json.JSONDecoder().decode(body)['chosenSolutions'])
        productComp = json.JSONEncoder().encode(json.JSONDecoder().decode(body)['productComp'])
        print(productComp)
        #project = json.loads(project['project'])
        cur = mysql.connection.cursor()
        res = cur.execute("SELECT * FROM articles WHERE project_id =" + str(project_id))
        a = cur.fetchone()
        if res > 0:
            cur.execute("UPDATE articles SET body=%s, customer=%s, chosen_solutions=%s, product_comp=%s, create_date=SYSDATE() WHERE project_id=%s", (cells, customer, chosenSolutions, productComp, str(project_id)))
        else:
            cur.execute("INSERT INTO articles (customer, username, body, chosen_solutions, product_comp, project_id) VALUES (%s, %s, %s, %s, %s, "+str(project_id)+")", (customer, username, cells, chosenSolutions, productComp))
        cur.execute("UPDATE projects SET is_active=FALSE, vn = '" + project + "', editor='' WHERE id=" + str(project_id))
        mysql.connection.commit()
        cur.close()

    return render_template('article_add_wizard_6.html', customer = customer, componentsJSON = componentsJSON, requirementsJSON = requirementsJSON, article_id = article_id, project_vn = project_vn)

@app.route('/delete_requirement_w3/<string:requirement_to_delete>')
@is_logged_in
def delete_requirement_w3(requirement_to_delete):
    requirements = json.JSONDecoder().decode(session['requirements'])
    session_requirements = []
    for requirement in requirements:
        if requirement != requirement_to_delete:
            session_requirements.append(requirement)
    session['requirements'] = json.JSONEncoder().encode(session_requirements)
    return redirect(url_for('add_article_w3'))


@app.route('/save_article/<string:body>')
@is_logged_in
def save_article(body):
    customer = session['customer']
    category = session['category']
    username = session['username']
    # app.logger.info('body = ' + body)
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO articles (customer, category, username, body) VALUES (%s, %s, %s, %s)", (customer, category, username, body))
    mysql.connection.commit()
    cur.close()

    flash('Article created.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/article_edit/<string:id>')
@is_logged_in
def article_edit(id):
    article = {}

    if session['id'] == '':
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])
        article = cur.fetchone()
        cur.close()
        session['id'] = article['id']
        session['customer'] = article['customer']
        #session['category'] = article['category']
        session['body'] = article['body']
        session['create_date'] = article['create_date']
    else:
        article['id'] = session['id']
        article['customer'] = session['customer']
        article['category'] = session['category']
        article['body'] = session['body']
        article['create_date'] = session['create_date']

    return render_template('article_edit.html', article = article)

@app.route('/article_edit_add_requirement', methods = ['GET', 'POST'])
@is_logged_in
def article_edit_add_requirement():
    form = ArticleAddRequirementForm(request.form)
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM requirements")
    if result > 0:
        requirements = cur.fetchall()
        requirement_choices = []
        for requirement in requirements:
            requirement_choices.append((str(requirement['id']), requirement['description']))
        form.requirements.choices = requirement_choices
    else:
        msg = 'No requirements found.'
        return render_template('dashboard.html', msg = msg)
    cur.close()

    if request.method == 'POST':
        body = json.JSONDecoder().decode(session['body'])
        requirement_ids = form.requirements.data
        for requirement_id in requirement_ids:
            for requirement in requirements:
                if requirement_id == str(requirement['id']):
                    body.insert(-1, [])
                    body[-2].append(requirement['description'])
                    body[-2].append('1')
                    for i in range(2, len(body[-1])):
                        body[-2].append('0')
        session['body'] = json.JSONEncoder().encode(body)
        return redirect(url_for('article_edit', id = session['id']))

    return render_template('article_edit_add_requirement.html', form = form)

@app.route('/article_edit_delete_requirement/<string:requirement_to_delete>')
@is_logged_in
def article_edit_delete_requirement(requirement_to_delete):
    body = json.JSONDecoder().decode(session['body'])
    new_body = []
    for row in body:
        if row[0] != requirement_to_delete:
            new_body.append(row)
    session['body'] = json.JSONEncoder().encode(new_body)
    return redirect(url_for('article_edit', id = session['id']))

@app.route('/update_article/<string:id>/<string:body>')
@is_logged_in
def update_article(id, body):
    # app.logger.info('body = ' + body)
    cur = mysql.connection.cursor()
    cur.execute("UPDATE articles SET body = %s WHERE id = %s", (body, id))
    mysql.connection.commit()
    cur.close()

    flash('Article updated.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/settings')
@is_logged_in
def settings():
    return render_template('settings.html', role = session['role'])

@app.route('/customers')
@is_logged_in
def customers():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM customers")
    customers = cur.fetchall()
    cur.close()

    if result > 0:
        return render_template('customers.html', customers = customers)
    else:
        msg = 'No customers found.'
        return render_template('customers.html', msg = msg)

class CustomerForm(Form):
    name = StringField('Name', [validators.Length(min = 2, max = 100)])
    comments = TextAreaField('Comments', [validators.Length(max = 4096)])

@app.route('/add_customer', methods = ['GET', 'POST'])
@is_logged_in
def add_customer():
    form = CustomerForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        comments = form.comments.data

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO customers(name, comments) VALUES(%s, %s)", (name, comments))
        mysql.connection.commit()
        cur.close()

        flash('Customer created.', 'success')
        return redirect(url_for('customers'))

    return render_template('add_customer.html', form = form)

#@app.route('/edit_customer/<string:id>', methods=['GET', 'POST'])
#@is_logged_in
#def edit_customer(id):
    #cur = mysql.connection.cursor()
    #result = cur.execute("SELECT * FROM customers WHERE id = %s", [id])
    #article = cur.fetchone()
    #cur.close()
    #form = CustomerForm(request.form)
    #form.name.data = article['name']
    #form.comments.data = article['comments']

    #if request.method == 'POST' and form.validate():
        #name = request.form['name']
        #comments = request.form['comments']
        #cur = mysql.connection.cursor()
        #cur.execute("SELECT name FROM customers WHERE id=" + str(id))
        #customer = cur.fetchone()
        #cur.execute("UPDATE customers SET name=%s, comments=%s WHERE id=%s",(name, comments, id))
        #cur.execute("UPDATE articles SET customer='" + str(name) + "' WHERE customer='"+ customer['name']+ "'")
        #cur.execute("UPDATE projects SET customer_name='" + str(name) +"' WHERE customer_name='"+ customer['name'] + "'")
        #mysql.connection.commit()
        #cur.close()

        #flash('Customer was updated', 'success')
        #return redirect(url_for('customers'))

    #return render_template('edit_customer.html', form=form)

@app.route('/delete_customer/<int:id>', methods=['GET', 'POST'])
@is_logged_in
def delete_customer(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT name FROM customers WHERE id = %s", [id])
    customer = cur.fetchone()
    cur.execute("DELETE FROM customers WHERE id = %s", [id])
    cur.execute("DELETE FROM users WHERE company = '" + customer['name'] + "' AND role='client'")
    cur.execute("DELETE FROM articles WHERE customer = '" + customer['name'] + "'")
    mysql.connection.commit()
    cur.close()
    return json.dumps({}), 200, {'ContentType':'application/json'}

@app.route('/categories')
@is_logged_in
def categories():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM categories")
    categories = cur.fetchall()
    result = cur.execute("SELECT * FROM components")
    components = cur.fetchall()
    categoriesJSON = json.JSONEncoder().encode(categories)
    componentsJSON = json.JSONEncoder().encode(components)
    cur.close()

    if result > 0:
        return render_template('categories.html', categories = categories, categoriesJSON = categoriesJSON, componentsJSON = componentsJSON)
    else:
        msg = 'No categories found.'
        return render_template('categories.html', msg = msg)

class CategoryForm(Form):
    name = StringField('Name', [validators.Length(min = 2, max = 100)])

@app.route('/add_category', methods = ['GET', 'POST'])
@is_logged_in
def add_category():
    cursor = mysql.connection.cursor()
    result = cursor.execute("SELECT * FROM groups")
    groups = cursor.fetchall()
    cursor.close()

    if request.method == 'POST':
        cur = mysql.connection.cursor()
        category = json.JSONDecoder().decode(request.data.decode('utf-8'))
        cur.execute("INSERT INTO categories(name, gname) VALUES (%s, %s)", (category['name'], category['group']))
        mysql.connection.commit()
        cur.close()
    return render_template('add_category.html', groups = groups)

@app.route('/edit_category/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_category(id):
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM categories WHERE id = %s", [id])
    category = cur.fetchone()
    result = cur.execute("SELECT * FROM groups")
    groups = cur.fetchall()
    result = cur.execute("SELECT * FROM components WHERE category='" + category['name'] + "'")
    components = cur.fetchall()
    componentsJSON = json.JSONEncoder().encode(components)
    cur.close()
    name_old = category['name']

    if request.method == 'POST':
        cursor = mysql.connection.cursor()
        category = json.JSONDecoder().decode(request.data.decode('utf-8'))
        if category['delete'] == True:
            cursor.execute("DELETE FROM categories WHERE id=" + id)
            cursor.execute("DELETE FROM components WHERE category='"+category['name']+"'")
        else:
            cursor.execute("UPDATE categories SET name=%s, gname=%s WHERE id= %s", (category['name'], category['group'], [id]))
            result = cursor.execute("SELECT * FROM components WHERE category='" + name_old + "'")
            comps = cursor.fetchall()
            for comp in comps:
                cursor.execute("UPDATE components SET category=%s, gname=%s WHERE id=%s", (category['name'], category['group'], comp['id']))
        mysql.connection.commit()
        cursor.close()

    return render_template('edit_category.html', category=category, groups = groups, components = components, componentsJSON = componentsJSON)

@app.route('/components')
@is_logged_in
def components():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM components")
    components = cur.fetchall()
    cur.close()

    if result > 0:
        return render_template('components.html', components = components)
    else:
        msg = 'No components found.'
        return render_template('components.html', msg = msg)

@app.route('/add_component', methods = ['GET', 'POST'])
@is_logged_in
def add_component():
    cursor = mysql.connection.cursor()
    result = cursor.execute("SELECT * FROM groups")
    groups = cursor.fetchall()
    result2 = cursor.execute("SELECT * FROM categories")
    categories = cursor.fetchall()
    categoriesJSON = json.JSONEncoder().encode(categories)
    cursor.close()

    if request.method == 'POST':
        cur = mysql.connection.cursor()
        newcomp = json.JSONDecoder().decode(request.data.decode('utf-8'))
        cur.execute("INSERT INTO components (name, category, gname, link) VALUES(%s, %s, %s, %s)", (newcomp['name'], newcomp['category'], newcomp['group'], newcomp['link']))
        mysql.connection.commit()
        cur.close()
    return render_template('add_component.html', categories=categories, groups = groups, categoriesJSON = categoriesJSON)

@app.route('/edit_component/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_component(id):
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM components WHERE id = %s", [id])
    component = cur.fetchone()
    result2 = cur.execute("SELECT * FROM groups")
    groups = cur.fetchall()
    result3 = cur.execute("SELECT * FROM categories")
    categories = cur.fetchall()
    categoriesJSON = json.JSONEncoder().encode(categories)
    cur.close()

    if request.method == 'POST':
        cursor = mysql.connection.cursor()
        comp = json.JSONDecoder().decode(request.data.decode('utf-8'))
        if comp['delete'] == True:
            cursor.execute("DELETE FROM components WHERE id=" + id)
        elif comp['edit'] == True:
            cursor.execute("UPDATE components SET name=%s, category=%s, gname=%s, link=%s WHERE id=%s", (comp['name'], comp['category'], comp['group'], comp['link'], comp['id']))
        mysql.connection.commit()
        cursor.close()
    return render_template('edit_component.html', groups = groups, categoriesJSON = categoriesJSON, component = component)

@app.route('/groups', methods = ['GET', 'POST'])
@is_logged_in
def groups():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM groups")
    groups = cur.fetchall()
    result = cur.execute("SELECT * FROM categories")
    categories = cur.fetchall()
    cur.close()
    groupsJSON = json.JSONEncoder().encode(groups)
    categoriesJSON = json.JSONEncoder().encode(categories)

    if request.method == 'POST':
        cursor = mysql.connection.cursor()
        newgroups = json.JSONDecoder().decode(request.data.decode('utf-8'))
        for group in newgroups:
            cursor.execute("INSERT INTO groups(name) VALUES ('" + group + "')")
        mysql.connection.commit()
        cursor.close()

    if result > 0:
        return render_template('groups.html', groups = groups, groupsJSON = groupsJSON, categoriesJSON = categoriesJSON)
    else:
        msg = 'No groups found.'
        return render_template('groups.html', msg = msg)

@app.route('/edit_group/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_group(id):
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT name FROM groups WHERE id = %s", [id])
    groupName = cur.fetchone()
    result = cur.execute("SELECT * FROM categories WHERE gname = (SELECT name FROM groups WHERE id = %s)", [id])
    categories = cur.fetchall()
    cur.close()
    categoriesJSON = json.JSONEncoder().encode(categories)
    groupId = id

    if request.method == 'POST':
        cursor = mysql.connection.cursor()
        reqJSON = json.JSONDecoder().decode(request.data.decode('utf-8'))
        if (reqJSON['rename']):
            cursor.execute("UPDATE groups SET name=%s WHERE id=%s", (reqJSON['name'], reqJSON['id']))
            resCats = cursor.execute("SELECT * FROM categories WHERE gname ='" + groupName['name'] +"'")
            cats = cursor.fetchall()
            for cat in cats:
                cursor.execute("UPDATE categories SET gname=%s WHERE id=%s", (reqJSON['name'], cat['id']))
            resComps = cursor.execute("SELECT * FROM components WHERE gname ='" + groupName['name'] +"'")
            comps = cursor.fetchall()
            for comp in comps:
                cursor.execute("UPDATE components SET gname=%s WHERE id=%s", (reqJSON['name'], comp['id']))
        elif (reqJSON['delete']):
            cursor.execute("DELETE FROM groups WHERE id =%s", [id])
            cursor.execute("DELETE FROM categories WHERE gname='" + reqJSON['name'] +"'")
            cursor.execute("DELETE FROM components WHERE gname='" + reqJSON['name'] +"'")
        mysql.connection.commit()
        cursor.close()
        #cursor = mysql.connection.cursor()
        #catList = json.JSONDecoder().decode(request.data.decode('utf-8'))
        #if (len(catList['add']) > 0):
            #for addCat in catList['add']:
                #cursor.execute("INSERT INTO categories(name, gname) VALUES('" + addCat + "', '" + catList['group'] + "')")
        #if (len(catList['remove']) > 0):
            #for removeCat in catList['remove']:
                #cursor.execute("DELETE FROM categories WHERE name = '" + removeCat + "'")
                #cursor.execute("DELETE FROM components WHERE category = '" + removeCat + "' AND gname = '" + catList['group'] + "'")
        #mysql.connection.commit()
        #cursor.close()

    return render_template('edit_group.html', categoriesJSON = categoriesJSON, groupName = groupName, groupId = groupId)

@app.route('/users', methods = ['GET', 'POST'])
@is_logged_in
def users():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM users")
    users = cur.fetchall()
    cur.close()

    if (session['role'] == "admin"):
        return render_template('users.html', users = users)
    else:
        return render_template('access_denided.html')

@app.route('/edit_user/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_user(id):
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM users WHERE id = %s", [id])
    user = cur.fetchone()
    result = cur.execute("SELECT * FROM customers")
    customers = cur.fetchall()
    cur.close()

    if (session['role'] == "admin"):
        return render_template('edit_user.html', user = user, customers = customers)
    else:
        return render_template('access_denided.html')

@app.route('/add_user', methods=['GET', 'POST'])
@is_logged_in
def add_user():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM customers")
    customers = cur.fetchall()
    #customersJSON = json.JSONEncoder().encode(customers)
    cur.close()

    if request.method == 'POST':
        cursor = mysql.connection.cursor()
        user = json.JSONDecoder().decode(request.data.decode('utf-8'))
        password = sha256_crypt.encrypt(str(user['password']))
        sql = "INSERT INTO users(name, email, username, password, role, company) VALUES(%s, %s, %s, %s, %s, %s)"
        cursor.execute(sql, (user['name'], user['email'], user['username'], password, user['role'], user['company']))
        mysql.connection.commit()
        cursor.close()
        try:
            msg = Message("Xentaurs VerbNoun Account", sender = 'vadim.e@lateco.net', recipients=[user['email']])
            msg.body = "Xentaurs VerbNoun account has been created for you: http://178.63.57.162:8081\nUsername: "+user['username']+"\nPassword: "+user['password']+"\n\nThis message has been sent automatically. Please, don't try to reply this email."
            mail.send(msg)
        except Exception as e:
            print(e)
    #return json.dumps({'success':True}), 200, {'ContentType':'application/json'}
    if (session['role'] == "admin"):
        return render_template('add_user.html', customers = customers)
    else:
        return render_template('access_denided.html')

@app.route('/update_user', methods=['POST'])
@is_logged_in
def update_user():
    if request.method == 'POST':
        cursor = mysql.connection.cursor()
        req = json.JSONDecoder().decode(request.data.decode('utf-8'))
        if (req['delete'] == True):
            cursor.execute("DELETE FROM users WHERE id=" + str(req['id']))
        elif (req['changePassword'] == True):
            password = sha256_crypt.encrypt(str(req['password']))
            sql = "UPDATE users SET name=%s, email=%s, username=%s, password=%s, role=%s, company=%s WHERE id=" + str(req['id'])
            cursor.execute(sql, (req['name'], req['email'], req['username'], password, req['role'], req['company']))
            cursor.execute("SELECT * FROM users WHERE id=" + str(req['id']))
            user = cursor.fetchone()
            msg = Message("Xentaurs VerbNoun Portal: Your Password Has Been Changed", sender = 'vadim.e@lateco.net', recipients=[user['email']])
            msg.html = "The password for your account on Xentaurs VerbNoun Portal has been changed.<br/><br/>Username: "+user['username']+ "<br/><b>New password: "+req['password']+"</b><br/><br/>This message has been sent automatically. Please, don't try to reply this email.<br/><br/>Best regards,<br/>Xentaurs VerbNoun Portal"
            mail.send(msg)
        elif (req['changePassword'] == False and req['delete'] == False):
            sql = "UPDATE users SET name=%s, email=%s, username=%s, role=%s, company=%s WHERE id=" + str(req['id'])
            cursor.execute(sql, (req['name'], req['email'], req['username'], req['role'], req['company']))
        mysql.connection.commit()
        cursor.close()
    return json.dumps({'success':True}), 200, {'ContentType':'application/json'}

@app.route('/check_project/<int:id>', methods=['GET'])
@is_logged_in
def check_project(id):
    cursor = mysql.connection.cursor()
    result = cursor.execute("SELECT is_active, editor FROM projects WHERE id = (SELECT project_id FROM articles WHERE id = " + str(id) + ")")
    project = cursor.fetchone()
    if result > 0:
        if (project['is_active'] and project['editor'] != session['username']):
            return json.dumps({ "message": "The VerbNoun is edited by the user " + project['editor']+ " right now"}), 500, {'ContentType':'application/json'}
        else:
            res = cursor.execute("SELECT * FROM articles WHERE id="+str(id))
            vn = cursor.fetchone()
            cursor.execute("UPDATE projects SET is_active=FALSE, editor='' WHERE editor='" + session['username'] + "'")
            cursor.execute("UPDATE projects SET is_active=TRUE, editor='" + session['username'] + "' WHERE id="+str(vn['project_id']))
            mysql.connection.commit()
            return json.dumps({}), 200, {'ContentType':'application/json'}
    else:
        return json.dumps({ "message": "VerbNoun is not found"}), 500, {'ContentType':'application/json'}
    cursor.close()

@app.route('/close_my_projects', methods=['GET'])
@is_logged_in
def close_my_projects():
    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE projects SET is_active=FALSE, editor='' WHERE editor='" + session['username'] + "'")
    mysql.connection.commit()
    cursor.close()
    return json.dumps({}), 200, {'ContentType':'application/json'}

@app.route('/add_group', methods=['POST'])
@is_logged_in
def add_group():
    cursor = mysql.connection.cursor()
    newgroup = json.JSONDecoder().decode(request.data.decode('utf-8'))
    cursor.execute("INSERT INTO groups(name) VALUES ('" + newgroup['name'] + "')")
    mysql.connection.commit()
    result = cursor.execute("SELECT * FROM groups")
    groups = cursor.fetchall()
    cursor.close()
    return json.dumps(groups), 200, {'ContentType':'application/json'}

@app.route('/delete_group/<int:id>', methods=['GET'])
@is_logged_in
def delete_group(id):
    cursor = mysql.connection.cursor()
    result = cursor.execute("SELECT * FROM groups WHERE id=" + str(id))
    group = cursor.fetchone()
    cursor.execute("DELETE FROM groups WHERE id=" + str(id))
    cursor.execute("DELETE FROM categories WHERE gname='" + group['name'] +"'")
    cursor.execute("DELETE FROM components WHERE gname='" + group['name'] +"'")
    mysql.connection.commit()
    result = cursor.execute("SELECT * FROM groups")
    groups = cursor.fetchall()
    cursor.close()
    return json.dumps(groups), 200, {'ContentType':'application/json'}

@app.route('/delete_category/<int:id>', methods=['GET'])
@is_logged_in
def delete_category(id):
    cursor = mysql.connection.cursor()
    result = cursor.execute("SELECT * FROM categories WHERE id=" + str(id))
    category = cursor.fetchone()
    cursor.execute("DELETE FROM categories WHERE name='" + category['name'] +"'")
    cursor.execute("DELETE FROM components WHERE category='" + category['name'] +"'")
    mysql.connection.commit()
    cursor.close()
    return json.dumps({}), 200, {'ContentType':'application/json'}

@app.route('/delete_component/<int:id>', methods=['GET'])
@is_logged_in
def delete_component(id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM components WHERE id=" + str(id))
    mysql.connection.commit()
    cursor.close()
    return json.dumps({}), 200, {'ContentType':'application/json'}

@app.route('/delete_user/<int:id>', methods=['GET'])
@is_logged_in
def delete_user(id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM users WHERE id=" + str(id))
    mysql.connection.commit()
    cursor.close()
    return json.dumps({}), 200, {'ContentType':'application/json'}

@app.route('/sendVN', methods=['POST'])
@is_logged_in
def sendVN():
    cursor = mysql.connection.cursor()
    vn = json.JSONDecoder().decode(request.data.decode('utf-8'))
    result = cursor.execute("SELECT * FROM users WHERE company='" + vn['customer'] + "'")
    clients = cursor.fetchall()

    id = vn['id']
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM articles WHERE id = %s", [id])
    article = cur.fetchone()
    cur.close()
    chosenSolutions = json.JSONDecoder().decode(article['chosen_solutions'])
    productComp = json.JSONDecoder().decode(article['product_comp'])
    productCompTable = '<table class="productComp">'
    # update top level header
    article_date = article['create_date'].strftime('%Y-%m-%d')
    customer = article['customer']
    article_title = 'VerbNoun-' + customer + '-' + article_date
    article_body = eval(article['body'])
    i = 0
    while len(article_body[0]) > i:
        k = 2
        if isinstance(article_body[0][i], int):
            # Find int value which mean how many columns do i have
            k = article_body[0][i]
            # remove column with number columns
            del article_body[0][i]
            # append all required columns from string value
            for j in range(1, k):
                article_body[0].insert(i-1+j, article_body[0][i - 1])
        i += k-1
    pd.set_option('max_colwidth', 400)
    df = pd.DataFrame(article_body)
    # Remove html tags
    df[0].replace({'<b>': ''}, regex=True, inplace=True)
    df[0].replace({'</b>': ''}, regex=True, inplace=True)
    # Convert object to int where it's possible
    ### Append subtotal row
    # firstly remove total row for grouping
    total = df.tail(1)
    df = df[:-1]
    # secondly add subtotal row
    df = df.groupby(df[0].str[:2], sort=False).apply(sum_group, ).reset_index(drop=True)
    # Add total row
    df = df.append(total, ignore_index=True)
    # create a html string  of header
    header_table = df.iloc[0]
    header_list = []
    j = 0
    for i in range(0, len(header_table)):
        if i != 0 and header_table.values[i] == header_table.values[i - 1]:
            j += 1
            header_list[-1] = '<td colspan=' + str(j) + '>' + header_table.values[i] + '</td>'
        else:
            j = 1
            header_list.append('<td colspan=' + str(j) + '>' + header_table.values[i] + '</td>')
    header_html = '\n' + '\n'.join(header_list) + '\n'
    header_html = '<tbody >\n<tr class=header>' + header_html + '</tr>\n'
    #Product comparsion table
    #Header
    productCompTable = productCompTable + header_html.replace('<td colspan=3></td>', '<td rowspan=2></td>') + '<tr>'
    for product in productComp['products']:
        productCompTable = productCompTable + '<td><b>' + product + '</b></td>'
    productCompTable = productCompTable + '</tr>'
    #Business
    productCompTable = productCompTable + '<tr><td>Business Requirement Scorecard</td>'
    for i in range(len(productComp['business']['weights'])):
        if (i in productComp['business']['max']):
            productCompTable = productCompTable + '<td class="greenColumn">' + str(productComp['business']['weights'][i]) + '</td>'
        else:
            productCompTable = productCompTable + '<td>' + str(productComp['business']['weights'][i]) + '</td>'
    productCompTable = productCompTable + '</tr>'
    #Technical
    productCompTable = productCompTable + '<tr><td>Technical Requirement Scorecard</td>'
    for i in range(len(productComp['technical']['weights'])):
        if (i in productComp['technical']['max']):
            productCompTable = productCompTable + '<td class="greenColumn">' + str(productComp['technical']['weights'][i]) + '</td>'
        else:
            productCompTable = productCompTable + '<td>' + str(productComp['technical']['weights'][i]) + '</td>'
    #Governance
    productCompTable = productCompTable + '</tr>'
    productCompTable = productCompTable + '<tr><td>Governance Requirement Scorecard</td>'
    for i in range(len(productComp['governance']['weights'])):
        if (i in productComp['governance']['max']):
            productCompTable = productCompTable + '<td class="greenColumn">' + str(productComp['governance']['weights'][i]) + '</td>'
        else:
            productCompTable = productCompTable + '<td>' + str(productComp['governance']['weights'][i]) + '</td>'
    #Total
    productCompTable = productCompTable + '</tr>'
    productCompTable = productCompTable + '<tr><td>Total</td>'
    for i in range(len(productComp['total']['weights'])):
        if (i in productComp['total']['max']):
            productCompTable = productCompTable + '<td class="greenColumn">' + str(productComp['total']['weights'][i]) + '</td>'
        else:
            productCompTable = productCompTable + '<td>' + str(productComp['total']['weights'][i]) + '</td>'
    productCompTable = productCompTable + '</tbody></table>'
    # Replace int values in priorities and weights to readable values
    priorities = ['', 'Nice to have', 'Whish list', 'Based on Policy', 'Best Practice', 'Must have']
    weights = ['N/A', 'No', 'Partial', 'Yes']
    update_series = df[2].ix[df[1] != 'Subtotal:']
    for i in range(len(priorities)):
        update_series = update_series.replace(i, priorities[i])
    df[2].ix[df[1] != 'Subtotal:'] = update_series
    # Need add to fix situation when total value will be weights or priorities
    for j in range(3, len(df.iloc[0])):
        update_series = df[j].ix[df[1] != 'Subtotal:']
        for k in range(len(weights)):
            update_series = update_series.replace(k, weights[k])
        df[j].ix[df[1] != 'Subtotal:'] = update_series
    # Create an index of rows where subtotal located
    list_sub = []
    for index, row in df.iterrows():
        if row[1] == 'Subtotal:':
            list_sub.append(index)
    # Initialize table with second header
    data_html = df.iloc[1:2].to_html(header=False, index=False, sparsify=False)
    data_html = data_html.replace('<tr>', '<tr class=header>')
    # Fill html string with data
    i = 1
    replace_part = '</tbody>\n</table>'
    for sub_ in list_sub:
        # i is value from which create html, initial value is equal 1 because header was created before
        part_data_html = (df.iloc[i+1:sub_].to_html(header=False, index=False, sparsify=False)).replace(
            '<table border="1" class="dataframe">\n  <tbody>\n', '')
        data_html = data_html.replace(replace_part, part_data_html)
        # Append subtotal row
        data_html = data_html.replace(replace_part, append_total_html(df.iloc[sub_]))
        i = sub_
    # Append last row to html string
    data_html = data_html.replace(replace_part, append_total_html(df.iloc[-1]))
    # Add first header to html string
    full_html = data_html.replace('<tbody>\n', header_html)
    full_html = full_html.replace('<td>N/A</td>', '<td class="greyColumn">N/A</td>')
    full_html = full_html.replace('<td>Yes</td>', '<td class="greenColumn">Yes</td>')
    full_html = full_html.replace('<td>No</td>', '<td class="redColumn">No</td>')
    full_html = full_html.replace('<td>Partial</td>', '<td class="yellowColumn">Partial</td>')
    # Create a html file for converting
    env = Environment(
        loader=FileSystemLoader('templates'),
        autoescape=select_autoescape(['html', 'htm', 'xml'])
    )
    template = env.get_template("article_export.html")
    font_size = 11
    template_vars = {"article": article, "article_title": article_title, "data_export": full_html, "customer": customer, "chosenSolutions": chosenSolutions, "productCompTable": productCompTable, "date": article_date, "font_size": getFontSize(len(header_table))}
    rendered = template.render(template_vars)
    pdf_output = HTML(string=rendered).write_pdf(stylesheets=['static/css/export_pdf.css'])
    response = make_response(pdf_output)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename={}.pdf'.format(article_title)
    response.mimetype = 'application/pdf'

    for cl in clients:
        msg = Message("Xentaurs VerbNoun for " + vn['customer'], sender = 'vadim.e@lateco.net', recipients=[cl['email']])
        msg.html = "<style>body{font-family: \"Helvetica Neue\",Helvetica,Arial,sans-serif;font-size: 14px;line-height: 1.42857143;width:100%}</style><b>Xentaurs VerbNoun for " + cl['company'] + "</b><br/><br/>Visit Xentaurs VerbNoun Portal to see VerbNoun: <a href=\"" + vn['url'] + "\">" + vn['url'] + "</a><br/>Also there is VerbNoun in PDF format in the attachment.<br/><br/>This message has been sent automatically. Please, don't try to reply this email.<br/><br/>Best regards,<br/>Xentaurs VerbNoun Portal"
        #msg.html = "<style>table{font-family: \"Helvetica Neue\",Helvetica,Arial,sans-serif;font-size: 14px;line-height: 1.42857143;color: #333;width:100%}.table{border-collapse:collapse!important}.table td,.table .table-bordered td,.table-bordered th{border:1px solid #ddd!important}}th {background-color: #f2f2f2;}#totalRow {background-color: #f2f2f2;font-weight: bold;}</style><b>Xentaurs VerbNoun for " + cl['company'] + "</b><br/><br/>Visit Xentaurs VerbNoun Portal to see VerbNoun: <a href=\"" + vn['url'] + "\">" + vn['url'] + "</a><br/><br/>" + vn['table'] + "<br/><br/>This message has been sent automatically. Please, don't try to reply this email.<br/><br/>Best regards,<br/>Xentaurs VerbNoun Portal"
        msg.attach("{}.pdf".format(article_title), "application/pdf", pdf_output)
        #with app.open_resource(pdf_output) as fp:
            #msg.attach("filename={}.pdf".format(article_title), "application/pdf", fp.read())
        mail.send(msg)
    cursor.close()
    return json.dumps({}), 200, {'ContentType':'application/json'}

@app.route('/return-files/<path:filename>', methods=['GET', 'POST'])
def return_files_tut(filename):
    try:
        return send_file('/doc/'+filename, attachment_filename=filename)
    except Exception as e:
        return str(e)

@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/restore_password', methods=['GET', 'POST'])
def restore_password():
    if request.method == 'POST':
        cursor = mysql.connection.cursor()
        req = json.JSONDecoder().decode(request.data.decode('utf-8'))
        password = sha256_crypt.encrypt(str(req['password']))
        sql = "UPDATE users SET password=%s WHERE email=%s"
        cursor.execute(sql, (password, req['email']))
        cursor.execute("SELECT * FROM users WHERE email='" + req['email'] + "'")
        user = cursor.fetchone()
        msg = Message("Xentaurs VerbNoun Portal: Your Password Has Been Changed", sender = 'vadim.e@lateco.net', recipients=[user['email']])
        msg.html = "The password for your account on Xentaurs VerbNoun Portal has been changed.<br/><br/>Username: "+user['username']+ "<br/><b>New password: "+req['password']+"</b><br/><br/>This message has been sent automatically. Please, don't try to reply this email.<br/><br/>Best regards,<br/>Xentaurs VerbNoun Portal"
        mail.send(msg)
        mysql.connection.commit()
        cursor.close()
    return render_template('restore_password.html')

#@app.route('/sum_group')
def sum_group(df_grouped):
# Add subtotal row only on the third row where data located
    if df_grouped.iloc[0, 0] is '' or df_grouped.iloc[0, 0] == 'R#':
        return df_grouped
    else:
        lenStr = len(df_grouped.iloc[0])
        sum_row_list = []
        sum_row_list.append('')
        sum_row_list.append('Subtotal:')
        for i in range(2, lenStr):
            df_grouped[i] = df_grouped[i].apply(pd.to_numeric)
            if i == 2:
                sum_row_list.append(df_grouped[i].sum())
            else:
            # Calculate subtotal for one column and add to row of subtotals
                sum_value = (df_grouped.as_matrix([2]) * getWeight(df_grouped.as_matrix([i])) * 0.5).sum()
                if int(sum_value) == sum_value:
                    sum_value = int(sum_value)
                sum_row_list.append(sum_value)
            # Create a series from the row of subtotals
        sum_row = pd.Series(sum_row_list, index=df_grouped.columns)
        return df_grouped.append(sum_row, ignore_index=True)

def getWeight(index_array):
    res = []
    for row in index_array:
        subres = []
        for elem in row:
            if elem == 0:
                subres.append(0)
            elif elem == 1:
                subres.append(0)
            elif elem == 2:
                subres.append(1)
            elif elem == 3:
                subres.append(2)
        res.append(subres)
    return res

@app.route('/verbnoun_recipients/<int:id>', methods=['GET'])
@is_logged_in
def verbnoun_recipients(id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT customer FROM articles WHERE id=%s", [id])
    customer = cursor.fetchone()
    cursor.execute("SELECT username FROM users WHERE company='" + customer['customer'] + "' AND role = 'client'")
    recipients = cursor.fetchall()
    rec_arr = []
    for recipient in recipients:
        rec_arr.append(recipient['username'])
    recipientsJSON = json.JSONEncoder().encode(rec_arr)
    cursor.close()
    return json.dumps(recipientsJSON), 200, {'ContentType':'application/json'}

# Function hasn't used yet
#@app.route('/_color_if_subtotal')
def _color_if_subtotal(s):
    for val in s:
        if val == 'Subtotal:':
            return ['background-color: grey']
        else:
            ''

#@app.route('/append_total_html')
def append_total_html(ds):
    # Create a html string of subtotal with united first first two columns
    sub_rows = list(ds)[1:]
    sub_html = '<tr class=total><td colspan=2>{}</td>\n'.format(sub_rows[0])
    for sub_row in sub_rows[1:]:
        sub_html += '<td>' + str(sub_row) + '</td>\n'
    sub_html += '</tr>\n</tbody>\n</table>'
    return sub_html

@app.route('/customer_sector', methods = ['GET', 'POST'])
@is_logged_in
def customer_sector():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM customer_sector")
    sectors = cur.fetchall()
    u_s = cur.execute("SELECT name, sector FROM customers")
    used_sectors = cur.fetchall()
    cur.close()
    sectorsJSON = json.JSONEncoder().encode(sectors)
    usedSectorsJSON = json.JSONEncoder().encode(used_sectors)

    if request.method == 'POST':
        cursor = mysql.connection.cursor()
        newsectors = json.JSONDecoder().decode(request.data.decode('utf-8'))
        for sector in newsectors:
            cursor.execute("INSERT INTO customer_sector(name) VALUES ('" + sector + "')")
        mysql.connection.commit()
        cursor.close()

    if result > 0:
        return render_template('customer_sector.html', sectors = sectors, sectorsJSON = sectorsJSON, usedSectorsJSON = usedSectorsJSON)
    else:
        msg = 'No groups found.'
        return render_template('customer_sector.html', msg = msg)

@app.route('/add_sector', methods=['POST'])
@is_logged_in
def add_sector():
    cursor = mysql.connection.cursor()
    newsector = json.JSONDecoder().decode(request.data.decode('utf-8'))
    cursor.execute("INSERT INTO customer_sector(name) VALUES ('" + newsector['name'] + "')")
    mysql.connection.commit()
    result = cursor.execute("SELECT * FROM customer_sector")
    sectors = cursor.fetchall()
    cursor.close()
    return json.dumps(sectors), 200, {'ContentType':'application/json'}

@app.route('/delete_sector/<int:id>', methods=['GET'])
@is_logged_in
def delete_sector(id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM customer_sector WHERE id=" + str(id))
    mysql.connection.commit()
    result = cursor.execute("SELECT * FROM customer_sector")
    sectors = cursor.fetchall()
    cursor.close()
    return json.dumps(sectors), 200, {'ContentType':'application/json'}

@app.route('/public_clouds', methods = ['GET', 'POST'])
@is_logged_in
def public_clouds():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM public_clouds")
    clouds = cur.fetchall()
    raw_data_result = cur.execute('SELECT name, public_clouds FROM customers WHERE public_clouds <> ""')
    raw_data = cur.fetchall()
    used_clouds = []
    for c in raw_data:
        obj = {}
        obj['name'] = c['name']
        obj['clouds'] = json.loads(c['public_clouds'])
        used_clouds.append(obj)
    cur.close()
    cloudsJSON = json.JSONEncoder().encode(clouds)
    usedCloudsJSON = json.dumps(used_clouds)


    if request.method == 'POST':
        cursor = mysql.connection.cursor()
        newclouds = json.JSONDecoder().decode(request.data.decode('utf-8'))
        for cloud in newclouds:
            cursor.execute("INSERT INTO public_clouds(name) VALUES ('" + cloud + "')")
        mysql.connection.commit()
        cursor.close()

    if result > 0:
        return render_template('public_clouds.html', clouds = clouds, cloudsJSON = cloudsJSON, usedCloudsJSON = usedCloudsJSON)
    else:
        msg = 'No groups found.'
        return render_template('public_clouds.html', msg = msg)

@app.route('/add_cloud', methods=['POST'])
@is_logged_in
def add_cloud():
    cursor = mysql.connection.cursor()
    newcloud = json.JSONDecoder().decode(request.data.decode('utf-8'))
    cursor.execute("INSERT INTO public_clouds(name) VALUES ('" + newcloud['name'] + "')")
    mysql.connection.commit()
    result = cursor.execute("SELECT * FROM public_clouds")
    clouds = cursor.fetchall()
    cursor.close()
    return json.dumps(clouds), 200, {'ContentType':'application/json'}

@app.route('/delete_cloud/<int:id>', methods=['GET'])
@is_logged_in
def delete_cloud(id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM public_clouds WHERE id=" + str(id))
    mysql.connection.commit()
    result = cursor.execute("SELECT * FROM public_clouds")
    clouds = cursor.fetchall()
    cursor.close()
    return json.dumps(clouds), 200, {'ContentType':'application/json'}

@app.route('/project_types', methods = ['GET', 'POST'])
@is_logged_in
def project_types():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM project_types")
    types = cur.fetchall()
    u_t = cur.execute("SELECT name, project_type FROM customers")
    used_types = cur.fetchall()
    cur.close()
    typesJSON = json.JSONEncoder().encode(types)
    usedTypesJSON = json.JSONEncoder().encode(used_types)

    if request.method == 'POST':
        cursor = mysql.connection.cursor()
        newprojects = json.JSONDecoder().decode(request.data.decode('utf-8'))
        for project in newprojects:
            cursor.execute("INSERT INTO project_types(name) VALUES ('" + project + "')")
        mysql.connection.commit()
        cursor.close()

    if result > 0:
        return render_template('project_types.html', types = types, typesJSON = typesJSON, usedTypesJSON = usedTypesJSON)
    else:
        msg = 'No groups found.'
        return render_template('project_types.html', msg = msg)

@app.route('/add_project_type', methods=['POST'])
@is_logged_in
def add_project_type():
    cursor = mysql.connection.cursor()
    newtype = json.JSONDecoder().decode(request.data.decode('utf-8'))
    cursor.execute("INSERT INTO project_types(name) VALUES ('" + newtype['name'] + "')")
    mysql.connection.commit()
    result = cursor.execute("SELECT * FROM project_types")
    types = cursor.fetchall()
    cursor.close()
    return json.dumps(types), 200, {'ContentType':'application/json'}

@app.route('/delete_project_type/<int:id>', methods=['GET'])
@is_logged_in
def delete_project_type(id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM project_types WHERE id=" + str(id))
    mysql.connection.commit()
    result = cursor.execute("SELECT * FROM project_types")
    types = cursor.fetchall()
    cursor.close()
    return json.dumps(types), 200, {'ContentType':'application/json'}

@app.route('/edit_customer/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_customer(id):
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM customers WHERE id =" + str(id))
    customer = cur.fetchone()
    result = cur.execute("SELECT * FROM customer_sector")
    sectors = cur.fetchall()
    result = cur.execute("SELECT * FROM project_types")
    types = cur.fetchall()
    result = cur.execute("SELECT * FROM public_clouds")
    clouds = cur.fetchall()
    cur.close()
    customerJSON = json.JSONEncoder().encode(customer)
    sectorsJSON = json.JSONEncoder().encode(sectors)
    typesJSON = json.JSONEncoder().encode(types)
    cloudsJSON = json.JSONEncoder().encode(clouds)

    try:
        customer_clouds = json.JSONEncoder().encode(json.loads(customer['public_clouds']))
    except:
        customer_clouds = json.JSONEncoder().encode('[]')
    customer_sector = customer['sector']
    customer_type = customer['project_type']

    if request.method == 'POST':
        cursor = mysql.connection.cursor()
        customer = json.JSONDecoder().decode(request.data.decode('utf-8'))
        cursor.execute('UPDATE customers SET name="' + customer['name'] + '", comments="' + customer['comment'] + '", sector="' + customer['sector'] + '", project_type ="' + customer['type'] + '", emp_number=' + customer['empNumber'] + ', valuation='+ customer['valuation'] +', spend_it=' + customer['spend'] + ', deploy_speed=' + customer['speed'] + ', public_clouds=\'' + str(customer['clouds']) + '\' WHERE id=' + str(id))
        mysql.connection.commit()
        cursor.close()

    if result > 0:
        return render_template('edit_customer.html', customer = customer, sectors = sectors, types = types, clouds = clouds, customerJSON = customerJSON, sectorsJSON = sectorsJSON, typesJSON = typesJSON, cloudsJSON = cloudsJSON, customer_clouds = customer_clouds, customer_sector = customer_sector, customer_type = customer_type)
    else:
        msg = 'No groups found.'
        return render_template('edit_customer.html', msg = msg)

#if __name__ == '__main__':
#app.secret_key='secret123'
#    app.run(host='0.0.0.0', port=80, debug=False)
#app.run(host='0.0.0.0')
