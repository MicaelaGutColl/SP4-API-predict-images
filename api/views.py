from fileinput import filename
import utils # module of the api
import settings # module of the api
from middleware import model_predict # module of the api
import os

# Contains the API endpoints

from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)


router = Blueprint("app_router", __name__, template_folder="templates")

@router.route("/", methods=["GET"]) 
def index():
    """
    Index endpoint, renders our HTML code.
    """
    return render_template("index.html") 


@router.route("/", methods=["POST"])
def upload_image():
    """
    Function used in our frontend so we can upload and show an image.
    When it receives an Uimage from the UI, it also calls our ML model to
    get and display the predictions.
    UI:(interfaz de usuario) es el conjunto de elementos de la pantalla 
    que permiten al usuario interactuar con una página web
    """ 
    
    # No file received, show basic UI
    if "file" not in request.files:
        flash("No file part")
        return redirect(request.url)

    # File received but no filename is provided, show basic UI
    file = request.files["file"]
    if file.filename == "":
        flash("No image selected for uploading")
        return redirect(request.url)

    # File received and it's an image, we must show it and get predictions
    if file and utils.allowed_file(file.filename):
        
        file_name = utils.get_file_hash(file) # 1
        if not os.path.exists(os.path.join(settings.UPLOAD_FOLDER, file_name)):
            file.save(os.path.join(settings.UPLOAD_FOLDER, file_name)) # 2 
        
        predict, score = model_predict(file_name) # 3
        predict = predict.replace("_"," ").title()
        score = round(score*100, 2)
        context = {  # 4
            "prediction": predict,
            "score": score,
            "filename": file_name,
        }
        
       
        return render_template(
            "index.html", filename=file_name, context=context
        )
    # File received and but it isn't an image
    else:
        flash("Allowed image types are -> png, jpg, jpeg, gif")
        return redirect(request.url)


@router.route("/display/<filename>")
def display_image(filename):
    """
    Display uploaded image in our UI.
    """
    return redirect(
        url_for("static", filename="uploads/" + filename), code=301
    ) # Generates a URL to the given endpoint with the method provided.


@router.route("/predict", methods=["POST"])
def predict():
    """
    Endpoint used to get predictions without need to access the UI.
                                    # esto significa que el method es POST
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
    
    if "file" in request.files:
        file = request.files["file"]
        if file and utils.allowed_file(file.filename):# 1
            file_name = utils.get_file_hash(file)
            if not os.path.exists(os.path.join(settings.UPLOAD_FOLDER, file_name)):
                file.save(os.path.join(settings.UPLOAD_FOLDER, file_name)) # 2 
            prediction, score = model_predict(file_name) # 3
            rpse = {"success": True, "prediction": prediction, "score": score} # 4

            return jsonify(rpse)
    
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
    # Get reported predictions from `report` key
    report = request.form.get("report")


    if report:
    # 'a': opens a file for appending at the end of the 
    # file without truncating it. Creates a new file if it does not exist.
        with open(settings.FEEDBACK_FILEPATH, "a") as feedback:
    # write: used to write into a file using the file object
            report = feedback.write(str(report)+ '\n')
            
    return render_template("index.html")
    
