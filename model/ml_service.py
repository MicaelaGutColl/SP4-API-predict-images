import time
import settings
import redis
import json
import os
from tensorflow.keras.applications import resnet50
from tensorflow.keras.preprocessing import image
import numpy as np

# Connect to Redis 
# Make use of settings.py module to get Redis settings like host, port, etc.
db = redis.Redis(
    host = settings.REDIS_IP,
    port = settings.REDIS_PORT,
    db = settings.REDIS_DB_ID,
    )


# Load ML model 
model = resnet50.ResNet50(include_top=True, weights="imagenet")



def predict(image_name):
    """
    Load image from the corresponding folder based on the image name
    received, then, run our ML model to get predictions.

    Parameters
    ----------
    image_name : str
        Image filename.

    Returns
    -------
    class_name, pred_probability : tuple(str, float)
        Model predicted class as a string and the corresponding confidence
        score as a number.
    """
    
    image_name = image.load_img(os.path.join(settings.UPLOAD_FOLDER, image_name), target_size=(224, 224))
    image_array = image.img_to_array(image_name)
    image_expand = np.expand_dims(image_array, axis=0)
    image_preproce = resnet50.preprocess_input(image_expand)
    preds_resnet50 = model.predict(image_preproce)
    preds_decode = resnet50.decode_predictions(preds_resnet50, top=1)
    class_name = preds_decode[0][0][1]
    pred_probability = round(float(preds_decode[0][0][2]), 4)
    
    return tuple([class_name, pred_probability])
    

def classify_process():
    """
    Loop indefinitely asking Redis for new jobs.
    When a new job arrives, takes it from the Redis queue, uses the loaded ML
    model to get predictions and stores the results back in Redis using
    the original job ID so other services can see it was processed and access
    the results.

    Load image from the corresponding folder based on the image name
    received, then, run our ML model to get predictions.
    """
    while True:
        _, data_json = db.brpop(settings.REDIS_QUEUE)
        data_dict = json.loads(data_json) # convert JSON str to a dict of Python
        prediction, score = predict(data_dict["image_name"])
        predict_dict = {"prediction":prediction , "score":score}
        db.set(data_dict["id"], json.dumps(predict_dict)) # serialize python objects to str
        
        # sleep for a bit at the end
        time.sleep(settings.SERVER_SLEEP)
        

if __name__ == "__main__":
    print("Launching ML service...")
    classify_process()
