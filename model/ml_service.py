from tensorflow.keras.applications import resnet50
from tensorflow.keras.preprocessing import image
from tensorflow import config
import os
import numpy as np
import json
import time
import redis
import settings


db = redis.Redis(
    host=settings.REDIS_IP, port=settings.REDIS_PORT, db=settings.REDIS_DB_ID
)

# Prevent tensorflow to allocate the entire GPU
physical_devices = config.list_physical_devices("GPU")
try:
    config.experimental.set_memory_growth(physical_devices[0], True)
except:
    pass

model = resnet50.ResNet50(include_top=True, weights="imagenet")


def predict(image_names):
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
    images = []

    if type(image_names) == str:
        img_path = os.path.join(settings.UPLOAD_FOLDER, image_names)
        img = image.load_img(img_path, target_size=(224, 224))
        img = image.img_to_array(img)
        images.append(img)
        
    else:
        # Loading images and preprocess
        for image_name in image_names:
            img_path = os.path.join(settings.UPLOAD_FOLDER, image_name)
            img = image.load_img(img_path, target_size=(224, 224))
            img = image.img_to_array(img)
            images.append(img)

    images = np.array(images)
    images = resnet50.preprocess_input(images)

    # Get predictions
    preds = model.predict(images)
    preds = resnet50.decode_predictions(preds, top=1)

    class_names = []
    pred_probabilities = []

    for pred in preds:
        _, class_name, pred_probability = pred[0]
        pred_probability = round(float(pred_probability), 4)
        class_names.append(class_name)
        pred_probabilities.append(pred_probability)

    return class_names, pred_probabilities


def classify_process(batch_size=1, brpop_timeout=0.1):
    """
    Loop indefinitely asking Redis for new jobs.
    When a new job arrives, takes it from the Redis queue, uses the loaded ML
    model to get predictions and stores the results back in Redis using
    the original job ID so other services can see it was processed and access
    the results.
    """
    while True:
        jobs_data = []
        received_jobs = 0

        while received_jobs <= batch_size:
            job = db.brpop(settings.REDIS_QUEUE, timeout=brpop_timeout)

            if job is None and received_jobs == 0:
                continue
            elif job is None and received_jobs > 0:
                break

            _, job_data_str = job
            job_data = json.loads(job_data_str)
            jobs_data.append(job_data)
            received_jobs += 1

        image_names = []

        for job_element in jobs_data:
            image_names.append(job_element["image_name"])

        preds = predict(image_names)
        pred_classes, pred_scores = preds

        for job_element, pred_class, pred_score in zip(
            jobs_data, pred_classes, pred_scores
        ):
            pred_data = {"prediction": pred_class, "score": pred_score}
            pred_data_str = json.dumps(pred_data)
            db.set(job_element["id"], pred_data_str)

        time.sleep(settings.SERVER_SLEEP)


def first_prediction():
    """Make a fake first prediction when running the containers
    to avoid first time loading time of the model.
    """

    img_path = os.path.join("tests/dog.jpeg")
    img = image.load_img(img_path, target_size=(224, 224))
    img = image.img_to_array(img)
    img = np.expand_dims(img, axis=0)
    model.predict(img)


if __name__ == "__main__":
    # Now launch process
    print("Launching ML service...")
    first_prediction()
    classify_process(batch_size=10)
