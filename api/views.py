import utils
from middleware import model_predict
from os import path
import settings
from flask import (
    Blueprint,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
    jsonify
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
    When it receives an image from the UI, it also calls our ML model to
    get and display the predictions.
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

        #   1. Get an unique file name using utils.get_file_hash() function
        new_name = utils.get_file_hash(file)

        #   2. Store the image to disk using the new name
        file.save(path.join(settings.UPLOAD_FOLDER, new_name))

        #   3. Send the file to be processed by the `model` service
        predict, predict_score = model_predict(new_name)

        #   4. Update `context` dict with the corresponding values
        context = {
            "prediction": predict,
            "score": predict_score,
            "filename": new_name,
        }

        # Update `render_template()` parameters as needed
        return render_template(
            "index.html", filename=new_name, context=context
        )

    # File received but it isn't an image
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
    )


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
    rpse = {'success': False, 'prediction': None, 'score': None}

    bad_request = make_response(jsonify(rpse), 400)
    #   1. Check a file was sent and that file is an image
    if "file" not in request.files:
        return bad_request

    file = request.files["file"]
    
    if file.filename=="":
        return bad_request


    if utils.allowed_file(file.filename):

        #   2. Store the image to disk
        new_name = utils.get_file_hash(file)

        if not path.exists(path.join(settings.UPLOAD_FOLDER, new_name)):
            file.save(path.join(settings.UPLOAD_FOLDER, new_name))

        #   3. Send the file to be processed by the `model` service
        predict, predict_score = model_predict(new_name)

        #   4. Update and return `rpse` dict with the corresponding values
        rpse = {'success': True, 'prediction': predict, 'score': predict_score} 
        resp = make_response(jsonify(rpse), 200)

        return resp
    # If user sends an invalid request return default values HTTP 400 Bad Request code
    else:
        return bad_request
    
    


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
    # already provided in settings.py module
    report = request.form.get('report')

    if report!=None:

        with open(f"{settings.FEEDBACK_FILEPATH}", 'a+') as fp:
            fp.write(str(report) + "\n")

    return render_template("index.html")
