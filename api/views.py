import utils
from flask import current_app, flash, jsonify, make_response, redirect, request, url_for
import os
from middleware import model_predict
import settings


from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

# GET & POST
# ej: https://www.pythondiario.com/articulos.html?tag=Flask

# POST: envía la información ocultándola del usuario 
# ej: https://www.pythondiario.com/articulos.html


router = Blueprint("app_router", __name__, template_folder="templates")

# get() recibe como parametro lo que queremos recuperar
@router.route("/", methods=["GET"])
def index():
    """
    Index endpoint, renders our HTML code.
    """
    return render_template("index.html") # renderizar un template con un formulario


@router.route("/", methods=["POST"])
def upload_image():
    """
    Function used in our frontend so we can upload and show an image.
    When it receives an image from the UI, it also calls our ML model to
    get and display the predictions.
    # REQUEST
    To access incoming request data, you can use the global request object. 
    Flask parses incoming request data
    for you and gives you access to it through that global object.
    The request object is an instance of a Request  
    """
    # No file received, show basic UI
    # si no es tipo file  --- muestra lo de flask
    if "file" not in request.files:
        flash("No file part")
        return redirect(request.url)

    # File received but no filename is provided, show basic UI
    # si es tipo file y no hay archivo
    file = request.files["file"]
    if file.filename == "":
        flash("No image selected for uploading")
        return redirect(request.url)
    # Flashes a message to the next request. In order to remove the flashed message
    # from the session and to display it to the user, 
    # the template has to call get_flashed_messages (SE USA EN HTML)


    # File received and it's an image, we must show it and get predictions
    if file and utils.allowed_file(file.filename):
        #   1. Get an unique file name using utils.get_file_hash() function
        # https://flask.palletsprojects.com/en/1.1.x/patterns/fileuploads/        
        newfile = utils.get_file_hash(file)

        #   2. Store image (os.path so as not to remplace images if they are the same)
        if not os.path.exists(os.path.join(settings.UPLOAD_FOLDER, newfile)):
            file.save(os.path.join(settings.UPLOAD_FOLDER, newfile)) 
        # Join two or more pathname components, inserting '/' as needed. 
        # If any component is an absolute path, all previous 
        # path components will be discarded.
        # An empty last part will result in a path that ends with a separator
        
        #   3. Send the file to be processed by the `model` service
        #      Hint: Use middleware.model_predict() for sending jobs to model
        #            service using Redis.
        model_pred, model_score = model_predict(newfile)
        model_pred = model_pred.replace("_"," ").title()        
        #   4. Update `context` dict with the corresponding values
        model_score = round(model_score*100, 2)
        context = {
            "prediction": model_pred,
            "score": model_score,
            "filename": newfile

        }        
        
        # Update `render_template()` parameters as needed


        return render_template("index.html", filename=newfile, context=context)

    # File received and but it isn't an image
    else:
        flash("Allowed image types are -> png, jpg, jpeg, gif")
        return redirect(request.url)


@router.route("/display/<filename>")
def display_image(filename):
    """
    Display uploaded image in our UI.
    """
    return redirect(url_for("static", filename="uploads/" + filename), code=301)


@router.route("/predict", methods=["POST"])
def predict():
    """
    Endpoint used to get predictions without need to access the UI.

    Parameters
    ----------
    file : str
        Input image we want to get predictions from.

    Returns
    -------
    flask.Response
        JSON response from our API having the following format:
            {
                "success": bool,
                "prediction": str,
                "score": float,
            }

        - "success" will be True if the input file is valid and we get a
          prediction from our ML model.
        - "prediction" model predicted class as string.
        - "score" model confidence score for the predicted class as float.
    """
    # To correctly implement this endpoint you should:
    #   1. Check a file was sent and that file is an image
    # mensaje de salida 
    rpse = {"success": False, "prediction": None, "score": None}    
    
    # si no recibe archivo
    if "file" not in request.files:
        return jsonify(rpse), 400 #400  status code

    # Recibe una imagen pero no es tipo "file"
    file = request.files["file"]
    if file.filename == "":
        return jsonify(rpse), 400 #400  status code

    #   2. Store the image to disk
    # File received and it's an image, we must show it and get predictions
    if file and utils.allowed_file(file.filename):
        #   1. Get an unique file name using utils.get_file_hash() function
        # https://flask.palletsprojects.com/en/1.1.x/patterns/fileuploads/        
        newfile = utils.get_file_hash(file)

        #   2. Store image (os.path so as not to remplace images if they are the same)
        if os.path.exists(newfile) == False: 
            if not os.path.exists(os.path.join(settings.UPLOAD_FOLDER, newfile)):
                file.save(os.path.join(settings.UPLOAD_FOLDER, newfile)) 
        #   3. Send the file to be processed by the `model` service
        #      Hint: Use middleware.model_predict() for sending jobs to model
        #            service using Redis.
            model_pred, model_score = model_predict(newfile) 
            rpse = {"success": True, "prediction": model_pred, "score": model_score}       
        #   4. Update `context` dict with the corresponding values
        context_2 = {
            "success": True,
            "prediction": model_pred,
            "score": model_score
        }        
        
        # Update `render_template()` parameters as needed
        # TODO

        return jsonify(context_2), 200
    #if it is none of the above optionss
    rpse = {"success": False, "prediction": None, "score": None}
    return jsonify(rpse), 400

@router.route("/feedback", methods=["GET", "POST"])
def feedback():
    """
    Store feedback from users about wrong predictions on a text file.
    Parameters
    ----------
    report : request.form
        Feedback given by the user with the following JSON format:
            {
                "filename": str,
                "prediction": str,
                "score": float
            }
        - "filename" corresponds to the image used stored in the uploads
          folder.
        - "prediction" is the model predicted class as string reported as
          incorrect.
        - "score" model confidence score for the predicted class as float.
    """
    # Get reported predictions from `report` key
    report = request.form.get("report")
    # Store the reported data to a file on the corresponding path
    # already provided in settings.py module

    with open(settings.FEEDBACK_FILEPATH, "a+") as feedback:
        # parametro 'a+' - (a) si no existe el archivo, lo crea. si existe lo abre y lo lee
        feedback.write(str(report) + "\n")

    # Alan
    # feedback = open(settings.FEEDBACK_FILEPATH, "a+")
    # feedback.write(str(report) + '\n')
    # feedback.close()

    return render_template("index.html")