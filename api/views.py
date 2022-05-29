import utils
import settings
import os
import middleware

from flask import (
    Blueprint,          # blueprint es una forma de dividir el codigo.
    flash,              # es el print de flask.
    redirect,           # para llevar el usuario de una pagina a otra.
    render_template,    # para poder escribir html.
    request,            # se para en el puerto y se obtiene la informacion que puede obtener de cada ruta (cada endpoint)
    url_for,            # Esta operación recibe como parámetro el nombre del método y nos devuelve la ruta.
)

router = Blueprint("app_router", __name__, template_folder="templates")

@router.route("/", methods=["GET"])
def index():
    """
    Index endpoint, renders our HTML code.
    """
    return render_template("index.html")

#endopoint to upload de image we want to identify 
@router.route("/", methods=["POST"]) 
def upload_image():
    """
    Function used in our frontend so we can upload and show an image.
    When it receives an image from the UI, 
    it also calls our ML model to
    get and display the predictions.
    
    """
    
    # UI --> user interface
    # No file received, show basic UI

    if "file" not in request.files:
        flash("No file part")
        return redirect(request.url) # if there is no file --> se queda en el mismo lugar?

    # File received but no filename is provided, show basic UI
    file = request.files["file"]
    if file.filename == "":
        flash("No image selected for uploading")
        return redirect(request.url)

    # File received and it's an image, we must show it and get predictions
    if file and utils.allowed_file(file.filename):
       
        # 1. Get an unique file name using utils.get_file_hash() function
        # usamos hash para que no se repita el nombre del archivo
        new_name = utils.get_file_hash(file) 
        
        # 2. Store the image to disk using the new name
        if os.path.lexist(new_name.path) == False:
            file.save(os.path.join(settings.UPLOAD_FOLDER, new_file))
        #   3. Send the file to be processed by the `model` service
        #      Hint: Use middleware.model_predict() for sending jobs to model
        #            service using Redis.
        predict, score = middleware.model_predict(new_name)

        #4. Update `context` dict with the corresponding values                     
        
        context = {
            "prediction": predict,
            "score": score,
            "filename": new_name,
        }

        # Update `render_template()` parameters as needed
        # TODO
        return render_template(
            "index.html", filename = new_name, context = context
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
    #   1. Check a file was sent and that file is an image:
    file = request.files["file"]
    if file and utils.allowed_file(file.filename):
       
        new_name = utils.get_file_hash(file)
    #   2. Store the image to disk
        if os.path.lexist(new_name.path) == False:
            file.save(os.path.join(settings.UPLOAD_FOLDER, new_file))
    
    #   3. Send the file to be processed by the `model` service
    #      Hint: Use middleware.model_predict() for sending jobs to model
    #            service using Redis.    
        predict, score = middleware.model_predict(new_name)

    #   4. Update and return `rpse` dict with the corresponding values
    # If user sends an invalid request (e.g. no file provided) this endpoint
    # should return `rpse` dict with default values HTTP 400 Bad Request code

        rpse = {
                "success":      True, 
                "prediction":   predict, 
                "score":        score
                }
        
       
    # File received and but it isn't an image
    else:
        flash("Allowed image types are -> png, jpg, jpeg, gif")
        rpse = {
                "success":      'HTTP 400 Bad Request code', 
                "prediction":   'HTTP 400 Bad Request code', 
                "score":        'HTTP 400 Bad Request code'
                }
        return rpse
    


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

    # Store the reported data to a file on the corresponding path
    # already provided in settings.py module
    # We will store user feedback on this file
    #FEEDBACK_FILEPATH = "feedback/feedback"
    
    # path = os.path.basename(settings.FEEDBACK_FILEPATH)

    try:
        os.makedirs(os.path.basename(settings.FEEDBACK_FILEPATH), exist_ok=True)
        print("The directory was created successfully" )
    except OSError as error:
        print("The directory can not be created")
    
    
    return render_template("index.html")
