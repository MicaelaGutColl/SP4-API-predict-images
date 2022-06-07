import json
import time
import uuid
import redis
import settings

# TODO
# Connect to Redis and assign to variable `db``
# Make use of settings.py module to get Redis settings like host, port, etc.

# setear la variable con la de redis
db = redis.Redis(
    host=settings.REDIS_IP, port=settings.REDIS_PORT, db=settings.REDIS_DB_ID
)
# assert db.ping() # si ping da false va a explotar, porque no te conectas a redis, si da True está ok!


def model_predict(image_name):
    """
    Receives an image name and queues the job into Redis.
    Will loop until getting the answer from our ML service.

    Parameters
    ----------
    image_name : str
        Name for the image uploaded by the user.

    Returns
    -------
    prediction, score : tuple(str, float)
        Model predicted class as a string and the corresponding confidence
        score as a number.
    """
    # Assign an unique ID for this job and add it to the queue.
    # We need to assing this ID because we must be able to keep track
    # of this particular job across all the services
    # TODO

    job_id = str(uuid.uuid4())

    # Create a dict with the job data we will send through Redis having the
    # following shape:
    # {
    #    "id": str,
    #    "image_name": str,
    # }
    # TODO
    job_data = {
        "id": job_id,
        "image_name": image_name,
    }

    #  Send the job to the model service using Redis
    # Hint: Using Redis `rpush()` function should be enough to accomplish this.
    # TODO
    db.rpush(settings.REDIS_QUEUE, json.dumps(job_data))
    # Loop until we received the response from our ML model
    while True:
        # Attempt to get model predictions using job_id
        #  Hint: Investigate how can we get a value using a key from Redis
        #  TODO
        # Sleep some time waiting for model results
        time.sleep(settings.API_SLEEP)
        if db.exists(job_id):
            output = db.get(job_id)  # obtengo de redis el resultado del modelo
            output_dict = json.loads(output)
            pred_class = output_dict["prediction"]
            pred_proba = output_dict["score"]
            # Don't forget to delete the job from Redis after we get the results!
            # Then exit the loop
            #  TODO
            db.delete(job_id)
            break
    return pred_class, pred_proba
