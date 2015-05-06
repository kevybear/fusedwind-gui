# -*- coding: utf-8 -*-

import os

from flask import Flask, request, render_template, flash
from wtforms.widgets import TextArea
from flask_bootstrap import Bootstrap
from flask_appconfig import AppConfig
from flask_wtf import Form, RecaptchaField
from flask.ext.mail import Message, Mail

import re

from jinja2 import evalcontextfilter, Markup, escape

import yaml

app = Flask(__name__)
configfile=None
AppConfig(app, configfile)  # Flask-Appconfig is not necessary, but
                            # highly recommend =)
                            # https://github.com/mbr/flask-appconfig

mail = Mail()

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USE_SSL"] = True
app.config["MAIL_USERNAME"] = 'fractalflows@gmail.com'
app.config["MAIL_PASSWORD"] = 'emergence'
mail.init_app(app)

Bootstrap(app)
# in a real app, these should be configured through Flask-Appconfig
app.config['SECRET_KEY'] = 'devkey'

@app.route('/')
def hello():
    provider = str(os.environ.get('PROVIDER', 'world'))
    return render_template('index.html', form={'hello':'world'})



#from webcomponent import deploy, start_app, register_Component, webgui
from paraboloid import Paraboloid

from SEAMTower.SEAMTower import SEAMTower

from webcomponent import *
from flask_wtf.file import FileField
from werkzeug import secure_filename


def WebGUIForm(dic, run=False):
    """Automagically generate the form from a FUSED I/O dictionary.
    TODO:
    * Add type validators
    * Add low/high validators
    * Add units nice looking extension using 'input-group-addon'
     (http://getbootstrap.com/components/#input-groups)
    """
    #field_dict = {k:type_fields[v['type']](k, **prep_field(v)) for k,v in dic.iteritems()}
    #if run: # Add the submit button
    #    field_dict['submit'] = SubmitField("Send")

    # 9th level python magic to dynamically create classes, don't try it at home kiddo...
    #MyForm = type('magicform', (Form,), field_dict)

    class MyForm(Form):
        pass

    # sorting the keys alphabetically
    skeys = dic.keys()
    skeys.sort()
    for k in skeys:
        v = dic[k]
        setattr(MyForm, k, type_fields[v['type']](k, **prep_field(v)))

    if run: # Add the run button
        setattr(MyForm, 'submit', SubmitField("Run"))

    return MyForm

class FormLoadInputFile(Form):
    upload = FileField('Input File')
    load = SubmitField('Load Inputs')



def webgui(cpnt, app=None):
    cpname = cpnt.__class__.__name__
    if app == None:
        app = start_app(cpname)

    def myflask():
        io = traits2json(cpnt)
        form_load = FormLoadInputFile()
        form_inputs = WebGUIForm(io['inputs'], run=True)()
        form_outputs = WebGUIForm(io['outputs'])()
        if request.method == 'POST':
            inputs =  request.form.to_dict()
            ### TODO: make the right format instead of float
            try:
                filename = secure_filename(form_load.upload.data.filename)
                if filename is not None:
                    form_load.upload.data.save('uploads/' + filename)
                    with open('uploads/'+filename, 'r') as f:
                        inputs = yaml.load(f)
            except: # no files are passed, using the form instead
                pass

            for k in inputs.keys():
                if k in io['inputs']:
                    setattr(cpnt, k, json2type[io['inputs'][k]['type']](inputs[k]))

            cpnt.run()
            outputs = {k:getattr(cpnt,k) for k in io['outputs'].keys()}

            return render_template('webgui.html',
                        inputs=WebGUIForm(io['inputs'], run=True)(MultiDict(inputs)),
                        outputs=WebGUIForm(io['outputs'])(MultiDict(outputs)),
                        load=form_load,
                        name=cpname)
        # Publish the interface definition of the class
        return render_template('webgui.html', inputs=form_inputs, outputs=None, load=form_load, name=cpname)

    myflask.__name__ = cpname
    app.route('/'+cpname, methods=['GET', 'POST'])(myflask)
    return app


webgui(SEAMTower(10), app)


if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
