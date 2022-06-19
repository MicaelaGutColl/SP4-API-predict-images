import time
import os
import redis
import json
import settings
import numpy as np
from tensorflow.keras.applications import resnet50
from tensorflow.keras.preprocessing import image

# escuhca la queue siempre
#  

# Connect to Redis and assign to variable `db``
# Make use of settings.py module to get Redis settings like host, port, etc.
db = redis.Redis(
    host=settings.REDIS_IP, 
    port=settings.REDIS_PORT, 
    db=settings.REDIS_DB_ID
)


# Load your ML model and assign to variable `model`

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
    # TODO
    path_images = os.path.join(settings.UPLOAD_FOLDER, image_name) 
    img = image.load_img(path_images, target_size=(224, 224)) # guardo en una variable la imagen en un formato 224x224 cuadrada, solo toma el archivo, especificar antes el path
    #plt.imshow(img)
    x = image.img_to_array(img) #lo paso a x
    x = np.expand_dims(x, axis=0) # le expando las dim
    x = resnet50.preprocess_input(x) # meto en el modelo
    
    # Get predictions
    preds = model.predict(x)
    decode=resnet50.decode_predictions(preds, top=1)
    # la respuesta del modelo es una lista de listas de dict, porque puedo enviar una lista de imágeners a predecir
    predict_pic=decode[0][0][1]
    score_pic=decode[0][0][2]

    return predict_pic, round(float(score_pic),4)


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
        # Inside this loop you should add the code to:
        #   1. Take a new job from Redis
        #   2. Run your ML model on the given data
        #   3. Store model prediction in a dict with the following shape:
        #      {
        #         "prediction": str,
        #         "score": float,
        #      }
        #   4. Store the results on Redis using the original job ID as the key
        #      so the API can match the results it gets to the original job
        #      sent
        # Hint: You should be able to successfully implement the communication
        #       code with Redis making use of functions `brpop()` and `set()`.
        # TODO
        #data_json = db.brpop(settings.REDIS_QUEUE)[1] #brpop te tira dos valores, el primero es el queue y el otro es el value
        #buscamos la informaicón del queue
        _, data_json = db.brpop(settings.REDIS_QUEUE) #brpop te tira dos valores, el primero es el queue y el otro es el value 
        # Don't forget to sleep for a bit at the end
        # si recibo algo, que prediga, sinó que vaya al time sleep
        if data_json: 
            # cambiamos de str a diccionario
            data_dict = json.loads(data_json)

            # llamamos al modelo:
            model_predict, model_score = predict(data_dict['image_name'])

            # esto lo tenemos que mandar a través dle middleware a redis:
            predict_dict = {"prediction": model_predict, "score": model_score}
            
            # solo puede hacerlo una vez, redis
            db.set(data_dict['id'], json.dumps(predict_dict))

        time.sleep(settings.SERVER_SLEEP)

# constructructor llama a la fc 

if __name__ == "__main__":
    # Now launch process
    print("Launching ML service...")
    classify_process()
