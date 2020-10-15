from flask import render_template
from flask_moment import datetime
from . import exam


@exam.route('/')
def exam():
    now = datetime.utcnow()
    print(now)
    # if now
    return render_template('exam.html')
