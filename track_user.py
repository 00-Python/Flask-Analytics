from flask import Flask, request, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "secret key"
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

db = SQLAlchemy(app)

class VisitsLog(db.Model):
    log_id = db.Column(db.Integer, primary_key=True)
    no_of_visits = db.Column(db.Integer)
    ip_address = db.Column(db.String(20))
    requested_url = db.Column(db.Text)
    referer_page = db.Column(db.Text)
    page_name = db.Column(db.Text)
    query_string = db.Column(db.Text)
    user_agent = db.Column(db.Text)
    is_unique = db.Column(db.Boolean, default=False)
    access_date = db.Column(db.DateTime, default=db.func.current_timestamp())

@app.before_request
def track_visitor():
    if not is_tracking_allowed():
        return
    else:
        ip_address = request.remote_addr
        requested_url = request.url
        referer_page = request.referrer
        page_name = request.path
        query_string = request.query_string
        user_agent = request.user_agent.string

        if track_session():
            log_id = session['log_id'] if 'log_id' in session else 0
            no_of_visits = session.get('no_of_visits')
            current_page = request.url
            previous_page = session['current_page'] if 'current_page' in session else ''

            if previous_page != current_page:
                log_visitor(ip_address, requested_url, referer_page, page_name, query_string, user_agent, no_of_visits)
        else:
            session.modified = True

            log_id = log_visitor(ip_address, requested_url, referer_page, page_name, query_string, user_agent)

            if log_id > 0:
                visit = VisitsLog.query.order_by(VisitsLog.no_of_visits.desc()).first()

                count = 0
                if visit:
                    count += 1
                else:
                    count = 1

                visit = VisitsLog.query.get(log_id)
                visit.no_of_visits = count
                db.session.commit()

                session['track_session'] = True
                session['no_of_visits'] = count
                session['current_page'] = requested_url
            else:
                session['track_session'] = False

def log_visitor(ip_address, requested_url, referer_page, page_name, query_string, user_agent, no_of_visits=None):
    # Calculate the number of visits for the current IP address
    no_of_visits = VisitsLog.query.filter_by(ip_address=ip_address).count()

    visit = VisitsLog(
        no_of_visits=no_of_visits,
        ip_address=ip_address,
        requested_url=requested_url,
        referer_page=referer_page,
        page_name=page_name,
        query_string=query_string,  # removed .decode('utf-8')
        user_agent=user_agent
    )

    try:
        db.session.add(visit)
        db.session.commit()

        return visit.log_id
    except Exception as e:
        print(e)

@app.route('/')
def home():
    return jsonify({'msg': 'hello'})

@app.route('/other')
def other():
    return '<a href="/">Click here</a>'


@app.route('/visits', methods=['GET'])
def get_visits():
    visits = VisitsLog.query.all()
    output = []
    for visit in visits:
        visit_data = {
            'log_id': visit.log_id, 
            'no_of_visits': visit.no_of_visits, 
            'ip_address': visit.ip_address, 
            'requested_url': visit.requested_url, 
            'referer_page': visit.referer_page, 
            'page_name': visit.page_name, 
            'query_string': visit.query_string.decode('utf-8') if visit.query_string else None, 
            'user_agent': visit.user_agent, 
            'is_unique': visit.is_unique, 
            'access_date': visit.access_date
        }
        output.append(visit_data)
    return jsonify({'visits': output})




def is_tracking_allowed():
    # Add your logic here to determine if tracking is allowed
    return True

def track_session():
    # Add your logic here to determine if session tracking is enabled
    return True

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run()

