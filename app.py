import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, jsonify, send_file
from werkzeug.utils import secure_filename
from flask_pymongo import PyMongo
from utils.services import UserService
from utils.utilfuncs import allowed_file,generate_story

db_user = os.getenv("db_user")
db_pass = os.getenv("db_pass")
gemini_api = os.getenv("GEMINI_API_KEY")
app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Change in production

app.config['MONGO_URI'] = f"mongodb+srv://{db_user}:{db_pass}@artisans.s8y9gfm.mongodb.net/marketplace?retryWrites=true&w=majority"
mongo = PyMongo(app)


UPLOAD_FOLDER = 'uploads'
ALLOWED_IMG_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_3D_EXTENSIONS = {'glb', 'gltf', 'obj', 'stl'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

artisans = mongo.db["artisans"]
users = mongo.db["users"]
products = mongo.db["product_details"]






# @app.route('/uploads/<filename>')
# def uploaded_file(filename):
#     return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    try:
        # Retrieve the file from GridFS
        return mongo.send_file(filename)
    except Exception as e:
        return f"File not found: {e}", 404

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':

        try:
            # Get form data
            first_name = request.form.get('firstName')
            last_name = request.form.get('lastName')
            email = request.form.get('email')
            password = request.form.get('password')
            user_type = request.form.get('userType')
            craft_type = request.form.get(
                'craftType') if user_type == 'artisan' else None
            newsletter = 'newsletter' in request.form
            address = request.form.get('address')

            # Validate required fields
            if not all([first_name, last_name, email, password, user_type]):
                return jsonify({'error': 'All required fields must be filled'}), 400

            # Validate artisan craft type
            if user_type == 'artisan' and not craft_type:
                return jsonify({'error': 'Please select your craft specialty'}), 400

            # Check if user already exists in either collection
            existing_user, _ = UserService.find_user_by_email(email)
            if existing_user:
                return jsonify({'error': 'Email already registered'}), 400
            profile_pic = request.files.get('profile_pic')
            if profile_pic:
                profile_picname = secure_filename(
                    filename=profile_pic.filename)
                profile_pic_id = mongo.save_file(
                    filename=profile_picname, fileobj=profile_pic)
                # Prepare user data
                session["user_data"] = {
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email.lower(),  # Store email in lowercase
                    'password': password,
                    'profile_pic_id': profile_pic_id,
                    'address': address,
                    'user_type': user_type,
                    'newsletter': newsletter,
                    'is_active': True
                }

            else:
                flash("No file uploaded")
                return ('No image')
            if user_type == 'artisan':
                session["user_data"]['craft_type'] = craft_type
                return redirect('/artisan_signup')
            else:
                user_data = session["user_data"]
                users.insert_one(user_data)
                session['user'] = user_data['email']
                session.pop("user_data", None)
                return redirect(url_for('dashboard', user_type=user_type))
            # Create user in appropriate collection
            # user_id, collection_type = UserService.create_user(user_data)

        except Exception as e:
            app.logger.error(f"Signup error: {str(e)}")
            return jsonify({'error': 'An error occurred while creating your account'}), 500

    return render_template('signup.html')


@app.route('/artisan_signup', methods=['GET', 'POST'])
def artisan_signup():
    if "user_data" not in session:
        return redirect('/signup')
    if request.method == 'POST':
        data = request.form
        # file = request.files['profile_pic']
        # filename = secure_filename(file.filename)
        # # file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        # # Save file to GridFS
        # file_id = mongo.save_file(filename, file)
        artisan = {
            **session["user_data"],
            "address": data['address'],
            "skills": data['skills'],
            "bank_info": data.get('bank_info', '')
        }
        artisans.insert_one(artisan)
        session['artisan'] = artisan['email']
        session.pop("user_data", None)
        # return redirect(url_for('upload_product'))
        return redirect(url_for('dashboard', user_type='artisan'))
    return render_template('artisan_signup.html')


@app.route('/upload_product', methods=['GET', 'POST'])
def upload_product():
    if 'artisan' not in session:
        return redirect(url_for('artisan_signup'))
    if request.method == 'POST':
        data = request.form
        img_file = request.files['product_img']
        model_file = request.files['product_3dfile']

        img_filename = secure_filename(img_file.filename)
        if not allowed_file(img_filename, ALLOWED_IMG_EXTENSIONS):
            flash('Invalid image type. Allowed: png, jpg, jpeg, gif.')
            return redirect(request.url)
        # img_file.save(os.path.join(app.config['UPLOAD_FOLDER'], img_filename))
        model_filename = secure_filename(model_file.filename)
        if not allowed_file(model_filename, ALLOWED_3D_EXTENSIONS):
            flash('Invalid 3D model type. Allowed: glb, gltf, obj, stl.')
            return redirect(request.url)
        # model_file.save(os.path.join(
        #     app.config['UPLOAD_FOLDER'], model_filename))
        model_id = mongo.save_file(model_filename, model_file)
        img_id = mongo.save_file(img_file.filename, img_file,)
        story = generate_story(data['product_name'])
        customization = {
            "color": data.get('color_options', ''),
            "material": data.get('material_options', ''),
            "design": data.get('design_options', ''),
        }
        product = {
            "name": data['product_name'],
            "price": data['price'],
            "artisan_email": session['artisan'],
            "product_img": img_filename,
            "product_3dfile": model_filename,
            "product_img_id": img_id,
            "product_3dfile_id": model_id,
            "story": story,
            "customization": customization
        }
        products.insert_one(product)
        return redirect(url_for('product_list'))
    return render_template('upload_product.html')


@app.route('/dashboard/<user_type>')
def dashboard(user_type):
    # return "dashboard"
    if user_type == 'artisan':
        return redirect('/artisan/dashboard')
    else:
        return redirect('/user/dashboard')


@app.route('/user/dashboard')
def user_dashboard():
    user = UserService.find_user_by_email(session['user'])
    print(user)
    return render_template('user_dashboard.html', user=user)


@app.route('/artisan/dashboard')
def artisan_dashboard():
    return render_template('artisan_dashboard.html')
# @app.route('/user_signup/', methods=['GET', 'POST'])
# def user_signup(user_data):
#     if request.method == 'POST':
#         data = request.form
#         file = request.files['profile_pic']
#         filename = secure_filename(file.filename)
#         # file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
#         # Save file to GridFS and get the unique ID
#         fileid = mongo.save_file(filename, file)
#         user = {
#             **user_data,
#             "profile_pic": filename,
#             "profile_pic_id": fileid
#         }
#         users.insert_one(user)
#         session['user'] = user['email']
#         return redirect(url_for('product_list'))
#     return render_template('user_signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        for user in users:
            if user['email'] == email and user['password'] == password:
                session['user'] = email
                return redirect(url_for('product_list'))
        flash('Invalid credentials')
    return render_template('login.html')


@app.route('/products')
def product_list():
    return render_template('product_list.html', products=list(products.find()))


@app.route('/product/<int:idx>', methods=['GET', 'POST'])
def product_detail(idx):
    products_len = products.count_documents({})
    if idx < 0 or idx > products_len:
        flash('Product does not exist!')
        return redirect(url_for('product_list'))
    product = products.find().sort('_id', 1).skip(idx).next()
    if request.method == 'POST':
        # Placeholder for customization/payment
        flash('Order placed! Payment flow to be implemented.')
        return redirect(url_for('product_list'))
    return render_template('product_detail.html', product=product, idx=idx)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
