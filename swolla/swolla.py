import os
import sys
import datetime
import smtplib
from urllib import unquote
from urllib2 import urlopen
from email.mime.text import MIMEText
from dwolla import *
import twilio
from twilio.rest import TwilioRestClient
from twilio import twiml
from uuid import uuid4
import random
import time
from decimal import Decimal

import model

import psycopg2
from flask import Blueprint, Flask, render_template, url_for, redirect, request, \
        session, g, send_file, jsonify, Response, flash
from functools import wraps
from psycopg2.extras import DictCursor
from jinja2 import TemplateNotFound

import default_settings

instance_path = os.path.expanduser('~/swolla_instance/')

app = Flask(__name__, instance_path=instance_path)
app.config.from_object('swolla.default_settings')
external_cfg = os.path.join(app.instance_path, 'application.cfg')
app.config.from_pyfile(external_cfg, silent=True)
app.TRAP_BAD_REQUEST_ERRORS = True

dwolla = DwollaClientApp(app.config['DWOLLA_KEY'],
        app.config['DWOLLA_SECRET'])
twilio_client = TwilioRestClient(app.config['TWILIO_ACCOUNT_SID'], 
        app.config['TWILIO_AUTH_TOKEN'])

@app.before_request
def before_request():
    g.db_conn = psycopg2.connect(app.config['DATABASE_CONNECTION'])
    model.User.set_conn(g.db_conn)
    model.Contact.set_conn(g.db_conn)

@app.teardown_request
def teardown_request(exception):
    g.db_conn.close()

@app.route('/')
def home():
    if 'user' in session:
        user_cred = model.User.get(session['user']['Id'])
    else:
        user_cred = None
    return render_template('home.html', user_cred=user_cred)

@app.route("/link")
def link():
    oauth_return_url = url_for('dwolla_oauth_return', _external=True) # Point back to this file/URL
    permissions = 'Send|Transactions|Balance|AccountInfoFull|Contacts'
    authUrl = dwolla.init_oauth_url(scope=permissions, redirect_uri=oauth_return_url)
    #return 'To begin the OAuth process, send the user off to <a href="%s">%s</a>' % (authUrl, authUrl)
    return redirect(authUrl)

@app.route("/dwolla/oauth_return")
def dwolla_oauth_return():
    oauth_return_url = url_for('dwolla_oauth_return', _external=True) # Point back to this file/URL
    code = request.args.get("code")
    token = dwolla.get_oauth_token(code, redirect_uri=oauth_return_url)
    user = DwollaUser(token)
    account_info = user.get_account_info()
    existing = model.User.get(account_info['Id'])
    if existing:
        existing['code'] = code
        existing['access_token'] = token
        existing.save()
        user_cred = existing
    else:
        user_cred = model.User.new({'user_id': account_info['Id'], 'code': code, 'access_token': token})
    session['user_id'] = user_cred.user_id
    session['user'] = account_info
    return redirect(url_for('home'))

@app.route("/sms", methods=["POST"])
def sms():
    form = request.form
    sys.stderr.write("%s" % form)
    body = form['Body']
    values = body.split(' ')
    resp = twiml.Response()
    try:
        sys.stderr.write("got to here\n")
        amount = Decimal(values[0])

        pin  = values[1]
        contact = ' '.join(values[2:])
        # remove +1
        from_num = form['From'][2:]
        user = model.User.where({'phone_number': model.normalize_phone_number(from_num)})
        if len(user) == 0:
            resp.sms("Hey, I don't know you. Can you go to " + \
                "http://swolla.derekarnold.net and log in with Dwolla?")
        else:
            user = user[0]
            found_contact = model.Contact.where({
                'user_id': user.user_id,
                'short_name': contact
            })
            if len(found_contact) == 0:
                resp.sms("I can't find a contact with that short name. Sorry!")
            else:
                found_contact = found_contact[0]
                # pay the person
                try:
                    sys.stderr.write("found contact\n")
                    dwolla_user = DwollaUser(user.access_token)
                    if not dwolla_user:
                        resp.sms("Couldn't find a Dwolla user for that short name.")
                    else:
                        try:
                            sys.stderr.write("trying to pay\n")
                            transaction_id = dwolla_user.send_funds(
                                amount.to_eng_string(), '812-713-9234', pin,
                                notes="Payment from Swolla")
                            if not transaction_id:
                                resp.sms("Couldn't send funds. Check your PIN" + \
                                    "and try again")
                            else:
                                # Success
                                trans = dwolla_user.get_transaction(transaction_id)
                                sys.stderr.write("%s" % trans)
                                resp.sms("""Your payment is on its way. Check your""" + \
                                    """ Dwolla account for further status info. Thanks!""")
                        except Exception as e:
                            sys.stderr.write("%s" % e)
                            resp.sms("Couldn't send funds. Check your PIN " + \
                                "and try again.")

                except Exception as e:
                    sys.stderr.write("%s" % e)
                    resp.sms("Couldn't find a Dwolla user for that short name.")

    except Exception as e:
        sys.stderr.write("%s" % e)
        resp.sms("Sorry, I couldn't parse that. Could you send that again " + \
            "in the format \"123.45 PIN short name\"?")
    return str(resp)

@app.route('/set-phone', methods=["POST"])
def set_phone():
    if 'user' not in session:
        return '500', 500
    form = request.form
    if not form['phone']:
        flash("No phone number entered.", "error")
        return redirect('home')
    user_cred = model.User.get(session['user']['Id'])
    user_cred.phone_number = model.normalize_phone_number(form['phone'])
    user_cred.save()
    flash("Your phone number has been updated.")
    return redirect(url_for('home'))


@app.route("/contacts", methods=["GET", "POST"])
def contacts():
    if 'user' not in session:
        return redirect('link')
    else:
        user_cred = model.User.get(session['user']['Id'])
        user = DwollaUser(user_cred.access_token)
        contacts = user.get_contacts()
        db_contacts = model.Contact.where({
            'user_id': session['user']['Id']
            })
        short_names = {}
        for dbc in db_contacts:
            if dbc.short_name is not None and len(dbc.short_name) > 0:
                short_names[dbc.contact_id] = dbc.short_name
        if request.method == 'POST':
            # add contact name
            form = request.form
            existing = model.Contact.where({
                'user_id': session['user']['Id'],
                'short_name': form['short_name']
                })
            if len(existing) > 0:
                # already exists
                flash("This short name already exists. Please choose another.")
                return render_template('contacts.html', contacts=contacts,
                    short_names=short_names)
            other_existing = model.Contact.where({
                'user_id': session['user']['Id'],
                'contact_id': form['contact_id']
                })
            if len(other_existing) > 0:
                # update existing
                other_existing[0].short_name = form['short_name']
                other_existing[0].save()
            else:
                new_contact = model.Contact.new({
                    'contact_id': form['contact_id'],
                    'short_name': form['short_name'],
                    'user_id': session['user']['Id']
                    })
            contacts = user.get_contacts()
            flash('Contact short name updated.')
            return render_template('contacts.html', contacts=contacts,
                short_names=short_names)
            
        else:
            return render_template('contacts.html', contacts=contacts,
                short_names=short_names)

@app.route('/logout')
def logout():
    if 'user' in session:
        del(session['user'])
    if 'user_id' in session:
        del(session['user_id'])
    return redirect(url_for('home'))



app.secret_key = app.config['SECRET']
app.debug = True

if __name__ == '__main__':
    app.run()

