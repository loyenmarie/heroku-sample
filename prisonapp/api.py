from prisonapp import *
from models import User, Comment, Visitation

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return jsonify ({'message':'token is missing!'}), 401

        try:
            data=jwt.decode(token, app.config['SECRET_KEY'])

            current_user=User.query.filter_by(public_id=data['public_id']).first()
        except:
            return jsonify({'message': 'token is invalid!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated


# START OF VISITOR API

@app.route('/api/register', methods=['POST'])
def register_user():
    data = request.get_json()
    hashed_password = generate_password_hash(data['password'], method='sha256')

    new_user = User(public_id=str(uuid.uuid4()), username=data['username'], password_hash=hashed_password, firstname=data['firstname'], middlename=data['middlename'],
                    lastname=data['lastname'], contact=data['contact'], address=data['address'], birthday=data['birthday'], prisoner=data['prisoner'], role_id=2, status=False,
                    age=data['age'])
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message':'Registered successfully!'})

@app.route('/api/login/', methods=['GET'])
def login():
    auth = request.authorization

    if not auth or not auth.username or not auth.password:
        return make_response('Could not verify', 401, {'WWW-Authenticate':'Basic realm = "Login required!"'})

    user = User.query.filter_by(username=auth.username).first()

    if not user:
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm = "Login required!"'})

    if check_password_hash(user.password_hash, auth.password):
        token = jwt.encode({'public_id':user.public_id, 'exp':datetime.datetime.utcnow()+datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])

        print 'Token generated!'
        return jsonify({'status':'ok', 'token': token.decode('UTF-8'), 'role_id':user.role_id, 'public_id':user.public_id,'message':'login successful!'})

@app.route('/api/user/visitation', methods=['POST'])
@token_required
def visitation(current_user):
    data = request.get_json()
    user = User.query.filter_by(public_id=data['public_id']).first()

    new_visit = Visitation(vId=int(user.id),nameP=data['nameP'],date=data['vDate'],numberOfVisitors=int(data['numV']), status='PENDING')
    db.session.add(new_visit)
    db.session.commit()

    return jsonify({ 'message' : 'Success!' })


@app.route('/api/user/comment', methods=['POST'])
@token_required
def post_comment(current_user):
    data = request.get_json()
    get_id = User.query.filter_by(public_id=data['public_id']).first()

    new_comment = Comment(uid=int(get_id.id), content=data['comment'])
    db.session.add(new_comment)
    db.session.commit()

    return jsonify({'message':'Comment submitted! Thank you for your opinion!'})


#END OF VISITOR API


#START OF CLERK API
@app.route('/api/clerk/get_users', methods=['GET'])
@token_required
def get_all_users(current_user):

    if current_user.role_id != '1':
        return jsonify ({'message':'Cannot perform that function!'})

    users = User.query.all()
    output = []

    for user in users:
        user_data = {}
        user_data['username'] = user.username
        output.append(user_data)

    return jsonify({ 'users':output })

@app.route('/api/clerk/visitor_data', methods=['GET'])
@token_required
def get_visitors(current_user):
    if current_user.role_id != '1':
        return jsonify ({'message':'Cannot perform that function!'})

    users = User.query.filter_by(role_id=2)

    res = []

    for user in users:
        user_data = {}
        user_data['firstname'] = user.firstname
        user_data['middlename'] = user.middlename
        user_data['lastname'] = user.lastname
        user_data['age'] = user.age
        user_data['contact'] = user.contact
        user_data['address'] = user.address
        user_data['birthday'] = user.birthday
        user_data['status'] = user.status
        user_data['id'] = user.id
        res.append(user_data)

    return jsonify({'status': 'ok', 'entries': res, 'count': len(res)})


@app.route('/api/clerk/account_accept', methods=['POST'])
@token_required
def accept(current_user):
    data = request.get_json()
    user = User.query.filter_by(id=data['user_id']).first()

    user.status = bool(1)
    print user.id
    db.session.commit()

    return jsonify({'message':'Account Verified!'})

@app.route('/api/clerk/manage_requests', methods=['GET'])
@token_required
def manage_requests(current_user):

    if current_user.role_id != '1':
        return jsonify ({'message':'Cannot perform that function!'})

    visitations = Visitation.query.all()
    res = []

    for visitation in visitations:
        user_data = {}
        user_data['vId'] = visitation.vId
        user_data['nameP'] = visitation.nameP
        user_data['date'] = visitation.date
        # user_data['time'] = visitations.time
        user_data['status'] = visitation.status

        res.append(user_data)

    return jsonify({'status': 'ok', 'entries': res, 'count': len(res)})


#END OF CLERK API
